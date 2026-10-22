"""Fixed Cloud Tasks/metadata endpoints; no credential discovery or write retries."""
import base64
import binascii
import json
import re
import time
from dataclasses import dataclass

import httpx

from .task_delivery import Delivery, TaskTarget


class PublishFailure(Exception):
    def __init__(self,code,*,unknown=False):
        self.code,self.unknown=code,unknown
        super().__init__(code)


@dataclass(frozen=True)
class TasksConfig:
    project: str
    region: str
    queue: str
    target: TaskTarget

    def __post_init__(self):
        if (not re.fullmatch(r'[a-z][a-z0-9-]{4,28}[a-z0-9]',self.project) or
                not re.fullmatch(r'[a-z]+-[a-z]+[0-9]{1,2}',self.region) or
                not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',self.queue) or
                not self.target.service_email.endswith('@'+self.project+'.iam.gserviceaccount.com')):
            raise ValueError('TASKS_CONFIGURATION_INVALID')

    @property
    def parent(self):return f'projects/{self.project}/locations/{self.region}/queues/{self.queue}'

    @classmethod
    def parse(cls,values):
        if values.get('CHOREOGRAPH_TASKS_ENABLED')!='true':raise ValueError('TASKS_NOT_ENABLED')
        return cls(values.get('CHOREOGRAPH_TASK_PROJECT',''),values.get('CHOREOGRAPH_TASK_REGION',''),
            values.get('CHOREOGRAPH_TASK_QUEUE',''),TaskTarget(values.get('CHOREOGRAPH_TASK_URL',''),
                values.get('CHOREOGRAPH_TASK_AUDIENCE',''),values.get('CHOREOGRAPH_TASK_SERVICE_EMAIL','')))


def _body(response,deadline,limit=16_384):
    if response.headers.get('content-encoding','identity').strip().lower() not in {'','identity'}:
        raise PublishFailure('TASK_RESPONSE_ENCODING',unknown=True)
    length=response.headers.get('content-length')
    if length and (not length.isascii() or not length.isdigit() or len(length)>9 or int(length)>limit):
        raise PublishFailure('TASK_RESPONSE_LIMIT',unknown=True)
    data=bytearray()
    parts=(response.content,) if response.is_stream_consumed else response.iter_raw()
    for part in parts:
        if time.monotonic()>=deadline:raise PublishFailure('TASK_TIMEOUT',unknown=True)
        if len(data)+len(part)>limit:raise PublishFailure('TASK_RESPONSE_LIMIT',unknown=True)
        data.extend(part)
    if time.monotonic()>=deadline:raise PublishFailure('TASK_TIMEOUT',unknown=True)
    try:value=json.loads(data)
    except (ValueError,UnicodeError):raise PublishFailure('TASK_RESPONSE_FORMAT',unknown=True) from None
    if not isinstance(value,dict):raise PublishFailure('TASK_RESPONSE_FORMAT',unknown=True)
    return value


class MetadataIdentity:
    def __init__(self):
        self.client=httpx.Client(trust_env=False,follow_redirects=False,timeout=httpx.Timeout(1,connect=2),
                                 limits=httpx.Limits(max_connections=1,max_keepalive_connections=1))
        self._token=None;self._expires=0.

    def __call__(self):
        if self._token and time.monotonic()<self._expires:return self._token
        try:
            deadline=time.monotonic()+4
            with self.client.stream('GET','http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',
                    headers={'Metadata-Flavor':'Google','accept-encoding':'identity'},follow_redirects=False) as response:
                if response.status_code!=200 or response.headers.get('metadata-flavor')!='Google':
                    raise PublishFailure('TASK_IDENTITY_UNAVAILABLE')
                value=_body(response,deadline,8192)
            token=value.get('access_token','');expiry=value.get('expires_in')
            if (not isinstance(token,str) or len(token)>4096 or not re.fullmatch(r'[A-Za-z0-9._~+/-]+={0,2}',token) or
                    str(value.get('token_type','')).lower()!='bearer' or type(expiry) is not int or not 60<expiry<=3600):
                raise PublishFailure('TASK_IDENTITY_UNAVAILABLE')
            self._token=token;self._expires=time.monotonic()+expiry-60
            return token
        except (httpx.HTTPError,ValueError):raise PublishFailure('TASK_IDENTITY_UNAVAILABLE') from None

    def close(self):self._token=None;self.client.close()


class CloudTasks:
    def __init__(self,config,*,authorized=False,client=None,bearer=None):
        if not authorized:raise ValueError('TASKS_NOT_ENABLED')
        self.config=config;self._owned=client is None;self._closed=False
        self.client=client or httpx.Client(base_url='https://cloudtasks.googleapis.com',trust_env=False,
            follow_redirects=False,timeout=httpx.Timeout(1,connect=3,write=3,pool=1),
            limits=httpx.Limits(max_connections=2,max_keepalive_connections=1))
        try:self._identity=MetadataIdentity() if bearer is None else None
        except BaseException:
            if self._owned:self.client.close()
            raise
        self.bearer=bearer if bearer is not None else self._identity

    def _name(self,name):
        prefix=self.config.parent+'/tasks/'
        if not isinstance(name,str) or not name.startswith(prefix) or not re.fullmatch(r'[a-f0-9]{64}',name[len(prefix):]):
            raise PublishFailure('TASK_IDENTITY_INVALID')

    def _request(self,method,path,**kwargs):
        try:
            token=self.bearer()
            if not isinstance(token,str) or len(token)>4096 or not re.fullmatch(r'[A-Za-z0-9._~+/-]+={0,2}',token):
                raise PublishFailure('TASK_IDENTITY_UNAVAILABLE')
            deadline=time.monotonic()+8
            # Absolute origin is deliberate even for a caller-borrowed client.
            with self.client.stream(method,'https://cloudtasks.googleapis.com/v2/'+path,
                    headers={'authorization':'Bearer '+token,'accept-encoding':'identity'},follow_redirects=False,**kwargs) as response:
                if response.status_code==404:
                    if method=='POST':raise PublishFailure('TASK_QUEUE_MISSING')
                    return None
                if response.status_code==409:raise PublishFailure('TASK_ALREADY_EXISTS',unknown=True)
                if response.status_code in {401,403}:raise PublishFailure('TASK_ACCESS_DENIED')
                if not 200<=response.status_code<300:
                    raise PublishFailure('TASK_UNAVAILABLE',unknown=method=='POST')
                return _body(response,deadline)
        except PublishFailure:raise
        except httpx.HTTPError:raise PublishFailure('TASK_TIMEOUT',unknown=method=='POST') from None

    def create(self,name,task):
        self._name(name)
        try:
            request=task['httpRequest'];target=self.config.target
            if (not isinstance(request,dict) or set(task)-{'httpRequest','dispatchDeadline'} or task.get('dispatchDeadline')!='120s' or
                    request.get('url')!=target.url or request.get('httpMethod')!='POST' or
                    request.get('headers')!={'Content-Type':'application/json'} or
                    request.get('oidcToken')!={'serviceAccountEmail':target.service_email,'audience':target.audience} or
                    set(request)-{'url','httpMethod','headers','body','oidcToken'} or
                    not isinstance(request.get('body'),str) or len(request['body'])>1500):
                raise ValueError()
            Delivery.model_validate_json(base64.b64decode(request['body'],validate=True))
        except (ValueError,KeyError,TypeError,binascii.Error):
            raise PublishFailure('TASK_PAYLOAD_INVALID') from None
        return self._request('POST',self.config.parent+'/tasks',json={'task':{'name':name,**task},'responseView':'FULL'})

    def get(self,name):
        self._name(name)
        return self._request('GET',name,params={'responseView':'FULL'})

    def close(self):
        if not self._closed:
            self._closed=True
            if self._owned:self.client.close()
            if self._identity:self._identity.close()
