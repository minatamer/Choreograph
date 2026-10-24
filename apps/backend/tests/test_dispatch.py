"""Crash, queue deletion and lease recovery use actual isolated PostgreSQL."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from uuid import UUID

import httpx
import pytest
from conftest import database as database_fixture
from sqlalchemy.orm import Session
from test_jobs import claim_for, connected_booking
from test_requests import NOW
from test_task_enqueue import CONFIG

from choreograph import dispatch, jobs
from choreograph.models import Outbox, TaskPublication
from choreograph.task_delivery import task_payload
from choreograph.task_enqueue import CloudTasks, PublishFailure


@pytest.fixture
def isolated():
    fixture=database_fixture.__wrapped__()
    try:yield next(fixture)
    finally:fixture.close()


def test_lost_create_ack_reconciles_then_deleted_task_gets_new_epoch(isolated):
    import json
    engine,settings=isolated;client,_,state,crm,event=connected_booking(isolated)
    clock=[NOW];tasks={};names=[];lose=[True]
    def handle(request):
        if request.method=='POST':
            task=json.loads(request.content)['task'];names.append(task['name']);tasks[task['name']]=task
            if lose[0]:lose[0]=False;raise httpx.ReadTimeout('synthetic-lost-ack',request=request)
            return httpx.Response(200,json=task)
        name=request.url.path.removeprefix('/v2/')
        return httpx.Response(200,json=tasks[name]) if name in tasks else httpx.Response(404)
    http=httpx.Client(transport=httpx.MockTransport(handle))
    queue=CloudTasks(CONFIG,authorized=True,client=http,bearer=lambda:'synthetic-google-access')
    try:
        first=dispatch.claim(engine,CONFIG,clock[0]);assert first.event_id==event and first.action=='create'
        assert not dispatch.publish(engine,queue,first,lambda:clock[0])
        clock[0]+=timedelta(seconds=3)
        reconcile=dispatch.claim(engine,CONFIG,clock[0]);assert reconcile.action=='get' and reconcile.name==first.name
        assert dispatch.publish(engine,queue,reconcile,lambda:clock[0]) and len(names)==1
        tasks.clear();clock[0]+=timedelta(seconds=31)
        missing=dispatch.claim(engine,CONFIG,clock[0]);assert missing.action=='get'
        assert not dispatch.publish(engine,queue,missing,lambda:clock[0])
        clock[0]+=timedelta(seconds=5)
        replacement=dispatch.claim(engine,CONFIG,clock[0]);assert replacement.action=='create' and replacement.name!=first.name
        assert dispatch.publish(engine,queue,replacement,lambda:clock[0]) and len(set(names))==2
        job=claim_for(engine,state,event,clock[0]);assert jobs.deliver(engine,settings,crm,job,lambda:clock[0])
        calls=list(crm.calls);clock[0]+=timedelta(seconds=31)
        assert dispatch.claim(engine,CONFIG,clock[0]) is None and crm.calls==calls
        with Session(engine) as db:
            assert db.get(Outbox,(UUID(state['workspace_id']),event)).state=='synced'
            assert db.get(TaskPublication,(UUID(state['workspace_id']),event)).attempts==4
    finally:client.close();http.close()


def test_stale_publication_ack_cannot_overwrite_new_lease_and_reset_stops_network(isolated):
    from choreograph import crm as connections
    from choreograph.models import Workspace
    engine,_=isolated;client,_,state,_,event=connected_booking(isolated)
    try:
        old=dispatch.claim(engine,CONFIG,NOW)
        newer=dispatch.claim(engine,CONFIG,NOW+timedelta(seconds=31))
        assert newer and newer.action=='get' and newer.lease_token!=old.lease_token
        result={'name':newer.name,**task_payload(CONFIG.target,newer.workspace_id,event)}
        assert not dispatch.finish(engine,CONFIG,old,NOW+timedelta(seconds=32),task=result)
        assert dispatch.finish(engine,CONFIG,newer,NOW+timedelta(seconds=32),task=result)
        with Session(engine) as db,db.begin():
            workspace=db.get(Workspace,UUID(state['workspace_id']))
            connections.detach(db,workspace,workspace.revision)
        assert not dispatch.current(engine,newer,NOW+timedelta(seconds=33))
        assert dispatch.claim(engine,CONFIG,NOW+timedelta(seconds=63)) is None
    finally:client.close()


def test_crash_before_create_and_wrong_receipt_never_claim_business_success(isolated):
    engine,_=isolated;client,_,state,_,event=connected_booking(isolated)
    try:
        original=dispatch.claim(engine,CONFIG,NOW)
        recovered=dispatch.claim(engine,CONFIG,NOW+timedelta(seconds=31))
        assert recovered.action=='get' and original.name==recovered.name
        assert not dispatch.finish(engine,CONFIG,recovered,NOW+timedelta(seconds=32))
        fresh=dispatch.claim(engine,CONFIG,NOW+timedelta(seconds=37))
        task={'name':fresh.name,**task_payload(CONFIG.target,fresh.workspace_id,event)}
        task['httpRequest']['oidcToken']['audience']='https://wrong.example.invalid'
        assert not dispatch.finish(engine,CONFIG,fresh,NOW+timedelta(seconds=38),task=task)
        with Session(engine) as db:
            publication=db.get(TaskPublication,(UUID(state['workspace_id']),event))
            assert publication.state=='attention' and publication.code=='TASK_RECEIPT_MISMATCH'
            assert db.get(Outbox,(UUID(state['workspace_id']),event)).state=='pending'
    finally:client.close()


def test_two_connection_leadership_releases_pool_session_lock_after_rollout(isolated):
    from choreograph.db import build_engine
    from choreograph.dispatcher import leadership
    engine=build_engine(isolated[1],pool_size=2,max_overflow=0)
    try:
        with leadership(engine) as first:
            assert first
            with leadership(engine) as second:assert not second
        with leadership(engine) as successor:assert successor
        with pytest.raises(RuntimeError),leadership(engine) as interrupted:
            assert interrupted
            raise RuntimeError('synthetic-interrupted-cycle')
        with leadership(engine) as recovered:assert recovered
        assert engine.pool.checkedout()==0
    finally:engine.dispose()


def test_unattended_cycle_expires_private_sources_and_only_enqueues_cleanup(isolated,monkeypatch):
    from uuid import uuid4

    from sqlalchemy import func, select

    from choreograph import knowledge
    from choreograph.dispatcher import cycle, status
    from choreograph.models import DocumentVersion, Workspace
    engine,_=isolated;client,_,state,crm,_=connected_booking(isolated)
    class Queue:
        config=CONFIG
        def __init__(self):self.calls=[]
        def create(self,name,task):self.calls.append(name);return {'name':name,**task}
        def get(self,name):return None
    queue=Queue()
    try:
        with Session(engine) as db,db.begin():
            knowledge.prepare_samples(db,NOW)
            workspace=db.get(Workspace,UUID(state['workspace_id']));knowledge.attach_samples(db,workspace)
            assert knowledge.replace(db,workspace,'preparation',b'Synthetic private preparation guide. Keep pets outside the cleaning rooms.','text',NOW)['ready']
        calls=list(crm.calls)
        def forbidden(*args,**kwargs):raise AssertionError('Dispatcher must not run direct CRM delivery')
        monkeypatch.setattr(jobs,'tick',forbidden)
        now=NOW+timedelta(hours=2,seconds=1)
        assert cycle(engine,queue,lambda:now,uuid4())==1 and len(queue.calls)==1 and crm.calls==calls
        with Session(engine) as db:
            assert not db.get(Workspace,UUID(state['workspace_id'])).active
            assert db.scalar(select(func.count()).select_from(DocumentVersion).where(DocumentVersion.owner_id==UUID(state['workspace_id'])))==0
            cleanup=db.scalar(select(Outbox).where(Outbox.workspace_id==UUID(state['workspace_id']),Outbox.kind=='crm_cleanup'))
            assert cleanup.state=='pending' and cleanup.attempts==0
        snapshot=status(engine,now);assert snapshot['cycles']==1 and snapshot['published']==1 and snapshot['publications']=={'accepted':1}
    finally:client.close()


def test_dispatcher_filters_provider_secrets_and_status_never_constructs_google_client(isolated,monkeypatch,capsys):
    from choreograph import dispatcher
    values={'CHOREOGRAPH_DATABASE_URL':isolated[1].database_url,'FAKE_MODE':'false',
        'OPENAI_API_KEY':'synthetic-must-be-ignored','CHOREOGRAPH_CRM_PROVIDER':'hubspot',
        'CHOREOGRAPH_TASKS_ENABLED':'true','CHOREOGRAPH_TASK_PROJECT':CONFIG.project,
        'CHOREOGRAPH_TASK_REGION':CONFIG.region,'CHOREOGRAPH_TASK_QUEUE':CONFIG.queue,
        'CHOREOGRAPH_TASK_URL':CONFIG.target.url,'CHOREOGRAPH_TASK_AUDIENCE':CONFIG.target.audience,
        'CHOREOGRAPH_TASK_SERVICE_EMAIL':CONFIG.target.service_email}
    settings=dispatcher.settings_for_dispatcher(values)
    assert settings.profile=='fake' and settings.crm_provider=='disabled' and settings.live_ai is None and settings.live_crm is None
    def forbidden(*args,**kwargs):raise AssertionError('Status must not create a Google client')
    monkeypatch.setattr(dispatcher,'CloudTasks',forbidden)
    dispatcher.run({'CHOREOGRAPH_DATABASE_URL':isolated[1].database_url},inspect=True)
    output=capsys.readouterr().out
    assert 'DISPATCH_NOT_STARTED' in output and 'synthetic-must-be-ignored' not in output


def test_unattended_sql_recovery_resolves_a_crashed_fifth_domain_attempt(isolated):
    engine,_=isolated;client,_,state,crm,event=connected_booking(isolated)
    try:
        with Session(engine) as db,db.begin():
            row=db.get(Outbox,(UUID(state['workspace_id']),event));row.state='processing';row.attempts=5
            row.lease_until=NOW-timedelta(seconds=1)
        before=list(crm.calls)
        jobs.maintenance(engine,NOW)
        with Session(engine) as db:
            row=db.get(Outbox,(UUID(state['workspace_id']),event))
            assert row.state=='needs_attention' and row.code=='CRM_ATTEMPTS_EXHAUSTED' and row.lease_until is None
        assert dispatch.claim(engine,CONFIG,NOW) is None and crm.calls==before
    finally:client.close()


def test_three_hour_window_stops_late_provider_access_and_remains_observable(isolated):
    from choreograph.dispatcher import status
    from choreograph.models import Workspace
    engine,settings=isolated;client,_,state,crm,event=connected_booking(isolated)
    try:
        expiry=NOW+timedelta(hours=2)
        with Session(engine) as db,db.begin():
            jobs.retire_workspace(db,db.get(Workspace,UUID(state['workspace_id'])),expiry)
            db.flush()
            from sqlalchemy import select
            event=db.scalar(select(Outbox.id).where(Outbox.workspace_id==UUID(state['workspace_id']),Outbox.kind=='crm_cleanup'))
        job=claim_for(engine,state,event,expiry)
        calls=list(crm.calls);late=NOW+timedelta(hours=3)
        # Even direct late delivery cannot refresh or contact the external system.
        with Session(engine) as db,db.begin():
            row=db.get(Outbox,(UUID(state['workspace_id']),event));row.lease_until=late+timedelta(seconds=180)
        assert jobs.deliver(engine,settings,crm,job,lambda:late)
        assert crm.calls==calls
        with Session(engine) as db:
            row=db.get(Outbox,(UUID(state['workspace_id']),event))
            assert row.state=='needs_attention' and row.code=='CRM_WINDOW_EXPIRED'
        assert status(engine,late)['work_codes']['CRM_WINDOW_EXPIRED']==1
        assert dispatch.claim(engine,CONFIG,late) is None
    finally:client.close()


def test_health_probes_expose_no_maintenance_operation_or_diagnostic_data():
    import time

    from choreograph.dispatcher import health_server
    health={'at':time.monotonic(),'ready':False}
    server,thread=health_server(0,health,host='127.0.0.1')
    try:
        with httpx.Client(base_url='http://127.0.0.1:'+str(server.server_port),trust_env=False,timeout=2) as client:
            assert client.get('/health/ready').status_code==503
            health['ready']=True
            for path in ['/health/ready','/health/live']:
                response=client.get(path);assert response.status_code==200 and response.content==b''
                assert response.headers['cache-control']=='no-store'
            assert client.get('/internal/maintenance').status_code==404
            assert client.post('/health/live',json={'run':'maintenance'}).status_code==501
    finally:server.shutdown();server.server_close();thread.join(timeout=2)


def test_dedup_tombstone_reconciles_missing_before_new_epoch_and_publish_limit_stops(isolated):
    engine,_=isolated;client,_,state,crm,event=connected_booking(isolated)
    class Tombstone:
        config=CONFIG
        def __init__(self):self.creates=[]
        def create(self,name,task):
            self.creates.append(name)
            if len(self.creates)==1:raise PublishFailure('TASK_ALREADY_EXISTS',unknown=True)
            return {'name':name,**task}
        def get(self,name):return None
    queue=Tombstone();clock=[NOW];calls=list(crm.calls)
    try:
        item=dispatch.claim(engine,CONFIG,clock[0]);assert not dispatch.publish(engine,queue,item,lambda:clock[0])
        clock[0]+=timedelta(seconds=3)
        item=dispatch.claim(engine,CONFIG,clock[0]);assert item.action=='get'
        assert not dispatch.publish(engine,queue,item,lambda:clock[0]) and len(queue.creates)==1
        clock[0]+=timedelta(seconds=5)
        item=dispatch.claim(engine,CONFIG,clock[0]);assert dispatch.publish(engine,queue,item,lambda:clock[0])
        assert len(set(queue.creates))==2 and crm.calls==calls
        with Session(engine) as db,db.begin():
            publication=db.get(TaskPublication,(UUID(state['workspace_id']),event))
            publication.attempts=120;publication.next_check=clock[0]
        assert dispatch.claim(engine,CONFIG,clock[0]) is None
        with Session(engine) as db:
            publication=db.get(TaskPublication,(UUID(state['workspace_id']),event))
            assert publication.state=='attention' and publication.code=='TASK_ATTEMPTS_EXHAUSTED'
            assert db.get(Outbox,(UUID(state['workspace_id']),event)).attempts==0
    finally:client.close()


def test_shared_claim_has_one_winner_and_changed_target_requires_attention(isolated):
    engine,_=isolated;client,_,state,_,event=connected_booking(isolated)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:claims=list(pool.map(lambda _:dispatch.claim(engine,CONFIG,NOW),range(2)))
        assert sum(item is not None for item in claims)==1
        original=next(item for item in claims if item is not None)
        assert dispatch.claim(engine,replace(CONFIG,queue='different-reviewed-queue'),NOW+timedelta(seconds=31)) is None
        with Session(engine) as db:
            publication=db.get(TaskPublication,(UUID(state['workspace_id']),event))
            assert publication.state=='attention' and publication.code=='TASK_TARGET_CHANGED' and publication.name==original.name
    finally:client.close()
