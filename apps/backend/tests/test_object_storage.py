"""Real private file persistence, injected providers, and public API parity."""
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from test_requests import NOW, command

from choreograph import jobs, knowledge
from choreograph.api import create_app
from choreograph.errors import DomainError
from choreograph.hubspot import FakeHubSpot
from choreograph.models import Enquiry, Outbox, Reservation, Workspace
from choreograph.object_store import FileObjects, ObjectEngine
from choreograph.persistence import Session, repo_rows
from choreograph.settings import Settings


@pytest.fixture
def object_database(tmp_path):
    key=base64.urlsafe_b64encode(bytes(32)).decode()
    settings=Settings.parse({'DATABASE_ENABLED':'false','FAKE_MODE':'true',
        'CHOREOGRAPH_BRIDGE_SECRET':'test-only-'+'x'*40,'CHOREOGRAPH_TOKEN_KEY':key},testing=True)
    engine=ObjectEngine(FileObjects(tmp_path/'private'),key)
    with Session(engine) as db,db.begin():knowledge.prepare_samples(db,NOW)
    yield engine,settings
    engine.dispose()


def start(database,clock=None,provider=None):
    engine,settings=database
    client=TestClient(create_app(settings,engine,clock or (lambda:NOW),crm_provider=provider))
    headers={'x-choreograph-bridge':settings.bridge_secret,'origin':settings.origin}
    result=client.post('/v1/session',headers=headers,json={'timezone':'Africa/Cairo'})
    assert result.status_code==200,result.text
    state=result.json();headers['x-csrf-token']=state['csrf']
    return client,headers,state


def ready(client,headers,state):
    response=command(client,headers,state,{'service':'regular','bedrooms':2})
    assert response.status_code==200,response.text
    state=response.json()['state']
    days=client.get('/v1/availability?week='+state['scenario']['week_start'],headers=headers).json()['days']
    day=next(day for day in days if day['date']==state['scenario']['alternative_date'])
    response=command(client,headers,state,{'preferred_at':day['slots'][0]['start']})
    assert response.status_code==200,response.text
    return response.json()['state']


def test_no_database_configuration_default_and_rejected_ambiguous_switch():
    values={'CHOREOGRAPH_BRIDGE_SECRET':'x'*40,'CHOREOGRAPH_TOKEN_KEY':base64.urlsafe_b64encode(bytes(32)).decode()}
    assert not Settings.parse(values,testing=True).database_enabled
    for invalid in ('False','0','yes',''):
        with pytest.raises(ValueError,match='DATABASE_ENABLED_INVALID'):
            Settings.parse({**values,'DATABASE_ENABLED':invalid},testing=True)


def test_authority_is_encrypted_durable_and_cas_fenced(object_database):
    engine,settings=object_database
    a=Session(engine)
    with a.begin():
        row=Workspace(session_hash='a'*64,timezone='UTC',created_at=NOW,expires_at=NOW+timedelta(hours=2))
        a.add(row);wid=row.id
    a=Session(engine);b=Session(engine)
    left=a.get(Workspace,wid);right=b.get(Workspace,wid)
    with a.begin():left.revision+=1
    with pytest.raises(DomainError,match='STALE_REVISION'),b.begin():right.revision+=1
    restarted=ObjectEngine(FileObjects(engine.objects.root),settings.token_key)
    with Session(restarted) as db:assert len(repo_rows(db,Workspace))==1
    assert b'workspaces' not in next(engine.objects.root.glob('*.bin')).read_bytes()


def test_public_booking_chat_sources_refresh_and_expiry_without_sql(object_database,monkeypatch):
    import sqlalchemy
    monkeypatch.setattr(sqlalchemy,'create_engine',lambda *_a,**_kw:pytest.fail('SQL engine in no-database mode'))
    time=[NOW];client,headers,state=start(object_database,lambda:time[0])
    try:
        assert len(state['documents'])==6
        chat=command(client,headers,state,{'text':'What cleaning supplies do you bring?'},'/v1/chat',method='post')
        assert chat.status_code==200,chat.text
        state=chat.json()['state'];assert state['messages'][-1]['claims']
        source=state['messages'][-1]['claims'][0]
        assert client.get('/v1/documents/'+source['version_id'],headers=headers).status_code==200
        state=ready(client,headers,state)
        key=str(uuid4());body={'accept_quote':True}
        accepted=command(client,headers,state,body,'/v1/bookings',key,method='post')
        assert accepted.status_code==200,accepted.text
        booked=accepted.json()['state'];assert booked['requests'][0]['quote']['cents']==8000
        assert command(client,headers,state,body,'/v1/bookings',key,method='post').json()['replayed']
        assert client.get('/v1/session',headers=headers).json()['requests']==booked['requests']
        engine,_=object_database
        with Session(engine) as db:
            assert len(repo_rows(db,Enquiry))==1 and not repo_rows(db,Outbox)
        time[0]+=timedelta(hours=3)
        assert client.get('/v1/session',headers=headers).status_code==410
        jobs.maintenance(engine,time[0])
        with Session(engine) as db:
            workspace=db.get(Workspace,UUID(state['workspace_id']))
            assert not workspace.active and workspace.messages==[] and not repo_rows(db,Reservation)
    finally:client.close()


def test_competing_bookings_are_atomic_and_one_wins(object_database):
    client,headers,state=start(object_database)
    try:
        state=ready(client,headers,state);barrier=Barrier(2)
        def reserve(_):
            with TestClient(create_app(object_database[1],object_database[0],lambda:NOW),
                            cookies={'choreograph_guest':client.cookies.get('choreograph_guest')}) as other:
                barrier.wait(timeout=5)
                return command(other,headers,state,{'accept_quote':True},'/v1/bookings',method='post')
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(reserve,range(2)))
        assert sorted(result.status_code for result in results)==[200,409]
        with Session(object_database[0]) as db:assert len(repo_rows(db,Enquiry))==1
    finally:client.close()


def test_hubspot_export_and_reset_cleanup_survive_process_restart(object_database):
    from test_crm import connect
    engine,settings=object_database;provider=FakeHubSpot(engine)
    client,headers,state=start(object_database,provider=provider)
    try:
        state,_=connect(client,headers,state)
        consent=command(client,headers,state,{'connection_id':state['connection']['id'],'confirm':True},
                        '/v1/crm/consent',method='post')
        assert consent.status_code==200,consent.text
        state=ready(client,headers,consent.json()['state'])
        result=command(client,headers,state,{'accept_quote':True},'/v1/bookings',method='post')
        assert result.status_code==200,result.text
        state=result.json()['state']
        restarted=ObjectEngine(FileObjects(engine.objects.root),settings.token_key)
        provider=FakeHubSpot(restarted)
        assert jobs.tick(restarted,settings,provider,lambda:NOW)==1
        refreshed=client.get('/v1/session',headers=headers).json()
        assert refreshed['requests'][0]['crm_state']=='simulated_synced'
        reset=client.post('/v1/reset',headers={**headers,'idempotency-key':str(uuid4())},
            json={'generation':state['generation'],'timezone':'UTC'})
        assert reset.status_code==200,reset.text
        assert jobs.tick(restarted,settings,provider,lambda:NOW)==1
        assert 'archive-deals' in provider.calls and 'archive-contacts' in provider.calls
        assert 'uninstall' not in provider.calls
    finally:client.close()
