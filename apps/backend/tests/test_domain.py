from datetime import UTC, date, datetime, timedelta

import pytest

from choreograph import domain
from choreograph.errors import DomainError


@pytest.mark.parametrize('service,bedrooms,cents,minutes',[
    ('regular',1,6000,90),('regular',2,8000,120),('regular',3,10000,150),
    ('deep',1,9000,150),('deep',2,12000,180),('deep',3,15000,210),
    ('move-out',1,12000,180),('move-out',2,16000,240),('move-out',3,20000,300)])
@pytest.mark.parametrize('oven',[False,True])
def test_exact_catalogue(service,bedrooms,cents,minutes,oven):
    result=domain.quote(service,bedrooms,oven,7)
    assert result['cents']==cents+(2500 if oven else 0)
    assert result['minutes']==minutes+(30 if oven else 0)
    assert result['revision']==7 and sum(item['cents'] for item in result['items'])==result['cents']


def test_unsupported_and_dst_times_are_rejected():
    for args in [('carpet',2,False),('deep',4,False),('deep',True,False)]:
        with pytest.raises(DomainError):domain.quote(*args)
    for day in [datetime(2026,3,29,2,30),datetime(2026,10,25,2,30)]:
        with pytest.raises(DomainError,match='TIME_UNCLEAR'):domain.local_to_utc(day,'Europe/Berlin')
    assert domain.local_to_utc(datetime(2026,10,23,9),'Asia/Kathmandu')==datetime(2026,10,23,3,15,tzinfo=UTC)


def test_full_duration_eligibility_half_open_and_local_week():
    start=datetime(2026,10,23,9,tzinfo=UTC)
    busy=[domain.Busy('ada',start,start+timedelta(hours=2)),domain.Busy('noah',start+timedelta(hours=3),start+timedelta(hours=4))]
    assert domain.eligible(start,120,busy)==['noah']
    assert domain.eligible(start,270,busy)==[]
    assert domain.eligible(start+timedelta(hours=2),60,busy)==['ada','noah']
    now=datetime(2026,10,25,12,tzinfo=UTC) # Monday in Auckland, Sunday in UTC.
    view=domain.availability(date(2026,10,26),270,'Pacific/Auckland',now,[])
    assert view['days'][0]['weekday']=='Mon' and view['days'][0]['slots'][0]['start'].hour==20


def test_hours_horizon_and_elapsed_day_explanations():
    now=datetime(2026,10,22,12,tzinfo=UTC)
    for day in [datetime(2026,10,22,8,tzinfo=UTC),datetime(2026,10,23,14,tzinfo=UTC),datetime(2026,10,25,9,tzinfo=UTC),datetime(2026,11,22,9,tzinfo=UTC)]:
        with pytest.raises(DomainError):domain.validate_start(day,270,'UTC',now)
    view=domain.availability(date(2026,10,19),270,'UTC',datetime(2026,10,22,18,tzinfo=UTC),[])
    assert view['days'][3]['status']=='past' and not view['days'][3]['slots']
