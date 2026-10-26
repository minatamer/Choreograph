"""Scheduler wakes existing durable commands; no queue, SQL or real provider."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from test_jobs import connected_booking
from test_object_storage import object_database as object_database
from test_object_storage import start
from test_requests import NOW

from choreograph import jobs
from choreograph.hubspot import CRMFailure, FakeHubSpot
from choreograph.models import (
    Connection,
    ExternalMapping,
    Outbox,
    SimulatedRecord,
    TaskPublication,
    Workspace,
)
from choreograph.object_store import FileObjects, ObjectEngine
from choreograph.persistence import Session, repo_rows
from choreograph.release import application
from choreograph.task_delivery import MaintenanceTarget, create_delivery_app

TARGET=MaintenanceTarget('https://worker.example.invalid/internal/maintenance',
    'https://worker.example.invalid','scheduler@test-project.iam.gserviceaccount.com')
CLAIMS={'iss':'https://accounts.google.com','aud':TARGET.audience,'email':TARGET.service_email,'email_verified':True}
HEADERS={'authorization':'Bearer injected'}


def row(engine,event):
    with Session(engine) as db:
        return next(r for r in repo_rows(db,Outbox) if r.id==event)


def test_object_release_requires_no_tasks_client_or_delivery_route(object_database,monkeypatch):
    engine,settings=object_database
    monkeypatch.setattr('choreograph.task_enqueue.CloudTasks',lambda *_a,**_k:pytest.fail('Tasks client constructed'))
    values={'CHOREOGRAPH_WORKER_AUDIENCE':TARGET.audience,'CHOREOGRAPH_MAINTENANCE_SERVICE_EMAIL':TARGET.service_email}
    with TestClient(application('api',settings,engine,{},crm_provider=FakeHubSpot(engine))) as api:
        assert api.get('/health').json()['profile']=='fake'
    with TestClient(application('worker',settings,engine,values,crm_provider=FakeHubSpot(engine))) as worker:
        assert worker.get('/health').status_code==200
        assert worker.post('/internal/tasks/crm',json={}).status_code==404
        assert worker.post('/v1/session',json={}).status_code==404
        assert worker.post('/internal/maintenance',json={'sweep':True}).status_code==403
    with pytest.raises(ValueError,match='OBJECT_TASKS_NOT_USED'):
        application('api',settings,engine,{'CHOREOGRAPH_TASKS_ENABLED':'true'})


@pytest.mark.parametrize('change',[{'email':'other@test-project.iam.gserviceaccount.com'},
    {'aud':'https://other.example.invalid'},{'iss':'untrusted'},{'email_verified':False}])
def test_scheduler_identity_is_exact_before_body_or_storage(object_database,change,monkeypatch):
    engine,settings=object_database
    monkeypatch.setattr(jobs,'scheduled_tick',lambda *_:pytest.fail('unauthorized work'))
    app=create_delivery_app(settings,engine,FakeHubSpot(engine),maintenance_target=TARGET,
        verifier=lambda *_:{**CLAIMS,**change})
    with TestClient(app) as client:
        assert client.post('/internal/maintenance',headers=HEADERS,content=b'bad').status_code==403


def test_scheduler_body_and_one_job_ingress(object_database):
    engine,settings=object_database;client,_,_,provider,event=connected_booking(object_database)
    app=create_delivery_app(settings,engine,provider,maintenance_target=TARGET,verifier=lambda *_:CLAIMS,clock=lambda:NOW)
    try:
        with TestClient(app) as worker:
            assert worker.post('/internal/maintenance',headers=HEADERS,json={'sweep':False}).status_code==422
            assert worker.post('/internal/maintenance',headers=HEADERS,json={'sweep':True,'command':'x'}).status_code==422
            assert worker.post('/internal/maintenance',headers=HEADERS,json={'sweep':True,'x':'x'*1100}).status_code==413
            assert worker.post('/internal/maintenance',headers=HEADERS,content='text').status_code==415
            assert worker.post('/internal/maintenance',headers=HEADERS,json={'sweep':True}).status_code==204
            calls=list(provider.calls)
            assert worker.post('/internal/maintenance',headers=HEADERS,json={'sweep':True}).status_code==204
        assert provider.calls==calls and row(engine,event).state=='synced'
        with Session(engine) as db:assert not repo_rows(db,TaskPublication)
    finally:client.close()


def test_unknown_create_retries_after_due_time_and_restart_without_duplicates(object_database):
    engine,settings=object_database
    class Uncertain(FakeHubSpot):
        fail=True
        def upsert(self,*args):
            result=super().upsert(*args)
            if self.fail:
                self.fail=False;raise CRMFailure('CRM_TIMEOUT',True,True)
            return result
    provider=Uncertain(engine);client,_,_,_,event=connected_booking(object_database,provider)
    try:
        assert jobs.scheduled_tick(engine,settings,provider,lambda:NOW)==1
        pending=row(engine,event);assert pending.state=='reconciling' and pending.attempts==1
        calls=list(provider.calls)
        assert jobs.scheduled_tick(engine,settings,provider,lambda:NOW)==0 and provider.calls==calls
        reopened=ObjectEngine(FileObjects(engine.objects.root),settings.token_key)
        try:assert jobs.scheduled_tick(reopened,settings,provider,lambda:pending.due_at)==1
        finally:reopened.dispose()
        assert row(engine,event).state=='synced' and row(engine,event).attempts==2
        with Session(engine) as db:assert len(repo_rows(db,SimulatedRecord))==2
    finally:client.close()


def test_duplicate_concurrent_sweep_is_immediate_noop_across_engines(object_database):
    engine,settings=object_database;entered,release=Event(),Event()
    class Controlled(FakeHubSpot):
        def upsert(self,*args):
            entered.set();assert release.wait(8)
            return super().upsert(*args)
    provider=Controlled(engine);client,_,_,_,event=connected_booking(object_database,provider)
    other=ObjectEngine(FileObjects(engine.objects.root),settings.token_key)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first=pool.submit(jobs.scheduled_tick,engine,settings,provider,lambda:NOW)
            try:
                assert entered.wait(5)
                assert pool.submit(jobs.scheduled_tick,other,settings,provider,lambda:NOW).result(timeout=2)==0
            finally:release.set()
            assert first.result(timeout=5)==1
        assert row(engine,event).state=='synced'
        assert provider.calls.count('upsert-contacts')==provider.calls.count('upsert-deals')==1
    finally:release.set();client.close();other.dispose()


def test_crashed_job_claim_recovers_and_late_finisher_cannot_change_receipt(object_database):
    engine,settings=object_database;client,_,_,provider,event=connected_booking(object_database)
    try:
        old=jobs.claim(engine,NOW)
        assert jobs.scheduled_tick(engine,settings,provider,lambda:NOW)==0
        later=NOW+timedelta(seconds=241)
        assert jobs.scheduled_tick(engine,settings,provider,lambda:later)==1
        assert not jobs.finish_job(engine,provider,old,lambda:later,error=CRMFailure('CRM_TIMEOUT',True,True))
        assert row(engine,event).state=='synced' and row(engine,event).attempts==2
    finally:client.close()


def test_sweep_claims_at_most_one_due_job(object_database):
    engine,settings=object_database;first=connected_booking(object_database);second=connected_booking(object_database)
    try:
        assert jobs.scheduled_tick(engine,settings,first[3],lambda:NOW)==1
        assert sorted(row(engine,event).state for event in (first[4],second[4]))==['pending','synced']
    finally:first[0].close();second[0].close()


def test_no_browser_expiry_cleanup_and_skip_need_no_queue(object_database):
    engine,settings=object_database;client,_,state,provider,event=connected_booking(object_database)
    client.close()
    assert jobs.scheduled_tick(engine,settings,provider,lambda:NOW)==1
    assert row(engine,event).state=='synced'
    assert jobs.scheduled_tick(engine,settings,provider,lambda:NOW+timedelta(hours=2,seconds=1))==1
    assert 'archive-contacts' in provider.calls and 'archive-deals' in provider.calls and 'uninstall' not in provider.calls
    with Session(engine) as db:
        workspace=db.get(Workspace,UUID(state['workspace_id']))
        assert not workspace.active
        connection=db.get(Connection,(workspace.id,UUID(state['connection']['id'])))
        assert connection.encrypted_tokens is None
    skipped=FakeHubSpot(engine);guest,_,_=start(object_database,provider=skipped);guest.close()
    jobs.scheduled_tick(engine,settings,skipped,lambda:NOW+timedelta(hours=2,seconds=1))
    assert skipped.calls==[]


def test_slow_maintenance_does_not_claim_new_work(object_database,monkeypatch):
    engine,settings=object_database;client,_,_,provider,event=connected_booking(object_database)
    instant=[100.];original=jobs.maintenance
    def slow(*args):
        original(*args);instant[0]+=61
    monkeypatch.setattr(jobs,'time',SimpleNamespace(monotonic=lambda:instant[0]));monkeypatch.setattr(jobs,'maintenance',slow)
    try:
        assert jobs.scheduled_tick(engine,settings,provider,lambda:NOW)==0
        assert row(engine,event).state=='pending' and row(engine,event).attempts==0
        assert 'upsert-contacts' not in provider.calls
    finally:client.close()


def test_late_provider_ack_stays_ambiguous_instead_of_success(object_database,monkeypatch):
    engine,settings=object_database;instant=[100.]
    class Late(FakeHubSpot):
        def verify_association(self,*args):
            result=super().verify_association(*args);instant[0]+=151;return result
    provider=Late(engine);client,_,_,_,event=connected_booking(object_database,provider)
    monkeypatch.setattr(jobs,'time',SimpleNamespace(monotonic=lambda:instant[0]))
    try:
        assert jobs.scheduled_tick(engine,settings,provider,lambda:NOW)==1
        assert row(engine,event).state=='reconciling' and row(engine,event).code=='CRM_TIMEOUT'
        with Session(engine) as db:assert not repo_rows(db,ExternalMapping)
    finally:client.close()


def test_expired_global_lease_recovers_and_old_release_preserves_new_owner(object_database):
    engine,_=object_database
    old=engine.acquire('scheduled-sweep-v1',seconds=-1,wait=False)
    current=engine.acquire('scheduled-sweep-v1',seconds=240,wait=False)
    assert current is not None and current!=old
    engine.release(old)
    assert engine.acquire('scheduled-sweep-v1',wait=False) is None
    engine.release(current)
    final=engine.acquire('scheduled-sweep-v1',wait=False)
    assert final is not None
    engine.release(final)
