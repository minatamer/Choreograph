"""Upcoming appointment windows, including Sunday and scoped rescheduling."""
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_requests import command

from choreograph.api import create_app
from choreograph.models import Reservation


@pytest.mark.parametrize('zone,now',[
    ('Africa/Cairo',datetime(2026,10,25,8,tzinfo=UTC)),
    ('America/New_York',datetime(2026,10,25,0,30,tzinfo=UTC)),
    ('America/New_York',datetime(2026,11,1,5,30,tzinfo=UTC)),
])
def test_upcoming_calendar_uses_saved_local_days_and_exact_duration(database,zone,now):
    engine, settings = database
    client = TestClient(create_app(settings,engine,lambda:now))
    headers = {'origin':settings.origin,'x-choreograph-bridge':settings.bridge_secret}
    today = now.astimezone(ZoneInfo(zone)).date()
    try:
        state = client.post('/v1/session',headers=headers,json={'timezone':zone}).json()
        headers['x-csrf-token'] = state['csrf']
        state = command(client,headers,state,{'service':'deep','bedrooms':2}).json()['state']
        view = client.get('/v1/availability?start='+today.isoformat(),headers=headers).json()
        assert view['week_start']==today.isoformat() and view['minutes']==180
        assert [item['date'] for item in view['days']]==[(today+timedelta(days=n)).isoformat() for n in range(7)]
        assert not view['can_previous'] and view['can_next']
        openings = [slot for item in view['days'] for slot in item['slots']]
        assert openings and all(datetime.fromisoformat(slot['start'])>now for slot in openings)
        assert all(datetime.fromisoformat(slot['end'])-datetime.fromisoformat(slot['start'])==timedelta(minutes=180)
                   for slot in openings)
        if today.weekday()==6:
            assert view['days'][0]['status']=='closed' and not view['days'][0]['slots']
            assert next(item for item in view['days'] if item['slots'])['date']>today.isoformat()
        tomorrow = client.get('/v1/availability?start='+(today+timedelta(days=1)).isoformat(),headers=headers).json()
        assert tomorrow['can_previous']  # the back control can clamp to today
        assert client.get('/v1/availability?start='+(today-timedelta(days=1)).isoformat(),headers=headers).status_code==422
    finally:
        client.close()


def test_reschedule_window_is_forward_looking_scoped_and_does_not_move_a_booking(database):
    engine, settings = database
    now = datetime(2026,10,25,8,tzinfo=UTC)
    today = now.date()
    app = create_app(settings,engine,lambda:now)
    client = TestClient(app)
    headers = {'origin':settings.origin,'x-choreograph-bridge':settings.bridge_secret}
    try:
        state = client.post('/v1/session',headers=headers,json={'timezone':'UTC'}).json()
        headers['x-csrf-token'] = state['csrf']
        state = command(client,headers,state,{'service':'deep','bedrooms':2}).json()['state']
        view = client.get('/v1/availability?start='+today.isoformat(),headers=headers).json()
        original = next(slot['start'] for item in view['days'] for slot in item['slots'])
        state = command(client,headers,state,{'preferred_at':original}).json()['state']
        booked = command(client,headers,state,{'accept_quote':True},'/v1/bookings',method='post')
        assert booked.status_code==200
        state = booked.json()['state']
        record = state['requests'][0]
        route = f"/v1/requests/{record['id']}/availability"
        response = client.get(route+'?start='+today.isoformat(),headers=headers)
        assert response.status_code==200
        view = response.json()
        assert view['week_start']==today.isoformat() and view['minutes']==180
        assert all(date.fromisoformat(item['date'])>=today for item in view['days'])
        # The current reservation is excluded only for this request's proposed
        # alternatives. Reading availability neither releases nor moves it.
        assert any(slot['start']==original for item in view['days'] for slot in item['slots'])
        with Session(engine) as db:
            reservation = db.scalar(select(Reservation).where(Reservation.enquiry_id==record['id']))
            assert reservation.state=='confirmed' and reservation.starts_at==datetime.fromisoformat(original)
        refreshed = client.get('/v1/session',headers=headers).json()
        assert refreshed['requests'][0]==record and refreshed['revision']==state['revision']
        for query in ['?start=2026-10-24','?start=2026-11-24','?start=2026-10-25&week=2026-10-19']:
            assert client.get(route+query,headers=headers).status_code==422
        legacy = client.get(route,headers=headers).json()
        assert date.fromisoformat(legacy['week_start']).weekday()==0
        other = TestClient(app)
        try:
            other.post('/v1/session',headers=headers,json={'timezone':'UTC'})
            assert other.get(route+'?start='+today.isoformat(),headers=headers).status_code==404
        finally:
            other.close()
    finally:
        client.close()
