import json
from datetime import timedelta
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_requests import NOW, command

from choreograph import crm
from choreograph.api import create_app
from choreograph.hubspot import KEY_PROPERTY, SCOPES, CRMFailure, FakeHubSpot, HubSpotConfig, HubSpotTransport
from choreograph.models import Connection, Installation, OAuthState, Outbox, SimulatedRecord


def begin(database,provider=None):
    engine,settings=database;provider=provider or FakeHubSpot(engine)
    c=TestClient(create_app(settings,engine,lambda:NOW,crm_provider=provider));h={'x-choreograph-bridge':settings.bridge_secret,'origin':settings.origin}
    s=c.post('/v1/session',headers=h,json={'timezone':'Africa/Cairo'}).json();h['x-csrf-token']=s['csrf']
    return c,h,s,provider


def connect(c,h,s):
    result=command(c,h,s,{},'/v1/crm/connect',method='post');assert result.status_code==200,result.text
    challenge=result.json()['oauth'];s=result.json()['state']
    result=command(c,h,s,{'state':challenge['state'],'code':'approved'},'/v1/crm/callback',method='post');assert result.status_code==200,result.text
    return result.json()['state'],challenge


def test_skip_denial_no_calls_and_state_binding(database):
    c,h,s,p=begin(database);other,oh,os,_=begin(database)
    try:
        skipped=command(c,h,s,{},'/v1/crm/skip',method='post').json()['state'];assert skipped['crm_mode']=='skipped' and not p.calls
        result=command(c,h,skipped,{},'/v1/crm/connect',method='post').json();s=result['state'];challenge=result['oauth']
        wrong=command(other,oh,os,{'state':challenge['state'],'code':'approved'},'/v1/crm/callback',method='post')
        assert wrong.status_code==409 and not p.calls
        denied=command(c,h,s,{'state':challenge['state'],'denied':True},'/v1/crm/callback',method='post')
        assert denied.status_code==200 and denied.json()['state']['crm_mode']=='skipped' and not p.calls
        assert command(c,h,denied.json()['state'],{'state':challenge['state'],'code':'approved'},'/v1/crm/callback',method='post').status_code==409
    finally:c.close();other.close()


def test_skip_retires_only_its_pending_oauth_before_late_callback(database):
    c,h,s,p=begin(database);other,oh,os,op=begin(database)
    try:
        attempt=command(c,h,s,{},'/v1/crm/connect',method='post').json()
        other_attempt=command(other,oh,os,{},'/v1/crm/connect',method='post').json()
        skipped=command(c,h,attempt['state'],{},'/v1/crm/skip',method='post').json()['state']
        late=command(c,h,skipped,{'state':attempt['oauth']['state'],'code':'approved'},'/v1/crm/callback',method='post')
        assert late.status_code==409 and late.json()['code']=='OAUTH_STATE' and not p.calls
        assert c.get('/v1/session',headers=h).json()['crm_mode']=='skipped'
        accepted=command(other,oh,other_attempt['state'],{'state':other_attempt['oauth']['state'],'code':'approved'},'/v1/crm/callback',method='post')
        assert accepted.status_code==200 and accepted.json()['state']['crm_mode']=='connected' and op.calls==['exchange']
    finally:c.close();other.close()


def test_connection_encryption_consent_install_dedup_and_shared_uninstall(database):
    engine,settings=database;p=FakeHubSpot(engine,account_id='shared-fixture-'+uuid4().hex)
    a,ah,sa,_=begin(database,p);b,bh,sb,_=begin(database,p)
    try:
        sa,_=connect(a,ah,sa);sb,_=connect(b,bh,sb)
        assert sa['connection']['provider']=='fake' and sa['connection']['state']=='ready'
        assert 'access_token' not in json.dumps(sa) and not sa['connection']['consented']
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(Installation).where(Installation.account_id==p.account_id))==1
            row=db.get(Connection,(sa['workspace_id'],sa['connection']['id']))
            assert b'fake-refresh' not in row.encrypted_tokens
            assert crm.tokens_for(db,row,settings.token_key,p,NOW)['account_id']==p.account_id
        sa=command(a,ah,sa,{'connection_id':sa['connection']['id'],'confirm':True},'/v1/crm/consent',method='post').json()['state']
        assert sa['connection']['consented']
        shared=command(a,ah,sa,{'connection_id':sa['connection']['id'],'confirm':True,'cleanup':True,'uninstall':True},'/v1/crm/finish',method='post')
        assert shared.status_code==409
        detached=command(a,ah,sa,{},'/v1/crm/disconnect',method='post').json()['state']
        assert detached['crm_mode']=='skipped' and detached['connection']['state']=='detached'
        assert 'uninstall' not in p.calls
        with Session(engine) as db:assert db.get(Installation,(p.app_id,p.account_id)).state=='installed'
    finally:a.close();b.close()


def test_capacity_is_conservative_and_does_not_disable_skip(database):
    engine,_=database;p=FakeHubSpot(engine);p.app_id='capacity-'+uuid4().hex
    with Session(engine) as db,db.begin():
        for i in range(25):db.add(Installation(app_id=p.app_id,account_id=str(i),state='installed',checked_at=NOW))
    c,h,s,_=begin(database,p)
    try:
        assert s['crm_available'] is False
        attempt=command(c,h,s,{},'/v1/crm/connect',method='post').json()
        assert attempt['oauth'] is None and not p.calls
        assert command(c,h,attempt['state'],{},'/v1/crm/skip',method='post').status_code==200
    finally:c.close()


@pytest.mark.parametrize('boundary',['exchange','preflight'])
def test_unverified_callback_preserves_skip_without_export_or_releasing_unknown_install(database,boundary):
    engine,_=database
    class Unavailable(FakeHubSpot):
        # Inject both reachable callback boundaries; neither implementation uses a network.
        provider='hubspot' if boundary=='preflight' else 'fake'
        app_id='callback-failure-'+uuid4().hex
        def exchange(self,code,workspace_id):
            if boundary=='exchange':
                self.calls.append('exchange');raise CRMFailure('CRM_UNAVAILABLE',True)
            return super().exchange(code,workspace_id)
        def destinations(self,tokens):
            self.calls.append('preflight');raise CRMFailure('CRM_SCOPES_REQUIRED')
    p=Unavailable(engine,account_id='unverified-'+uuid4().hex);c,h,s,_=begin(database,p)
    try:
        attempt=command(c,h,s,{},'/v1/crm/connect',method='post').json()
        assert attempt['oauth']
        fields={'state':attempt['oauth']['state'],'code':'approved'}
        failed=command(c,h,attempt['state'],fields,'/v1/crm/callback',method='post')
        assert failed.status_code==200
        result=failed.json();current=result['state']
        assert current['crm_mode']=='skipped' and current['connection'] is None and result['oauth'] is None
        assert 'could not be verified' in result['crm_notice']
        assert p.calls==(['exchange','preflight'] if boundary=='preflight' else ['exchange'])
        skipped=command(c,h,current,{},'/v1/crm/skip',method='post')
        assert skipped.status_code==200 and skipped.json()['state']['crm_mode']=='skipped'
        late=command(c,h,skipped.json()['state'],fields,'/v1/crm/callback',method='post')
        assert late.status_code==409 and late.json()['code']=='OAUTH_STATE'
        with Session(engine) as db,db.begin():
            challenge=db.scalar(select(OAuthState).where(OAuthState.workspace_id==current['workspace_id']))
            assert challenge.used and challenge.outcome==('installed' if boundary=='preflight' else 'unknown')
            install=db.get(Installation,(p.app_id,p.account_id))
            assert (install is not None and install.state=='unknown') if boundary=='preflight' else install is None
            assert db.scalar(select(func.count()).select_from(Connection).where(Connection.workspace_id==current['workspace_id']))==0
            assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.workspace_id==current['workspace_id']))==0
            assert db.scalar(select(func.count()).select_from(SimulatedRecord).where(SimulatedRecord.account_id==p.account_id))==0
            for i in range(24):db.add(Installation(app_id=p.app_id,account_id='capacity-'+str(i),state='installed',checked_at=NOW))
            db.flush()
            assert crm.available(db,p,NOW+timedelta(minutes=11)) is False
        assert p.calls==(['exchange','preflight'] if boundary=='preflight' else ['exchange'])
    finally:c.close()


def test_fake_records_are_durable_unique_and_cleanup_is_scoped(database):
    engine,_=database;p=FakeHubSpot(engine);tokens=p.exchange('approved',uuid4());key='a'*64;other='b'*64
    contact=p.upsert(tokens,'contacts',key,{'firstname':'Demo'})
    assert FakeHubSpot(engine).upsert(tokens,'contacts',key,{'firstname':'Updated'})==contact
    p.upsert(tokens,'contacts',other,{'firstname':'Pre-existing fixture'})
    p.archive(tokens,'contacts',key)
    assert p.read(tokens,'contacts',key) is None and p.read(tokens,'contacts',other)['properties']['firstname']=='Pre-existing fixture'


def test_real_adapter_is_injected_bounded_and_uses_only_owned_identity():
    seen=[];records={}
    def handler(request):
        seen.append(request)
        path=request.url.path
        if path=='/settings/currencies/2026-09/company-currency':return httpx.Response(200,json={'id':'USD'})
        if path.startswith('/oauth/'):
            if path.endswith('/introspect'):return httpx.Response(200,json={'active':True,'app_id':123,'hub_id':456,'scopes':SCOPES,'client_id':'test-client','token_use':'access_token','token_type':'Bearer','is_private_distribution':False})
            return httpx.Response(200,json={'access_token':'test-access','refresh_token':'test-refresh','expires_in':1800})
        if '/properties/' in path:return httpx.Response(200,json={'hasUniqueValue':True,'type':'string'})
        kind='contacts' if '/contacts' in path else 'deals'
        if request.method=='GET':return httpx.Response(200,json=records[kind]) if kind in records else httpx.Response(404)
        if request.method in ('POST','PATCH'):
            data=json.loads(request.content)['properties'];records[kind]={'id':'111' if kind=='contacts' else '222','properties':data};return httpx.Response(200,json=records[kind])
        return httpx.Response(204)
    config=HubSpotConfig('123','test-client','test-secret','http://localhost:45860/auth/hubspot/callback')
    transport=HubSpotTransport(config,authorized=True,client=httpx.Client(base_url='https://api.hubapi.com',transport=httpx.MockTransport(handler)))
    tokens=transport.exchange('test-code',uuid4());assert tokens['account_id']=='456';transport.preflight(tokens)
    key='a'*64;assert transport.upsert(tokens,'contacts',key,{'firstname':'Demo',KEY_PROPERTY:key})=='111'
    assert transport.read(tokens,'contacts',key)['properties'][KEY_PROPERTY]==key
    assert all(request.url.host=='api.hubapi.com' for request in seen)
    assert any(request.url.path=='/oauth/2026-09/token/introspect' and 'test-access' not in str(request.url) for request in seen)
    with pytest.raises(CRMFailure):transport.read(tokens,'contacts','bad-key')
    limited=HubSpotTransport(config,authorized=True,client=httpx.Client(base_url='https://api.hubapi.com',transport=httpx.MockTransport(lambda request:httpx.Response(429,headers={'retry-after':'9999'}))))
    with pytest.raises(CRMFailure) as error:limited.read(tokens,'contacts',key)
    assert error.value.code=='CRM_RATE_LIMIT' and error.value.retry_after==300
    def timeout(request):raise httpx.ReadTimeout('private data',request=request)
    ambiguous=HubSpotTransport(config,authorized=True,client=httpx.Client(base_url='https://api.hubapi.com',transport=httpx.MockTransport(timeout)))
    with pytest.raises(CRMFailure) as error:ambiguous._request('POST','/crm/v3/objects/contacts',tokens=tokens,json={})
    assert error.value.ambiguous and error.value.retryable and str(error.value)=='CRM_TIMEOUT'
