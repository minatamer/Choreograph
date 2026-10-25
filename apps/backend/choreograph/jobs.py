"""Durable bounded delivery; local polling and authenticated tasks share this code."""
import time
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from uuid import uuid4
from zoneinfo import ZoneInfo

from . import crm, knowledge, service
from .hubspot import KEY_PROPERTY, CRMFailure
from .models import (
    Activity,
    Connection,
    Enquiry,
    ExternalMapping,
    Idempotency,
    Installation,
    OAuthState,
    Outbox,
    Reservation,
    Staff,
    Workspace,
)
from .persistence import (
    Session,
    advisory,
    change,
    remove,
    repo_desc,
    repo_first,
    repo_rows,
    repo_value,
    repo_values,
    storage_retry,
)

LEASE=timedelta(seconds=180)


def recover_exhausted(db,now):
    change(db,Outbox,{'state':'needs_attention','code':'CRM_ATTEMPTS_EXHAUSTED','lease_until':None,'lease_token':None},
        predicate=lambda row:row.state=='processing' and row.lease_until is not None and row.lease_until<=now and row.attempts>=5,
        limit=20,lock=True)


def window_open(db,row,now):
    workspace=db.get(Workspace,row.workspace_id)
    return bool(workspace and now<workspace.created_at+timedelta(hours=3))


def expire_delivery_window(db,now):
    old={row.id for row in repo_rows(db,Workspace,predicate=lambda row:row.created_at<=now-timedelta(hours=3))}
    change(db,Outbox,{'state':'needs_attention','code':'CRM_WINDOW_EXPIRED','lease_until':None,'lease_token':None},
        predicate=lambda row:row.workspace_id in old and row.state in {'pending','retrying','reconciling','processing'} and
        (row.state!='processing' or (row.lease_until is not None and row.lease_until<=now)),limit=20,lock=True)


@storage_retry
def claim(engine,now,*,event_id=None,workspace_id=None):
    from .dispatch import eligible
    with Session(engine) as db,db.begin():
        advisory(db,45864,1)
        if len(repo_rows(db,Outbox,predicate=lambda row:row.state=='processing' and row.lease_until and row.lease_until>now))>=4:return None
        candidates=repo_rows(db,Outbox,predicate=lambda row:eligible(row,now) and
            (event_id is None or (row.id==event_id and row.workspace_id==workspace_id)),
            order=lambda row:(row.due_at,row.id),limit=20,lock=True)
        for row in candidates:
            connection=db.get(Connection,(row.workspace_id,row.connection_id),with_for_update=True)
            if not connection:continue
            if repo_first(db,Outbox,filters={'workspace_id':row.workspace_id,'connection_id':row.connection_id},
                predicate=lambda item,row=row:item.id!=row.id and item.state=='processing' and item.lease_until and item.lease_until>now):continue
            row.state='processing';row.attempts+=1;row.lease_until=now+LEASE;row.lease_token=uuid4();db.flush()
            return {'workspace_id':row.workspace_id,'event_id':row.id,'lease_token':row.lease_token}
        recover_exhausted(db,now)
    return None


def owned_job(db,job,now):
    row=db.get(Outbox,(job['workspace_id'],job['event_id']))
    if not row or row.state!='processing' or row.lease_token!=job['lease_token'] or row.lease_until<=now:return None
    return row


def valid(db,row,now):
    ws=db.get(Workspace,row.workspace_id);connection=db.get(Connection,(row.workspace_id,row.connection_id))
    if not ws or not connection or row.account_id!=connection.account_id or row.connection_generation!=connection.generation or row.workspace_generation!=ws.generation:return False
    if row.kind=='crm_cleanup':return connection.state=='finishing'
    enquiry=db.get(Enquiry,(row.workspace_id,row.enquiry_id))
    return bool(ws.active and ws.expires_at>now and ws.crm_mode=='connected' and connection.state=='ready' and connection.export_consent and
                enquiry and enquiry.revision==row.revision and enquiry.status in {'confirmed','cancelled','completed'})


def guard(engine,job,clock,provider=None):
    with Session(engine) as db:
        row=owned_job(db,job,clock())
        if not row or not valid(db,row,clock()):raise CRMFailure('CRM_RETIRED')
        if provider is not None:crm.require_provider(db.get(Connection,(row.workspace_id,row.connection_id)),provider)


def prepare(engine,settings,provider,job,clock):
    with Session(engine) as db,db.begin():
        row=owned_job(db,job,clock())
        if not row or not valid(db,row,clock()):raise CRMFailure('CRM_RETIRED')
        connection=repo_first(db, Connection, filters={'workspace_id': row.workspace_id, 'id': row.connection_id}, lock=True)
        if not window_open(db,row,clock()):raise CRMFailure('CRM_WINDOW_EXPIRED')
        tokens=crm.tokens_for(db,connection,settings.token_key,provider,clock())
        workspace=db.get(Workspace,row.workspace_id)
        data={'tokens':tokens,'kind':row.kind,'account_id':connection.account_id,'connection_id':connection.id,'payload':dict(row.payload or {})}
        data['contact_key']=crm.record_key(settings.bridge_secret,workspace.id,connection.id,'contacts')
        if row.kind=='crm_upsert':
            enquiry=db.get(Enquiry,(workspace.id,row.enquiry_id));booking=repo_first(db, Reservation, filters={'workspace_id': workspace.id, 'enquiry_id': enquiry.id})
            if not booking:raise CRMFailure('CRM_RETIRED')
            data['deal_key']=crm.record_key(settings.bridge_secret,workspace.id,connection.id,'deals',enquiry.id)
            contact=crm.contact_details()
            local=booking.starts_at.astimezone(ZoneInfo(workspace.timezone))
            local_end=booking.ends_at.astimezone(ZoneInfo(workspace.timezone))
            data['contact']={**contact,KEY_PROPERTY:data['contact_key']}
            data['deal']={KEY_PROPERTY:data['deal_key'],'dealname':'[Choreograph demo] '+enquiry.quote['items'][0]['name'],
                'description':f"Fictional demo booking\nStatus: {enquiry.status}\nAppointment: {local.isoformat(timespec='minutes')}\nEnds: {local_end.isoformat(timespec='minutes')}\nCleaner: {booking.staff_id.title()}\nQuote: USD {enquiry.quote['cents']/100:.2f}\nDuration: {enquiry.quote['minutes']} minutes\nNo real service or payment.",
                'amount':str(Decimal(enquiry.quote['cents'])/100),'deal_currency_code':'USD',
                'pipeline':connection.destination.get('pipeline_id','') if provider.provider=='hubspot' else 'simulated-pipeline',
                'dealstage':connection.destination.get('stage_id','') if provider.provider=='hubspot' else 'simulated-'+enquiry.status}
            if provider.provider=='hubspot' and not all((data['deal']['pipeline'],data['deal']['dealstage'])):
                raise CRMFailure('CRM_DESTINATION_REQUIRED')
        else:
            data['deal_keys']=[crm.record_key(settings.bridge_secret,workspace.id,connection.id,'deals',eid) for eid in repo_values(db, Enquiry, 'id', filters={'workspace_id': workspace.id})]
            data['can_uninstall']=not crm.other_uses(db,workspace,connection,clock())
        return data


def same_properties(actual,expected):
    for key,value in expected.items():
        if key=='amount':
            try:
                if Decimal(actual.get(key,''))!=Decimal(value):return False
            except InvalidOperation:return False
        elif str(actual.get(key,''))!=str(value):return False
    return True


def perform(engine,provider,job,data,clock,deadline):
    tokens=data['tokens']
    def call(method,*args):
        if time.monotonic()>deadline:raise CRMFailure('CRM_TIMEOUT',True,True)
        guard(engine,job,clock,provider);return method(tokens,*args)
    if data['kind']=='crm_upsert':
        if provider.provider=='hubspot':call(provider.verify_currency)
        contact_id=call(provider.upsert,'contacts',data['contact_key'],data['contact'])
        deal_id=call(provider.upsert,'deals',data['deal_key'],data['deal'])
        call(provider.associate,contact_id,deal_id)
        contact=call(provider.read,'contacts',data['contact_key']);deal=call(provider.read,'deals',data['deal_key'])
        if not contact or not deal or contact['id']!=contact_id or deal['id']!=deal_id or not same_properties(contact['properties'],data['contact']) or not same_properties(deal['properties'],data['deal']):
            raise CRMFailure('CRM_READBACK',True,True)
        if not call(provider.verify_association,contact_id,deal_id):raise CRMFailure('CRM_ASSOCIATION',True,True)
        return {'contact_id':contact_id,'deal_id':deal_id,'cleanup':'not_requested','uninstall':'not_requested'}
    result={'cleanup':'not_requested','uninstall':'not_requested'}
    if data['payload'].get('cleanup'):
        # Deterministic identity lookups also find a create whose acknowledgement was lost.
        for key in data['deal_keys']:call(provider.archive,'deals',key)
        call(provider.archive,'contacts',data['contact_key'])
        result['cleanup']='removed'
    if data['payload'].get('uninstall'):
        with Session(engine) as db,db.begin():
            ws=db.get(Workspace,job['workspace_id']);connection=db.get(Connection,(ws.id,data['connection_id']))
            crm.account_lock(db)
            # Hold the install registry lock through account-wide removal so a new
            # callback cannot bind before the verified registry removal commits.
            try:
                if crm.other_uses(db,ws,connection,clock()):raise CRMFailure('CRM_SHARED_INSTALL')
                call(provider.uninstall)
            except CRMFailure as error:error.progress=result;raise
            install=db.get(Installation,(provider.app_id,connection.account_id))
            if install:install.state='uninstalled';install.checked_at=clock()
        result['uninstall']='removed'
    return result


@storage_retry
def finish_job(engine,provider,job,clock,*,result=None,error=None):
    with Session(engine) as db,db.begin():
        workspace=repo_first(db, Workspace, filters={'id': job['workspace_id']}, lock=True)
        if not workspace:return False
        row=db.get(Outbox,(job['workspace_id'],job['event_id']))
        if not row:return False
        connection=repo_first(db, Connection, filters={'workspace_id': workspace.id, 'id': row.connection_id}, lock=True)
        row=repo_first(db, Outbox, filters={'workspace_id': workspace.id, 'id': row.id}, lock=True)
        if row.state!='processing' or row.lease_token!=job['lease_token'] or row.lease_until<=clock():return False
        current=valid(db,row,clock());row.lease_token=None;row.lease_until=None
        if not current or (error and error.code=='CRM_RETIRED'):
            row.state='retired';row.code='CRM_RETIRED';return False
        if error:
            if getattr(error,'progress',None):row.payload={**row.payload,'result':error.progress}
            row.code=error.code
            if error.retryable and row.attempts<5 and clock()<workspace.created_at+timedelta(hours=3):
                row.state='reconciling' if error.ambiguous else 'retrying'
                row.due_at=clock()+timedelta(seconds=max(error.retry_after,min(300,5*2**(row.attempts-1))))
            else:
                row.state='needs_attention'
                if row.kind=='crm_cleanup':connection.state='needs_attention'
                if error.code=='CRM_AUTH_REQUIRED':connection.encrypted_tokens=None;connection.state='needs_attention';connection.export_consent=False
            return True
        row.code=None;row.state='synced' if row.kind=='crm_upsert' else 'completed'
        if row.kind=='crm_upsert':
            mapping=db.get(ExternalMapping,(workspace.id,connection.id,row.enquiry_id))
            if not mapping:
                mapping=ExternalMapping(workspace_id=workspace.id,connection_id=connection.id,enquiry_id=row.enquiry_id,account_id=connection.account_id,
                                        revision=row.revision,state='synced',verified=True);db.add(mapping)
            mapping.contact_id=result['contact_id'];mapping.deal_id=result['deal_id'];mapping.revision=row.revision;mapping.state='synced';mapping.verified=True
        else:
            row.payload={**row.payload,'result':result};connection.state='finished';connection.encrypted_tokens=None
            if result['cleanup']=='removed':
                change(db, ExternalMapping, {'verified': False, 'state': 'removed'}, filters={'workspace_id': workspace.id, 'connection_id': connection.id})
        return True


def deliver(engine,settings,provider,job,clock):
    deadline=time.monotonic()+90
    provider=crm.scoped(provider,job['workspace_id'],seconds=90)
    try:
        data=prepare(engine,settings,provider,job,clock)
        result=perform(engine,provider,job,data,clock,deadline)
    except CRMFailure as error:return finish_job(engine,provider,job,clock,error=error)
    except Exception:  # noqa: BLE001 - the durable boundary records a bounded retry without exposing provider payloads.
        return finish_job(engine,provider,job,clock,error=CRMFailure('CRM_PROCESSING_FAILED',True))
    return finish_job(engine,provider,job,clock,result=result)


def retire_workspace(db,workspace,now):
    if not workspace.active:return
    service.workspace_lock(db,workspace)
    workspace.active=False;workspace.generation+=1;workspace.revision+=1
    workspace.messages=[];workspace.draft={};workspace.scenario={}
    knowledge.purge_private(db,workspace)
    for connection in repo_rows(db, Connection, filters={'workspace_id': workspace.id}, lock=True):
        crm.connection_lock(db,connection)
        if connection.state in {'finished','retired'}:continue
        existing=repo_first(db, Outbox, filters={'workspace_id': workspace.id, 'connection_id': connection.id, 'kind': 'crm_cleanup'}, order=lambda candidate: (repo_desc(candidate.revision),), limit=1)
        needs_cleanup=bool(connection.export_consent or repo_value(db, Outbox, 'id', filters={'workspace_id': workspace.id, 'connection_id': connection.id, 'kind': 'crm_upsert'}, limit=1))
        choices=existing.payload if existing else {'cleanup':needs_cleanup,'uninstall':False}
        connection.generation+=1;connection.export_consent=False
        change(db, Outbox, {'state': 'retired'}, filters={'workspace_id': workspace.id, 'connection_id': connection.id}, predicate=lambda row: row.state in ['pending', 'retrying', 'reconciling'])
        if connection.encrypted_tokens and (choices.get('cleanup') or choices.get('uninstall')):
            connection.state='finishing'
            db.add(Outbox(workspace_id=workspace.id,connection_id=connection.id,account_id=connection.account_id,
                          connection_generation=connection.generation,workspace_generation=workspace.generation,revision=workspace.revision,
                          kind='crm_cleanup',state='pending',attempts=0,due_at=now,payload={k:bool(choices.get(k)) for k in ('cleanup','uninstall')}))
        else:connection.state='retired';connection.encrypted_tokens=None
    workspace.crm_mode='skipped'


@storage_retry
def maintenance(engine,now):
    retired=0
    with Session(engine) as db,db.begin():
        for workspace in repo_rows(db,Workspace,predicate=lambda row:row.active and row.expires_at<=now,limit=10,lock=True):
            retire_workspace(db,workspace,now);retired+=1
        for workspace in repo_rows(db,Workspace,filters={'active':False},limit=256,lock=True):
            knowledge.purge_private(db,workspace)
            workspace.messages=[];workspace.draft={};workspace.scenario={}
            outstanding=repo_first(db,Outbox,filters={'workspace_id':workspace.id},predicate=lambda row:
                row.state in {'pending','retrying','reconciling','processing','needs_attention'})
            if outstanding:continue
            if workspace.purged_at is None:
                for model in (Idempotency,Activity,Reservation,Enquiry,Staff):remove(db,model,filters={'workspace_id':workspace.id})
                remove(db,OAuthState,filters={'workspace_id':workspace.id},predicate=lambda row:row.outcome!='unknown')
                workspace.purged_at=now
            unknown=repo_first(db,OAuthState,filters={'workspace_id':workspace.id,'outcome':'unknown'})
            if workspace.expires_at<now-timedelta(hours=24) and not unknown:db.delete(workspace)
        recover_exhausted(db,now)
        expire_delivery_window(db,now)
    return retired


def tick(engine,settings,provider,clock,limit=3):
    maintenance(engine,clock());processed=0
    for _ in range(min(3,max(0,limit))):
        job=claim(engine,clock())
        if not job:break
        deliver(engine,settings,provider,job,clock);processed+=1
    return processed
