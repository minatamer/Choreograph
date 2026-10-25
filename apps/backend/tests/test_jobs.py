import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import UUID, uuid4

from test_booking import book
from test_crm import begin, connect
from test_requests import NOW, command

from choreograph import jobs, knowledge
from choreograph.hubspot import CRMFailure, FakeHubSpot
from choreograph.models import (
    Chunk,
    Connection,
    DocumentVersion,
    Installation,
    Manifest,
    Outbox,
    SimulatedRecord,
    Workspace,
)
from choreograph.persistence import Session, repo_first, repo_rows, repo_value


def connected_booking(database,provider=None):
    c,h,s,p=begin(database,provider);s,_=connect(c,h,s)
    s=command(c,h,s,{'connection_id':s['connection']['id'],'confirm':True},'/v1/crm/consent',method='post').json()['state']
    s=command(c,h,s,{'service':'regular','bedrooms':2}).json()['state']
    week=c.get('/v1/availability?week='+s['scenario']['week_start'],headers=h).json()
    start=next(day['slots'][0]['start'] for day in week['days'] if day['date']==s['scenario']['alternative_date'])
    s=command(c,h,s,{'preferred_at':start}).json()['state']
    s=command(c,h,s,{'accept_quote':True},'/v1/requests',method='post').json()['state']
    s=book(c,h,s,s['requests'][0]['id']).json()['state']
    with Session(database[0]) as db:
        event=repo_first(db, Outbox, filters={'workspace_id': s['workspace_id'], 'kind': 'crm_upsert'})
        eid=event.id
    return c,h,s,p,eid


def claim_for(engine,state,event,now=NOW):return jobs.claim(engine,now,event_id=event,workspace_id=UUID(state['workspace_id']))


def test_durable_duplicate_and_concurrent_delivery(database):
    engine,settings=database;c,h,s,p,eid=connected_booking(database)
    try:
        barrier=threading.Barrier(2)
        def race():barrier.wait();return claim_for(engine,s,eid)
        with ThreadPoolExecutor(max_workers=2) as pool:claims=list(pool.map(lambda _:race(),range(2)))
        assert len([item for item in claims if item])==1
        job=next(item for item in claims if item)
        assert jobs.deliver(engine,settings,p,job,lambda:NOW)
        assert not claim_for(engine,s,eid)
        assert not jobs.deliver(engine,settings,p,job,lambda:NOW)
        current=c.get('/v1/session',headers=h).json();record=current['requests'][0]
        assert record['crm_state']=='simulated_synced' and record['crm_receipt']['provider']=='fake' and not record['crm_links']
        with Session(engine) as db:
            assert len(repo_rows(db, SimulatedRecord, filters={'account_id': 'simulated-' + s['workspace_id']}, predicate=lambda candidate: candidate.archived is False))==2
        assert p.calls.count('upsert-contacts')==1
    finally:c.close()


def test_shared_install_appearing_during_cleanup_preserves_progress_and_reports_attention(database):
    engine,settings=database

    class ConcurrentInstall(FakeHubSpot):
        on_archived=None
        def archive(self,tokens,kind,key):
            super().archive(tokens,kind,key)
            if kind=='contacts' and self.on_archived:
                callback,self.on_archived=self.on_archived,None
                callback()

    provider=ConcurrentInstall(engine,account_id='cleanup-race-'+uuid4().hex)
    c,h,state,_,eid=connected_booking(database,provider)
    other,other_headers,other_state,_=begin(database,provider)
    try:
        assert jobs.deliver(engine,settings,provider,claim_for(engine,state,eid),lambda:NOW)
        state=c.get('/v1/session',headers=h).json()
        response=command(c,h,state,{'connection_id':state['connection']['id'],'confirm':True,
            'cleanup':True,'uninstall':True},'/v1/crm/finish',method='post')
        assert response.status_code==200
        state=response.json()['state']
        with Session(engine) as db:
            cleanup=repo_value(db, Outbox, 'id', filters={'workspace_id': state['workspace_id'], 'kind': 'crm_cleanup'})
        provider.on_archived=lambda:connect(other,other_headers,other_state)
        assert jobs.deliver(engine,settings,provider,claim_for(engine,state,cleanup),lambda:NOW)
        current=c.get('/v1/session',headers=h).json()
        assert current['connection']['cleanup_state']=='removed'
        assert current['connection']['uninstall_state']=='not_requested'
        assert current['connection']['state']=='needs_attention'
        assert current['requests'][0]['status']=='confirmed'
        assert other.get('/v1/session',headers=other_headers).json()['connection']['state']=='ready'
        assert 'uninstall' not in provider.calls
        with Session(engine) as db:
            event=db.get(Outbox,(UUID(state['workspace_id']),cleanup))
            assert event.state=='needs_attention' and event.code=='CRM_SHARED_INSTALL'
            assert db.get(Installation,(provider.app_id,provider.account_id)).state=='installed'
            assert len(repo_rows(db, SimulatedRecord, filters={'account_id': provider.account_id}, predicate=lambda candidate: candidate.archived is True))==2
    finally:c.close();other.close()


def test_expired_lease_recovers_without_accepting_old_worker(database):
    engine,settings=database;c,_h,s,p,eid=connected_booking(database)
    try:
        old=claim_for(engine,s,eid);later=NOW+jobs.LEASE+timedelta(seconds=1)
        new=claim_for(engine,s,eid,later);assert new and new['lease_token']!=old['lease_token']
        assert jobs.deliver(engine,settings,p,old,lambda:later) is False
        assert jobs.deliver(engine,settings,FakeHubSpot(engine),new,lambda:later)
        with Session(engine) as db:
            row=db.get(Outbox,(UUID(s['workspace_id']),eid));assert row.attempts==2 and row.state=='synced'
    finally:c.close()


def test_revoked_auth_keeps_booking_and_exposes_attention_without_stale_sync(database):
    engine,settings=database
    class Revoked(FakeHubSpot):
        revoked=False
        def upsert(self,*args):
            if self.revoked:raise CRMFailure('CRM_AUTH_REQUIRED')
            return super().upsert(*args)
    c,h,s,p,eid=connected_booking(database,Revoked(engine))
    try:
        assert jobs.deliver(engine,settings,p,claim_for(engine,s,eid),lambda:NOW)
        s=c.get('/v1/session',headers=h).json()
        assert s['requests'][0]['crm_state']=='simulated_synced' and s['requests'][0]['crm_receipt']
        record=s['requests'][0]
        s=book(c,h,s,record['id'],'reschedule',{'staff_id':'noah','preferred_at':record['preferred_at']}).json()['state']
        with Session(engine) as db:
            eid=repo_value(db, Outbox, 'id', filters={'workspace_id': s['workspace_id'], 'kind': 'crm_upsert', 'revision': s['requests'][0]['revision']})
        p.revoked=True
        assert jobs.deliver(engine,settings,p,claim_for(engine,s,eid),lambda:NOW)
        current=c.get('/v1/session',headers=h).json();record=current['requests'][0]
        assert record['status']=='confirmed' and record['booking']['staff_id']=='noah'
        assert record['crm_state']=='needs_attention' and record['crm_receipt'] is None and record['crm_links']=={}
        assert current['connection']['state']=='needs_attention' and not current['connection']['consented']
        with Session(engine) as db:
            connection=db.get(Connection,(UUID(s['workspace_id']),UUID(s['connection']['id'])))
            event=db.get(Outbox,(UUID(s['workspace_id']),eid))
            assert connection.encrypted_tokens is None and event.state=='needs_attention' and event.code=='CRM_AUTH_REQUIRED'
        assert claim_for(engine,s,eid) is None
    finally:c.close()


def test_ambiguous_create_reconciles_by_unique_owned_key(database):
    engine,settings=database
    class Ambiguous(FakeHubSpot):
        failed=False
        def upsert(self,*args):
            result=super().upsert(*args)
            if not self.failed:self.failed=True;raise CRMFailure('CRM_TIMEOUT',True,True)
            return result
    p=Ambiguous(engine);c,h,s,p,eid=connected_booking(database,p)
    try:
        assert jobs.deliver(engine,settings,p,claim_for(engine,s,eid),lambda:NOW)
        with Session(engine) as db:assert db.get(Outbox,(UUID(s['workspace_id']),eid)).state=='reconciling'
        later=NOW+timedelta(seconds=6);assert jobs.deliver(engine,settings,p,claim_for(engine,s,eid,later),lambda:later)
        account='simulated-'+s['workspace_id']
        with Session(engine) as db:assert len(repo_rows(db, SimulatedRecord, filters={'account_id': account}))==2
        assert c.get('/v1/session',headers=h).json()['requests'][0]['crm_state']=='simulated_synced'
    finally:c.close()


def test_new_revision_retires_old_delivery_before_external_call(database):
    engine,settings=database;c,h,s,p,eid=connected_booking(database)
    try:
        old=claim_for(engine,s,eid);before=len(p.calls)
        s=book(c,h,s,s['requests'][0]['id'],'cancel').json()['state']
        assert jobs.deliver(engine,settings,p,old,lambda:NOW) is False and len(p.calls)==before
        with Session(engine) as db:new=repo_first(db, Outbox, filters={'workspace_id': s['workspace_id'], 'kind': 'crm_upsert', 'revision': s['requests'][0]['revision']}).id
        assert jobs.deliver(engine,settings,p,claim_for(engine,s,new),lambda:NOW)
        current=c.get('/v1/session',headers=h).json();assert current['requests'][0]['status']=='cancelled' and current['requests'][0]['crm_state']=='simulated_synced'
    finally:c.close()


def test_reset_during_external_create_fences_late_work_and_cleans_it(database):
    engine,settings=database
    class ResetAfterCreate(FakeHubSpot):
        reset=None;done=False
        def upsert(self,*args):
            result=super().upsert(*args)
            if not self.done:self.done=True;self.reset()
            return result
    p=ResetAfterCreate(engine);c,h,s,p,eid=connected_booking(database,p)
    try:
        old_workspace=s['workspace_id']
        p.reset=lambda:c.post('/v1/reset',headers=h,json={'generation':s['generation'],'timezone':s['timezone']})
        assert jobs.deliver(engine,settings,p,claim_for(engine,s,eid),lambda:NOW) is False
        with Session(engine) as db:
            cleanup=repo_first(db, Outbox, filters={'workspace_id': old_workspace, 'kind': 'crm_cleanup'}).id
            assert not db.get(Workspace,old_workspace).active
        job=jobs.claim(engine,NOW,event_id=cleanup,workspace_id=UUID(old_workspace));assert job
        assert jobs.deliver(engine,settings,p,job,lambda:NOW)
        with Session(engine) as db:
            assert len(repo_rows(db, SimulatedRecord, filters={'account_id': 'simulated-' + old_workspace}, predicate=lambda candidate: candidate.archived is False))==0
            assert db.get(Installation,(p.app_id,'simulated-'+old_workspace)).state=='installed'
        assert 'uninstall' not in p.calls
    finally:c.close()


def test_expiry_purges_private_sources_and_does_not_uninstall(database):
    engine,_settings=database;c,_h,s,p,_eid=connected_booking(database)
    try:
        with Session(engine) as db,db.begin():
            knowledge.prepare_samples(db,NOW);ws=db.get(Workspace,s['workspace_id']);knowledge.attach_samples(db,ws)
            assert knowledge.replace(db,ws,'preparation',b'Pet preparation: keep pets outside the home for this revised fictional instruction.','text',NOW)['ready']
            private=db.get(Manifest,(ws.id,'preparation')).version_id
        later=NOW+timedelta(hours=2)
        # The session-scoped test DB may contain a backlog from earlier cases.
        # Maintenance is intentionally bounded; drain due batches until this
        # fixture retires rather than assuming it belongs to the first batch.
        with Session(engine) as db:
            due=len(repo_rows(db, Workspace, predicate=lambda candidate: (candidate.active is True) and (candidate.expires_at <= later)))
        for _ in range(due+1):
            jobs.maintenance(engine,later)
            with Session(engine) as db:
                if not db.get(Workspace,s['workspace_id']).active:break
        with Session(engine) as db:
            assert db.get(DocumentVersion,private) is None and len(repo_rows(db, Chunk, filters={'version_id': private}))==0
            assert not db.get(Workspace,s['workspace_id']).messages
            assert len(repo_rows(db, DocumentVersion, predicate=lambda candidate: (candidate.owner_id is None)))>=6
        assert not p.calls.count('upsert-contacts') and 'uninstall' not in p.calls
    finally:c.close()


def test_retry_attempt_limit_and_explicit_cleanup_uninstall_receipts(database):
    engine,settings=database
    class Limited(FakeHubSpot):
        def upsert(self,*args):raise CRMFailure('CRM_RATE_LIMIT',True,retry_after=5)
    c,h,s,p,eid=connected_booking(database,Limited(engine))
    try:
        instant=NOW
        for _ in range(5):
            job=claim_for(engine,s,eid,instant);assert job
            assert jobs.deliver(engine,settings,p,job,lambda instant=instant:instant)
            instant+=timedelta(seconds=301)
        with Session(engine) as db:
            row=db.get(Outbox,(UUID(s['workspace_id']),eid));assert row.attempts==5 and row.state=='needs_attention'
        assert claim_for(engine,s,eid,instant) is None
    finally:c.close()
    c,h,s,p,eid=connected_booking(database)
    try:
        assert jobs.deliver(engine,settings,p,claim_for(engine,s,eid),lambda:NOW)
        s=c.get('/v1/session',headers=h).json()
        result=command(c,h,s,{'connection_id':s['connection']['id'],'confirm':True,'cleanup':True,'uninstall':True},'/v1/crm/finish',method='post')
        assert result.status_code==200,result.text
        with Session(engine) as db:cleanup=repo_first(db, Outbox, filters={'workspace_id': s['workspace_id'], 'kind': 'crm_cleanup'}).id
        assert jobs.deliver(engine,settings,p,claim_for(engine,s,cleanup),lambda:NOW)
        current=c.get('/v1/session',headers=h).json()['connection'];assert current['cleanup_state']=='removed' and current['uninstall_state']=='removed'
        with Session(engine) as db:assert db.get(Installation,(p.app_id,'simulated-'+s['workspace_id'])).state=='uninstalled'
    finally:c.close()
