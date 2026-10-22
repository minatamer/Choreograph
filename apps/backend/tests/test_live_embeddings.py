"""The installed SDK is exercised only through bounded injected HTTP streams."""
import json
from types import SimpleNamespace

import httpx
import pytest
from openai import OpenAI

from choreograph.ai_admission import EmbeddingSpec
from choreograph.errors import DomainError
from choreograph.knowledge import OpenAIEmbedding, embed_version, parse_version
from choreograph.providers import BoundedOpenAIClient


class Tokens:
    def encode(self,text):return list(text.encode())
    def decode(self,tokens):return bytes(tokens).decode()


SPEC=EmbeddingSpec('openai','synthetic-embedding',3,'llama-token-section-v4','synthetic-byte-tokens')


class Gate:
    grant=SimpleNamespace(embedding_model=SPEC.model)
    def __init__(self):self.calls=[]
    def run(self,phase,batch,**options):
        result=options.pop('invoke')();self.calls.append((phase,batch,options,result.usage));return result.value


def adapter(handler,gate):
    sdk=OpenAI(api_key='injected-not-a-key',base_url='https://example.invalid/v1',max_retries=0,
        http_client=BoundedOpenAIClient(transport=httpx.MockTransport(handler),response_bytes=524_288))
    return OpenAIEmbedding(SPEC,client=sdk,authorized=True,admission=gate,tokenizer=Tokens())


def test_batch_indexes_usage_and_explicit_dimension_request():
    requests=[];gate=Gate()
    def handle(request):
        body=json.loads(request.content);requests.append(body)
        assert body['encoding_format']=='float' and body['dimensions']==3 and body['model']==SPEC.model
        rows=[{'object':'embedding','index':index,'embedding':[float(index+1),0.,0.]} for index in range(len(body['input']))]
        return httpx.Response(200,json={'object':'list','model':SPEC.model,'data':list(reversed(rows)),
                                       'usage':{'prompt_tokens':8,'total_tokens':8}})
    instance=adapter(handle,gate)
    try:
        assert instance.get_text_embedding_batch(['one','two','three','four','five'])==[
            [1.,0.,0.],[2.,0.,0.],[3.,0.,0.],[4.,0.,0.],[1.,0.,0.]]
        assert [len(body['input']) for body in requests]==[4,1]
        assert [(phase,batch) for phase,batch,_,_ in gate.calls]==[('ingest_embed',0),('ingest_embed',1)]
        assert gate.calls[0][3].input_tokens==8
    finally:instance.close()


@pytest.mark.parametrize('problem',['dimension','zero','nan','index','model','missing','error'])
def test_invalid_embedding_or_error_never_becomes_fake_success(problem):
    calls=[]
    def handle(request):
        calls.append(1)
        row={'object':'embedding','index':0,'embedding':[1.,0.,0.]}
        if problem=='dimension':row['embedding']=[1.,0.]
        if problem=='zero':row['embedding']=[0.,0.,0.]
        if problem=='nan':row['embedding']=[float('nan'),0.,0.]
        if problem=='index':row['index']=1
        body={'object':'list','model':'wrong' if problem=='model' else SPEC.model,
              'data':[] if problem=='missing' else [row], 'usage':{'prompt_tokens':3,'total_tokens':3}}
        return httpx.Response(502 if problem=='error' else 200,content=json.dumps(body),headers={'content-type':'application/json'})
    instance=adapter(handle,Gate())
    try:
        with pytest.raises(DomainError) as error:instance.get_query_embedding('pets')
        assert error.value.code in {'EMBEDDING_FORMAT','EMBEDDING_UNAVAILABLE'} and calls==[1]
    finally:instance.close()


def test_document_preflight_finishes_before_first_embedding():
    from datetime import UTC, datetime
    gate=Gate();calls=[]
    instance=adapter(lambda request:calls.append(1),gate)
    try:
        with pytest.raises(DomainError) as error:
            parsed=parse_version(b'Synthetic pet preparation passage. '*800,'text','preparation','Synthetic','1',
                datetime(2026,10,22,tzinfo=UTC),spec=SPEC,tokenizer=Tokens())
            embed_version(parsed,instance)
        assert error.value.code=='DOCUMENT_COMPLEX' and not calls and not gate.calls
    finally:instance.close()


def test_direct_sdk_constructors_ignore_ambient_routing_and_require_allowance(monkeypatch):
    from choreograph.providers import OpenAITransport
    monkeypatch.setenv('OPENAI_BASE_URL','https://untrusted.invalid/v1')
    monkeypatch.setenv('OPENAI_ORG_ID','synthetic-ambient-org')
    monkeypatch.setenv('OPENAI_PROJECT_ID','synthetic-ambient-project')
    monkeypatch.setenv('OPENAI_CUSTOM_HEADERS','X-Fixture: synthetic-ambient-header')
    response=OpenAITransport(model='synthetic-response',api_key='injected-not-a-key',authorized=True,tokenizer=Tokens())
    embedding=OpenAIEmbedding(SPEC,api_key='injected-not-a-key',authorized=True,tokenizer=Tokens())
    try:
        for client in (response.client,embedding._client):
            assert str(client.base_url)=='https://api.openai.com/v1/' and client._custom_headers=={}
            assert not client.organization and not client.project
        with pytest.raises(DomainError) as error:response.interpret('hello',{},'UTC','2026-10-22')
        assert error.value.code=='LIVE_NOT_CONFIGURED'
        with pytest.raises(DomainError) as error:embedding.get_query_embedding('pets')
        assert error.value.code=='LIVE_NOT_CONFIGURED'
    finally:response.close();embedding.close()
