import json
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_ai_config import live_values
from test_requests import NOW, command

from choreograph import assistant, knowledge
from choreograph.api import create_app
from choreograph.models import Workspace
from choreograph.settings import Settings
from choreograph.verification import TurnstileConfig, TurnstileVerifier, configuration


def test_standard_mode_switches_reject_live_without_master():
    original=live_values()
    values={**original,'OPENAI_API_KEY':'explicit-synthetic-key',
            'FAKE_MODE':'false','PAID_DEMO_ENABLED':'true'}
    current=Settings.parse(values)
    assert current.profile=='live' and current.live_ai.api_key=='explicit-synthetic-key'
    assert 'explicit-synthetic-key' not in repr(current)
    with pytest.raises(ValueError,match='LIVE_AI_NOT_ENABLED'):
        Settings.parse({**values,'PAID_DEMO_ENABLED':'false'})
    fake=Settings.parse({**values,'FAKE_MODE':'true','PAID_DEMO_ENABLED':'false'},testing=True)
    assert fake.profile=='fake' and fake.live_ai is None
    with pytest.raises(ValueError,match='TEST_PROVIDER_FORBIDDEN'):Settings.parse(values,testing=True)
    with pytest.raises(ValueError,match='AI_MODE_SWITCH_INVALID'):Settings.parse({**values,'FAKE_MODE':'False'})
    bounded=Settings.parse({**values,'CHOREOGRAPH_AI_RESPONSE_TOKENIZER':'utf8-upper-v1',
                           'CHOREOGRAPH_AI_REASONING_EFFORT':'low'})
    from choreograph.tokenizers import load_tokenizer
    assert bounded.live_ai.reasoning_effort=='low'
    assert len(load_tokenizer('utf8-upper-v1').encode('🧹 policy'))==len('🧹 policy'.encode())


def test_turnstile_keys_are_explicit_complete_and_secret_repr_is_safe():
    assert configuration({},'http://127.0.0.1:45860') is None
    with pytest.raises(ValueError):configuration({'TURNSTILE_SITE_KEY':'site-only'},'http://127.0.0.1:45860')
    config=configuration({'TURNSTILE_SITE_KEY':'site','TURNSTILE_SECRET_KEY':'secret-marker'},'http://127.0.0.1:45860')
    assert config.hostname=='127.0.0.1' and 'secret-marker' not in repr(config)


@pytest.mark.parametrize('change',[{'success':False},{'success':1},{'hostname':'other.invalid'},
    {'action':'documents'},{'cdata':'another-command'},{'hostname':None},{'success':None}])
def test_siteverify_checks_success_host_action_and_command(change):
    value={'success':True,'hostname':'127.0.0.1','action':'assistant','cdata':'command'}
    verifier=TurnstileVerifier(TurnstileConfig('site','secret','127.0.0.1'),
        transport=httpx.MockTransport(lambda request:httpx.Response(200,json={**value,**change})))
    try:assert not verifier.verify('proof','assistant','command')
    finally:verifier.close()


@pytest.mark.parametrize('body,headers,status',[(b'x'*8193,{},200),(b'not json',{},200),
    (b'{}',{'content-encoding':'gzip'},200),(b'{}',{'content-length':'99999'},200),
    (b'{}',{},302),(b'{}',{},500)])
def test_siteverify_bounds_errors_bytes_and_encoding(body,headers,status):
    verifier=TurnstileVerifier(TurnstileConfig('site','secret','127.0.0.1'),
        transport=httpx.MockTransport(lambda request:httpx.Response(status,content=body,headers=headers)))
    try:assert not verifier.verify('proof','assistant','command')
    finally:verifier.close()


def test_siteverify_closes_on_late_eof_and_never_retries():
    now=[0];calls=[]
    class Stream(httpx.SyncByteStream):
        closed=False
        def __iter__(self):
            yield json.dumps({'success':True,'hostname':'127.0.0.1','action':'assistant','cdata':'id'}).encode()
            now[0]=7
        def close(self):self.closed=True
    stream=Stream()
    def respond(request):calls.append(request);return httpx.Response(200,stream=stream)
    verifier=TurnstileVerifier(TurnstileConfig('site','secret','127.0.0.1'),transport=httpx.MockTransport(respond),clock=lambda:now[0])
    try:assert not verifier.verify('proof','assistant','id') and len(calls)==1 and stream.closed
    finally:verifier.close()


def test_api_proof_precedes_work_and_completed_chat_replay_needs_no_new_proof(database):
    engine,base=database;proofs={};used=set();calls=[]
    with Session(engine) as db,db.begin():knowledge.prepare_samples(db,NOW)
    class Counted(assistant.FakeAssistant):
        count=0
        def interpret(self,*args):self.count+=1;return super().interpret(*args)
    provider=Counted();config=TurnstileConfig('public-site','private-secret-marker','127.0.0.1')
    def siteverify(request):
        assert engine.pool.checkedout()==0
        assert str(request.url)=='https://challenges.cloudflare.com/turnstile/v0/siteverify'
        body=json.loads(request.content);assert set(body)=={'secret','response'}
        assert body['secret']==config.secret_key
        token=body['response'];calls.append(token)
        if token in used or token not in proofs:return httpx.Response(200,json={'success':False})
        used.add(token);action,binding=proofs[token]
        return httpx.Response(200,json={'success':True,'hostname':config.hostname,'action':action,'cdata':binding})
    verifier=TurnstileVerifier(config,transport=httpx.MockTransport(siteverify))
    settings=replace(base,turnstile=config)
    client=TestClient(create_app(settings,engine,lambda:NOW,assistant_provider=provider,verification_provider=verifier))
    headers={'origin':settings.origin,'x-choreograph-bridge':settings.bridge_secret}
    try:
        with Session(engine) as db:before=db.scalar(select(func.count()).select_from(Workspace))
        assert client.post('/v1/session',headers=headers,json={'timezone':'UTC'}).status_code==403
        with Session(engine) as db:assert db.scalar(select(func.count()).select_from(Workspace))==before
        public=client.get('/v1/verification',headers=headers).json()
        assert public=={'enabled':True,'site_key':'public-site','required':True} and config.secret_key not in json.dumps(public)
        nonce=str(uuid4());proofs['session-proof']=('workspace',nonce)
        initial={**headers,'x-turnstile-token':'session-proof','idempotency-key':nonce}
        result=client.post('/v1/session',headers=initial,json={'timezone':'UTC'});assert result.status_code==200
        state=result.json();headers['x-csrf-token']=state['csrf']
        # Exercise the missing-proof boundary without a recent session receipt.
        client.cookies.delete('choreograph_human')
        failed=command(client,headers,state,{'text':'Hello'},'/v1/chat',method='post')
        assert failed.status_code==403 and provider.count==0
        key=str(uuid4());proofs['chat-proof']=('assistant',key)
        accepted=command(client,{**headers,'x-turnstile-token':'chat-proof'},state,{'text':'Hello'},'/v1/chat',key,method='post')
        assert accepted.status_code==200 and provider.count==1
        count=len(calls)
        replay=command(client,headers,state,{'text':'Hello'},'/v1/chat',key,method='post')
        assert replay.status_code==200 and replay.json()['replayed'] and len(calls)==count and provider.count==1
        assert verifier.verify('chat-proof','assistant',key) is False
        bad_replace=command(client,headers,accepted.json()['state'],{'kind':'text','data':'Tm90IGEgcGFpZCB1cGxvYWQu'},
            '/v1/documents/preparation/replace',method='post')
        assert bad_replace.status_code==403
        assert client.get('/v1/session',headers=headers).json()['replacements_left']==3
    finally:client.close();verifier.close()
