"""Reservation discovery shares actual scheduling rules in fake/live composition."""
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_live_assistant import live_runtime
from test_requests import command

from choreograph import assistant, knowledge
from choreograph.ai_admission import AttemptScope
from choreograph.api import create_app
from choreograph.models import Enquiry, Outbox, Reservation

NOW=datetime(2026,10,30,23,40,tzinfo=UTC)
TEXT='Reserve an appointment.'


class Verification:
    def verify(self,*args):return True


@pytest.mark.parametrize('mode',['fake','live'])
@pytest.mark.parametrize('zone',['Asia/Kathmandu','America/New_York'])
def test_shortcut_browses_next_seven_local_days_without_choosing_or_booking(database,mode,zone):
    engine,settings=database;calls=[];embeddings=[];runtime=None
    def forbidden(request):
        calls.append(request);raise AssertionError('Calendar discovery must not call an AI model')
    if mode=='live':
        settings,runtime,embeddings=live_runtime(database,forbidden)
        operator=runtime.for_scope(AttemptScope(None,0,str(uuid4())))
        knowledge.prepare_pack(engine,NOW,spec=runtime.spec,embedder=operator.embedder,tokenizer=operator.tokenizer)
    else:
        with Session(engine) as db,db.begin():knowledge.prepare_samples(db,NOW)
    before_embeddings=len(embeddings)
    client=TestClient(create_app(settings,engine,lambda:NOW,ai_runtime=runtime,verification_provider=Verification()))
    headers={'origin':settings.origin,'x-choreograph-bridge':settings.bridge_secret,
             'idempotency-key':str(uuid4()),'x-turnstile-token':'synthetic-proof'}
    try:
        state=client.post('/v1/session',headers=headers,json={'timezone':zone}).json()
        headers['x-csrf-token']=state['csrf']
        assert state['profile']==mode
        draft=state['draft'].copy();today=NOW.astimezone(ZoneInfo(zone)).date()
        response=command(client,headers,state,{'text':TEXT},'/v1/chat',method='post')
        assert response.status_code==200,response.text
        state=response.json()['state'];reply=state['messages'][-1]
        assert reply['cards']==['reserve'] and reply['requested_date']==today.isoformat()
        assert 'potential openings' in reply['text'] and state['draft']==draft and state['quote'] is None
        overview=client.get('/v1/availability?start='+today.isoformat(),headers=headers).json()
        assert overview['preview'] and overview['week_start']==today.isoformat() and len(overview['days'])==7
        assert [day['date'] for day in overview['days']]==[(today+timedelta(days=i)).isoformat() for i in range(7)]
        assert any(day['status']=='available' for day in overview['days'])
        assert all(not day['slots'] for day in overview['days']) and not overview['can_previous'] and overview['can_next']
        with Session(engine) as db:
            ids=list(db.scalars(select(Reservation.id).where(Reservation.workspace_id==UUID(state['workspace_id']))))
        state=command(client,headers,state,{'bedrooms':3,'oven':True}).json()['state']
        partial=client.get('/v1/availability?start='+today.isoformat(),headers=headers).json()
        assert partial['preview'] and partial['minutes']==180  # shortest eligible completion of the known details
        state=command(client,headers,state,{'service':'move-out'}).json()['state']
        exact=client.get('/v1/availability?start='+today.isoformat(),headers=headers).json()
        assert not exact['preview'] and exact['minutes']==330
        slot=next(slot for day in exact['days'] for slot in day['slots'])
        assert all((datetime.fromisoformat(slot['end'])-datetime.fromisoformat(slot['start'])).total_seconds()==330*60
                   for day in exact['days'] for slot in day['slots'])
        state=command(client,headers,state,{'preferred_at':slot['start']}).json()['state']
        before=state['draft'].copy();key=str(uuid4())
        result=command(client,headers,state,{'text':TEXT},'/v1/chat',key,method='post')
        assert result.status_code==200,result.text
        replay=command(client,headers,state,{'text':TEXT},'/v1/chat',key,method='post')
        assert replay.status_code==200 and replay.json()['replayed']
        state=result.json()['state']
        assert state['draft']==before and state['requests']==[]
        assert 'whole clean' in state['messages'][-1]['text']
        last=client.get('/v1/availability?start='+(today+timedelta(days=28)).isoformat(),headers=headers).json()
        assert not last['can_next'] and last['can_previous'] and len(last['days'])==7
        assert all(not day['slots'] for day in last['days'] if day['status']=='outside')
        assert client.get('/v1/availability?start='+(today-timedelta(days=1)).isoformat(),headers=headers).status_code==422
        assert client.get('/v1/availability?start='+today.isoformat()+'&week='+today.isoformat(),headers=headers).status_code==422
        with Session(engine) as db:
            assert list(db.scalars(select(Reservation.id).where(Reservation.workspace_id==UUID(state['workspace_id']))))==ids
            assert db.scalar(select(func.count()).select_from(Enquiry).where(Enquiry.workspace_id==UUID(state['workspace_id'])))==0
            assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.workspace_id==UUID(state['workspace_id'])))==0
        assert not calls and len(embeddings)==before_embeddings
    finally:
        client.close()
        if runtime:runtime.close()


@pytest.mark.parametrize('text',['Reserve an appointment.',' reserve an appointment! ','RESERVE AN APPOINTMENT'])
def test_reservation_shortcut_is_a_narrow_explicit_command(text):
    assert assistant.is_reservation_shortcut(text)
    assert not assistant.is_reservation_shortcut(text+' Cancel my booking.')
