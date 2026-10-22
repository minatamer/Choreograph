import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_requests import NOW, begin, command

from choreograph.api import create_app
from choreograph.models import Connection, Outbox, Reservation, Workspace


def prepare(database):
    c,h,s=begin(database,'UTC')
    s=command(c,h,s,{'service':'regular','bedrooms':2}).json()['state']
    week=c.get('/v1/availability?week='+s['scenario']['week_start'],headers=h).json()
    day=next(day for day in week['days'] if day['date']==s['scenario']['alternative_date'])
    start=day['slots'][0]['start']
    s=command(c,h,s,{'preferred_at':start}).json()['state']
    s=command(c,h,s,{'accept_quote':True},'/v1/requests',method='post').json()['state']
    return c,h,s,start


def book(c,h,s,request_id,action='approve',fields=None,key=None):
    record=next(row for row in s['requests'] if row['id']==request_id)
    return command(c,h,s,{'request_revision':record['revision'],'confirm':True,**(fields or {})},
                   f'/v1/requests/{request_id}/{action}',key,method='post')


def add_request(c,h,s,start):
    s=command(c,h,s,{'preferred_at':start}).json()['state']
    return command(c,h,s,{'accept_quote':True},'/v1/requests',method='post').json()['state']


def test_approval_replay_conflict_and_two_staff_authority(database):
    engine,_=database;c,h,s,start=prepare(database)
    try:
        second=(datetime.fromisoformat(start)+timedelta(minutes=30)).isoformat()
        s=add_request(c,h,s,second);first_id,second_id=[row['id'] for row in s['requests']]
        key=str(uuid4());old=s
        accepted=book(c,h,s,first_id,fields={'staff_id':'ada'},key=key)
        assert accepted.status_code==200 and accepted.json()['receipt']['action']=='confirmed'
        s=accepted.json()['state'];assert s['requests'][0]['booking']['staff_id']=='ada'
        replay=book(c,h,old,first_id,fields={'staff_id':'ada'},key=key)
        assert replay.status_code==200 and replay.json()['replayed']
        assert replay.json()['receipt']==accepted.json()['receipt']
        assert book(c,h,s,second_id,fields={'staff_id':'ada'}).json()['code']=='TIME_OCCUPIED'
        result=book(c,h,s,second_id,fields={'staff_id':'noah'})
        assert result.status_code==200
        assert result.json()['state']['summary']=={'requests_count':2,'awaiting_count':0,'confirmed_count':2,'booked_cents':16000}
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(Reservation).where(Reservation.workspace_id==s['workspace_id'],Reservation.state=='confirmed'))==2
            assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.workspace_id==s['workspace_id']))==0
    finally:c.close()


def test_real_competing_approval_transactions_are_fenced(database):
    engine,settings=database;c,h,s,start=prepare(database)
    try:
        s=add_request(c,h,s,(datetime.fromisoformat(start)+timedelta(minutes=30)).isoformat())
        ids=[row['id'] for row in s['requests']];barrier=threading.Barrier(2)
        token=c.cookies.get('choreograph_guest')
        def approve(request_id):
            with TestClient(create_app(settings,engine,lambda:NOW),cookies={'choreograph_guest':token}) as client:
                barrier.wait(timeout=3)
                return book(client,h,s,request_id,fields={'staff_id':'ada'})
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(approve,ids))
            assert sorted(result.status_code for result in outcomes)==[200,409]
            assert next(result for result in outcomes if result.status_code==409).json()['code']=='STALE_REVISION'
        current=c.get('/v1/session',headers=h).json()
        assert sum(row['status']=='confirmed' for row in current['requests'])==1
        assert sum(row['status']=='awaiting_review' for row in current['requests'])==1
        loser=next(row for row in current['requests'] if row['status']=='awaiting_review')
        occupied=book(c,h,current,loser['id'],fields={'staff_id':'ada'})
        assert occupied.status_code==409 and occupied.json()['code']=='TIME_OCCUPIED'
        assert c.get('/v1/session',headers=h).json()['requests']==current['requests']
    finally:c.close()


def test_failed_reschedule_preserves_old_then_cancel_releases_and_complete_is_distinct(database):
    c,h,s,start=prepare(database)
    try:
        s=add_request(c,h,s,(datetime.fromisoformat(start)+timedelta(hours=3)).isoformat())
        first,second=[row['id'] for row in s['requests']]
        s=book(c,h,s,first,fields={'staff_id':'ada'}).json()['state']
        s=book(c,h,s,second,fields={'staff_id':'ada'}).json()['state']
        original=s['requests'][0]['booking'];before_revision=s['revision']
        collision=(datetime.fromisoformat(start)+timedelta(hours=2)).isoformat()
        failed=book(c,h,s,first,'reschedule',{'staff_id':'ada','preferred_at':collision})
        assert failed.status_code==409
        fresh=c.get('/v1/session',headers=h).json()
        assert fresh['requests'][0]['booking']==original and fresh['revision']==before_revision
        changed=book(c,h,fresh,first,'reschedule',{'staff_id':'noah','preferred_at':collision})
        assert changed.status_code==200 and changed.json()['state']['requests'][0]['booking']['staff_id']=='noah'
        s=changed.json()['state']
        cancelled=book(c,h,s,first,'cancel');assert cancelled.status_code==200
        s=cancelled.json()['state'];assert s['requests'][0]['booking']['state']=='cancelled'
        complete=book(c,h,s,second,'complete');assert complete.status_code==200
        assert complete.json()['state']['requests'][1]['status']=='completed'
        assert complete.json()['receipt']['action']=='completed'
        assert complete.json()['state']['summary']=={'requests_count':2,'awaiting_count':0,'confirmed_count':0,'booked_cents':8000}
        alternatives=c.get(f'/v1/requests/{first}/availability',headers=h).json()
        assert any('noah' in slot['staff_ids'] and slot['start']==collision.replace('+00:00','Z') for day in alternatives['days'] for slot in day['slots'])
    finally:c.close()


def test_authorized_connected_booking_and_outbox_commit_together(database):
    engine,_=database;c,h,s,_start=prepare(database)
    try:
        with Session(engine) as db,db.begin():
            ws=db.get(Workspace,s['workspace_id']);ws.crm_mode='connected'
            connection=Connection(workspace_id=ws.id,account_id='fake-account-a',provider='fake',state='ready',
                                  generation=1,export_consent=True,created_at=NOW)
            db.add(connection);db.flush();cid=connection.id
        result=book(c,h,s,s['requests'][0]['id'])
        assert result.status_code==200 and result.json()['receipt']['crm_state']=='pending'
        with Session(engine) as db:
            row=db.scalar(select(Outbox).where(Outbox.workspace_id==s['workspace_id']))
            assert row and row.connection_id==cid and row.account_id=='fake-account-a'
            assert row.workspace_generation==s['generation'] and row.revision==2 and row.state=='pending'
            assert db.scalar(select(func.count()).select_from(Reservation).where(Reservation.workspace_id==s['workspace_id'],Reservation.state=='confirmed'))==1
    finally:c.close()


def test_cross_guest_request_and_explicit_confirmation_are_rejected(database):
    c,h,s,_start=prepare(database);other,oh,os=begin(database,'UTC')
    try:
        request_id=s['requests'][0]['id']
        assert other.get(f'/v1/requests/{request_id}/availability',headers=oh).status_code==404
        result=command(other,oh,os,{'request_revision':1,'confirm':True},f'/v1/requests/{request_id}/approve',method='post')
        assert result.status_code==404
        result=command(c,h,s,{'request_revision':1,'confirm':False},f'/v1/requests/{request_id}/approve',method='post')
        assert result.status_code==422
    finally:c.close();other.close()
