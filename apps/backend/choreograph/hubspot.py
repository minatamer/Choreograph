"""Narrow HubSpot transports. No generic proxy, secret logging or automatic retries."""
import json
import re
import time
from copy import copy
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .models import SimulatedRecord

SCOPES=('oauth','crm.objects.contacts.read','crm.objects.contacts.write','crm.objects.deals.read','crm.objects.deals.write',
        'crm.schemas.contacts.read','crm.schemas.contacts.write','crm.schemas.deals.read','crm.schemas.deals.write','settings.currencies.read')
KEY_PROPERTY='choreograph_demo_key'
CURRENCY_PATH='/account-info/2026-09/details'


class CRMFailure(Exception):
    def __init__(self,code,retryable=False,ambiguous=False,retry_after=0):
        self.code=code;self.retryable=retryable;self.ambiguous=ambiguous;self.retry_after=min(300,max(0,retry_after))
        super().__init__(code)


class FakeHubSpot:
    provider='fake'
    app_id='choreograph-local-simulation'
    capacity=25
    def __init__(self,engine,account_id=None):self.engine=engine;self.account_id=account_id;self.calls=[]
    def authorization_url(self,state):return None
    def exchange(self,code,workspace_id):
        self.calls.append('exchange')
        if code!='approved':raise CRMFailure('CRM_DENIED')
        return {'access_token':'fake-'+uuid4().hex,'refresh_token':'fake-refresh-'+uuid4().hex,
                'account_id':self.account_id or 'simulated-'+str(workspace_id),'expires_at':(datetime.now(UTC)+timedelta(minutes=30)).isoformat()}
    def refresh(self,tokens):self.calls.append('refresh');return {**tokens,'expires_at':(datetime.now(UTC)+timedelta(minutes=30)).isoformat()}
    def upsert(self,tokens,kind,key,properties):
        self.calls.append('upsert-'+kind)
        with Session(self.engine) as db,db.begin():
            db.execute(insert(SimulatedRecord).values(account_id=tokens['account_id'],object_type=kind,external_key=key,
                       id='sim-'+uuid4().hex,properties=properties,archived=False).on_conflict_do_update(
                       index_elements=['account_id','object_type','external_key'],set_={'properties':properties,'archived':False}))
            row=db.get(SimulatedRecord,(tokens['account_id'],kind,key))
            return row.id
    def read(self,tokens,kind,key):
        self.calls.append('read-'+kind)
        with Session(self.engine) as db:
            row=db.get(SimulatedRecord,(tokens['account_id'],kind,key))
            return None if not row or row.archived else {'id':row.id,'properties':row.properties}
    def associate(self,tokens,contact_id,deal_id):
        self.calls.append('associate')
        with Session(self.engine) as db,db.begin():
            contact=db.scalar(select(SimulatedRecord).where(SimulatedRecord.account_id==tokens['account_id'],SimulatedRecord.id==contact_id,SimulatedRecord.object_type=='contacts'))
            deal=db.scalar(select(SimulatedRecord).where(SimulatedRecord.account_id==tokens['account_id'],SimulatedRecord.id==deal_id,SimulatedRecord.object_type=='deals'))
            if not contact or not deal:raise CRMFailure('CRM_IDENTITY')
            deal.properties={**deal.properties,'__contact_id':contact_id}
    def verify_association(self,tokens,contact_id,deal_id):
        self.calls.append('verify-association')
        with Session(self.engine) as db:
            deal=db.scalar(select(SimulatedRecord).where(SimulatedRecord.account_id==tokens['account_id'],SimulatedRecord.id==deal_id,SimulatedRecord.object_type=='deals'))
            return bool(deal and deal.properties.get('__contact_id')==contact_id)
    def archive(self,tokens,kind,key):
        self.calls.append('archive-'+kind)
        with Session(self.engine) as db,db.begin():
            row=db.get(SimulatedRecord,(tokens['account_id'],kind,key))
            if row:row.archived=True
    def uninstall(self,tokens):self.calls.append('uninstall');return True
    def close(self):pass


@dataclass(frozen=True)
class HubSpotConfig:
    app_id:str
    client_id:str
    client_secret:str=field(repr=False)
    redirect_uri:str
    pipeline_id:str=''
    stage_id:str=''
    schema_setup_allowed:bool=False
    capacity:int=25
    distribution:str='marketplace_unlisted'


class HubSpotTransport:
    provider='hubspot'
    def __init__(self,config:HubSpotConfig,*,authorized=False,client=None,engine=None,allowance=None,clock=None):
        if not authorized or not all((config.app_id,config.client_id,config.client_secret,config.redirect_uri)):
            raise CRMFailure('CRM_NOT_CONFIGURED')
        self.config=config;self.app_id=config.app_id;self.capacity=config.capacity
        self.engine,self.allowance,self.clock=engine,allowance,clock or (lambda:datetime.now(UTC))
        self.admission=None;self.deadline=None;self.requires_admission=client is None or allowance is not None
        self._owned=client is None;self._closed=False
        self.client=client or httpx.Client(base_url='https://api.hubapi.com',timeout=httpx.Timeout(1,connect=3,write=3,pool=1),
             trust_env=False,follow_redirects=False,limits=httpx.Limits(max_connections=4,max_keepalive_connections=2))

    def with_workspace(self,workspace_id,*,deadline=None):
        from .crm_admission import CRMAdmission
        scoped=copy(self);scoped._owned=False
        scoped.admission=CRMAdmission(self.engine,self.allowance,workspace_id,self.clock) if self.allowance else None
        scoped.deadline=deadline
        return scoped

    def close(self):
        if self._owned and not self._closed:self._closed=True;self.client.close()

    def _request(self,method,path,*,tokens=None,**kwargs):
        if (not path.startswith(('/oauth/2026-09/','/crm/v3/','/crm/v4/','/appinstalls/v3/')) and
                not (method=='GET' and path==CURRENCY_PATH)) or '..' in path:
            raise CRMFailure('CRM_ROUTE')
        if self.deadline is not None and time.monotonic()>=self.deadline:raise CRMFailure('CRM_TIMEOUT')
        if self.admission:self.admission.reserve()
        elif self.requires_admission:raise CRMFailure('CRM_NOT_CONFIGURED')
        headers={'Authorization':'Bearer '+tokens['access_token']} if tokens else {}
        headers['accept-encoding']='identity'
        deadline=min(time.monotonic()+8,self.deadline) if self.deadline is not None else time.monotonic()+8
        try:
            with self.client.stream(method,'https://api.hubapi.com'+path,headers=headers,follow_redirects=False,**kwargs) as response:
                ambiguous=method in {'POST','PATCH','PUT','DELETE'}
                if response.headers.get('content-encoding','identity').strip().lower() not in {'','identity'}:
                    raise CRMFailure('CRM_RESPONSE_ENCODING',ambiguous=ambiguous)
                length=response.headers.get('content-length')
                if length and (not length.isascii() or not length.isdigit() or len(length)>9 or int(length)>262_144):
                    raise CRMFailure('CRM_RESPONSE_LIMIT',ambiguous=ambiguous)
                data=bytearray()
                parts=(response.content,) if response.is_stream_consumed else response.iter_raw()
                for part in parts:
                    if time.monotonic()>=deadline:raise CRMFailure('CRM_TIMEOUT',True,ambiguous=ambiguous)
                    if len(data)+len(part)>262_144:raise CRMFailure('CRM_RESPONSE_LIMIT',ambiguous=ambiguous)
                    data.extend(part)
                if time.monotonic()>=deadline:raise CRMFailure('CRM_TIMEOUT',True,ambiguous=ambiguous)
                if response.status_code==404:return None
                if response.status_code in (401,403):raise CRMFailure('CRM_AUTH_REQUIRED')
                if response.status_code==429:
                    value=response.headers.get('retry-after','30');delay=int(value) if value.isdigit() else 30
                    raise CRMFailure('CRM_RATE_LIMIT',True,retry_after=delay)
                if response.status_code==409:raise CRMFailure('CRM_DUPLICATE',True)
                if response.status_code>=500:raise CRMFailure('CRM_UNAVAILABLE',True,ambiguous=method in {'POST','PATCH','PUT','DELETE'})
                if not 200<=response.status_code<300:raise CRMFailure('CRM_REJECTED')
                payload=json.loads(data) if data else {}
                if not isinstance(payload,dict):raise CRMFailure('CRM_FORMAT',ambiguous=ambiguous)
                return payload
        except CRMFailure:raise
        except (httpx.TimeoutException,httpx.TransportError):raise CRMFailure('CRM_TIMEOUT',True,ambiguous=method in {'POST','PATCH','PUT','DELETE'}) from None
        except (ValueError,KeyError):raise CRMFailure('CRM_FORMAT',ambiguous=method in {'POST','PATCH','PUT','DELETE'}) from None

    def authorization_url(self,state):
        return 'https://app.hubspot.com/oauth/authorize?'+urlencode({'client_id':self.config.client_id,'redirect_uri':self.config.redirect_uri,'scope':' '.join(SCOPES),'state':state})

    def _token(self,data):
        payload=self._request('POST','/oauth/2026-09/token',data={**data,'client_id':self.config.client_id,'client_secret':self.config.client_secret})
        if (not payload or any(not isinstance(payload.get(name),str) or not 1<=len(payload[name])<=4096 or
                any(char.isspace() for char in payload[name]) for name in ('access_token','refresh_token')) or
                type(payload.get('expires_in')) is not int or not 1<=payload['expires_in']<=1800):
            raise CRMFailure('CRM_AUTH_REQUIRED')
        meta=self._request('POST','/oauth/2026-09/token/introspect',data={'client_id':self.config.client_id,'client_secret':self.config.client_secret,
              'token_type_hint':'access_token','token':payload['access_token']})
        if (not meta or meta.get('active') is not True or str(meta.get('app_id'))!=self.config.app_id or
            meta.get('client_id')!=self.config.client_id or meta.get('token_use')!='access_token' or
            str(meta.get('token_type','')).lower()!='bearer' or
            not re.fullmatch(r'[0-9]{1,30}',str(meta.get('hub_id',''))) or not isinstance(meta.get('scopes'),list) or
            any(not isinstance(scope,str) for scope in meta['scopes']) or not set(SCOPES).issubset(meta['scopes']) or
            meta.get('is_private_distribution') is not (self.config.distribution=='private')):
            raise CRMFailure('CRM_SCOPES_REQUIRED')
        return {'access_token':payload['access_token'],'refresh_token':payload['refresh_token'],'account_id':str(meta['hub_id']),
                'expires_at':(self.clock()+timedelta(seconds=payload['expires_in'])).isoformat()}

    def exchange(self,code,workspace_id):
        return self._token({'grant_type':'authorization_code','code':code,'redirect_uri':self.config.redirect_uri})
    def refresh(self,tokens):
        refreshed=self._token({'grant_type':'refresh_token','refresh_token':tokens['refresh_token']})
        if refreshed['account_id']!=tokens['account_id']:raise CRMFailure('CRM_ACCOUNT_CHANGED')
        return refreshed

    def verify_currency(self,tokens):
        currency=self._request('GET',CURRENCY_PATH,tokens=tokens)
        code=currency.get('companyCurrency') if currency else None
        if not isinstance(code,str) or not re.fullmatch(r'[A-Z]{3}',code):raise CRMFailure('CRM_CURRENCY_UNAVAILABLE',True)
        if type(currency.get('portalId')) is not int or str(currency['portalId'])!=tokens.get('account_id'):
            raise CRMFailure('CRM_ACCOUNT_CHANGED')
        if code!='USD':raise CRMFailure('CRM_CURRENCY_REQUIRED')

    def preflight(self,tokens,*,allow_schema=False):
        self.verify_currency(tokens)
        for kind in ('contacts','deals'):
            prop=self._request('GET',f'/crm/v3/properties/{kind}/{KEY_PROPERTY}',tokens=tokens)
            if prop is None:
                if not self.config.schema_setup_allowed or not allow_schema:raise CRMFailure('CRM_SETUP_REQUIRED')
                prop=self._request('POST',f'/crm/v3/properties/{kind}',tokens=tokens,json={'name':KEY_PROPERTY,'label':'Choreograph demo key',
                  'type':'string','fieldType':'text','groupName':'contactinformation' if kind=='contacts' else 'dealinformation','hasUniqueValue':True})
            if not prop or prop.get('hasUniqueValue') is not True or prop.get('type')!='string':raise CRMFailure('CRM_UNIQUENESS_REQUIRED')

    def destinations(self,tokens):
        result=self._request('GET','/crm/v3/pipelines/deals',tokens=tokens)
        if not result or not isinstance(result.get('results'),list) or len(result['results'])>20 or result.get('paging'):
            raise CRMFailure('CRM_PIPELINES_LIMIT')
        options=[]
        for pipeline in result['results']:
            if not isinstance(pipeline,dict):raise CRMFailure('CRM_FORMAT')
            if pipeline.get('archived'):continue
            if (not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',str(pipeline.get('id',''))) or
                    not isinstance(pipeline.get('label'),str) or not 1<=len(pipeline['label'])<=120 or
                    not isinstance(pipeline.get('stages'),list) or len(pipeline['stages'])>50):raise CRMFailure('CRM_PIPELINES_LIMIT')
            stages=[]
            for stage in pipeline['stages']:
                if not isinstance(stage,dict):raise CRMFailure('CRM_FORMAT')
                metadata=stage.get('metadata',{})
                if not isinstance(metadata,dict):raise CRMFailure('CRM_FORMAT')
                if stage.get('archived') or str(metadata.get('isClosed','')).lower()!='false':continue
                if (not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',str(stage.get('id',''))) or
                        not isinstance(stage.get('label'),str) or not 1<=len(stage['label'])<=120):raise CRMFailure('CRM_PIPELINES_LIMIT')
                stages.append({'id':str(stage['id']),'label':stage['label']})
            if stages:options.append({'id':str(pipeline['id']),'label':pipeline['label'],'stages':stages})
        if not options:raise CRMFailure('CRM_DESTINATION_REQUIRED')
        return options

    def read(self,tokens,kind,key):
        if kind not in ('contacts','deals') or not re.fullmatch(r'[a-f0-9]{64}',key):raise CRMFailure('CRM_IDENTITY')
        properties=[KEY_PROPERTY,'firstname','lastname','email'] if kind=='contacts' else [KEY_PROPERTY,'dealname','description','amount','deal_currency_code','pipeline','dealstage']
        row=self._request('GET',f'/crm/v3/objects/{kind}/{key}',tokens=tokens,params={'idProperty':KEY_PROPERTY,'properties':','.join(properties)})
        if row and row.get('properties',{}).get(KEY_PROPERTY)!=key:raise CRMFailure('CRM_OWNERSHIP')
        return row

    def upsert(self,tokens,kind,key,properties):
        current=self.read(tokens,kind,key)
        if current:
            if not str(current.get('id','')).isdigit():raise CRMFailure('CRM_IDENTITY')
            row=self._request('PATCH',f"/crm/v3/objects/{kind}/{current['id']}",tokens=tokens,json={'properties':properties})
        else:
            try:row=self._request('POST',f'/crm/v3/objects/{kind}',tokens=tokens,json={'properties':{**properties,KEY_PROPERTY:key}})
            except CRMFailure as error:
                if error.code!='CRM_DUPLICATE':raise
                row=self.read(tokens,kind,key)
        if not row or not str(row.get('id','')).isdigit():raise CRMFailure('CRM_AMBIGUOUS',True,True)
        return str(row['id'])

    def associate(self,tokens,contact_id,deal_id):
        if not str(contact_id).isdigit() or not str(deal_id).isdigit():raise CRMFailure('CRM_IDENTITY')
        self._request('PUT',f'/crm/v4/objects/deals/{deal_id}/associations/default/contacts/{contact_id}',tokens=tokens)

    def verify_association(self,tokens,contact_id,deal_id):
        result=self._request('GET',f'/crm/v4/objects/deals/{deal_id}/associations/contacts',tokens=tokens,params={'limit':'100'})
        return bool(result and any(str(item.get('toObjectId'))==contact_id for item in result.get('results',[])))

    def archive(self,tokens,kind,key):
        row=self.read(tokens,kind,key)
        if row:self._request('DELETE',f"/crm/v3/objects/{kind}/{row['id']}",tokens=tokens)

    def uninstall(self,tokens):
        result=self._request('DELETE','/appinstalls/v3/external-install',tokens=tokens)
        if result is None:raise CRMFailure('CRM_UNINSTALL_UNKNOWN')
        return True
