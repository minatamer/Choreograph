"""Profile, migration, publication and source boundaries on actual pgvector."""
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from conftest import postgres_database as database_fixture
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_live_embeddings import Tokens

from choreograph import knowledge
from choreograph.ai_admission import FAKE_SPEC, EmbeddingSpec
from choreograph.errors import DomainError
from choreograph.migrate import downgrade, migrate
from choreograph.models import Chunk, DocumentVersion, EmbeddingProfile, Manifest, Workspace
from choreograph.sessions import create_workspace

NOW=datetime(2026,10,22,10,tzinfo=UTC)
SPEC=EmbeddingSpec('openai','synthetic-semantic-'+uuid4().hex,3,'llama-token-section-v4','synthetic-byte-tokens')


class Vectors:
    spec=SPEC
    def __init__(self):self.calls=0
    def get_text_embedding_batch(self,texts):self.calls+=1;return [[1.,0.,0.] for _ in texts]


def test_live_profile_coexistence_semantic_search_and_atomic_publication(database):
    engine,_=database;owned=[];versions=[];vectors=Vectors()
    try:
        with Session(engine) as db,db.begin():
            knowledge.prepare_samples(db,NOW);knowledge.register_profile(db,SPEC)
            fake,_=create_workspace(db,'UTC',NOW);owned.append(fake.id);knowledge.attach_samples(db,fake)
            live,_=create_workspace(db,'UTC',NOW,embedding_profile_id=SPEC.profile_id);owned.append(live.id)
            other,_=create_workspace(db,'UTC',NOW,embedding_profile_id=SPEC.profile_id);owned.append(other.id)
            fake_id,live_id,other_id=fake.id,live.id,other.id
        parsed=knowledge.parse_version(b'Pets wait outside the home during the synthetic clean.','text','preparation','Synthetic','1',
            NOW,spec=SPEC,tokenizer=Tokens())
        row,chunks=knowledge.embed_version(parsed,vectors);versions.append(row.id);original=row.id
        with Session(engine) as db,db.begin():
            db.add(row);db.flush();db.add_all(chunks);db.flush()
            live=db.get(Workspace,live_id);other=db.get(Workspace,other_id)
            knowledge.attach_samples(db,live);knowledge.attach_samples(db,other)
            # No word overlaps. Real vector ranking must still return an authorized candidate.
            hits=knowledge.retrieve(db,live,'feline guardianship',vector=[1.,0.,0.],spec=SPEC)
            assert hits and hits[0].node.metadata['version_id']==str(original)
            assert knowledge.source(db,live,original).source==parsed.data
            with pytest.raises(DomainError):knowledge.source(db,db.get(Workspace,fake_id),original)
            with pytest.raises(IntegrityError),db.begin_nested():
                db.add(Chunk(version_id=original,page=1,section='Invalid',content='Wrong dimension',embedding=[1.,0.]))
                db.flush()
            with pytest.raises(IntegrityError),db.begin_nested():
                db.merge(Manifest(workspace_id=fake_id,slot='preparation',version_id=original));db.flush()
            with pytest.raises(IntegrityError),db.begin_nested():
                db.get(EmbeddingProfile,SPEC.profile_id).dimensions=4;db.flush()
        replacement=knowledge.parse_version(b'Pets remain with their trusted guardian outside the synthetic work area.','text',
            'preparation','Synthetic','2',NOW,owner=live_id,generation=1,spec=SPEC,tokenizer=Tokens())
        built=knowledge.embed_version(replacement,vectors)
        replacement_id=built[0].id
        with Session(engine) as db,db.begin():db.get(Workspace,live_id).revision+=1
        with Session(engine) as db,db.begin(),pytest.raises(DomainError):
            knowledge.publish_replacement(db,db.get(Workspace,live_id),replacement,built,original,1,NOW)
        with Session(engine) as db:
            assert knowledge.source(db,db.get(Workspace,live_id),original).source==parsed.data
        with Session(engine) as db,db.begin():
            notice=knowledge.publish_replacement(db,db.get(Workspace,live_id),replacement,built,original,2,NOW)
            assert notice['ready']
        with Session(engine) as db:
            assert knowledge.source(db,db.get(Workspace,live_id),replacement_id).source==replacement.data
            assert knowledge.source(db,db.get(Workspace,other_id),original).source==parsed.data
            with pytest.raises(DomainError):knowledge.source(db,db.get(Workspace,live_id),original)
            with pytest.raises(DomainError):knowledge.source(db,db.get(Workspace,other_id),replacement_id)
    finally:
        with Session(engine) as db,db.begin():
            db.execute(delete(Workspace).where(Workspace.id.in_(owned)))
            db.execute(delete(DocumentVersion).where(DocumentVersion.id.in_(versions)))


def test_ready_sample_preparation_is_immutable_and_never_reembeds(database):
    engine,_=database
    with Session(engine) as db,db.begin():
        knowledge.prepare_samples(db,NOW)
        before=list(db.execute(select(DocumentVersion.id,DocumentVersion.sha256,DocumentVersion.embedding_profile_id).where(
            DocumentVersion.owner_id.is_(None))).all())
    fake=knowledge.FakeEmbedding()
    assert knowledge.prepare_pack(engine,NOW,spec=FAKE_SPEC,embedder=fake)=={'prepared':0}
    assert fake._calls==0
    with Session(engine) as db:
        assert list(db.execute(select(DocumentVersion.id,DocumentVersion.sha256,DocumentVersion.embedding_profile_id).where(
            DocumentVersion.owner_id.is_(None))).all())==before


def test_populated_legacy_migration_preserves_source_vectors_and_manifest_identity():
    fixture=database_fixture.__wrapped__();engine,_=next(fixture)
    try:
        downgrade(engine,'0006')
        wid,vid,cid=uuid4(),uuid4(),uuid4();source=b'Synthetic legacy pet preparation guide.'
        vector='['+','.join(['1']+['0']*63)+']'
        with engine.begin() as db:
            db.execute(text("INSERT INTO workspaces (id,session_hash,timezone,created_at,expires_at,active,generation,revision,"
                "seeded,draft,messages,crm_mode) VALUES (:id,:hash,'UTC',:now,:until,true,1,1,false,'{}','[]','skipped')"),
                {'id':wid,'hash':uuid4().hex+uuid4().hex,'now':NOW,'until':NOW.replace(hour=12)})
            db.execute(text("INSERT INTO document_versions (id,owner_id,generation,slot,title,version,media_type,source,sha256,"
                "page_count,state,created_at,embedding_model,chunker_version) VALUES (:id,:owner,1,'preparation','Synthetic','1',"
                "'text/plain',:source,:sha,1,'ready',:now,'fake-hash-64-v1','llama-token-page-v1')"),
                {'id':vid,'owner':wid,'source':source,'sha':'0'*64,'now':NOW})
            db.execute(text("INSERT INTO knowledge_chunks (id,version_id,page,section,content,embedding) "
                "VALUES (:id,:version,1,'Preparation','Synthetic pet preparation.',CAST(:vector AS vector))"),
                {'id':cid,'version':vid,'vector':vector})
            db.execute(text("INSERT INTO document_manifest VALUES (:workspace,'preparation',:version)"),{'workspace':wid,'version':vid})
        migrate(engine,'0007')
        with Session(engine) as db:
            workspace=db.get(Workspace,wid);version=knowledge.source(db,workspace,vid)
            spec=knowledge.spec_for_workspace(db,workspace)
            assert spec==EmbeddingSpec('fake','fake-hash-64-v1',64,'llama-token-page-v1','whitespace-v1')
            assert version.source==source and version.embedding_model=='fake-hash-64-v1'
            assert db.get(Manifest,(wid,'preparation')).version_id==vid
            assert list(db.get(Chunk,cid).embedding)==[1.]+[0.]*63
            assert knowledge.retrieve(db,workspace,'pet preparation',spec=spec)
        with Session(engine) as db,db.begin():
            workspace=db.get(Workspace,wid)
            notice=knowledge.replace(db,workspace,'preparation',b'Synthetic replacement that needs a current profile.','text',NOW)
            assert not notice['ready'] and notice['code']=='KNOWLEDGE_PROFILE_RESET'
        with Session(engine) as db:
            assert knowledge.source(db,db.get(Workspace,wid),vid).source==source
            assert db.get(Manifest,(wid,'preparation')).version_id==vid
    finally:fixture.close()
