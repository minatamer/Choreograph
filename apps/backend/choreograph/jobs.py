"""Durable bounded delivery; local polling and authenticated tasks share this code."""
import time
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import and_, delete, func, or_, select, tuple_, update
from sqlalchemy.orm import Session

from . import crm, knowledge
from .hubspot import KEY_PROPERTY, CRMFailure
from .models import (
    Activity,
    Connection,
    DocumentVersion,
    Enquiry,
    ExternalMapping,
    Idempotency,
    Installation,
    Manifest,
    OAuthState,
    Outbox,
    Reservation,
    Staff,
    Workspace,
)

LEASE=timedelta(seconds=180)


def recover_exhausted(db,now):
    keys=select(Outbox.workspace_id,Outbox.id).where(Outbox.state=='processing',Outbox.lease_until<=now,
        Outbox.attempts>=5).limit(20).with_for_update(skip_locked=True)
    db.execute(update(Outbox).where(tuple_(Outbox.workspace_id,Outbox.id).in_(keys)).values(
        state='needs_attention',code='CRM_ATTEMPTS_EXHAUSTED',lease_until=None,lease_token=None))


def window_open(db,row,now):
    workspace=db.get(Workspace,row.workspace_id)
    return bool(workspace and now<workspace.created_at+timedelta(hours=3))


def expire_delivery_window(db,now):
    keys=select(Outbox.workspace_id,Outbox.id).join(Workspace,Workspace.id==Outbox.workspace_id).where(
        Workspace.created_at<=now-timedelta(hours=3),Outbox.state.in_(['pending','retrying','reconciling','processing']),
        or_(Outbox.state!='processing',Outbox.lease_until<=now)).limit(20).with_for_update(of=Outbox,skip_locked=True)
    db.execute(update(Outbox).where(tuple_(Outbox.workspace_id,Outbox.id).in_(keys)).values(
        state='needs_attention',code='CRM_WINDOW_EXPIRED',lease_until=None,lease_token=None))


def claim(engine,now,*,event_id=None,workspace_id=None):
    with Session(engine) as db,db.begin():
        from sqlalchemy import text
        db.execute(text('SELECT pg_advisory_xact_lock(45864,1)'))
        if db.scalar(select(func.count()).select_from(Outbox).where(Outbox.state=='processing',Outbox.lease_until>now))>=4:return None
        eligible=or_(and_(Outbox.state.in_(['pending','retrying','reconciling']),Outbox.due_at<=now),
                     and_(Outbox.state=='processing',Outbox.lease_until<=now))
        query=select(Outbox.workspace_id,Outbox.id,Outbox.connection_id).where(eligible,Outbox.attempts<5).order_by(Outbox.due_at,Outbox.id).limit(20)
        if event_id is not None:query=query.where(Outbox.id==event_id,Outbox.workspace_id==workspace_id)
        for wid,eid,cid in db.execute(query):
            connection=db.scalar(select(Connection).where(Connection.workspace_id==wid,Connection.id==cid).with_for_update(skip_locked=True))
            if not connection:continue
            if db.scalar(select(Outbox.id).where(Outbox.workspace_id==wid,Outbox.connection_id==cid,Outbox.id!=eid,
                Outbox.state=='processing',Outbox.lease_until>now).limit(1)):continue
            row=db.scalar(select(Outbox).where(Outbox.workspace_id==wid,Outbox.id==eid,eligible,Outbox.attempts<5).with_for_update(skip_locked=True))
            if not row:continue
            row.state='processing';row.attempts+=1;row.lease_until=now+LEASE;row.lease_token=uuid4();db.flush()
            return {'workspace_id':wid,'event_id':eid,'lease_token':row.lease_token}
        # Exhausted crashed work cannot remain processing forever.
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
        connection=db.scalar(select(Connection).where(Connection.workspace_id==row.workspace_id,Connection.id==row.connection_id).with_for_update())
        if not window_open(db,row,clock()):raise CRMFailure('CRM_WINDOW_EXPIRED')
        tokens=crm.tokens_for(db,connection,settings.token_key,provider,clock())
        workspace=db.get(Workspace,row.workspace_id)
        data={'tokens':tokens,'kind':row.kind,'account_id':connection.account_id,'connection_id':connection.id,'payload':dict(row.payload or {})}
        data['contact_key']=crm.record_key(settings.bridge_secret,workspace.id,connection.id,'contacts')
        if row.kind=='crm_upsert':
            enquiry=db.get(Enquiry,(workspace.id,row.enquiry_id));booking=db.scalar(select(Reservation).where(Reservation.workspace_id==workspace.id,Reservation.enquiry_id==enquiry.id))
            if not booking:raise CRMFailure('CRM_RETIRED')
            data['deal_key']=crm.record_key(settings.bridge_secret,workspace.id,connection.id,'deals',enquiry.id)
            contact=crm.contact_details(settings.bridge_secret,workspace,connection)
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
            data['deal_keys']=[crm.record_key(settings.bridge_secret,workspace.id,connection.id,'deals',eid) for eid in db.scalars(select(Enquiry.id).where(Enquiry.workspace_id==workspace.id))]
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


def finish_job(engine,provider,job,clock,*,result=None,error=None):
    with Session(engine) as db,db.begin():
        workspace=db.scalar(select(Workspace).where(Workspace.id==job['workspace_id']).with_for_update())
        if not workspace:return False
        row=db.get(Outbox,(job['workspace_id'],job['event_id']))
        if not row:return False
        connection=db.scalar(select(Connection).where(Connection.workspace_id==workspace.id,Connection.id==row.connection_id).with_for_update())
        row=db.scalar(select(Outbox).where(Outbox.workspace_id==workspace.id,Outbox.id==row.id).with_for_update())
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
                db.execute(update(ExternalMapping).where(ExternalMapping.workspace_id==workspace.id,ExternalMapping.connection_id==connection.id).values(verified=False,state='removed'))
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
    workspace.active=False;workspace.generation+=1;workspace.revision+=1
    workspace.messages=[];workspace.draft={};workspace.scenario={}
    knowledge.purge_private(db,workspace)
    for connection in db.scalars(select(Connection).where(Connection.workspace_id==workspace.id).with_for_update()):
        if connection.state in {'finished','retired'}:continue
        existing=db.scalar(select(Outbox).where(Outbox.workspace_id==workspace.id,Outbox.connection_id==connection.id,Outbox.kind=='crm_cleanup').order_by(Outbox.revision.desc()).limit(1))
        needs_cleanup=bool(connection.export_consent or db.scalar(select(Outbox.id).where(Outbox.workspace_id==workspace.id,Outbox.connection_id==connection.id,Outbox.kind=='crm_upsert').limit(1)))
        choices=existing.payload if existing else {'cleanup':needs_cleanup,'uninstall':False}
        connection.generation+=1;connection.export_consent=False
        db.execute(update(Outbox).where(Outbox.workspace_id==workspace.id,Outbox.connection_id==connection.id,Outbox.state.in_(['pending','retrying','reconciling'])).values(state='retired'))
        if connection.encrypted_tokens and (choices.get('cleanup') or choices.get('uninstall')):
            connection.state='finishing'
            db.add(Outbox(workspace_id=workspace.id,connection_id=connection.id,account_id=connection.account_id,
                          connection_generation=connection.generation,workspace_generation=workspace.generation,revision=workspace.revision,
                          kind='crm_cleanup',state='pending',attempts=0,due_at=now,payload={k:bool(choices.get(k)) for k in ('cleanup','uninstall')}))
        else:connection.state='retired';connection.encrypted_tokens=None
    workspace.crm_mode='skipped'


def maintenance(engine,now):
    retired=0
    with Session(engine) as db,db.begin():
        for workspace in db.scalars(select(Workspace).where(Workspace.active.is_(True),Workspace.expires_at<=now).limit(10).with_for_update(skip_locked=True)):
            retire_workspace(db,workspace,now);retired+=1
        # Retired private source bytes never wait for remote cleanup.
        private=(select(DocumentVersion.id).where(DocumentVersion.owner_id==Workspace.id).exists())
        manifests=select(Manifest.workspace_id).where(Manifest.workspace_id==Workspace.id).exists()
        for workspace in db.scalars(select(Workspace).where(Workspace.active.is_(False),or_(private,manifests,Workspace.messages!=[],Workspace.draft!={})).limit(20).with_for_update(skip_locked=True)):
            knowledge.purge_private(db,workspace)
            workspace.messages=[];workspace.draft={};workspace.scenario={}
        outstanding=select(Outbox.id).where(Outbox.workspace_id==Workspace.id,Outbox.state.in_(['pending','retrying','reconciling','processing','needs_attention'])).exists()
        for workspace in db.scalars(select(Workspace).where(Workspace.active.is_(False),Workspace.purged_at.is_(None),~outstanding).limit(20).with_for_update(skip_locked=True)):
            for model in (Idempotency,Activity,Reservation,Enquiry,Staff):db.execute(delete(model).where(model.workspace_id==workspace.id))
            db.execute(delete(OAuthState).where(OAuthState.workspace_id==workspace.id,OAuthState.outcome!='unknown'))
            workspace.purged_at=now
        unknown=select(OAuthState.state_hash).where(OAuthState.workspace_id==Workspace.id,OAuthState.outcome=='unknown').exists()
        for workspace in db.scalars(select(Workspace).where(Workspace.active.is_(False),Workspace.purged_at.is_not(None),
            Workspace.expires_at<now-timedelta(hours=24),~unknown,~outstanding).limit(20).with_for_update(skip_locked=True)):db.delete(workspace)
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
