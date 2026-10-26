"""Offline container/file-store acceptance. No listeners, SQL or real providers."""
# Bootstrap the packaged backend path before importing the application.
# ruff: noqa: E402
import base64
import json
import secrets
import subprocess
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

root=Path(__file__).resolve().parents[1] if '__file__' in globals() and Path(__file__).name!='<stdin>' else Path('/app')
sys.path.insert(0,str(root/'apps/backend'))
from choreograph import knowledge
from choreograph.api import create_app
from choreograph.hubspot import FakeHubSpot
from choreograph.object_store import FileObjects, ObjectEngine
from choreograph.persistence import Session
from choreograph.settings import Settings

now=datetime.now(UTC)
key=base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
bridge=secrets.token_hex(32)
values={'DATABASE_ENABLED':'false','FAKE_MODE':'true','CHOREOGRAPH_TOKEN_KEY':key,
        'CHOREOGRAPH_BRIDGE_SECRET':bridge}
settings=Settings.parse(values,testing=True)

with tempfile.TemporaryDirectory(prefix='choreograph-object-smoke-') as private:
    engine=ObjectEngine(FileObjects(private),key)
    with Session(engine) as db,db.begin():knowledge.prepare_samples(db,now)
    provider=FakeHubSpot(engine)
    headers={'origin':settings.origin,'x-choreograph-bridge':bridge}
    with TestClient(create_app(settings,engine,lambda:now,crm_provider=provider)) as client:
        response=client.post('/v1/session',headers=headers,json={'timezone':'Africa/Cairo'})
        assert response.status_code==200,response.text
        state=response.json();headers['x-csrf-token']=state['csrf']
        assert len(state['documents'])==6 and state['profile']=='fake'
        def command(path,fields,method='post',action_key=None):
            global state
            result=getattr(client,method)(path,headers={**headers,'idempotency-key':action_key or str(uuid4())},
                json={'generation':state['generation'],'revision':state['revision'],**fields})
            assert result.status_code==200,result.text
            state=result.json()['state']
            return result.json()
        command('/v1/chat',{'text':'What cleaning supplies do you bring?'})
        claim=state['messages'][-1]['claims'][0]
        source=client.get('/v1/documents/'+claim['version_id']+'/source',headers=headers)
        assert source.status_code==200 and source.content.startswith(b'%PDF')
        command('/v1/chat',{'text':'Reserve an appointment.'})
        assert state['messages'][-1]['cards']==['reserve'] and state['quote'] is None
        challenge=command('/v1/crm/connect',{})['oauth']
        command('/v1/crm/callback',{'state':challenge['state'],'code':'approved'})
        command('/v1/crm/consent',{'connection_id':state['connection']['id'],'confirm':True})
        command('/v1/draft',{'service':'regular','bedrooms':2},'put')
        week=client.get('/v1/availability?week='+state['scenario']['week_start'],headers=headers).json()
        day=next(item for item in week['days'] if item['date']==state['scenario']['alternative_date'])
        assert day['slots']
        command('/v1/draft',{'preferred_at':day['slots'][0]['start']},'put')
        action_key=str(uuid4());review=dict(state)
        accepted=command('/v1/bookings',{'accept_quote':True},action_key=action_key)
        assert accepted['receipt']['action']=='confirmed' and state['requests'][0]['quote']['cents']==8000
        replay=client.post('/v1/bookings',headers={**headers,'idempotency-key':action_key},
            json={'generation':review['generation'],'revision':review['revision'],'accept_quote':True})
        assert replay.status_code==200 and replay.json()['replayed']
        request=state['requests'][0]
        alternatives=client.get('/v1/requests/'+request['id']+'/availability?start='+day['date'],headers=headers).json()
        later=next(slot for item in alternatives['days'] for slot in item['slots']
                   if slot['start']!=request['booking']['starts_at'])
        command('/v1/requests/'+request['id']+'/reschedule',{'request_revision':request['revision'],
            'confirm':True,'preferred_at':later['start']})
        token=client.cookies.get('choreograph_guest');wid=state['workspace_id']
        assert state['requests'][0]['preferred_at']==later['start']
    # A distinct Python process owns delivery/expiry after the browser closes.
    child='''import json,sys
from datetime import datetime
from choreograph.object_store import FileObjects,ObjectEngine
from choreograph.settings import Settings
from choreograph.hubspot import FakeHubSpot
from choreograph.task_delivery import MaintenanceTarget,create_delivery_app
from fastapi.testclient import TestClient
data=json.load(sys.stdin)
engine=ObjectEngine(FileObjects(data['root']),data['values']['CHOREOGRAPH_TOKEN_KEY'])
settings=Settings.parse(data['values'],testing=True)
provider=FakeHubSpot(engine)
target=MaintenanceTarget('https://worker.example.invalid/internal/maintenance','https://worker.example.invalid',
    'scheduler@test-project.iam.gserviceaccount.com')
claims={'iss':'https://accounts.google.com','aud':target.audience,'email':target.service_email,'email_verified':True}
app=create_delivery_app(settings,engine,provider,maintenance_target=target,verifier=lambda *_:claims,
    clock=lambda:datetime.fromisoformat(data['now']))
with TestClient(app) as client:
    assert client.post('/internal/tasks/crm',json={}).status_code==404
    assert client.post('/internal/maintenance',json={'sweep':True}).status_code==403
    response=client.post('/internal/maintenance',headers={'authorization':'Bearer injected-scheduler'},json={'sweep':True})
    assert response.status_code==204,response.text
print(json.dumps({'calls':provider.calls}))
engine.dispose()
'''
    def process(at):
        result=subprocess.run([sys.executable,'-c',child],input=json.dumps({'root':private,'values':values,'now':at.isoformat()}),
            text=True,capture_output=True,timeout=30,check=True,cwd=root/'apps/backend')
        return json.loads(result.stdout)
    # Booking and rescheduling leave two intents. A bounded sweep may retire
    # the stale revision first; UUID ordering must not decide test success.
    delivered=[]
    for _ in range(2):delivered.extend(process(now)['calls'])
    assert delivered.count('upsert-contacts')==1 and delivered.count('upsert-deals')==1
    restarted=ObjectEngine(FileObjects(private),key)
    with TestClient(create_app(settings,restarted,lambda:now,crm_provider=FakeHubSpot(restarted)),
                    cookies={'choreograph_guest':token}) as client:
        restored=client.get('/v1/session',headers=headers).json()
        assert restored['workspace_id']==wid and restored['requests'][0]['crm_state']=='simulated_synced'
    cleaned=process(now+timedelta(hours=2,seconds=1))
    assert 'archive-deals' in cleaned['calls'] and 'archive-contacts' in cleaned['calls']
    assert 'uninstall' not in cleaned['calls']
    with TestClient(create_app(settings,restarted,lambda:now+timedelta(hours=3),crm_provider=FakeHubSpot(restarted)),
                    cookies={'choreograph_guest':token}) as client:
        assert client.get('/v1/session',headers=headers).status_code==410
    assert all(b'fake-refresh' not in path.read_bytes() for path in Path(private).glob('*.bin'))
    engine.dispose();restarted.dispose()
print(json.dumps({'storage':'encrypted-private-objects','sql_connections':0,'real_provider_calls':0,
    'checks':['original_sources','guide_retrieval','rolling_discovery','quote','booking','idempotent_replay',
              'reschedule','separate_process_scheduled_sync','refresh','browser_closed_scheduled_cleanup',
              'encrypted_credentials','no_tasks_route','scheduler_identity']}))
