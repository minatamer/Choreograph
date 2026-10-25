"""Guest-bound connections, independent account installs and protected tokens."""
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timedelta
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken

from . import service
from .errors import DomainError
from .hubspot import CRMFailure
from .models import (
    Connection,
    Enquiry,
    ExternalMapping,
    Installation,
    OAuthState,
    Outbox,
    Reservation,
    Workspace,
)
from .persistence import Session, advisory, change, is_object, repo_desc, repo_first, repo_rows, repo_value


def latest_connection(db,workspace):
    return repo_first(db,Connection,filters={'workspace_id':workspace.id},
        order=lambda row:({'ready':0,'finishing':1}.get(row.state,2),repo_desc(row.created_at),row.id))


def installed_count(db,app_id):
    return len(repo_rows(db, Installation, filters={'app_id': app_id}, predicate=lambda candidate: candidate.state != 'uninstalled'))


def available(db,provider,now):
    pending=len(repo_rows(db, OAuthState, filters={'app_id': provider.app_id, 'provider': provider.provider}, predicate=lambda candidate: candidate.used is False and candidate.expires_at > now or candidate.outcome == 'unknown'))
    return installed_count(db,provider.app_id)+pending<getattr(provider,'capacity',25)


def matches(connection,provider):
    return connection.provider==provider.provider and connection.app_id==provider.app_id


def require_provider(connection,provider):
    if not matches(connection,provider):raise CRMFailure('CRM_PROVIDER_CHANGED')


def scoped(provider,workspace_id,*,seconds=45):
    return provider.with_workspace(workspace_id,deadline=time.monotonic()+seconds) if hasattr(provider,'with_workspace') else provider


def account_lock(db):
    # Account registry serialization, unrelated to TCP ports.
    if is_object(db):db.hold_lease('crm-account-v1')
    else:advisory(db,45863,1)


def begin(db,workspace,revision,provider,now):
    service.require_revision(workspace,revision);account_lock(db)
    current=latest_connection(db,workspace)
    if current and current.state in {'ready','finishing','setup'}:
        return {'request_id':None,'crm_notice':'This workspace already has a connection.'}
    change(db, OAuthState, {'used': True, 'outcome': 'superseded'}, filters={'workspace_id': workspace.id, 'outcome': 'pending'})
    if not available(db,provider,now):
        return {'request_id':None,'crm_notice':'HubSpot connection capacity is unavailable. Continue without CRM.'}
    state=secrets.token_urlsafe(36)
    db.add(OAuthState(state_hash=hashlib.sha256(state.encode()).hexdigest(),workspace_id=workspace.id,generation=workspace.generation,
                      expires_at=now+timedelta(minutes=10),used=False,provider=provider.provider,app_id=provider.app_id))
    workspace.crm_mode='connecting';workspace.revision+=1
    return {'request_id':None,'oauth':{'state':state,'authorize_url':provider.authorization_url(state),'simulated':provider.provider=='fake'}}


def encrypt(tokens,key):return Fernet(key.encode()).encrypt(json.dumps(tokens).encode())


def connection_lock(db,connection):
    if is_object(db):db.hold_lease('crm-token-'+str(connection.id))
    else:
        db.get(Connection,(connection.workspace_id,connection.id),with_for_update=True,populate_existing=True)


def tokens_for(db,connection,key,provider,now):
    # Caller locks the connection across refresh, preventing rotating-token races.
    require_provider(connection,provider)
    connection_lock(db,connection)
    try:tokens=json.loads(Fernet(key.encode()).decrypt(connection.encrypted_tokens))
    except (InvalidToken,TypeError,ValueError):raise CRMFailure('CRM_AUTH_REQUIRED') from None
    if tokens.get('account_id')!=connection.account_id:raise CRMFailure('CRM_ACCOUNT_CHANGED')
    if datetime.fromisoformat(tokens['expires_at'])<=now+timedelta(seconds=60):
        tokens=provider.refresh(tokens);connection.encrypted_tokens=encrypt(tokens,key);db.flush()
    return tokens


def claim_oauth_attempt(db,state,now):
    # Persist uncertainty BEFORE HTTP. A crashed exchange cannot become an
    # expired, reusable pending state or silently release installation capacity.
    engine=db.engine if is_object(db) else db.get_bind()
    with Session(engine) as claim,claim.begin():
        current=claim.get(OAuthState,state.state_hash,with_for_update=True)
        if (current is None or current.used or current.expires_at<=now or
                current.workspace_id!=state.workspace_id or current.generation!=state.generation or
                current.provider!=state.provider or current.app_id!=state.app_id):
            raise DomainError('OAUTH_STATE','The connection attempt expired. Start it again.',409)
        current.used=True;current.outcome='unknown'
    if is_object(db):db.adopt_committed(OAuthState,state.state_hash,{'used':True,'outcome':'unknown'})
    else:state.used=True;state.outcome='unknown'


def callback(db,workspace,body,provider,key,now):
    state=db.get(OAuthState,hashlib.sha256(body.state.encode()).hexdigest())
    if not state or state.workspace_id!=workspace.id or state.generation!=workspace.generation or state.used or state.expires_at<=now:
        raise DomainError('OAUTH_STATE','The connection attempt expired. Start it again.',409)
    if state.provider!=provider.provider or state.app_id!=provider.app_id:
        raise DomainError('CRM_PROVIDER_CHANGED','The connection configuration changed. Start again.',409)
    if body.denied:
        state.used=True;workspace.revision+=1
        state.outcome='denied'
        workspace.crm_mode='skipped'
        return {'request_id':None,'crm_notice':'Connection cancelled. No CRM records were sent.'}
    claim_oauth_attempt(db,state,now)
    workspace.revision+=1
    account_lock(db)
    provider=scoped(provider,workspace.id)
    account=None;install=None
    options=[]
    try:
        tokens=provider.exchange(body.code,workspace.id)
        account=tokens['account_id']
        install=db.get(Installation,(provider.app_id,account))
        if (not install or install.state=='uninstalled') and installed_count(db,provider.app_id)>=getattr(provider,'capacity',25):
            # OAuth may already have installed remotely. Keep this account conservative.
            if not install:db.add(Installation(app_id=provider.app_id,account_id=account,state='unknown',checked_at=now))
            else:install.state='unknown';install.checked_at=now
            state.outcome='installed';workspace.crm_mode='skipped'
            return {'request_id':None,'crm_notice':'Connection capacity is unavailable. The account installation needs operator review; no records were exported.'}
        if provider.provider=='hubspot':options=provider.destinations(tokens)
    except CRMFailure as error:
        # A failed exchange/introspection may follow a real installation.
        if provider.provider=='fake' and error.code=='CRM_DENIED':
            state.outcome='denied'
        elif account:
            # Identified accounts reserve capacity in the registry, not a second
            # unidentified OAuth slot. A prior uninstall cannot release this one.
            state.outcome='installed'
            if not install:db.add(Installation(app_id=provider.app_id,account_id=account,state='unknown',checked_at=now))
            else:install.state='unknown';install.checked_at=now
        else:state.outcome='unknown'
        workspace.crm_mode='skipped'
        return {'request_id':None,'crm_notice':'The connection could not be verified. Continue without CRM or try again.'}
    if install:install.state='installed';install.checked_at=now
    else:db.add(Installation(app_id=provider.app_id,account_id=account,state='installed',checked_at=now))
    state.outcome='installed'
    connection=Connection(workspace_id=workspace.id,id=uuid4(),account_id=account,generation=1,
                          state='setup' if provider.provider=='hubspot' else 'ready',
                          provider=provider.provider,app_id=provider.app_id,destination_options=options,
                          encrypted_tokens=encrypt(tokens,key),export_consent=False,created_at=now)
    db.add(connection);workspace.crm_mode='connected'
    return {'request_id':None,'crm_notice':'Simulated HubSpot connected. No records have been shared.' if provider.provider=='fake' else 'HubSpot connected. Choose a destination before sharing.'}


def setup_destination(db,workspace,body,provider,key,now):
    service.require_revision(workspace,body.revision)
    connection=latest_connection(db,workspace)
    if (not connection or connection.id!=body.connection_id or connection.state!='setup' or
            workspace.crm_mode!='connected' or provider.provider!='hubspot'):
        raise DomainError('CRM_CONNECTION_CHANGED','Review the current connection before setup.',409)
    try:
        provider=scoped(provider,workspace.id)
        tokens=tokens_for(db,connection,key,provider,now)
        options=provider.destinations(tokens)
        pipeline=next((row for row in options if row['id']==body.pipeline_id),None)
        if not pipeline or not any(row['id']==body.stage_id for row in pipeline['stages']):
            raise CRMFailure('CRM_DESTINATION_CHANGED')
        provider.preflight(tokens,allow_schema=body.allow_schema)
    except CRMFailure as error:
        workspace.revision+=1
        if error.code=='CRM_CURRENCY_REQUIRED':
            return {'request_id':None,'crm_notice':'Juniper’s sample quotes use USD. Choose a HubSpot account whose company currency is USD, or continue without HubSpot. No records were shared.'}
        if error.code=='CRM_CURRENCY_UNAVAILABLE':
            return {'request_id':None,'crm_notice':'HubSpot’s account currency could not be verified. Try again shortly. No records were shared.'}
        return {'request_id':None,'crm_notice':('The selected destination is unavailable. Review the account setup or continue without CRM.'
            if error.code not in {'CRM_SETUP_REQUIRED','CRM_UNIQUENESS_REQUIRED'} else
            'The account needs compatible demo ID fields. Authorize setup or continue without CRM.')}
    connection.destination={'pipeline_id':body.pipeline_id,'stage_id':body.stage_id,'label':pipeline['label']}
    connection.destination_options=[];connection.state='ready';connection.generation+=1
    connection.export_consent=False;workspace.revision+=1
    return {'request_id':None,'crm_notice':'Destination verified. Review the fictional data before allowing sharing.'}


def record_key(secret,workspace_id,connection_id,kind,enquiry_id=''):
    value=f'{workspace_id}:{connection_id}:{kind}:{enquiry_id}'
    return hmac.new(secret.encode(),value.encode(),hashlib.sha256).hexdigest()


def contact_details():
    # The unique demo key owns identity. HubSpot rejects .invalid email domains;
    # omit email rather than substituting a potentially deliverable address.
    return {'firstname':'Demo','lastname':'Guest'}


def other_uses(db,workspace,connection,now):
    active={row.id for row in repo_rows(db,Workspace,predicate=lambda row:row.active and row.expires_at>now)}
    return bool(repo_first(db,Connection,filters={'account_id':connection.account_id,'provider':connection.provider,
        'app_id':connection.app_id},predicate=lambda row:row.workspace_id!=workspace.id and row.workspace_id in active and
        row.state in {'ready','finishing','setup'}))


def public_view(db,workspace,secret,now,*,connection,events,provider=None):
    if not connection:return None
    cleanup=max((row for row in events if row.workspace_id==workspace.id and row.connection_id==connection.id
                 and row.kind=='crm_cleanup'),key=lambda row:(row.revision,row.id),default=None)
    outcomes=cleanup.payload.get('result',{}) if cleanup else {}
    return {'id':connection.id,'label':'Demo HubSpot account' if connection.provider=='fake' else f'HubSpot account {connection.account_id}',
            'provider':connection.provider,'state':connection.state if provider is None or matches(connection,provider) else 'needs_attention',
            'consented':connection.export_consent if provider is None or matches(connection,provider) else False,
            'destinations':connection.destination_options,'destination_label':connection.destination.get('label'),
            'can_uninstall':not other_uses(db,workspace,connection,now),'contact_name':'Demo Guest','contact_email':'',
            'cleanup_state':outcomes.get('cleanup',cleanup.state if cleanup and cleanup.payload.get('cleanup') else 'not_requested'),
            'uninstall_state':outcomes.get('uninstall',cleanup.state if cleanup and cleanup.payload.get('uninstall') else 'not_requested')}


def consent(db,workspace,body,provider=None,*,now):
    service.require_revision(workspace,body.revision);connection=latest_connection(db,workspace)
    if connection:connection_lock(db,connection)
    if not connection or connection.id!=body.connection_id or connection.state!='ready' or workspace.crm_mode!='connected':
        raise DomainError('CRM_CONNECTION_CHANGED','Review the current connection before sharing.',409)
    if provider is not None and not matches(connection,provider):
        raise DomainError('CRM_PROVIDER_CHANGED','The connection configuration changed. Disconnect before continuing.',409)
    if connection.provider=='hubspot' and not connection.destination:
        raise DomainError('CRM_DESTINATION_REQUIRED','Choose a CRM destination before sharing.',409)
    if not connection.export_consent:
        connection.export_consent=True
        # Consent covers already reviewed records too. Destination and record
        # revision remain explicit; pending requests cannot become exports.
        booked={row.enquiry_id for row in repo_rows(db,Reservation,filters={'workspace_id':workspace.id})}
        reviewed=repo_rows(db,Enquiry,filters={'workspace_id':workspace.id},
            predicate=lambda row:row.status in {'confirmed','completed','cancelled'} and row.id in booked)
        for enquiry in reviewed:
            existing=repo_value(db, Outbox, 'id', filters={'workspace_id': workspace.id, 'connection_id': connection.id, 'enquiry_id': enquiry.id, 'revision': enquiry.revision, 'kind': 'crm_upsert'}, limit=1)
            if existing is None:service.queue_crm(db,workspace,enquiry,now)
    workspace.revision+=1
    return {'request_id':None,'crm_notice':'Fictional contact and reviewed booking details can now be shared with this account.'}


def detach(db,workspace,revision):
    service.require_revision(workspace,revision);connection=latest_connection(db,workspace)
    if connection:connection_lock(db,connection)
    change(db, OAuthState, {'used': True, 'outcome': 'skipped'}, filters={'workspace_id': workspace.id, 'outcome': 'pending'})
    if connection and connection.state in {'ready','setup'}:
        connection.state='detached';connection.generation+=1;connection.export_consent=False
        change(db, Outbox, {'state': 'retired'}, filters={'workspace_id': workspace.id, 'connection_id': connection.id}, predicate=lambda row: row.state in ['pending', 'retrying', 'reconciling'])
    workspace.crm_mode='skipped';workspace.revision+=1
    return {'request_id':None,'crm_notice':'Disconnected from this workspace. Existing CRM records and the account installation have not been removed.'}


def finish(db,workspace,body,now):
    service.require_revision(workspace,body.revision);connection=latest_connection(db,workspace)
    if connection:connection_lock(db,connection)
    if not connection or connection.id!=body.connection_id or connection.state not in {'ready','detached','setup'}:
        raise DomainError('CRM_CONNECTION_CHANGED','Review the current connection before finishing.',409)
    if body.uninstall and other_uses(db,workspace,connection,now):
        raise DomainError('CRM_SHARED_INSTALL','Another active demo uses this account. Disconnect this workspace without uninstalling.',409)
    connection.generation+=1;connection.state='finishing';connection.export_consent=False;workspace.crm_mode='skipped';workspace.revision+=1
    change(db, Outbox, {'state': 'retired'}, filters={'workspace_id': workspace.id, 'connection_id': connection.id}, predicate=lambda row: row.state in ['pending', 'retrying', 'reconciling'])
    db.add(Outbox(workspace_id=workspace.id,enquiry_id=None,connection_id=connection.id,account_id=connection.account_id,
                  connection_generation=connection.generation,workspace_generation=workspace.generation,revision=workspace.revision,
                  kind='crm_cleanup',state='pending',attempts=0,due_at=now,payload={'cleanup':body.cleanup,'uninstall':body.uninstall}))
    return {'request_id':None,'crm_notice':'Finishing is pending. Record cleanup and uninstall will be reported separately.'}


def apply_receipts(db,workspace,state,*,connection,events,provider=None):
    if connection and provider is not None and not matches(connection,provider):connection=None
    workspace_events=[row for row in events if row.workspace_id==workspace.id and row.kind=='crm_upsert']
    historical={row.enquiry_id for row in workspace_events}
    current={(row.enquiry_id,row.revision):row for row in workspace_events if connection
             and row.connection_id==connection.id and row.connection_generation==connection.generation
             and row.workspace_generation==workspace.generation}
    mappings={}
    if connection and connection.state=='ready' and workspace.crm_mode=='connected' and state.requests:
        mappings={row.enquiry_id:row for row in repo_rows(db, ExternalMapping, filters={'workspace_id': workspace.id, 'connection_id': connection.id}, predicate=lambda candidate: candidate.enquiry_id in [request.id for request in state.requests])}
    for request in state.requests:
        request.crm_state='not_connected';request.crm_receipt=None;request.crm_links={}
        event=current.get((request.id,request.revision))
        if connection and connection.state=='needs_attention' and workspace.crm_mode=='connected':
            request.crm_state='needs_attention' if event else 'not_shared'
            continue
        if not connection or connection.state!='ready' or workspace.crm_mode!='connected':
            if request.id in historical:request.crm_state='disconnected'
            continue
        request.crm_state='not_shared'
        if event:request.crm_state=event.state
        mapping=mappings.get(request.id)
        if mapping and mapping.verified and mapping.account_id==connection.account_id and mapping.revision==request.revision:
            request.crm_state='simulated_synced' if connection.provider=='fake' else 'synced'
            request.crm_receipt={'provider':connection.provider,'contact_id':mapping.contact_id or '',
                                 'deal_id':mapping.deal_id or '', 'revision':str(mapping.revision)}
            if connection.provider=='hubspot' and connection.account_id.isdigit():
                for kind,object_type,object_id in [('contact','0-1',mapping.contact_id),('booking','0-3',mapping.deal_id)]:
                    if object_id and object_id.isdigit():request.crm_links[kind]=f'https://app.hubspot.com/contacts/{connection.account_id}/record/{object_type}/{object_id}'
