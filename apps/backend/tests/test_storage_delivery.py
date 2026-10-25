"""Request publication and authenticated unattended recovery in both storage modes."""
import base64
import json
from datetime import timedelta

import pytest
from conftest import postgres_database as postgres_fixture
from fastapi.testclient import TestClient
from test_jobs import connected_booking
from test_requests import NOW, command
from test_task_enqueue import CONFIG

from choreograph.api import create_app
from choreograph.task_delivery import MaintenanceTarget, create_delivery_app
from choreograph.task_enqueue import PublishFailure


class Queue:
    config=CONFIG
    def __init__(self):self.tasks={};self.calls=[];self.lose=True
    def create(self,name,task):
        self.tasks[name]={'name':name,**task};self.calls.append(('create',name))
        if self.lose:
            self.lose=False;raise PublishFailure('TASK_TIMEOUT',unknown=True)
        return self.tasks[name]
    def get(self,name):self.calls.append(('get',name));return self.tasks.get(name)
    def close(self):pass


@pytest.fixture
def isolated_storage(database):
    # A maintenance sweep intentionally sees every workspace. Give this scenario
    # its own SQL store just as the object parameter already has its own shard.
    if not database[1].database_enabled:
        yield database
        return
    fixture=postgres_fixture.__wrapped__()
    try:yield next(fixture)
    finally:fixture.close()


def test_request_publication_loss_is_recovered_then_browser_closed_expiry_is_cleaned(isolated_storage):
    database=isolated_storage
    engine,settings=database;client,headers,state,provider,event=connected_booking(database)
    queue=Queue();time=[NOW]
    scheduler=MaintenanceTarget(CONFIG.target.audience+'/internal/maintenance',CONFIG.target.audience,
                                'scheduler@test-project.iam.gserviceaccount.com')
    def verify(token,audience):
        return {'iss':'https://accounts.google.com','aud':audience,'email_verified':True,
                'email':scheduler.service_email if token=='scheduler' else CONFIG.target.service_email}
    worker=create_delivery_app(settings,engine,provider,CONFIG.target,verifier=verify,clock=lambda:time[0],
                               maintenance_target=scheduler,publisher=queue)
    try:
        with TestClient(create_app(settings,engine,lambda:time[0],crm_provider=provider,publisher=queue),
                        cookies={'choreograph_guest':client.cookies.get('choreograph_guest')}) as api:
            result=command(api,headers,state,{'oven':True})
            assert result.status_code==200 and result.json()['state']['requests'][0]['status']=='confirmed'
            assert len(queue.calls)==1 and queue.calls[0][0]=='create'
            assert 'upsert-contacts' not in provider.calls
        client.close()  # No browser polling participates in the remaining work.
        with TestClient(worker) as private:
            assert private.post('/internal/maintenance',json={'sweep':True}).status_code==403
            assert private.post('/internal/maintenance',headers={'authorization':'Bearer task'},json={'sweep':True}).status_code==403
            assert private.post('/internal/maintenance',headers={'authorization':'Bearer scheduler'},json={'sweep':False}).status_code==422
            time[0]+=timedelta(seconds=3)
            assert private.post('/internal/maintenance',headers={'authorization':'Bearer scheduler'},json={'sweep':True}).status_code==204
            assert queue.calls[-1][0]=='get'
            delivery={'workspace_id':state['workspace_id'],'event_id':str(event)}
            assert private.post('/internal/tasks/crm',headers={'authorization':'Bearer task'},json=delivery).status_code==204
            assert provider.calls.count('upsert-contacts')==1 and provider.calls.count('upsert-deals')==1
            time[0]=NOW+timedelta(hours=2,seconds=1)
            assert private.post('/internal/maintenance',headers={'authorization':'Bearer scheduler'},json={'sweep':True}).status_code==204
            assert queue.calls[-1][0]=='create'
            cleanup=json.loads(base64.b64decode(queue.tasks[queue.calls[-1][1]]['httpRequest']['body']))
            assert cleanup['event_id']!=str(event)
            assert private.post('/internal/tasks/crm',headers={'authorization':'Bearer task'},json=cleanup).status_code==204
            calls=list(provider.calls)
            assert private.post('/internal/tasks/crm',headers={'authorization':'Bearer task'},json=cleanup).status_code==204
            assert provider.calls==calls and 'archive-deals' in calls and 'archive-contacts' in calls
            assert 'uninstall' not in calls
    finally:client.close()
