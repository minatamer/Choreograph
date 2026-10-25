"""Real HubSpot code paths with synthetic HTTP and isolated PostgreSQL only."""
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import httpx
import pytest
from conftest import database as database_fixture
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_booking import book
from test_crm import begin, connect
from test_requests import NOW, command

from choreograph import crm, jobs
from choreograph.api import create_app
from choreograph.crm_admission import CRMAdmission, CRMAllowance
from choreograph.crm_composition import compose_crm
from choreograph.crm_config import parse_live_crm
from choreograph.hubspot import SCOPES, CRMFailure, HubSpotConfig, HubSpotTransport
from choreograph.migrate import downgrade, migrate
from choreograph.models import (
    Connection,
    CRMCall,
    CRMGrant,
    ExternalMapping,
    Installation,
    OAuthState,
    Outbox,
)
from choreograph.settings import Settings


def config_values():
    return {'CHOREOGRAPH_HUBSPOT_APP_ID':'123',
        'CHOREOGRAPH_HUBSPOT_CLIENT_ID':'synthetic-client','CHOREOGRAPH_HUBSPOT_CLIENT_SECRET':'synthetic-secret',
        'CHOREOGRAPH_HUBSPOT_REDIRECT_URI':'http://localhost:45860/auth/hubspot/callback',
        'CHOREOGRAPH_HUBSPOT_DISTRIBUTION':'private','CHOREOGRAPH_HUBSPOT_CAPACITY':'10',
        'CHOREOGRAPH_CRM_GRANT_ID':'synthetic-'+uuid4().hex,'CHOREOGRAPH_CRM_EXPIRES_AT':'2030-01-01T00:00:00Z',
        'CHOREOGRAPH_CRM_REQUESTS':'100','CHOREOGRAPH_CRM_WORKSPACE_REQUESTS':'60',
        'CHOREOGRAPH_HUBSPOT_SCHEMA_SETUP_ALLOWED':'true'}


@pytest.mark.parametrize('changes,origin', [
    ({'CHOREOGRAPH_HUBSPOT_CLIENT_SECRET':''},'http://localhost:45860'),
    ({},'http://127.0.0.1:45860'),({},'http://other.invalid'),
    ({'CHOREOGRAPH_HUBSPOT_REDIRECT_URI':'https://other.invalid/auth/hubspot/callback'},'http://localhost:45860'),
    ({'CHOREOGRAPH_HUBSPOT_CAPACITY':'11'},'http://localhost:45860'),
    ({'CHOREOGRAPH_CRM_WORKSPACE_REQUESTS':'101'},'http://localhost:45860'),
    ({'CHOREOGRAPH_CRM_EXPIRES_AT':'2020-01-01T00:00:00Z'},'http://localhost:45860'),
    ({'CHOREOGRAPH_HUBSPOT_REDIRECT_URI':'https:///auth/hubspot/callback'},'https://'),
    ({'CHOREOGRAPH_HUBSPOT_REDIRECT_URI':'https://example.invalid:bad/auth/hubspot/callback'},'https://example.invalid:bad'),
])
def test_invalid_configuration_rejected_without_client_or_network(changes,origin):
    with pytest.raises(ValueError):parse_live_crm({**config_values(),**changes},origin,now=NOW)


class NativeFixture:
    def __init__(self):self.requests=[];self.records={};self.properties=False;self.associated=False;self.currency='USD'
    def __call__(self,request):
        self.requests.append(request);path=request.url.path
        assert request.url.host=='api.hubapi.com'
        assert request.headers['accept-encoding']=='identity'
        if path=='/account-info/2026-09/details':return httpx.Response(200,json={'companyCurrency':self.currency,'portalId':456,'accountType':'STANDARD'})
        if path.endswith('/token'):
            return httpx.Response(200,json={'access_token':'synthetic-access','refresh_token':'synthetic-refresh','expires_in':1800})
        if path.endswith('/introspect'):
            form=parse_qs(request.content.decode())
            assert form['token']==['synthetic-access'] and 'access_token' not in form
            return httpx.Response(200,json={'active':True,'app_id':123,'hub_id':456,'scopes':SCOPES,
                'client_id':'synthetic-client','token_use':'access_token','token_type':'Bearer','is_private_distribution':True})
        if path=='/crm/v3/pipelines/deals':
            return httpx.Response(200,json={'results':[{'id':'visitor-pipeline','label':'Visitor bookings','stages':[
                {'id':'queue','label':'To review','metadata':{'isClosed':'false'}},
                {'id':'won','label':'Won','metadata':{'isClosed':'true'}}]}]})
        if '/properties/' in path:
            if request.method=='GET' and not self.properties:return httpx.Response(404)
            if request.method=='POST':self.properties=True
            return httpx.Response(200,json={'hasUniqueValue':True,'type':'string'})
        if '/associations/' in path:
            if request.method=='PUT':self.associated=True;return httpx.Response(204)
            return httpx.Response(200,json={'results':[{'toObjectId':'111'}] if self.associated else []})
        if path=='/appinstalls/v3/external-install':return httpx.Response(204)
        kind='contacts' if '/contacts' in path else 'deals'
        if request.method=='GET':return httpx.Response(200,json=self.records[kind]) if kind in self.records else httpx.Response(404)
        if request.method=='DELETE':self.records.pop(kind,None);return httpx.Response(204)
        data=json.loads(request.content)['properties']
        if kind=='contacts' and str(data.get('email','')).endswith('.invalid'):
            return httpx.Response(400,json={'category':'VALIDATION_ERROR','errors':[
                {'code':'INVALID_EMAIL','context':{'propertyName':['email']}}]})
        self.records[kind]={'id':'111' if kind=='contacts' else '222','properties':data}
        return httpx.Response(200,json=self.records[kind])


def native(database,zone='UTC',*,wire=None):
    engine,settings=database;wire=wire if wire is not None else NativeFixture()
    config=parse_live_crm(config_values(),'http://localhost:45860',now=NOW)
    settings=replace(settings,testing=False,origin='http://localhost:45860',crm_provider='hubspot',live_crm=config)
    http=httpx.Client(base_url='https://api.hubapi.com',transport=httpx.MockTransport(wire))
    provider=compose_crm(settings,engine,client=http,clock=lambda:NOW)
    client=TestClient(create_app(settings,engine,lambda:NOW,crm_provider=provider))
    headers={'x-choreograph-bridge':settings.bridge_secret,'origin':settings.origin}
    state=client.post('/v1/session',headers=headers,json={'timezone':zone}).json();headers['x-csrf-token']=state['csrf']
    return client,headers,state,provider,wire,settings,http


def setup(client,headers,state,*,allow_schema=True,pipeline='visitor-pipeline'):
    return command(client,headers,state,{'connection_id':state['connection']['id'],'confirm':True,
        'pipeline_id':pipeline,'stage_id':'queue','allow_schema':allow_schema},'/v1/crm/setup',method='post')


def test_acceptance_crm_lane_runs_only_reviewed_destination_and_cleanup(database,monkeypatch):
    from choreograph.acceptance import execute_crm
    original=config_values
    monkeypatch.setattr('test_live_crm.config_values',lambda:{**original(),'CHOREOGRAPH_CRM_REQUESTS':'60'})
    client,headers,state,provider,wire,settings,http=native(database)
    try:
        state,_=connect(client,headers,state);state=setup(client,headers,state).json()['state']
        state=command(client,headers,state,{'connection_id':state['connection']['id'],'confirm':True},'/v1/crm/consent',method='post').json()['state']
        state=command(client,headers,state,{'service':'regular','bedrooms':1}).json()['state']
        week=client.get('/v1/availability?week='+state['scenario']['week_start'],headers=headers).json()
        start=next(day['slots'][0]['start'] for day in week['days'] if day['date']==state['scenario']['alternative_date'])
        state=command(client,headers,state,{'preferred_at':start}).json()['state']
        state=command(client,headers,state,{'accept_quote':True},'/v1/requests',method='post').json()['state']
        state=book(client,headers,state,state['requests'][0]['id']).json()['state']
        wid=UUID(state['workspace_id'])
        with pytest.raises(Exception,match='ACCEPTANCE_CRM_SCOPE'):
            execute_crm(database[0],settings,uuid4(),wid,'another-account','sync',provider=provider,clock=lambda:NOW,injected=True)
        receipt=execute_crm(database[0],settings,uuid4(),wid,'456','sync',provider=provider,clock=lambda:NOW,injected=True)
        assert receipt['mode']=='injected' and receipt['verification']=='fresh_provider_readback'
        assert receipt['verified_record_references']=={'contact':'111','deal':'222'}
        result=execute_crm(database[0],settings,uuid4(),wid,'456','cleanup',provider=provider,clock=lambda:NOW,injected=True,uninstall=True)
        assert result['status']=='succeeded' and not wire.records
        assert len(wire.requests)<=60 and not http.is_closed
    finally:client.close();http.close()


def test_borrowed_transport_cannot_redirect_or_retarget_credentials():
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(302,headers={'location':'https://other.invalid/stolen'})
    http=httpx.Client(base_url='https://wrong.invalid',follow_redirects=True,transport=httpx.MockTransport(handler))
    provider=HubSpotTransport(HubSpotConfig('123','synthetic-client','synthetic-secret',
        'http://localhost:45860/auth/hubspot/callback'),authorized=True,client=http)
    try:
        with pytest.raises(CRMFailure):provider._request('GET','/crm/v3/pipelines/deals',tokens={'access_token':'fixture'})
        assert len(calls)==1 and calls[0].url.host=='api.hubapi.com'
    finally:http.close()


def test_native_account_destination_schema_consent_booking_verified_links_and_cleanup(database):
    client,headers,state,provider,wire,settings,http=native(database)
    try:
        assert state['profile']=='fake' and state['crm_provider']=='hubspot'
        state,_=connect(client,headers,state)
        assert state['connection']['state']=='setup' and len(wire.requests)==3
        assert not wire.properties and not wire.records
        assert len(state['connection']['destinations'][0]['stages'])==1
        assert command(client,headers,state,{'connection_id':state['connection']['id'],'confirm':True},
            '/v1/crm/consent',method='post').status_code==409
        failed=setup(client,headers,state,allow_schema=False).json()
        state=failed['state'];assert state['connection']['state']=='setup' and not wire.properties
        wrong=setup(client,headers,state,pipeline='operator-pipeline').json()
        state=wrong['state'];assert state['connection']['state']=='setup' and not wire.properties
        state=setup(client,headers,state).json()['state']
        assert state['connection']['state']=='ready' and wire.properties and not wire.records
        state=command(client,headers,state,{'connection_id':state['connection']['id'],'confirm':True},
            '/v1/crm/consent',method='post').json()['state']
        state=command(client,headers,state,{'service':'regular','bedrooms':2}).json()['state']
        week=client.get('/v1/availability?week='+state['scenario']['week_start'],headers=headers).json()
        start=next(day['slots'][0]['start'] for day in week['days'] if day['date']==state['scenario']['alternative_date'])
        state=command(client,headers,state,{'preferred_at':start}).json()['state']
        state=command(client,headers,state,{'accept_quote':True},'/v1/requests',method='post').json()['state']
        state=book(client,headers,state,state['requests'][0]['id']).json()['state']
        assert not state['requests'][0]['crm_links']
        assert jobs.tick(database[0],settings,provider,lambda:NOW)==1
        state=client.get('/v1/session',headers=headers).json()
        assert state['requests'][0]['crm_state']=='synced' and len(state['requests'][0]['crm_links'])==2
        mapping_key=(UUID(state['workspace_id']),UUID(state['connection']['id']),UUID(state['requests'][0]['id']))
        with Session(database[0]) as db,db.begin():db.get(ExternalMapping,mapping_key).contact_id='not-numeric'
        assert set(client.get('/v1/session',headers=headers).json()['requests'][0]['crm_links'])=={'booking'}
        with Session(database[0]) as db,db.begin():db.get(ExternalMapping,mapping_key).contact_id='111'
        with Session(database[0]) as db,pytest.raises(IntegrityError),db.begin():
            db.get(Connection,mapping_key[:2]).destination={'pipeline_id':'different','stage_id':'queue'}
        assert wire.records['deals']['properties']['pipeline']=='visitor-pipeline'
        assert wire.records['deals']['properties']['dealstage']=='queue'
        state=command(client,headers,state,{'connection_id':state['connection']['id'],'confirm':True,
            'cleanup':True,'uninstall':True},'/v1/crm/finish',method='post').json()['state']
        assert jobs.tick(database[0],settings,provider,lambda:NOW)==1
        assert not wire.records
        with Session(database[0]) as db:
            assert db.get(Installation,('123','456')).state=='uninstalled'
            assert db.get(CRMGrant,settings.live_crm.allowance.grant_id).requests==len(wire.requests)
        provider.close();assert not http.is_closed  # Borrowed transport remains caller-owned.
    finally:client.close();http.close()


@pytest.mark.parametrize('connection_state',['setup','ready','detached'])
def test_explicit_uninstall_without_record_cleanup_uses_native_delete_and_separate_receipt(database,connection_state):
    account=1_000_000_000+int(uuid4().hex[:8],16)

    class AccountFixture(NativeFixture):
        def __call__(self,request):
            response=super().__call__(request)
            if request.url.path.endswith('/introspect'):
                return httpx.Response(200,json={**response.json(),'hub_id':account})
            if request.url.path=='/account-info/2026-09/details':
                return httpx.Response(200,json={**response.json(),'portalId':account})
            return response

    client,headers,state,provider,wire,settings,http=native(database,wire=AccountFixture())
    try:
        state,_=connect(client,headers,state)
        if connection_state!='setup':state=setup(client,headers,state).json()['state']
        if connection_state=='detached':state=command(client,headers,state,{},'/v1/crm/disconnect',method='post').json()['state']
        assert state['connection']['state']==connection_state and state['connection']['can_uninstall']
        before=len(wire.requests)
        response=command(client,headers,state,{'connection_id':state['connection']['id'],'confirm':True,
            'cleanup':False,'uninstall':True},'/v1/crm/finish',method='post')
        assert response.status_code==200
        state=response.json()['state']
        assert state['connection']['state']=='finishing' and len(wire.requests)==before
        assert jobs.tick(database[0],settings,provider,lambda:NOW)==1
        calls=wire.requests[before:]
        assert [(request.method,request.url.path) for request in calls]==[('DELETE','/appinstalls/v3/external-install')]
        assert calls[0].headers['authorization']=='Bearer synthetic-access'
        state=client.get('/v1/session',headers=headers).json()
        assert state['crm_mode']=='skipped' and state['connection']['state']=='finished'
        assert state['connection']['cleanup_state']=='not_requested' and state['connection']['uninstall_state']=='removed'
        with Session(database[0]) as db:
            connection=db.get(Connection,(UUID(state['workspace_id']),UUID(state['connection']['id'])))
            assert connection.encrypted_tokens is None
            assert db.get(Installation,('123',str(account))).state=='uninstalled'
        assert jobs.tick(database[0],settings,provider,lambda:NOW)==0
        assert len(wire.requests)==before+1
    finally:client.close();http.close()


def test_true_skip_has_zero_real_calls_and_mismatched_tokens_and_oauth_never_reach_transport(database):
    client,headers,state,provider,wire,_,http=native(database)
    fake,fh,fs,_=begin(database)
    try:
        state=command(client,headers,state,{},'/v1/crm/skip',method='post').json()['state']
        assert not wire.requests
        fs,_=connect(fake,fh,fs)
        with Session(database[0]) as db,pytest.raises(CRMFailure) as mismatch:
            connection=db.get(Connection,(UUID(fs['workspace_id']),UUID(fs['connection']['id'])))
            crm.tokens_for(db,connection,database[1].token_key,provider,NOW)
        assert mismatch.value.code=='CRM_PROVIDER_CHANGED' and not wire.requests
        challenge=command(client,headers,state,{},'/v1/crm/connect',method='post').json()
        provider.app_id='999'
        result=command(client,headers,challenge['state'],{'state':challenge['oauth']['state'],'code':'synthetic'},
            '/v1/crm/callback',method='post')
        assert result.status_code==409 and result.json()['code']=='CRM_PROVIDER_CHANGED' and not wire.requests
        with Session(database[0]) as db:
            assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.workspace_id==state['workspace_id']))==0
    finally:client.close();fake.close();http.close()


def test_existing_booking_exports_only_after_consent_and_tracks_move_cancel_without_duplicates(database):
    client,headers,state,provider,wire,settings,http=native(database,'Asia/Kathmandu')
    try:
        state=command(client,headers,state,{'service':'regular','bedrooms':1}).json()['state']
        week=client.get('/v1/availability',headers=headers).json()
        start=next(slot['start'] for day in week['days'] for slot in day['slots'])
        state=command(client,headers,state,{'preferred_at':start}).json()['state']
        state=command(client,headers,state,{'accept_quote':True},'/v1/bookings',method='post').json()['state']
        record=state['requests'][0];assert not wire.requests
        # A declined unreserved request is not a reviewed booking to export.
        state=command(client,headers,state,{'accept_quote':True},'/v1/requests',method='post').json()['state']
        pending=state['requests'][-1]
        state=book(client,headers,state,pending['id'],'cancel').json()['state']
        state,_=connect(client,headers,state);state=setup(client,headers,state).json()['state']
        assert not wire.records
        consent={'connection_id':state['connection']['id'],'confirm':True}
        state=command(client,headers,state,consent,'/v1/crm/consent',method='post').json()['state']
        state=command(client,headers,state,consent,'/v1/crm/consent',method='post').json()['state']
        with Session(database[0]) as db:
            assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.workspace_id==state['workspace_id'],Outbox.kind=='crm_upsert'))==1
        assert jobs.tick(database[0],settings,provider,lambda:NOW)==1
        deal=wire.records['deals']['properties']
        assert deal['amount']=='60' and deal['deal_currency_code']=='USD'
        assert '+05:45' in deal['description'] and 'Asia/Kathmandu' not in deal['description']
        assert 'Status: confirmed' in deal['description'] and wire.associated
        alternatives=client.get(f"/v1/requests/{record['id']}/availability",headers=headers).json()
        candidate=next(slot['start'] for day in alternatives['days'] for slot in day['slots'] if slot['start']!=start)
        state=book(client,headers,state,record['id'],'reschedule',{'preferred_at':candidate}).json()['state']
        assert jobs.tick(database[0],settings,provider,lambda:NOW)==1
        key=str(uuid4());before=state
        state=book(client,headers,state,record['id'],'cancel',key=key).json()['state']
        assert jobs.tick(database[0],settings,provider,lambda:NOW)==1
        replay=book(client,headers,before,record['id'],'cancel',key=key).json()
        assert replay['replayed'] and jobs.tick(database[0],settings,provider,lambda:NOW)==0
        assert len(wire.records)==2 and 'Status: cancelled' in wire.records['deals']['properties']['description']
        assert sum(request.method=='POST' and request.url.path=='/crm/v3/objects/deals' for request in wire.requests)==1
        current=client.get('/v1/session',headers=headers).json()
        assert next(row for row in current['requests'] if row['id']==record['id'])['crm_state']=='synced'
    finally:client.close();http.close()


def test_booking_schedule_and_completion_update_same_verified_native_deal(database):
    client,headers,state,provider,wire,settings,http=native(database,'Asia/Kathmandu')
    try:
        state,_=connect(client,headers,state);state=setup(client,headers,state).json()['state']
        state=command(client,headers,state,{'connection_id':state['connection']['id'],'confirm':True},
            '/v1/crm/consent',method='post').json()['state']
        state=command(client,headers,state,{'service':'regular','bedrooms':1}).json()['state']
        week=client.get('/v1/availability',headers=headers).json()
        start=next(slot['start'] for day in week['days'] for slot in day['slots'])
        state=command(client,headers,state,{'preferred_at':start}).json()['state']
        assert not wire.records  # Draft/calendar selection does not export a booking.
        state=command(client,headers,state,{'accept_quote':True},'/v1/bookings',method='post').json()['state']
        record=state['requests'][0]
        assert record['crm_state']=='pending' and not record['crm_links']
        assert jobs.tick(database[0],settings,provider,lambda:NOW)==1
        current=client.get('/v1/session',headers=headers).json()['requests'][0]
        assert current['crm_state']=='synced' and set(current['crm_links'])=={'contact','booking'}
        links=dict(current['crm_links'])
        local_start=datetime.fromisoformat(record['booking']['starts_at']).astimezone(ZoneInfo('Asia/Kathmandu'))
        local_end=datetime.fromisoformat(record['booking']['ends_at']).astimezone(ZoneInfo('Asia/Kathmandu'))
        assert local_end-local_start==timedelta(minutes=90)
        expected_description=(f'Fictional demo booking\nStatus: confirmed\nAppointment: {local_start.isoformat(timespec="minutes")}\n'
            f'Ends: {local_end.isoformat(timespec="minutes")}\nCleaner: {record["booking"]["staff_id"].title()}\n'
            'Quote: USD 60.00\nDuration: 90 minutes\nNo real service or payment.')
        deal=wire.records['deals']['properties']
        assert deal['description']==expected_description and deal['amount']=='60'
        assert deal['deal_currency_code']=='USD' and deal['pipeline']=='visitor-pipeline' and deal['dealstage']=='queue'
        contact=wire.records['contacts']['properties']
        assert contact['firstname']=='Demo' and contact['lastname']=='Guest' and 'email' not in contact
        assert state['connection']['contact_email']==''
        assert wire.associated
        state=client.get('/v1/session',headers=headers).json()
        state=book(client,headers,state,record['id'],'complete').json()['state']
        assert state['requests'][0]['status']=='completed' and state['requests'][0]['crm_state']=='pending'
        assert not state['requests'][0]['crm_links']
        assert jobs.tick(database[0],settings,provider,lambda:NOW)==1
        current=client.get('/v1/session',headers=headers).json()['requests'][0]
        assert current['crm_state']=='synced' and current['crm_links']==links
        assert wire.records['deals']['properties']['description']==expected_description.replace('Status: confirmed','Status: completed')
        assert wire.records['deals']['properties']['dealstage']=='queue'
        for kind in ('contacts','deals'):
            assert sum(request.method=='POST' and request.url.path==f'/crm/v3/objects/{kind}' for request in wire.requests)==1
        assert not any('/meetings' in request.url.path or '/appointments' in request.url.path for request in wire.requests)
    finally:client.close();http.close()


@pytest.mark.parametrize('tamper,code',[('deal','CRM_READBACK'),('association','CRM_ASSOCIATION')])
def test_native_readback_mismatch_never_claims_sync_or_loses_local_booking(database,tamper,code):
    class UnverifiedResult(NativeFixture):
        def __call__(self,request):
            result=super().__call__(request)
            if request.method=='GET' and result.status_code==200:
                if tamper=='deal' and request.url.path.startswith('/crm/v3/objects/deals/'):
                    payload=result.json()
                    return httpx.Response(200,json={**payload,'properties':{**payload['properties'],'amount':'999'}})
                if tamper=='association' and request.url.path.endswith('/associations/contacts'):
                    return httpx.Response(200,json={'results':[]})
            return result
    client,headers,state,provider,wire,settings,http=native(database,wire=UnverifiedResult())
    try:
        state,_=connect(client,headers,state);state=setup(client,headers,state).json()['state']
        state=command(client,headers,state,{'connection_id':state['connection']['id'],'confirm':True},
            '/v1/crm/consent',method='post').json()['state']
        state=command(client,headers,state,{'service':'regular','bedrooms':1}).json()['state']
        week=client.get('/v1/availability',headers=headers).json()
        start=next(slot['start'] for day in week['days'] for slot in day['slots'])
        state=command(client,headers,state,{'preferred_at':start}).json()['state']
        state=command(client,headers,state,{'accept_quote':True},'/v1/bookings',method='post').json()['state']
        record=state['requests'][0]
        assert jobs.tick(database[0],settings,provider,lambda:NOW)==1
        current=client.get('/v1/session',headers=headers).json()['requests'][0]
        assert current['status']=='confirmed' and current['booking']==record['booking']
        assert current['crm_state']=='reconciling' and current['crm_receipt'] is None and not current['crm_links']
        with Session(database[0]) as db:
            event=db.scalar(select(Outbox).where(Outbox.workspace_id==state['workspace_id'],Outbox.kind=='crm_upsert'))
            assert event.code==code and event.state=='reconciling'
    finally:client.close();http.close()


def test_missing_account_currency_response_is_not_reported_as_non_usd_or_allowed_to_write_schema(database):
    class MissingDetails(NativeFixture):
        def __call__(self,request):
            if request.url.path=='/account-info/2026-09/details':
                self.requests.append(request);return httpx.Response(404)
            return super().__call__(request)
    client,headers,state,_,wire,_,http=native(database,wire=MissingDetails())
    try:
        state,_=connect(client,headers,state)
        rejected=setup(client,headers,state).json()
        assert rejected['state']['connection']['state']=='setup'
        assert 'currency could not be verified' in rejected['crm_notice'] and 'USD' not in rejected['crm_notice']
        assert not wire.properties and not wire.records
    finally:client.close();http.close()


def test_currency_mismatch_blocks_schema_setup_and_later_export_without_changing_account(database):
    client,headers,state,provider,wire,settings,http=native(database)
    try:
        state,_=connect(client,headers,state);wire.currency='EGP'
        rejected=setup(client,headers,state).json();state=rejected['state']
        assert state['connection']['state']=='setup' and 'USD' in rejected['crm_notice']
        assert not wire.properties and not wire.records
        wire.currency='USD';state=setup(client,headers,state).json()['state']
        state=command(client,headers,state,{'connection_id':state['connection']['id'],'confirm':True},'/v1/crm/consent',method='post').json()['state']
        state=command(client,headers,state,{'service':'regular','bedrooms':1}).json()['state']
        week=client.get('/v1/availability',headers=headers).json()
        start=next(slot['start'] for day in week['days'] for slot in day['slots'])
        state=command(client,headers,state,{'preferred_at':start}).json()['state']
        state=command(client,headers,state,{'accept_quote':True},'/v1/bookings',method='post').json()['state']
        wire.currency='EGP';assert jobs.tick(database[0],settings,provider,lambda:NOW)==1
        assert not wire.records
        with Session(database[0]) as db:
            event=db.scalar(select(Outbox).where(Outbox.workspace_id==state['workspace_id'],Outbox.kind=='crm_upsert'))
            assert event.code=='CRM_CURRENCY_REQUIRED' and event.state=='needs_attention'
        assert all(request.method=='GET' for request in wire.requests if request.url.path.startswith(('/settings/','/account-info/')))
    finally:client.close();http.close()


def test_last_crm_request_has_one_winner_and_survives_business_rollback(database):
    engine,_=database;scope=uuid4();allowance=CRMAllowance('race-'+uuid4().hex,'123',NOW+timedelta(hours=1),1,1)
    def reserve():
        try:CRMAdmission(engine,allowance,scope,lambda:NOW).reserve();return True
        except CRMFailure:return False
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(lambda _:reserve(),range(2)))==[False,True]
    with Session(engine) as db:
        assert db.get(CRMGrant,allowance.grant_id).requests==1
        assert db.scalar(select(func.count()).select_from(CRMCall).where(CRMCall.grant_id==allowance.grant_id))==1
    assert reserve() is False


def test_unknown_oauth_capacity_is_scoped_to_app(database):
    engine,_=database
    client,headers,state,provider,wire,_,http=native(database)
    try:
        with Session(engine) as db,db.begin():
            for _ in range(10):db.add(OAuthState(state_hash=uuid4().hex+uuid4().hex,
                workspace_id=UUID(state['workspace_id']),generation=1,expires_at=NOW,used=True,outcome='unknown',
                provider='hubspot',app_id='other-app'))
            db.flush();assert crm.available(db,provider,NOW)
        assert not wire.requests
    finally:client.close();http.close()


@pytest.mark.parametrize('response,code', [
    (lambda:httpx.Response(200,headers={'content-encoding':'gzip'},stream=httpx.ByteStream(b'not expanded')),'CRM_RESPONSE_ENCODING'),
    (lambda:httpx.Response(200,headers={'content-length':'262145'},content=b'{}'),'CRM_RESPONSE_LIMIT'),
    (lambda:httpx.Response(200,content=b'x'*262145),'CRM_RESPONSE_LIMIT'),
    (lambda:httpx.Response(200,json=[]),'CRM_FORMAT'),
])
def test_raw_response_bounds_reject_without_retry(response,code):
    calls=[]
    def handler(request):calls.append(1);return response()
    http=httpx.Client(base_url='https://api.hubapi.com',transport=httpx.MockTransport(handler))
    provider=HubSpotTransport(HubSpotConfig('123','synthetic-client','synthetic-secret',
        'http://localhost:45860/auth/hubspot/callback'),authorized=True,client=http)
    try:
        with pytest.raises(CRMFailure) as error:provider._request('GET','/crm/v3/pipelines/deals')
        assert error.value.code==code and calls==[1]
    finally:http.close()


def test_composed_real_provider_requires_workspace_admission_and_test_settings_reject_live(database):
    client,_,_,provider,wire,settings,http=native(database)
    try:
        with pytest.raises(CRMFailure) as error:provider._request('GET','/crm/v3/pipelines/deals')
        assert error.value.code=='CRM_NOT_CONFIGURED' and not wire.requests
        with pytest.raises(ValueError,match='TEST_PROVIDER_FORBIDDEN'):
            Settings.parse({**config_values(),'CHOREOGRAPH_CRM_PROVIDER':'hubspot',
                'CHOREOGRAPH_DATABASE_URL':settings.database_url,'CHOREOGRAPH_ORIGIN':settings.origin,
                'CHOREOGRAPH_BRIDGE_SECRET':settings.bridge_secret,'CHOREOGRAPH_TOKEN_KEY':settings.token_key},testing=True)
        expired=replace(settings.live_crm,allowance=replace(settings.live_crm.allowance,expires_at=NOW-timedelta(seconds=1)))
        with pytest.raises(ValueError,match='CRM_ALLOWANCE_EXPIRED'):
            compose_crm(replace(settings,live_crm=expired),database[0],clock=lambda:NOW)
    finally:client.close();http.close()


def test_response_deadline_is_checked_even_when_late_eof_has_no_chunk(monkeypatch):
    from choreograph import hubspot
    clock=[0.]
    class LateEOF(httpx.SyncByteStream):
        def __iter__(self):
            yield b'{}'
            clock[0]=9.
    monkeypatch.setattr(hubspot,'time',SimpleNamespace(monotonic=lambda:clock[0]))
    http=httpx.Client(base_url='https://api.hubapi.com',transport=httpx.MockTransport(
        lambda _:httpx.Response(200,stream=LateEOF())))
    provider=HubSpotTransport(HubSpotConfig('123','synthetic-client','synthetic-secret',
        'http://localhost:45860/auth/hubspot/callback'),authorized=True,client=http)
    try:
        with pytest.raises(CRMFailure) as error:provider._request('DELETE','/appinstalls/v3/external-install')
        assert error.value.code=='CRM_TIMEOUT' and error.value.ambiguous
    finally:http.close()


def test_refresh_is_admitted_and_retains_the_selected_account(database):
    client,_,state,provider,wire,settings,http=native(database)
    try:
        scoped=provider.with_workspace(UUID(state['workspace_id']))
        refreshed=scoped.refresh({'account_id':'456','refresh_token':'synthetic-refresh'})
        assert refreshed['account_id']=='456' and len(wire.requests)==2
        with Session(database[0]) as db:
            assert db.get(CRMGrant,settings.live_crm.allowance.grant_id).requests==2
        limited=replace(settings.live_crm.allowance,grant_id='limited-'+uuid4().hex,requests=1,workspace_requests=1)
        scoped=compose_crm(replace(settings,live_crm=replace(settings.live_crm,allowance=limited)),
            database[0],client=http,clock=lambda:NOW).with_workspace(UUID(state['workspace_id']))
        with pytest.raises(CRMFailure) as error:scoped.refresh({'account_id':'456','refresh_token':'synthetic-refresh'})
        assert error.value.code=='CRM_ALLOWANCE_LIMIT' and len(wire.requests)==3
    finally:client.close();http.close()


def test_populated_crm_migration_preserves_fake_tokens_and_quarantines_unattributed_real_tokens():
    fixture=database_fixture.__wrapped__();engine,_=next(fixture)
    try:
        downgrade(engine,'0007')
        wid=uuid4();fake,live=uuid4(),uuid4()
        with engine.begin() as db:
            db.execute(text("INSERT INTO workspaces (id,session_hash,timezone,created_at,expires_at,active,generation,revision,seeded,draft,messages,crm_mode) "
                "VALUES (:id,:hash,'UTC',:now,:until,true,1,1,false,'{}','[]','skipped')"),
                {'id':wid,'hash':uuid4().hex+uuid4().hex,'now':NOW,'until':NOW+timedelta(hours=2)})
            for cid,kind in [(fake,'fake'),(live,'hubspot')]:
                db.execute(text("INSERT INTO crm_connections(workspace_id,id,account_id,generation,state,provider,encrypted_tokens,export_consent,created_at) "
                    "VALUES (:wid,:id,:account,1,'ready',:provider,:token,true,:now)"),
                    {'wid':wid,'id':cid,'account':str(cid),'provider':kind,'token':b'synthetic-encrypted-opaque','now':NOW})
        migrate(engine)
        with Session(engine) as db:
            old_fake=db.get(Connection,(wid,fake));old_live=db.get(Connection,(wid,live))
            assert old_fake.app_id=='choreograph-local-simulation' and old_fake.state=='ready' and old_fake.export_consent
            assert old_fake.encrypted_tokens==b'synthetic-encrypted-opaque'
            assert old_live.app_id=='legacy-unverified' and old_live.state=='needs_attention' and not old_live.export_consent
            assert old_live.encrypted_tokens==b'synthetic-encrypted-opaque'
        with pytest.raises(RuntimeError,match='LIVE_CRM_DOWNGRADE_FORBIDDEN'):downgrade(engine,'0007')
    finally:fixture.close()
