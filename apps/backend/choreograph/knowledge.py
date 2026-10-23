"""Bounded LlamaIndex adapter over the application's authorized pgvector schema."""
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode
from pydantic import PrivateAttr
from sqlalchemy import delete, or_, select, text
from sqlalchemy.orm import Session, defer

from .ai_admission import FAKE_SPEC, EmbeddingSpec, ProviderResult, SafeUsage
from .errors import DomainError
from .models import Chunk, DocumentVersion, EmbeddingProfile, Manifest

PACK=Path(__file__).resolve().parents[3]/'assets'/'knowledge'
SLOTS=('service','preparation','access','changes','safety','questions')
STOP=set(['a', 'an', 'the', 'and', 'or', 'of', 'in', 'on', 'to', 'for', 'is', 'are', 'do', 'does', 'i', 'my', 'we', 'you', 'your', 'me', 'can', 'with', 'it', 'this', 'that', 'what', 'how', 'about', 'have', 'be', 'at', 'as', 'our', 'will', 'when'])
SYNONYMS={'cats':'pet','cat':'pet','dogs':'pet','dog':'pet','pets':'pet','vacuuming':'vacuum','vacuumed':'vacuum',
          'carpets':'carpet','rugs':'carpet','shampooing':'shampoo','products':'product','supplies':'product',
          'unscented':'fragrance','scent':'fragrance','smell':'fragrance','scents':'fragrance','allergies':'allergy',
          'reschedule':'change','cancellations':'cancel','cancelling':'cancel','cancelled':'cancel','methods':'method',
          'kittens':'pet','feline':'pet','pooch':'pet','shampooed':'shampoo','cleaning':'clean','cleaners':'cleaner'}
SYNONYMS.update({'brings':'bring','services':'service','cancellation':'cancel','rescheduling':'change','vacuum':'vacuum','methods':'method'})


def terms(text):
    return [SYNONYMS.get(token,token) for token in re.findall(r'[a-z]{2,}',text.lower()) if token not in STOP]


class FakeEmbedding(BaseEmbedding):
    """Deterministic local fixture; never presented as semantic provider quality."""
    model_name:str='fake-hash-64-v2'
    _calls:int=PrivateAttr(default=0)
    _spec:EmbeddingSpec=PrivateAttr(default=FAKE_SPEC)
    def __init__(self,spec=FAKE_SPEC,**kwargs):
        if spec.provider!='fake' or spec.dimensions!=64:raise ValueError('FAKE_EMBEDDING_SPEC_INVALID')
        super().__init__(model_name=spec.model,**kwargs);self._spec=spec
    @property
    def spec(self):return self._spec
    def with_admission(self,admission):return self
    def close(self):pass
    def _vector(self,text):
        self._calls+=1;vector=[0.0]*64
        for token in terms(text):
            value=int.from_bytes(hashlib.sha256(token.encode()).digest()[:4],'big')
            vector[value%64]+=1.0 if value&64 else -1.0
        norm=math.sqrt(sum(v*v for v in vector)) or 1
        return [v/norm for v in vector]
    def _get_text_embedding(self,text):return self._vector(text)
    def _get_query_embedding(self,text):return self._vector(text)
    async def _aget_query_embedding(self,text):return self._vector(text)


def validate_vector(vector,spec):
    if (not isinstance(vector,list) or len(vector)!=spec.dimensions or
            any(type(value) not in (int,float) or not math.isfinite(value) for value in vector) or
            (spec.provider!='fake' and not any(vector))):
        raise DomainError('EMBEDDING_FORMAT','The document could not be indexed. Try again later.',503)
    return [float(value) for value in vector]


class OpenAIEmbedding(BaseEmbedding):
    """The existing LlamaIndex interface with explicit finite admission per batch."""
    _spec:EmbeddingSpec=PrivateAttr()
    _client:object=PrivateAttr()
    _tokenizer:object=PrivateAttr()
    _admission:object=PrivateAttr(default=None)
    _batch:int=PrivateAttr(default=0)
    def __init__(self,spec,*,api_key=None,client=None,authorized=False,admission=None,tokenizer=None):
        if spec.provider!='openai' or spec.chunker!='llama-token-section-v4' or not authorized or not hasattr(tokenizer,'encode'):
            raise ValueError('LIVE_EMBEDDING_NOT_CONFIGURED')
        if client is None:
            if not api_key:raise ValueError('LIVE_EMBEDDING_NOT_CONFIGURED')
            from openai import OpenAI

            from .providers import PROVIDER_TIMEOUT, BoundedOpenAIClient
            client=OpenAI(api_key=api_key,base_url='https://api.openai.com/v1',organization='',project='',
                          admin_api_key='',webhook_secret='',max_retries=0,timeout=PROVIDER_TIMEOUT,
                          http_client=BoundedOpenAIClient(response_bytes=524_288))
            client._custom_headers={}
        super().__init__(model_name=spec.model,embed_batch_size=4)
        self._spec,self._client,self._tokenizer,self._admission=spec,client,tokenizer,admission
    @property
    def spec(self):return self._spec
    def with_admission(self,admission):
        return OpenAIEmbedding(self.spec,client=self._client,authorized=True,admission=admission,tokenizer=self._tokenizer)
    def close(self):self._client.close()
    def get_text_embedding_batch(self,texts,**kwargs):
        # BaseEmbedding otherwise divides first, concealing an invalid later
        # batch until earlier batches have already consumed provider allowance.
        if (not texts or len(texts)>64 or any(not isinstance(value,str) or not value.strip() or
                not 0<len(self._tokenizer.encode(value))<=8192 for value in texts)):
            raise DomainError('EMBEDDING_INPUT','Use a shorter document or question.',422)
        return super().get_text_embedding_batch(texts,**kwargs)
    def _embed(self,texts,phase):
        counts=[len(self._tokenizer.encode(value)) for value in texts]
        if not texts or len(texts)>64 or any(not value.strip() for value in texts) or any(not 0<count<=8192 for count in counts):
            raise DomainError('EMBEDDING_INPUT','Use a shorter document or question.',422)
        if not self._admission or self._admission.grant.embedding_model!=self.spec.model:
            raise DomainError('LIVE_NOT_CONFIGURED','A finite live allowance is required.',503)
        result=[]
        for offset in range(0,len(texts),4):
            batch=texts[offset:offset+4];batch_counts=counts[offset:offset+4]
            number=self._batch;self._batch+=1
            def invoke(batch=batch):
                response=self._client.embeddings.create(model=self.spec.model,input=batch,
                    dimensions=self.spec.dimensions,encoding_format='float')
                payload=response.model_dump(mode='json');usage=payload.get('usage') or {}
                return ProviderResult(payload,SafeUsage(usage.get('prompt_tokens'),0))
            try:
                payload=self._admission.run(phase,number,input_tokens=sum(batch_counts),vectors=len(batch),invoke=invoke)
                rows=payload.get('data',[])
                if payload.get('model')!=self.spec.model or len(rows)!=len(batch):raise ValueError()
                indexes=[item.get('index') for item in rows]
                if any(type(index) is not int for index in indexes) or sorted(indexes)!=list(range(len(batch))):raise ValueError()
                result.extend(validate_vector(item.get('embedding'),self.spec) for item in sorted(rows,key=lambda item:item['index']))
            except DomainError:raise
            except Exception as error:  # noqa: BLE001 - provider errors must never expose request or response bodies.
                code='ASSISTANT_TIMEOUT' if 'Timeout' in type(error).__name__ else 'EMBEDDING_UNAVAILABLE'
                raise DomainError(code,'The document could not be indexed. Try again later.',503) from None
        return result
    def _get_text_embeddings(self,texts):return self._embed(texts,'ingest_embed')
    def _get_text_embedding(self,text):return self._embed([text],'ingest_embed')[0]
    def _get_query_embedding(self,text):return self._embed([text],'query_embed')[0]
    async def _aget_query_embedding(self,text):return self._get_query_embedding(text)


def register_profile(db,spec):
    from sqlalchemy.dialects.postgresql import insert
    values=dict(id=spec.profile_id,provider=spec.provider,model=spec.model,dimensions=spec.dimensions,
                chunker=spec.chunker,tokenizer=spec.tokenizer)
    db.execute(insert(EmbeddingProfile).values(**values).on_conflict_do_nothing())
    row=db.get(EmbeddingProfile,spec.profile_id)
    if any(getattr(row,key)!=value for key,value in values.items()):raise ValueError('EMBEDDING_PROFILE_INVALID')


def spec_for_workspace(db,workspace):
    row=db.get(EmbeddingProfile,workspace.embedding_profile_id)
    if not row:raise DomainError('KNOWLEDGE_PROFILE','The document configuration needs review.',503)
    return EmbeddingSpec(row.provider,row.model,row.dimensions,row.chunker,row.tokenizer)


@dataclass(frozen=True)
class ParsedChunk:
    page:int
    section:str
    content:str


@dataclass(frozen=True)
class ParsedVersion:
    data:bytes
    kind:str
    slot:str
    title:str
    version:str
    now:datetime
    owner:UUID|None
    generation:int
    spec:EmbeddingSpec
    chunks:tuple[ParsedChunk,...]


def parse(data:bytes,kind:str):
    if not data or len(data)>2_097_152:
        raise DomainError('DOCUMENT_TOO_LARGE','Choose a file smaller than 2 MiB.',422)
    try:
        result=subprocess.run([sys.executable,'-B','-I',str(Path(__file__).with_name('parse_document.py')),kind],
                              input=data,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=5,check=False,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        output=json.loads(result.stdout)
        if result.returncode or 'pages' not in output:raise ValueError()
        return output['pages']
    except (ValueError,OSError,subprocess.TimeoutExpired):
        raise DomainError('DOCUMENT_UNREADABLE','Use a text PDF (up to 10 pages), UTF-8 TXT or Markdown without scripts or attachments.',422) from None


def parse_version(data,kind,slot,title,version,now,*,owner=None,generation=1,spec=FAKE_SPEC,tokenizer=None):
    if slot not in SLOTS:raise DomainError('DOCUMENT_SLOT','Choose a document to replace.',422)
    if spec.provider=='fake' and spec!=FAKE_SPEC:
        raise DomainError('KNOWLEDGE_PROFILE_RESET','Start a new demo to replace this legacy document.',409)
    if spec.provider=='openai' and (spec.chunker!='llama-token-section-v4' or not hasattr(tokenizer,'encode')):
        raise DomainError('LIVE_NOT_CONFIGURED','The document tokenizer is not configured.',503)
    pages=parse(data,kind)
    if kind=='pdf':
        # Authored headings are used only when their bodies occur in the actual
        # extracted PDF page. This preserves section provenance without invented pages.
        digest=hashlib.sha256(data).hexdigest()
        item=next((item for item in json.loads((PACK/'manifest.json').read_text()) if item['sha256']==digest),None)
        if item:
            guide=next(g for g in json.loads((PACK/'sources/guides.json').read_text()) if g['file']==item['file'])
            sections=[]
            for index,page in enumerate(guide['pages']):
                for heading,body in page['sections']:
                    if body not in pages[index]['text']:raise DomainError('SOURCE_MAPPING','The sample source mapping needs review.',503)
                    sections.append({'page':index+1,'section':heading,'text':body})
            pages=sections
    encode=tokenizer.encode if spec.provider=='openai' else lambda value:value.split()
    splitter=TokenTextSplitter(chunk_size=220,chunk_overlap=20,tokenizer=encode,include_metadata=False)
    chunks=[]
    for page in pages:
        for chunk_text in splitter.split_text(page['text']):
            if len(chunk_text)>6000 or not 0<len(encode(chunk_text))<=8192:
                raise DomainError('DOCUMENT_COMPLEX','Use shorter paragraphs in this document.',422)
            chunks.append(ParsedChunk(page['page'],page['section'],chunk_text))
            if len(chunks)>64:raise DomainError('DOCUMENT_COMPLEX','Use a shorter document.',422)
    if not chunks:raise DomainError('DOCUMENT_NO_TEXT','Choose a document with selectable text.',422)
    return ParsedVersion(data,kind,slot,title,version,now,owner,generation,spec,tuple(chunks))


def embed_version(parsed,embedder=None):
    if not 1<=len(parsed.chunks)<=64:
        raise DomainError('DOCUMENT_COMPLEX','Use a shorter document.',422)
    if embedder is None:
        if parsed.spec.provider!='fake':raise DomainError('LIVE_NOT_CONFIGURED','Live embedding is not configured.',503)
        embedder=FakeEmbedding(parsed.spec)
    if embedder.spec!=parsed.spec:raise DomainError('KNOWLEDGE_PROFILE','The document configuration changed.',409)
    vectors=embedder.get_text_embedding_batch([item.content for item in parsed.chunks])
    if len(vectors)!=len(parsed.chunks):raise DomainError('EMBEDDING_FORMAT','The document could not be indexed.',503)
    version_id=uuid4() if parsed.owner else uuid5(NAMESPACE_URL,
        'choreograph:'+parsed.slot+':'+hashlib.sha256(parsed.data).hexdigest()+':'+parsed.spec.profile_id)
    row=DocumentVersion(id=version_id,owner_id=parsed.owner,generation=parsed.generation,slot=parsed.slot,title=parsed.title,
        version=parsed.version,media_type='application/pdf' if parsed.kind=='pdf' else 'text/plain',source=parsed.data,
        sha256=hashlib.sha256(parsed.data).hexdigest(),page_count=max(item.page for item in parsed.chunks),state='ready',
        created_at=parsed.now,embedding_model=parsed.spec.model,chunker_version=parsed.spec.chunker,
        embedding_profile_id=parsed.spec.profile_id)
    chunks=[Chunk(id=uuid4(),version_id=version_id,page=item.page,section=item.section,content=item.content,
                  embedding=validate_vector(vector,parsed.spec)) for item,vector in zip(parsed.chunks,vectors,strict=True)]
    return row,chunks


def build_version(data,kind,slot,title,version,now,*,owner=None,generation=1,spec=FAKE_SPEC,embedder=None,tokenizer=None):
    return embed_version(parse_version(data,kind,slot,title,version,now,owner=owner,generation=generation,
                                       spec=spec,tokenizer=tokenizer),embedder)


def prepare_samples(db,now):
    """Deliberate fake-provider preparation command, never called by guest routes."""
    register_profile(db,FAKE_SPEC)
    for item in json.loads((PACK/'manifest.json').read_text(encoding='utf-8')):
        if item['replacement']:continue
        data=(PACK/item['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('SAMPLE_HASH_MISMATCH')
        existing=db.scalar(select(DocumentVersion.id).where(DocumentVersion.owner_id.is_(None),DocumentVersion.slot==item['slot'],
            DocumentVersion.sha256==item['sha256'],DocumentVersion.embedding_profile_id==FAKE_SPEC.profile_id))
        if existing:continue
        row,chunks=build_version(data,'pdf' if item['file'].endswith('.pdf') else 'text',item['slot'],item['title'],item['version'],now)
        db.add(row)
        db.flush();db.add_all(chunks)
    db.flush()


def prepare_pack(engine,now,*,spec,embedder,tokenizer=None):
    """Explicit operator command: preflight the whole corpus before any embedding."""
    parsed=[]
    with Session(engine) as db,db.begin():
        register_profile(db,spec)
        for item in json.loads((PACK/'manifest.json').read_text(encoding='utf-8')):
            if item['replacement']:continue
            data=(PACK/item['file']).read_bytes()
            if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('SAMPLE_HASH_MISMATCH')
            if db.scalar(select(DocumentVersion.id).where(DocumentVersion.owner_id.is_(None),DocumentVersion.slot==item['slot'],
                DocumentVersion.sha256==item['sha256'],DocumentVersion.embedding_profile_id==spec.profile_id)):continue
            parsed.append(parse_version(data,'pdf' if item['file'].endswith('.pdf') else 'text',item['slot'],
                item['title'],item['version'],now,spec=spec,tokenizer=tokenizer))
    for item in parsed:
        row,chunks=embed_version(item,embedder)
        with Session(engine) as db,db.begin():
            # A concurrent completed preparation cannot rewrite a ready version.
            if db.get(DocumentVersion,row.id):continue
            db.add(row);db.flush();db.add_all(chunks)
    return {'prepared':len(parsed)}


def attach_samples(db,workspace):
    existing=set(db.scalars(select(Manifest.slot).where(Manifest.workspace_id==workspace.id)))
    for slot in SLOTS:
        if slot in existing:continue
        version_id=db.scalar(select(DocumentVersion.id).where(DocumentVersion.owner_id.is_(None),DocumentVersion.slot==slot,
            DocumentVersion.state=='ready',DocumentVersion.embedding_profile_id==workspace.embedding_profile_id).order_by(DocumentVersion.created_at.desc()).limit(1))
        if version_id:db.add(Manifest(workspace_id=workspace.id,slot=slot,version_id=version_id))
    db.flush()


def authorized(db,workspace):
    return select(DocumentVersion).join(Manifest,Manifest.version_id==DocumentVersion.id).where(
        Manifest.workspace_id==workspace.id,DocumentVersion.state=='ready',
        or_(DocumentVersion.owner_id.is_(None),DocumentVersion.owner_id==workspace.id))


def documents(db,workspace):
    return [{'id':r.id,'slot':r.slot,'title':r.title,'version':r.version,'pages':r.page_count,'media_type':r.media_type,
             'private':r.owner_id is not None} for r in db.scalars(authorized(db,workspace).options(
                 defer(DocumentVersion.source,raiseload=True)).order_by(DocumentVersion.slot))]


def source(db,workspace,version_id):
    row=db.scalar(authorized(db,workspace).where(DocumentVersion.id==version_id))
    if not row:raise DomainError('SOURCE_UNAVAILABLE','This source is no longer available in this demo.',404)
    return row


class ScopedRetriever(BaseRetriever):
    def __init__(self,db,workspace,*,vector=None,spec=None,embedder=None):
        super().__init__();self.db=db;self.workspace=workspace;self.spec=spec or spec_for_workspace(db,workspace)
        if self.spec.profile_id!=workspace.embedding_profile_id:
            raise DomainError('KNOWLEDGE_PROFILE','The documents changed. Start a fresh demo.',409)
        self.vector=vector;self.embed=embedder
    def _retrieve(self,query_bundle:QueryBundle):
        question=query_bundle.query_str[:1200];tokens=set(terms(question))
        if self.vector is None:
            if self.spec.provider!='fake':raise DomainError('EMBEDDING_REQUIRED','Prepare the question embedding first.',503)
            self.vector=(self.embed or FakeEmbedding(self.spec)).get_query_embedding(question)
        vector=validate_vector(self.vector,self.spec)
        profile=(DocumentVersion.embedding_profile_id==self.spec.profile_id)
        if self.spec.model=='legacy-mixed-fake64' and self.spec.provider=='fake':
            profile=DocumentVersion.embedding_profile_id.in_(select(EmbeddingProfile.id).where(
                EmbeddingProfile.provider=='fake',EmbeddingProfile.dimensions==64))
        # Server manifest and ready/owner joins run BEFORE similarity search.
        query=select(Chunk,DocumentVersion,Chunk.embedding.cosine_distance(vector).label('distance')).join(
            DocumentVersion,DocumentVersion.id==Chunk.version_id).join(Manifest,Manifest.version_id==DocumentVersion.id).where(
                Manifest.workspace_id==self.workspace.id,DocumentVersion.state=='ready',
                profile,or_(DocumentVersion.owner_id.is_(None),DocumentVersion.owner_id==self.workspace.id)).options(
                    defer(DocumentVersion.source,raiseload=True)).order_by('distance').limit(64)
        ranked=[]
        for chunk,doc,distance in self.db.execute(query):
            overlap=tokens.intersection(terms(chunk.content+' '+chunk.section+' '+doc.title))
            if not overlap and self.spec.provider=='fake':continue
            score=len(overlap)/max(1,len(tokens))+(1-float(distance))*(.12 if self.spec.provider=='fake' else 1)
            node=TextNode(id_=str(chunk.id),text=chunk.content,metadata={'version_id':str(doc.id),'title':doc.title,'version':doc.version,
                           'page':chunk.page,'section':chunk.section,'media_type':doc.media_type,'slot':doc.slot})
            ranked.append(NodeWithScore(node=node,score=score))
        return sorted(ranked,key=lambda item:item.score or 0,reverse=True)[:4]


def retrieve(db,workspace,question,*,vector=None,spec=None,embedder=None):
    if not workspace.active:raise DomainError('SESSION_EXPIRED','This demo has ended.',410)
    return ScopedRetriever(db,workspace,vector=vector,spec=spec,embedder=embedder).retrieve(question)


def query_embedding(embedder,question):
    if not isinstance(question,str) or not 1<=len(question)<=1200:
        raise DomainError('ASSISTANT_CONTEXT','Use a shorter cleaning question.',422)
    return validate_vector(embedder.get_query_embedding(question),embedder.spec)


def publish_replacement(db,workspace,parsed,built,expected_version_id,expected_revision,now):
    if not workspace.active or workspace.expires_at<=now or workspace.generation!=parsed.generation:
        raise DomainError('SESSION_EXPIRED','This demo has ended.',410)
    if (workspace.revision!=expected_revision or workspace.id!=parsed.owner or
            workspace.embedding_profile_id!=parsed.spec.profile_id):
        raise DomainError('STALE_REVISION','The demo or documents changed. Refresh before continuing.')
    current=db.scalar(authorized(db,workspace).where(DocumentVersion.slot==parsed.slot))
    if not current or str(current.id)!=str(expected_version_id):
        raise DomainError('DOCUMENT_CHANGED','The document changed. Refresh before continuing.')
    row,chunks=built
    if (row.owner_id!=workspace.id or row.generation!=workspace.generation or row.slot!=parsed.slot or
            row.embedding_profile_id!=workspace.embedding_profile_id):
        raise DomainError('DOCUMENT_CHANGED','The document changed. Refresh before continuing.')
    db.add(row);db.flush();db.add_all(chunks);db.flush()
    db.get(Manifest,(workspace.id,parsed.slot)).version_id=row.id;db.flush()
    if current.owner_id==workspace.id:db.delete(current)
    return {'ready':True,'code':'DOCUMENT_READY','message':'The new document is ready.'}


def replace(db,workspace,slot,data,kind,now):
    if not workspace.active or workspace.expires_at<=now:
        raise DomainError('SESSION_EXPIRED','This demo has ended.',410)
    if slot not in SLOTS:raise DomainError('DOCUMENT_SLOT','Choose a document to replace.',422)
    if workspace.ingestion_attempts>=3:raise DomainError('DOCUMENT_LIMIT','This demo has used its three document replacements.',422)
    # At most two document parses across API processes sharing this database.
    if not any(db.scalar(text('SELECT pg_try_advisory_xact_lock(45860,:slot)'),{'slot':slot}) for slot in (1,2)):
        raise DomainError('DOCUMENT_BUSY','Other documents are processing. Try again shortly.',429)
    workspace.ingestion_attempts+=1
    try:
        current=db.scalar(authorized(db,workspace).where(DocumentVersion.slot==slot))
        if not current:raise DomainError('DOCUMENT_UNAVAILABLE','Prepare the sample pack first.',503)
        spec=spec_for_workspace(db,workspace)
        parsed=parse_version(data,kind,slot,current.title,f'Guest {workspace.ingestion_attempts}',now,
                             owner=workspace.id,generation=workspace.generation,spec=spec)
        built=embed_version(parsed)
    except DomainError as error:
        workspace.revision+=1
        return {'ready':False,'code':error.code,'message':error.message}
    if not workspace.active or workspace.expires_at<=now:
        raise DomainError('SESSION_EXPIRED','This demo has ended.',410)
    notice=publish_replacement(db,workspace,parsed,built,current.id,workspace.revision,now)
    workspace.revision+=1
    return notice


def purge_private(db,workspace):
    db.execute(delete(Manifest).where(Manifest.workspace_id==workspace.id))
    db.execute(delete(DocumentVersion).where(DocumentVersion.owner_id==workspace.id))
