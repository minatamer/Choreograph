import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from test_booking import book, prepare
from test_requests import NOW, begin, command

from choreograph import service
from choreograph.api import create_app
from choreograph.errors import DomainError
from choreograph.models import Connection, Enquiry, Outbox, Reservation, Workspace
from choreograph.persistence import Session, repo_rows


def ready(database):
    client,headers,state=begin(database)
    state=command(client,headers,state,{'service':'move-out','bedrooms':2,'oven':True}).json()['state']
    week=client.get('/v1/availability?week='+state['scenario']['week_start'],headers=headers).json()
    day=next(day for day in week['days'] if day['date']==state['scenario']['alternative_date'])
    state=command(client,headers,state,{'preferred_at':day['slots'][0]['start']}).json()['state']
    return client,headers,state


def confirm(client,headers,state,key=None):
    return command(client,headers,state,{'accept_quote':True},'/v1/bookings',key,method='post')


def test_customer_booking_is_reserved_replayable_and_persisted(database):
    engine,_=database;client,headers,state=ready(database)
    try:
        key=str(uuid4());result=confirm(client,headers,state,key)
        assert result.status_code==200,result.text
        accepted=result.json();current=accepted['state'];record=current['requests'][0]
        assert record['status']=='confirmed' and record['booking']['state']=='confirmed'
        assert record['quote']['cents']==18500 and record['quote']['minutes']==270
        assert datetime.fromisoformat(record['booking']['starts_at'])==datetime.fromisoformat(state['draft']['preferred_at'])
        assert current['summary']['awaiting_count']==0 and current['summary']['confirmed_count']==1
        assert accepted['receipt']['action']=='confirmed'
        assert len(current['messages'])==1 and current['messages'][0]['role']=='assistant'
        assert current['messages'][0]['request_id']==record['id'] and current['messages'][0]['cards']==['booking']
        replay=confirm(client,headers,state,key).json()
        assert replay['replayed'] and replay['receipt']==accepted['receipt']
        assert replay['state']['messages']==current['messages']
        refreshed=client.get('/v1/session',headers=headers).json()
        assert refreshed['requests']==current['requests'] and refreshed['messages']==current['messages']
        with Session(engine) as db:
            assert len(repo_rows(db, Reservation, filters={'workspace_id': state['workspace_id'], 'state': 'confirmed'}))==1
            assert len(repo_rows(db, Outbox, filters={'workspace_id': state['workspace_id']}))==0
    finally:client.close()


def test_customer_booking_requires_quote_acceptance_current_revision_and_csrf(database):
    client,headers,state=ready(database)
    try:
        assert command(client,headers,state,{'accept_quote':False},'/v1/bookings',method='post').status_code==422
        assert command(client,headers,state,{'accept_quote':True,'revision':state['revision']-1},
                       '/v1/bookings',method='post').json()['code']=='STALE_REVISION'
        assert command(client,headers,state,{'accept_quote':True,'generation':state['generation']+1},
                       '/v1/bookings',method='post').status_code==409
        assert confirm(client,{k:v for k,v in headers.items() if k!='x-csrf-token'},state).status_code==403
        current=client.get('/v1/session',headers=headers).json()
        assert current['requests']==[] and current['messages']==[] and current['revision']==state['revision']
    finally:client.close()


def test_occupied_customer_booking_leaves_no_pending_request_or_confirmation(database):
    engine,_=database;client,headers,state=ready(database)
    try:
        start=datetime.fromisoformat(state['draft']['preferred_at'])
        with Session(engine) as db,db.begin():
            for staff in ['ada','noah']:
                db.add(Reservation(workspace_id=UUID(state['workspace_id']),staff_id=staff,starts_at=start,
                    ends_at=start+timedelta(minutes=270),state='blocked',label='Existing appointment'))
        result=confirm(client,headers,state)
        assert result.status_code==409 and result.json()['code']=='TIME_OCCUPIED'
        current=client.get('/v1/session',headers=headers).json()
        assert current['requests']==[] and current['messages']==[] and current['revision']==state['revision']
    finally:client.close()


@pytest.mark.parametrize('fail_after_receipt',[False,True])
def test_connected_customer_booking_and_confirmation_commit_or_roll_back_together(database,monkeypatch,fail_after_receipt):
    engine,_=database;client,headers,state=ready(database)
    try:
        with Session(engine) as db,db.begin():
            workspace=db.get(Workspace,state['workspace_id']);workspace.crm_mode='connected'
            connection=Connection(workspace_id=workspace.id,account_id='fake-customer-booking',provider='fake',
                state='ready',generation=1,export_consent=True,created_at=NOW)
            db.add(connection);db.flush();connection_id=connection.id
        if fail_after_receipt:
            original=service.booking_receipt
            def fail(*args):
                original(*args)
                raise DomainError('BOOKING_FAILED','The booking could not be saved.',503)
            monkeypatch.setattr(service,'booking_receipt',fail)
        result=confirm(client,headers,state)
        assert result.status_code==(503 if fail_after_receipt else 200)
        current=client.get('/v1/session',headers=headers).json()
        assert len(current['requests'])==len(current['messages'])==(0 if fail_after_receipt else 1)
        with Session(engine) as db:
            assert len(repo_rows(db, Enquiry, filters={'workspace_id': state['workspace_id']}))==(0 if fail_after_receipt else 1)
            assert len(repo_rows(db, Reservation, filters={'workspace_id': state['workspace_id'], 'state': 'confirmed'}))==(0 if fail_after_receipt else 1)
            outbox=list(repo_rows(db, Outbox, filters={'workspace_id': state['workspace_id']}))
            assert len(outbox)==(0 if fail_after_receipt else 1)
            if outbox:
                assert outbox[0].connection_id==connection_id and outbox[0].account_id=='fake-customer-booking'
                assert outbox[0].workspace_generation==state['generation'] and outbox[0].revision==2
    finally:client.close()


def test_competing_customer_booking_actions_create_one_reservation(database):
    engine,settings=database;client,headers,state=ready(database)
    try:
        token=client.cookies.get('choreograph_guest');barrier=threading.Barrier(2)
        def competing(_):
            with TestClient(create_app(settings,engine,lambda:NOW),cookies={'choreograph_guest':token}) as other:
                barrier.wait(timeout=3)
                return confirm(other,headers,state)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(competing,range(2)))
        assert sorted(result.status_code for result in results)==[200,409]
        current=client.get('/v1/session',headers=headers).json()
        assert len(current['requests'])==len(current['messages'])==1
        assert current['requests'][0]['status']=='confirmed'
    finally:client.close()


def test_existing_pending_request_can_be_explicitly_booked_with_one_chat_confirmation(database):
    client,headers,state,_=prepare(database)
    try:
        request_id=state['requests'][0]['id'];key=str(uuid4())
        accepted=book(client,headers,state,request_id,key=key)
        assert accepted.status_code==200
        current=accepted.json()['state']
        assert current['requests'][0]['status']=='confirmed' and len(current['messages'])==1
        replay=book(client,headers,state,request_id,key=key).json()
        assert replay['replayed'] and replay['state']['messages']==current['messages']
    finally:client.close()


def test_booking_card_binding_survives_later_chat_and_projects_older_receipts(database):
    engine,_=database;client,headers,state=ready(database)
    try:
        accepted=confirm(client,headers,state).json()['state'];original=accepted['messages'][0]
        old={k:v for k,v in original.items() if k!='request_id'};old['cards']=[]
        with Session(engine) as db,db.begin():
            db.get(Workspace,state['workspace_id']).messages=[old]
        restored=client.get('/v1/session',headers=headers).json()
        assert restored['messages'][0]['request_id']==accepted['requests'][0]['id']
        later=command(client,headers,restored,{'text':'Thanks.'},'/v1/chat',method='post').json()['state']
        assert later['messages'][0]['id']==original['id'] and later['messages'][0]['cards']==['booking']
        assert later['messages'][-1]['request_id'] is None and 'booking' not in later['messages'][-1]['cards']
        assert sum('booking' in message['cards'] for message in later['messages'])==1
    finally:client.close()
