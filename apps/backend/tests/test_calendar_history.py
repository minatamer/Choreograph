from datetime import UTC, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from test_booking import book, prepare
from test_requests import NOW, begin, command

from choreograph import service
from choreograph.api import create_app
from choreograph.models import Activity, Outbox, Reservation, Workspace


def test_examples_are_additive_once_only_and_do_not_change_available_times(database):
    engine,_=database
    c,h,s,_=prepare(database)
    try:
        s=book(c,h,s,s['requests'][0]['id']).json()['state']
        originals={row['id']:(row['starts_at'],row['ends_at'],row['state']) for row in s['calendar']
                   if row['state'] not in {'completed','cancelled'}}
        history=[row for row in s['calendar'] if row['state'] in {'completed','cancelled'}]
        assert len(history)==4
        assert sum(row['state']=='completed' for row in history)==2
        assert all(datetime.fromisoformat(row['ends_at'])<NOW for row in history if row['state']=='completed')
        before=c.get('/v1/availability',headers=h).json()
        # Model an already exposed legacy guest, retaining its actual booking.
        with Session(engine) as db,db.begin():
            db.execute(delete(Reservation).where(Reservation.workspace_id==s['workspace_id'],
                       Reservation.enquiry_id.is_(None),Reservation.state.in_(['completed','cancelled'])))
            db.execute(delete(Activity).where(Activity.workspace_id==s['workspace_id'],Activity.kind=='calendar_examples_v1'))
        upgraded=c.get('/v1/session',headers=h).json()
        for row in upgraded['calendar']:
            if row['id'] in originals:
                assert (row['starts_at'],row['ends_at'],row['state'])==originals[row['id']]
        assert originals.keys() <= {row['id'] for row in upgraded['calendar']}
        assert upgraded['requests']==s['requests'] and upgraded['summary']==s['summary']
        assert c.get('/v1/availability',headers=h).json()==before
        assert c.get('/v1/session',headers=h).json()['calendar']==upgraded['calendar']
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(Activity).where(
                Activity.workspace_id==s['workspace_id'],Activity.kind=='calendar_examples_v1'))==1
            assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.workspace_id==s['workspace_id']))==0
    finally:
        c.close()


def test_monday_history_is_reachable_and_dates_follow_workspace_zone(database):
    engine,settings=database
    now=datetime(2026,10,19,1,tzinfo=UTC)
    for zone in ['UTC','Asia/Kathmandu','America/Los_Angeles']:
        with TestClient(create_app(settings,engine,lambda:now)) as c:
            h={'x-choreograph-bridge':settings.bridge_secret,'origin':settings.origin}
            s=c.post('/v1/session',headers=h,json={'timezone':zone}).json()
            completed=[row for row in s['calendar'] if row['state']=='completed']
            assert len(completed)==2
            assert all(datetime.fromisoformat(row['ends_at'])<now for row in completed)
            assert s['calendar_first_week_start']<=s['calendar_week_start']
            assert all(s['calendar_first_week_start']<=datetime.fromisoformat(row['starts_at']).astimezone(
                ZoneInfo(zone)).date().isoformat() for row in completed)
            if zone!='America/Los_Angeles':
                assert s['calendar_first_week_start']<s['calendar_week_start']


def test_clear_is_scoped_guarded_idempotent_and_persistent(database):
    engine,_=database
    c,h,s=begin(database,'UTC')
    other,oh,os=begin(database,'UTC')
    try:
        cancelled=next(row for row in s['calendar'] if row['state']=='cancelled')
        path=f"/v1/calendar/{cancelled['id']}/clear"
        assert command(other,oh,os,{},path,method='post').status_code==404
        assert command(c,{**h,'x-csrf-token':'bad'},s,{},path,method='post').status_code==403
        assert command(c,h,{**s,'generation':s['generation']+1},{},path,method='post').status_code==409
        assert command(c,h,{**s,'revision':s['revision']+1},{},path,method='post').json()['code']=='STALE_REVISION'
        for row in s['calendar']:
            if row['state'] in {'blocked','completed'}:
                assert command(c,h,s,{},f"/v1/calendar/{row['id']}/clear",method='post').json()['code']=='APPOINTMENT_NOT_CANCELLED'
        key=str(uuid4())
        result=command(c,h,s,{},path,key,method='post')
        assert result.status_code==200
        current=result.json()['state']
        assert cancelled['id'] not in {row['id'] for row in current['calendar']}
        assert current['revision']==s['revision']+1
        assert command(c,h,s,{},path,key,method='post').json()['replayed'] is True
        assert command(c,h,current,{},path,method='post').json()['state']['revision']==current['revision']
        assert c.get('/v1/session',headers=h).json()['calendar']==current['calendar']
        with Session(engine) as db:
            row=db.get(Reservation,(s['workspace_id'],cancelled['id']))
            assert row and row.state=='cancelled'
            ws=db.get(Workspace,s['workspace_id'])
            assert all(busy.start!=row.starts_at or busy.staff_id!=row.staff_id for busy in service.busy_records(db,ws))
            assert db.scalar(select(func.count()).select_from(Activity).where(Activity.workspace_id==ws.id,
                Activity.kind=='calendar_cleared',Activity.reference==cancelled['id']))==1
            assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.workspace_id==ws.id))==0
    finally:
        c.close();other.close()


def test_clearing_a_cancelled_booking_retains_request_history(database):
    engine,_=database
    c,h,s,_=prepare(database)
    try:
        request_id=s['requests'][0]['id']
        s=book(c,h,s,request_id).json()['state']
        s=book(c,h,s,request_id,'cancel').json()['state']
        booking=s['requests'][0]['booking']
        result=command(c,h,s,{},f"/v1/calendar/{booking['id']}/clear",method='post')
        assert result.status_code==200
        current=result.json()['state']
        assert current['requests']==s['requests'] and current['summary']==s['summary']
        assert current['requests'][0]['booking']==booking
        assert booking['id'] not in {row['id'] for row in current['calendar']}
        assert c.get('/v1/session',headers=h).json()['requests']==s['requests']
        with Session(engine) as db:
            assert db.get(Reservation,(s['workspace_id'],booking['id'])).state=='cancelled'
    finally:
        c.close()
