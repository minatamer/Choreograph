"""Receipt snapshots batch reads while preserving reviewed destination fences."""
import json
from collections import Counter
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_booking import add_request, prepare
from test_jobs import claim_for, connected_booking
from test_requests import NOW, command

from choreograph import jobs, knowledge
from choreograph.models import Connection, ExternalMapping, Outbox


@pytest.fixture(scope='module')
def prepared_database(database):
    with Session(database[0]) as db,db.begin():
        knowledge.prepare_samples(db,NOW)
    return database


def counted_snapshot(engine,client,headers):
    counts=Counter({'all':0,'connection':0,'outbox':0,'mapping':0})

    def capture(_connection,_cursor,statement,_parameters,_context,_many):
        if not statement.lstrip().upper().startswith('SELECT'):return
        counts['all']+=1
        for name,table in [('connection','crm_connections'),('outbox','outbox'),('mapping','external_mappings')]:
            if table in statement:counts[name]+=1

    event.listen(engine,'before_cursor_execute',capture)
    try:
        response=client.get('/v1/session',headers=headers)
        assert response.status_code==200
        return response.json(),dict(counts)
    finally:
        event.remove(engine,'before_cursor_execute',capture)


def assert_without_receipt(record,status):
    assert record['crm_state']==status
    assert record['crm_receipt'] is None and record['crm_links']=={}


def test_skipped_snapshot_query_cost_is_flat_from_one_to_ten(prepared_database):
    engine,_=prepared_database
    client,headers,state,start=prepare(prepared_database)
    try:
        one,one_count=counted_snapshot(engine,client,headers)
        for _ in range(9):state=add_request(client,headers,state,start)
        ten,ten_count=counted_snapshot(engine,client,headers)
        assert len(one['requests'])==1 and len(ten['requests'])==10
        assert one_count==ten_count
        assert one_count['outbox']==1 and one_count['mapping']==0
        for record in ten['requests']:assert_without_receipt(record,'not_connected')
        assert ten['crm_mode']=='skipped' and not client.app.state.crm.calls
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.workspace_id==UUID(state['workspace_id'])))==0
        print(json.dumps({'snapshot':'skipped','one':one_count,'ten':ten_count},sort_keys=True))
    finally:client.close()


def test_connected_snapshot_query_cost_is_flat_and_keeps_delivered_receipt(prepared_database):
    engine,settings=prepared_database
    client,headers,state,provider,event_id=connected_booking(prepared_database)
    try:
        assert jobs.deliver(engine,settings,provider,claim_for(engine,state,event_id),lambda:NOW)
        one,one_count=counted_snapshot(engine,client,headers)
        original=one['requests'][0]
        assert original['crm_state']=='simulated_synced' and original['crm_receipt']['provider']=='fake'
        assert original['crm_links']=={}
        week=client.get('/v1/availability?week='+state['scenario']['week_start'],headers=headers).json()
        start=next(day['slots'][0]['start'] for day in week['days'] if day['slots'])
        state=one
        for _ in range(9):state=add_request(client,headers,state,start)
        calls=list(provider.calls)
        ten,ten_count=counted_snapshot(engine,client,headers)
        assert len(ten['requests'])==10 and one_count==ten_count
        assert one_count['outbox']==1 and one_count['mapping']==1
        current=next(row for row in ten['requests'] if row['id']==original['id'])
        assert current==original
        for record in ten['requests']:
            if record['id']!=original['id']:assert_without_receipt(record,'not_shared')
        assert provider.calls==calls
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.workspace_id==UUID(state['workspace_id'])))==1
        print(json.dumps({'snapshot':'connected','one':one_count,'ten':ten_count},sort_keys=True))
    finally:client.close()


def test_batched_snapshot_preserves_event_mapping_and_disconnect_fences(prepared_database):
    engine,settings=prepared_database
    client,headers,state,provider,event_id=connected_booking(prepared_database)
    workspace_id=UUID(state['workspace_id']);connection_id=UUID(state['connection']['id'])
    request_id=UUID(state['requests'][0]['id'])

    def record():
        response=client.get('/v1/session',headers=headers)
        assert response.status_code==200
        return next(row for row in response.json()['requests'] if UUID(row['id'])==request_id)

    def change(model,key,**fields):
        with Session(engine) as db,db.begin():
            row=db.get(model,key)
            for name,value in fields.items():setattr(row,name,value)

    try:
        with Session(engine) as db:
            row=db.get(Outbox,(workspace_id,event_id))
            baseline={name:getattr(row,name) for name in
                      ('workspace_generation','connection_generation','revision','connection_id','account_id')}
        assert_without_receipt(record(),'pending')
        for name in ('workspace_generation','connection_generation','revision'):
            change(Outbox,(workspace_id,event_id),**{name:baseline[name]+1})
            assert_without_receipt(record(),'not_shared')
            change(Outbox,(workspace_id,event_id),**{name:baseline[name]})
        old_connection=uuid4()
        with Session(engine) as db,db.begin():
            db.add(Connection(workspace_id=workspace_id,id=old_connection,account_id='old-fixture-account',
                              state='detached',provider='fake',generation=1,export_consent=False,
                              created_at=NOW-timedelta(seconds=1)))
        change(Outbox,(workspace_id,event_id),connection_id=old_connection,account_id='old-fixture-account')
        assert_without_receipt(record(),'not_shared')
        change(Outbox,(workspace_id,event_id),**baseline)
        assert jobs.deliver(engine,settings,provider,claim_for(engine,state,event_id),lambda:NOW)
        mapping_key=(workspace_id,connection_id,request_id)
        assert record()['crm_state']=='simulated_synced'
        for fields in ({'verified':False},{'account_id':'another-fixture-account'},{'revision':baseline['revision']-1}):
            change(ExternalMapping,mapping_key,**fields)
            assert_without_receipt(record(),'synced')
            change(ExternalMapping,mapping_key,verified=True,account_id=baseline['account_id'],revision=baseline['revision'])

        # A fake receipt cannot be relabelled as a real account. Native link
        # construction is covered by the full injected flow in test_live_crm.
        with pytest.raises(IntegrityError):
            change(Connection,(workspace_id,connection_id),provider='hubspot',account_id='456')
        assert record()['crm_state']=='simulated_synced' and record()['crm_links']=={}

        change(Connection,(workspace_id,connection_id),state='needs_attention')
        assert_without_receipt(record(),'needs_attention')
        change(Outbox,(workspace_id,event_id),connection_generation=baseline['connection_generation']+1)
        assert_without_receipt(record(),'not_shared')
        change(Outbox,(workspace_id,event_id),connection_generation=baseline['connection_generation'])
        change(Connection,(workspace_id,connection_id),state='ready')
        state=client.get('/v1/session',headers=headers).json()
        week=client.get('/v1/availability?week='+state['scenario']['week_start'],headers=headers).json()
        start=next(day['slots'][0]['start'] for day in week['days'] if day['slots'])
        state=add_request(client,headers,state,start)
        calls=list(provider.calls)
        response=command(client,headers,state,{},'/v1/crm/disconnect',method='post')
        assert response.status_code==200
        records=response.json()['state']['requests']
        for row in records:
            assert_without_receipt(row,'disconnected' if UUID(row['id'])==request_id else 'not_connected')
        assert provider.calls==calls
    finally:client.close()
