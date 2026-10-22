from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from choreograph.api import create_app
from choreograph.models import Enquiry, Reservation

NOW=datetime(2026,10,22,10,tzinfo=UTC)


def begin(database,zone='Asia/Kathmandu'):
    engine,settings=database
    client=TestClient(create_app(settings,engine,lambda:NOW))
    headers={'x-choreograph-bridge':settings.bridge_secret,'origin':settings.origin}
    state=client.post('/v1/session',headers=headers,json={'timezone':zone}).json()
    headers['x-csrf-token']=state['csrf']
    return client,headers,state


def command(client,headers,state,fields,path='/v1/draft',key=None,method='put'):
    return getattr(client,method)(path,headers={**headers,'idempotency-key':key or str(uuid4())},
                                 json={'generation':state['generation'],'revision':state['revision'],**fields})


def test_seed_is_persisted_busy_alternative_and_open_week_share_records(database):
    engine,_=database
    c,h,s=begin(database)
    try:
        s=command(c,h,s,{'service':'move-out','bedrooms':2,'oven':True}).json()['state']
        assert s['quote']['cents']==18500 and s['quote']['minutes']==270
        week=c.get('/v1/availability?week='+s['scenario']['week_start'],headers=h).json()
        busy=next(d for d in week['days'] if d['date']==s['scenario']['busy_date'])
        alternative=next(d for d in week['days'] if d['date']==s['scenario']['alternative_date'])
        assert busy['status']=='busy' and not busy['slots'] and len(busy['occupied'])==2
        assert alternative['slots'][0]['staff_ids']==['ada','noah']
        with Session(engine) as db:
            first=list(db.scalars(select(Reservation.id).where(Reservation.workspace_id==s['workspace_id']).order_by(Reservation.id)))
        assert c.get('/v1/availability?week='+s['scenario']['week_start'],headers=h).json()==week
        c.get('/v1/session',headers=h)
        with Session(engine) as db:
            assert list(db.scalars(select(Reservation.id).where(Reservation.workspace_id==s['workspace_id']).order_by(Reservation.id)))==first
        occupied_start=busy['occupied'][0]['start']
        assert command(c,h,s,{'preferred_at':occupied_start}).status_code==409
        s=command(c,h,s,{'preferred_at':alternative['slots'][0]['start']}).json()['state']
        before=s['revision']; key=str(uuid4())
        result=command(c,h,s,{'accept_quote':True},'/v1/requests',key,method='post')
        assert result.status_code==200
        replay=command(c,h,s,{'accept_quote':True},'/v1/requests',key,method='post')
        assert replay.json()['request_id']==result.json()['request_id'] and replay.json()['replayed'] is True
        assert replay.json()['state']['revision']==before+1
        assert result.json()['state']['requests'][0]['status']=='awaiting_review'
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(Enquiry).where(Enquiry.workspace_id==s['workspace_id']))==1
            assert db.scalar(select(func.count()).select_from(Reservation).where(Reservation.workspace_id==s['workspace_id'],Reservation.state=='confirmed'))==0
        assert command(c,h,s,{'oven':False}).json()['code']=='STALE_REVISION'
        assert command(c,h,s,{'accept_quote':False},'/v1/requests',str(uuid4()),method='post').status_code==422
    finally:c.close()


def test_changed_service_invalidates_old_preference_and_idempotency_rejects_different_body(database):
    c,h,s=begin(database,'UTC')
    try:
        key=str(uuid4())
        result=command(c,h,s,{'service':'regular','bedrooms':1},key=key)
        assert result.status_code==200
        assert command(c,h,s,{'service':'deep','bedrooms':1},key=key).json()['code']=='IDEMPOTENCY_MISMATCH'
        s=result.json()['state']
        week=c.get('/v1/availability?week='+s['scenario']['week_start'],headers=h).json()
        slot=next(d['slots'][0]['start'] for d in week['days'] if d['slots'])
        s=command(c,h,s,{'preferred_at':slot}).json()['state']
        s=command(c,h,s,{'service':'deep'}).json()['state']
        assert s['draft']['preferred_at'] is None and s['quote']['cents']==9000
        assert command(c,h,s,{'accept_quote':True},'/v1/requests',method='post').json()['code']=='REVIEW_REQUIRED'
    finally:c.close()


def test_request_limit_rejects_eleventh_without_hiding_existing_requests(database):
    c,h,s=begin(database,'UTC')
    try:
        s=command(c,h,s,{'service':'regular','bedrooms':1}).json()['state']
        week=c.get('/v1/availability?week='+s['scenario']['week_start'],headers=h).json()
        slot=next(d['slots'][0]['start'] for d in week['days'] if d['slots'])
        s=command(c,h,s,{'preferred_at':slot}).json()['state']
        for _ in range(10):
            result=command(c,h,s,{'accept_quote':True},'/v1/requests',method='post')
            assert result.status_code==200;s=result.json()['state']
        result=command(c,h,s,{'accept_quote':True},'/v1/requests',method='post')
        assert result.status_code==429 and result.json()['code']=='REQUEST_LIMIT'
        assert len(c.get('/v1/session',headers=h).json()['requests'])==10
    finally:c.close()
