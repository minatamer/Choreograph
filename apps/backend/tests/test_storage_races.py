"""Reset cannot lose an in-flight OAuth result or a rotated HubSpot token."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from uuid import UUID, uuid4

from test_crm import begin
from test_jobs import connected_booking
from test_requests import NOW, command

from choreograph import crm, jobs
from choreograph.hubspot import CRMFailure, FakeHubSpot
from choreograph.models import Connection, Installation
from choreograph.persistence import Session


class ObserveReset:
    def __init__(self,app,*,arrived):self.app=app;self.arrived=arrived
    async def __call__(self,scope,receive,send):
        if scope.get('path')=='/v1/reset':self.arrived.set()
        await self.app(scope,receive,send)


def reset(client,headers,state):
    return client.post('/v1/reset',headers={**headers,'idempotency-key':str(uuid4())},
        json={'generation':state['generation'],'timezone':state['timezone']})


def finish_reset(client,headers,state,result):
    if result.status_code==409:
        current=client.get('/v1/session',headers=headers)
        assert current.status_code==200,current.text
        result=reset(client,headers,current.json())
    assert result.status_code==200,result.text
    assert result.json()['workspace_id']!=state['workspace_id']


def test_reset_serializes_with_oauth_exchange_and_retains_installation_identity(database):
    engine,_=database;entered,release,arrived=Event(),Event(),Event()
    class Controlled(FakeHubSpot):
        def exchange(self,*args):
            entered.set();assert release.wait(5)
            return super().exchange(*args)
    provider=Controlled(engine)
    client,headers,state,_=begin(database,provider)
    client.app.middleware_stack=ObserveReset(client.app.middleware_stack,arrived=arrived)
    challenge=command(client,headers,state,{},'/v1/crm/connect',method='post').json()
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            connecting=pool.submit(command,client,headers,challenge['state'],
                {'state':challenge['oauth']['state'],'code':'approved'},'/v1/crm/callback',None,'post')
            assert entered.wait(5)
            resetting=pool.submit(reset,client,headers,challenge['state'])
            try:
                assert arrived.wait(5)
                assert not resetting.done()
            finally:release.set()
            accepted=connecting.result(timeout=8);assert accepted.status_code==200,accepted.text
            finish_reset(client,headers,challenge['state'],resetting.result(timeout=8))
        connection=accepted.json()['state']['connection'];wid=UUID(state['workspace_id'])
        with Session(engine) as db:
            stored=db.get(Connection,(wid,UUID(connection['id'])))
            assert stored.state=='retired' and stored.encrypted_tokens is None
            assert db.get(Installation,(provider.app_id,stored.account_id)).state=='installed'
        assert provider.calls==['exchange']
    finally:release.set();client.close()


def test_reset_waits_for_token_rotation_and_cleanup_uses_the_rotated_token(database):
    engine,settings=database;entered,release,arrived=Event(),Event(),Event();used=[]
    class Controlled(FakeHubSpot):
        def refresh(self,tokens):
            entered.set();assert release.wait(5)
            self.calls.append('refresh')
            return {**tokens,'refresh_token':'rotated-'+uuid4().hex,'expires_at':(NOW+timedelta(minutes=30)).isoformat()}
        def archive(self,tokens,*args):
            used.append(tokens['refresh_token']);return super().archive(tokens,*args)
    provider=Controlled(engine)
    client,headers,state,_,event=connected_booking(database,provider)
    client.app.middleware_stack=ObserveReset(client.app.middleware_stack,arrived=arrived)
    wid=UUID(state['workspace_id']);cid=UUID(state['connection']['id'])
    try:
        with Session(engine) as db,db.begin():
            connection=db.get(Connection,(wid,cid))
            tokens=crm.tokens_for(db,connection,settings.token_key,provider,NOW)
            connection.encrypted_tokens=crm.encrypt({**tokens,'expires_at':(NOW-timedelta(seconds=1)).isoformat()},settings.token_key)
        job=jobs.claim(engine,NOW,event_id=event,workspace_id=wid)
        with ThreadPoolExecutor(max_workers=2) as pool:
            rotating=pool.submit(jobs.prepare,engine,settings,provider,job,lambda:NOW)
            assert entered.wait(5)
            resetting=pool.submit(reset,client,headers,state)
            try:
                assert arrived.wait(5)
                assert not resetting.done()
            finally:release.set()
            prepared=rotating.result(timeout=8)
            assert prepared['tokens']['refresh_token'].startswith('rotated-')
            finish_reset(client,headers,state,resetting.result(timeout=8))
        jobs.finish_job(engine,provider,job,lambda:NOW,error=CRMFailure('CRM_RETIRED'))
        assert jobs.tick(engine,settings,provider,lambda:NOW)==1
        assert used and set(used)=={prepared['tokens']['refresh_token']}
        assert 'uninstall' not in provider.calls
        with Session(engine) as db:
            assert db.get(Connection,(wid,cid)).state=='finished'
            assert db.get(Connection,(wid,cid)).encrypted_tokens is None
    finally:release.set();client.close()
