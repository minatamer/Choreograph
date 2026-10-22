"""No Google identity, account or network is inherited by these transport tests."""
from dataclasses import replace
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from choreograph.task_delivery import TaskTarget, task_payload
from choreograph.task_enqueue import CloudTasks, PublishFailure, TasksConfig

TARGET=TaskTarget('https://worker.example.invalid/internal/tasks/crm','https://worker.example.invalid',
                  'delivery@test-project.iam.gserviceaccount.com')
CONFIG=TasksConfig('test-project','us-central1','choreograph',TARGET)
NAME=CONFIG.parent+'/tasks/'+'a'*64


def test_create_get_use_fixed_google_origin_full_view_and_uuid_only_payload():
    seen=[];body=task_payload(TARGET,uuid4(),uuid4())
    def handle(request):
        import json
        seen.append(request)
        assert request.url.host=='cloudtasks.googleapis.com' and request.headers['accept-encoding']=='identity'
        assert request.headers['authorization']=='Bearer synthetic-google-access'
        if request.method=='POST':
            value=json.loads(request.content);assert value['responseView']=='FULL'
            return httpx.Response(200,json=value['task'])
        assert request.url.params['responseView']=='FULL'
        return httpx.Response(404)
    http=httpx.Client(base_url='https://wrong.example.invalid',transport=httpx.MockTransport(handle))
    transport=CloudTasks(CONFIG,authorized=True,client=http,bearer=lambda:'synthetic-google-access')
    try:
        assert transport.create(NAME,body)=={'name':NAME,**body}
        assert transport.get(NAME) is None and len(seen)==2
        transport.close();transport.close();assert not http.is_closed
    finally:http.close()


def test_invalid_configuration_payload_and_task_identity_fail_before_auth():
    with pytest.raises(ValueError):TasksConfig.parse({})
    with pytest.raises(ValueError):replace(CONFIG,project='another-project')
    with pytest.raises(ValueError):TaskTarget(TARGET.url,TARGET.audience+'/wrong',TARGET.service_email)
    with pytest.raises(ValueError):TaskTarget(TARGET.url,TARGET.audience,'wrong@other.invalid')
    calls=[]
    http=httpx.Client(transport=httpx.MockTransport(lambda _:(calls.append(1),httpx.Response(200,json={}))[1]))
    transport=CloudTasks(CONFIG,authorized=True,client=http,bearer=lambda:(_ for _ in ()).throw(AssertionError('auth reached')))
    try:
        with pytest.raises(PublishFailure):transport.get(CONFIG.parent+'/tasks/../other')
        body=task_payload(TARGET,uuid4(),uuid4());body['httpRequest']['url']='https://other.invalid'
        with pytest.raises(PublishFailure):transport.create(NAME,body)
        assert calls==[]
    finally:http.close()


@pytest.mark.parametrize('status,code,unknown',[(409,'TASK_ALREADY_EXISTS',True),(403,'TASK_ACCESS_DENIED',False),
    (404,'TASK_QUEUE_MISSING',False),
    (500,'TASK_UNAVAILABLE',True)])
def test_create_errors_are_sanitized_conservative_and_never_retried(status,code,unknown):
    calls=[]
    def handle(request):calls.append(1);return httpx.Response(status,json={'message':'synthetic-private-provider-text'})
    http=httpx.Client(transport=httpx.MockTransport(handle))
    transport=CloudTasks(CONFIG,authorized=True,client=http,bearer=lambda:'synthetic-access')
    try:
        with pytest.raises(PublishFailure) as error:transport.create(NAME,task_payload(TARGET,uuid4(),uuid4()))
        assert str(error.value)==code and error.value.unknown is unknown and calls==[1]
    finally:http.close()


@pytest.mark.parametrize('response,code',[
    (lambda:httpx.Response(200,stream=httpx.ByteStream(b'compressed'),headers={'content-encoding':'gzip'}),'TASK_RESPONSE_ENCODING'),
    (lambda:httpx.Response(200,content=b'x'*16385),'TASK_RESPONSE_LIMIT'),
    (lambda:httpx.Response(200,json=[]),'TASK_RESPONSE_FORMAT'),
])
def test_get_response_bounds(response,code):
    http=httpx.Client(transport=httpx.MockTransport(lambda _:response()))
    transport=CloudTasks(CONFIG,authorized=True,client=http,bearer=lambda:'synthetic-access')
    try:
        with pytest.raises(PublishFailure) as error:transport.get(NAME)
        assert error.value.code==code
    finally:http.close()


def test_metadata_identity_is_fixed_bounded_and_cached_without_environment_credentials(monkeypatch):
    from choreograph import task_enqueue
    original=httpx.Client;seen=[];options=[];clock=[0.]
    def handle(request):
        seen.append(request)
        assert str(request.url)=='http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token'
        assert request.headers['metadata-flavor']=='Google'
        return httpx.Response(200,json={'access_token':'synthetic-access','token_type':'Bearer','expires_in':3600},headers={'metadata-flavor':'Google'})
    def client(**kwargs):options.append(kwargs);return original(transport=httpx.MockTransport(handle),**kwargs)
    monkeypatch.setenv('GCE_METADATA_HOST','untrusted.example.invalid')
    monkeypatch.setenv('GOOGLE_APPLICATION_CREDENTIALS','must-not-be-read.json')
    monkeypatch.setattr(task_enqueue.httpx,'Client',client)
    monkeypatch.setattr(task_enqueue,'time',SimpleNamespace(monotonic=lambda:clock[0]))
    identity=task_enqueue.MetadataIdentity()
    try:
        assert identity()==identity()=='synthetic-access' and len(seen)==1
        assert options[0]['trust_env'] is False and options[0]['follow_redirects'] is False
        clock[0]=3541.;assert identity()=='synthetic-access' and len(seen)==2
    finally:identity.close()
