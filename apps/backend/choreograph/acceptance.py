"""Finite operator acceptance. Dry run is default; a CLI flag is not owner approval."""
import argparse
import base64
import hashlib
import json
import time
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import ai_admission, assistant, crm, jobs, knowledge
from .contracts import CRMFinish
from .errors import DomainError
from .models import AcceptanceRun, AIAttempt, Enquiry, ExternalMapping, Manifest, Outbox, Workspace
from .readiness import ROOT, database_status
from .sessions import COOKIE, create_workspace, csrf_token

AI_LIMITS={'interpret':6,'evidence':24,'query_embed':24,'ingest_embed':24,
    'document_vectors':64,'query_vectors':24,'response_input_tokens':300_000,
    'document_input_tokens':32_768,'query_input_tokens':4096,'output_tokens':42_000,'seconds':1800}


def dry_plan(lane,step):
    return {'mode':'dry-run','lane':lane,'step':step,'provider_calls':0,'account_changes':0,'cloud_changes':0,
        'limits':AI_LIMITS if lane=='ai' else {'seconds':1800,'http_requests':60,'owned_contacts':1,'owned_deals':1},
        'requires':['separate trusted owner authorization','reviewed current source/model/pricing or account/project',
            'explicit finite grant and cleanup choices','unique run UUID'],
        'ai_cases':18 if lane=='ai' else 0,'additional_cases':6 if lane=='ai' else 0}


def reserve_run(engine,run_id,kind,fingerprint,now):
    run_id=UUID(str(run_id))
    try:
        with Session(engine) as db,db.begin():
            db.add(AcceptanceRun(id=run_id,kind=kind,config_hash=fingerprint,state='running',created_at=now,
                                 counts={},workspace_ids=[]))
    except IntegrityError:raise DomainError('ACCEPTANCE_RUN_USED','This acceptance run cannot be repeated.',409) from None
    return run_id


def finish_run(engine,run_id,*,state,code=None,clock):
    with Session(engine) as db,db.begin():
        row=db.get(AcceptanceRun,run_id,with_for_update=True)
        if row is None:return
        row.state=state;row.finished_at=clock()
        if code:row.counts={**row.counts,'failure_code':code}


def marker(engine,run_id,stage,receipt=None):
    with Session(engine) as db,db.begin():
        row=db.get(AcceptanceRun,run_id,with_for_update=True);counts={**row.counts,'stage':stage}
        if receipt is not None:
            previous=counts.get('case_receipts',[])
            if len(previous)>=24:raise DomainError('ACCEPTANCE_LIMIT','Acceptance case limit reached.',429)
            counts['case_receipts']=[*previous,receipt]
        row.counts=counts


class RunAdmission:
    """A conservative run ceiling commits before the ordinary provider grant."""
    def __init__(self,engine,run_id,inner,deadline,max_cost):
        self.engine,self.run_id,self.inner,self.deadline,self.max_cost=engine,run_id,inner,deadline,max_cost
        self.grant=inner.grant

    def run(self,phase,batch,*,input_tokens,output_tokens=0,vectors=0,invoke):
        if time.monotonic()>=self.deadline:raise DomainError('ACCEPTANCE_TIMEOUT','Acceptance window ended.',429)
        embedding=phase in {'query_embed','ingest_embed'}
        category='query' if phase=='query_embed' else 'document' if embedding else 'response'
        cost=(input_tokens*(self.grant.embedding_input_rate if embedding else self.grant.response_input_rate)+
            output_tokens*(0 if embedding else self.grant.response_output_rate)+999_999)//1_000_000
        updates={phase:1,category+'_input_tokens':input_tokens,'output_tokens':output_tokens,'cost_micros':cost}
        if embedding:updates[category+'_vectors']=vectors
        with Session(self.engine) as db,db.begin():
            row=db.get(AcceptanceRun,self.run_id,with_for_update=True)
            if row is None or row.state!='running':raise DomainError('ACCEPTANCE_RUN_USED','Acceptance is no longer active.',409)
            counts=dict(row.counts)
            for key,amount in updates.items():
                counts[key]=counts.get(key,0)+amount
                if counts[key]>(self.max_cost if key=='cost_micros' else AI_LIMITS[key]):
                    raise DomainError('ACCEPTANCE_LIMIT','Acceptance reached its finite ceiling.',429)
            row.counts=counts
        started=time.monotonic()
        try:return self.inner.run(phase,batch,input_tokens=input_tokens,output_tokens=output_tokens,vectors=vectors,invoke=invoke)
        finally:
            with Session(self.engine) as db,db.begin():
                row=db.get(AcceptanceRun,self.run_id,with_for_update=True)
                key=phase+'_elapsed_ms';row.counts={**row.counts,key:row.counts.get(key,0)+int((time.monotonic()-started)*1000)}


class RunRuntime:
    def __init__(self,base,engine,run_id,deadline,max_cost):
        self.base,self.engine,self.run_id,self.deadline,self.max_cost=base,engine,run_id,deadline,max_cost
        self.spec,self.tokenizer,self.assistant=base.spec,base.tokenizer,base.assistant

    def for_scope(self,scope,*,clock=None,deadline=None):
        scoped=self.base.for_scope(scope,clock=clock,deadline=min(deadline or self.deadline,self.deadline))
        if scoped.admission is None:raise DomainError('ACCEPTANCE_ADMISSION_REQUIRED','An explicit acceptance allowance is required.',503)
        meter=RunAdmission(self.engine,self.run_id,scoped.admission,self.deadline,self.max_cost)
        return replace(scoped,assistant=scoped.assistant.with_admission(meter),embedder=scoped.embedder.with_admission(meter),admission=meter)


def _fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,default=str).encode()).hexdigest()


def _rag(engine,runtime,wid,run_id,label,question,clock,*,expected=None,status='supported'):
    started=time.monotonic();key=str(uuid5(run_id,label))
    with Session(engine) as db:
        ws=db.get(Workspace,wid)
        scope=ai_admission.AttemptScope(ws.id,ws.generation,key,ws.revision)
        manifest={row.slot:str(row.version_id) for row in db.scalars(select(Manifest).where(Manifest.workspace_id==wid))}
    claim=ai_admission.claim_interaction(engine,scope,operation='chat',request_hash=_fingerprint({'question':question}),
        profile_id=runtime.spec.profile_id,manifest_ids=manifest,now=clock())
    try:
        scoped=runtime.for_scope(scope,clock=clock)
        vector=knowledge.query_embedding(scoped.embedder,question)
        with Session(engine) as db:
            ws=db.get(Workspace,wid);ai_admission.check_interaction(db,claim,ws,clock())
            hits=knowledge.retrieve(db,ws,question,vector=vector,spec=runtime.spec)
        answer=scoped.assistant.evidence(question,hits);claims=assistant.validate_claims(answer,hits)
        if answer.status!=status:raise DomainError('ACCEPTANCE_ANSWER','Answer disposition needs review.',422)
        if expected and not any(c.page==expected['page'] and expected['contains'].lower() in c.excerpt.lower() and
            any(h.node.id_==str(c.passage_id) and h.node.metadata['slot']==expected['slot'] for h in hits) for c in claims):
            raise DomainError('ACCEPTANCE_SOURCE','The expected source was not supported.',422)
        with Session(engine) as db,db.begin():
            ws=db.get(Workspace,wid,with_for_update=True);ai_admission.check_interaction(db,claim,ws,clock())
            ai_admission.complete_interaction(db,claim,ws,clock())
        return {'case':label,'status':answer.status,'elapsed_ms':int((time.monotonic()-started)*1000),
            'sources':[{'version_id':str(c.version_id),'passage_id':str(c.passage_id),'page':c.page} for c in claims]}
    except BaseException:
        ai_admission.finish_interaction(engine,claim,now=clock());raise


def _guest(engine,runtime,run_id,clock):
    with Session(engine) as db,db.begin():
        row=db.get(AcceptanceRun,run_id,with_for_update=True)
        if len(row.workspace_ids)>=2:raise DomainError('ACCEPTANCE_LIMIT','Two guests are the acceptance limit.',429)
        ws,token=create_workspace(db,'UTC',clock(),embedding_profile_id=runtime.spec.profile_id)
        knowledge.attach_samples(db,ws);row.workspace_ids=[*row.workspace_ids,str(ws.id)]
        return ws.id,token


def _client(settings,engine,runtime,token,clock):
    from fastapi.testclient import TestClient

    from .api import create_app
    client=TestClient(create_app(settings,engine,clock,ai_runtime=runtime))
    client.cookies.set(COOKIE,token)
    return client,{'x-choreograph-bridge':settings.bridge_secret,'origin':settings.origin,
                   'x-csrf-token':csrf_token(token,settings.bridge_secret)}


def _command(client,headers,state,run_id,label,path,fields):
    response=client.post('/v1/'+path,headers={**headers,'idempotency-key':str(uuid5(run_id,label))},
        json={'generation':state['generation'],'revision':state['revision'],**fields})
    if response.status_code!=200:raise DomainError('ACCEPTANCE_COMMAND','The acceptance command failed.',422)
    return response.json()


def complete_ai_run(engine,run_id,grant,clock):
    """Usage and success are one receipt transaction after private cleanup."""
    try:
        with Session(engine) as db,db.begin():
            row=db.get(AcceptanceRun,run_id,with_for_update=True)
            if row is None or row.state!='running':raise DomainError('ACCEPTANCE_RUN_USED','Acceptance is no longer active.',409)
            attempts=list(db.scalars(select(AIAttempt).where(AIAttempt.grant_id==grant.grant_id,
                or_(AIAttempt.workspace_id.in_([UUID(value) for value in row.workspace_ids]),
                    (AIAttempt.workspace_id.is_(None)) & (AIAttempt.command_key==str(run_id))))))
            usage={'attempts':len(attempts),'reported_input_tokens':sum(a.actual_input_tokens or 0 for a in attempts),
                'reported_output_tokens':sum(a.actual_output_tokens or 0 for a in attempts),
                'unreported_attempts':sum(a.actual_input_tokens is None for a in attempts)}
            row.counts={**row.counts,'reported_usage':usage};row.state='succeeded';row.finished_at=clock()
            return dict(row.counts)
    except DomainError:raise
    except Exception:  # noqa: BLE001 - failed reporting cannot leave a successful acceptance receipt.
        finish_run(engine,run_id,state='failed',code='ACCEPTANCE_RECEIPT_FAILED',clock=clock)
        raise DomainError('ACCEPTANCE_RECEIPT_FAILED','Acceptance reporting needs attention.',503) from None


def execute_ai(engine,settings,run_id,step,max_cost,*,runtime=None,clock=None,injected=False):
    from .composition import compose_ai
    clock=clock or (lambda:datetime.now(UTC));owned=runtime is None;run_id=UUID(str(run_id))
    if runtime is not None and not injected:raise DomainError('ACCEPTANCE_INJECTION_LABEL','Injected execution must be labelled.',422)
    if step not in {'prepare','evaluate'} or (settings.profile!='live' and not injected):
        raise DomainError('ACCEPTANCE_LIVE_REQUIRED','Use an explicit live acceptance configuration.',422)
    grant=settings.live_ai.grant if settings.live_ai else getattr(runtime,'_grant',None)
    if (grant is None or type(max_cost) is not int or not 0<max_cost<=grant.cost_micros or
            grant.requests>78 or grant.vectors>88 or grant.input_tokens>336_864 or grant.output_tokens>42_000):
        raise DomainError('ACCEPTANCE_GRANT_INVALID','Use the reviewed finite acceptance allowance.',422)
    spec=settings.live_ai.spec if settings.live_ai else runtime.spec
    database=database_status(engine,spec)
    if database['code'] not in ({'DATABASE_READY','KNOWLEDGE_NOT_READY'} if step=='prepare' else {'DATABASE_READY'}):
        raise DomainError('ACCEPTANCE_NOT_READY','Prepare the reviewed schema and profile first.',422)
    settings=replace(settings,crm_provider='disabled',live_crm=None)
    cases=json.loads((knowledge.PACK/'evaluation.json').read_text())
    if len(cases)!=18 or any(not isinstance(case.get('question'),str) or not 1<=len(case['question'])<=1200 for case in cases):
        raise DomainError('ACCEPTANCE_CORPUS','Review the authored evaluation set first.',422)
    reserve_run(engine,run_id,'ai_'+step,_fingerprint({'grant':asdict(grant),'profile':spec.profile_id,'limits':AI_LIMITS}),clock())
    base=runtime;result={'mode':'injected' if injected else 'real-provider','run_id':str(run_id),'step':step,'cases':[]}
    clients=[];deadline=time.monotonic()+AI_LIMITS['seconds']
    try:
        base=base or compose_ai(settings,engine,clock=clock)
        runtime=RunRuntime(base,engine,run_id,deadline,max_cost)
        if step=='prepare':
            marker(engine,run_id,'prepare-corpus')
            scoped=runtime.for_scope(ai_admission.AttemptScope(None,0,str(run_id)),clock=clock)
            parsed=[]
            for item in json.loads((knowledge.PACK/'manifest.json').read_text()):
                if not item['replacement']:
                    parsed.append(knowledge.parse_version((knowledge.PACK/item['file']).read_bytes(),
                        'pdf' if item['file'].endswith('.pdf') else 'text',item['slot'],item['title'],item['version'],
                        clock(),spec=runtime.spec,tokenizer=runtime.tokenizer))
            if sum(len(item.chunks) for item in parsed)>AI_LIMITS['document_vectors']:
                raise DomainError('ACCEPTANCE_LIMIT','Corpus exceeds the reviewed vector ceiling.',422)
            result['preparation']=knowledge.prepare_pack(engine,clock(),spec=runtime.spec,embedder=scoped.embedder,tokenizer=runtime.tokenizer)
        else:
            a,at=_guest(engine,runtime,run_id,clock);b,bt=_guest(engine,runtime,run_id,clock)
            for i,case in enumerate(cases):
                label=f'authored-{i+1}';marker(engine,run_id,label)
                receipt=_rag(engine,runtime,a,run_id,label,case['question'],clock,expected=case)
                result['cases'].append(receipt);marker(engine,run_id,label,receipt)
            marker(engine,run_id,'absent')
            receipt=_rag(engine,runtime,a,run_id,'absent','Does Juniper arrange international flights?',clock,status='insufficient')
            result['cases'].append(receipt);marker(engine,run_id,'absent',receipt)
            ac,ah=_client(settings,engine,runtime,at,clock);bc,bh=_client(settings,engine,runtime,bt,clock);clients.extend([ac,bc])
            state=bc.get('/v1/session',headers=bh).json();old=next(d['id'] for d in state['documents'] if d['slot']=='preparation')
            for label,file,kind,expected_status,expected in [
                ('revision','preparation-guide-v2.pdf','pdf','supported',{'slot':'preparation','page':1,'contains':'outside the home'}),
                ('untrusted','evaluation-adversarial.txt','text','conflicting',None)]:
                marker(engine,run_id,label);data=(knowledge.PACK/file).read_bytes()
                outcome=_command(bc,bh,state,run_id,label,'documents/preparation/replace',{'kind':kind,'data':base64.b64encode(data).decode()})
                if not outcome.get('document_notice',{}).get('ready'):raise DomainError('ACCEPTANCE_REPLACEMENT','Replacement failed.',422)
                state=outcome['state'];version=next(d['id'] for d in state['documents'] if d['slot']=='preparation')
                if ac.get('/v1/documents/'+version,headers=ah).status_code!=404 or bc.get('/v1/documents/'+old,headers=bh).status_code!=404:
                    raise DomainError('ACCEPTANCE_SCOPE','Source authorization failed.',422)
                source=bc.get('/v1/documents/'+version+'/source',headers=bh)
                if source.status_code!=200 or hashlib.sha256(source.content).digest()!=hashlib.sha256(data).digest():
                    raise DomainError('ACCEPTANCE_SOURCE','Source bytes did not match.',422)
                receipt=_rag(engine,runtime,b,run_id,label+'-answer','Where should pets stay during cleaning?',clock,
                    expected=expected,status=expected_status)
                result['cases'].append(receipt);marker(engine,run_id,label,receipt);old=version
            state=ac.get('/v1/session',headers=ah).json()
            for label,question in [('policy','I need a regular clean for one bedroom. What do I do with my cats?'),
                                   ('week','When is this service free this week?'),('supplies','What cleaning supplies do you bring?')]:
                marker(engine,run_id,label)
                state=_command(ac,ah,state,run_id,label,'chat',{'text':question})['state']
                if not state['quote'] or state['quote']['cents']!=6000 or state['quote']['minutes']!=90:
                    raise DomainError('ACCEPTANCE_DOMAIN','The exact quote or context changed.',422)
                message=state['messages'][-1]
                if (label=='week' and 'week' not in message['cards']) or (label!='week' and not message['claims']):
                    raise DomainError('ACCEPTANCE_CONTEXT','The grounded context did not continue.',422)
                receipt={'case':label,'status':'passed'};result['cases'].append(receipt);marker(engine,run_id,label,receipt)
            if len(result['cases'])!=24:raise DomainError('ACCEPTANCE_CASE_COUNT','Acceptance case count changed.',422)
    except BaseException as error:
        finish_run(engine,run_id,state='failed',code=error.code if isinstance(error,DomainError) else 'ACCEPTANCE_FAILED',clock=clock)
        raise
    finally:
        try:
            for client in clients:client.close()
            with Session(engine) as db,db.begin():
                row=db.get(AcceptanceRun,run_id)
                for wid in row.workspace_ids:
                    ws=db.get(Workspace,UUID(wid),with_for_update=True)
                    if ws:jobs.retire_workspace(db,ws,clock())
        except Exception:  # noqa: BLE001 - cleanup failure cannot become a successful acceptance receipt.
            finish_run(engine,run_id,state='failed',code='ACCEPTANCE_CLEANUP_FAILED',clock=clock)
            raise DomainError('ACCEPTANCE_CLEANUP_FAILED','Private cleanup needs attention.',503) from None
        finally:
            if owned and base:base.close()
    result['reserved']=complete_ai_run(engine,run_id,grant,clock);result['status']='succeeded'
    return result


def execute_crm(engine,settings,run_id,workspace_id,account_id,step,*,provider=None,clock=None,injected=False,uninstall=False):
    from .crm_composition import compose_crm
    clock=clock or (lambda:datetime.now(UTC));run_id=UUID(str(run_id));wid=UUID(str(workspace_id));owned=provider is None
    if provider is not None and not injected:raise DomainError('ACCEPTANCE_INJECTION_LABEL','Injected execution must be labelled.',422)
    if step not in {'sync','cleanup'} or settings.crm_provider!='hubspot' and not injected:
        raise DomainError('ACCEPTANCE_CRM_REQUIRED','Use the explicitly selected visitor account.',422)
    if settings.live_crm and settings.live_crm.allowance.requests>60:
        raise DomainError('ACCEPTANCE_GRANT_INVALID','Use the finite sixty-request acceptance allowance.',422)
    with Session(engine) as db:
        ws=db.get(Workspace,wid)
        connection=crm.latest_connection(db,ws) if ws else None
        if (not ws or not ws.active or ws.expires_at<=clock() or not connection or connection.account_id!=account_id or
                connection.state!='ready' or not connection.export_consent):
            raise DomainError('ACCEPTANCE_CRM_SCOPE','Review this account, destination and sharing consent first.',422)
    reserve_run(engine,run_id,'crm_'+step,_fingerprint({'workspace':str(wid),'account':account_id,'step':step,'uninstall':uninstall}),clock())
    try:
        provider=provider or compose_crm(replace(settings,profile='fake',live_ai=None),engine,clock=clock)
        with Session(engine) as db,db.begin():
            ws=db.get(Workspace,wid,with_for_update=True);connection=crm.latest_connection(db,ws);crm.require_provider(connection,provider)
            if step=='cleanup':
                crm.finish(db,ws,CRMFinish(generation=ws.generation,revision=ws.revision,connection_id=connection.id,
                    confirm=True,cleanup=True,uninstall=uninstall),clock());db.flush()
                event=db.scalar(select(Outbox).where(Outbox.workspace_id==wid,Outbox.kind=='crm_cleanup',
                    Outbox.connection_id==connection.id).order_by(Outbox.revision.desc()).limit(1))
            else:
                requests=list(db.scalars(select(Enquiry.id).where(Enquiry.workspace_id==wid,Enquiry.status=='confirmed')))
                if len(requests)!=1:raise DomainError('ACCEPTANCE_CRM_SCOPE','Review exactly one fictional booking first.',422)
                event=db.scalar(select(Outbox).where(Outbox.workspace_id==wid,Outbox.enquiry_id==requests[0],
                    Outbox.connection_id==connection.id,Outbox.kind=='crm_upsert').order_by(Outbox.revision.desc()).limit(1))
            if event is None:raise DomainError('ACCEPTANCE_CRM_SCOPE','No reviewed CRM work is available.',422)
            event_id=event.id
        job=jobs.claim(engine,clock(),workspace_id=wid,event_id=event_id)
        if job:jobs.deliver(engine,settings,provider,job,clock)
        with Session(engine) as db:
            event=db.get(Outbox,(wid,event_id))
            if event.state not in {'synced','completed'}:raise DomainError('ACCEPTANCE_CRM_PENDING','CRM verification or cleanup needs attention.',422)
            result={'mode':'injected' if injected else 'real-provider','run_id':str(run_id),'status':'succeeded','step':step,
                    'delivery_performed':bool(job),'verification':'fresh_provider_readback' if job else 'stored_verified_receipt'}
            if step=='sync':
                mapping=db.get(ExternalMapping,(wid,event.connection_id,event.enquiry_id))
                if not mapping or not mapping.verified:raise DomainError('ACCEPTANCE_CRM_UNVERIFIED','Native records are not verified.',422)
                result['verified_record_references']={'contact':mapping.contact_id,'deal':mapping.deal_id}
            else:result['cleanup']=event.payload.get('result',{})
        finish_run(engine,run_id,state='succeeded',clock=clock);return result
    except BaseException as error:
        finish_run(engine,run_id,state='failed',code=error.code if isinstance(error,DomainError) else 'ACCEPTANCE_FAILED',clock=clock)
        raise
    finally:
        if owned and provider:provider.close()


def initialize_database(values,run_id):
    """Create one uniquely named disposable database on the owned local server."""
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url

    from .migrate import migrate
    url=make_url(values.get('CHOREOGRAPH_DATABASE_URL',''))
    if (url.drivername!='postgresql+psycopg' or url.host not in {'localhost','127.0.0.1'} or
            url.port!=45862 or url.database!='choreograph' or url.query):raise ValueError('OWNED_LOCAL_POSTGRES_REQUIRED')
    name='choreograph_acceptance_'+UUID(str(run_id)).hex
    admin=create_engine(url.set(database='postgres'),isolation_level='AUTOCOMMIT',hide_parameters=True)
    engine=None
    try:
        with admin.connect() as connection:connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
        engine=create_engine(url.set(database=name),hide_parameters=True)
        migrate(engine)
        return {'status':'succeeded','database_name':name,'provider_calls':0,'cloud_changes':0}
    finally:
        if engine:engine.dispose()
        admin.dispose()


def main():
    from dotenv import dotenv_values

    from .db import build_engine
    from .settings import Settings
    parser=argparse.ArgumentParser(description='Prepare a finite plan; real execution requires later owner authorization.')
    parser.add_argument('lane',choices=['ai','crm']);parser.add_argument('step',choices=['init-db','prepare','evaluate','sync','cleanup'])
    parser.add_argument('--execute',action='store_true');parser.add_argument('--run-id',type=UUID)
    parser.add_argument('--env-file',type=Path,default=ROOT/'.env.local');parser.add_argument('--database-name')
    parser.add_argument('--max-cost-micros',type=int);parser.add_argument('--workspace-id',type=UUID)
    parser.add_argument('--account-id');parser.add_argument('--uninstall',action='store_true')
    args=parser.parse_args()
    if not args.execute:print(json.dumps(dry_plan(args.lane,args.step)));return
    engine=None
    try:
        if args.run_id is None:raise ValueError('RUN_ID_REQUIRED')
        values={key:value for key,value in dotenv_values(args.env_file,interpolate=False).items() if value is not None}
        if args.step=='init-db':
            if args.lane!='ai':raise ValueError('ACCEPTANCE_STEP_INVALID')
            print(json.dumps(initialize_database(values,args.run_id)));return
        values['CHOREOGRAPH_CRM_PROVIDER']='disabled' if args.lane=='ai' else 'hubspot'
        if args.lane=='crm':values['CHOREOGRAPH_PROFILE']='fake'
        settings=Settings.parse(values)
        from sqlalchemy.engine import make_url
        url=make_url(settings.database_url)
        if args.database_name:
            if not args.database_name.startswith('choreograph_acceptance_') or not args.database_name.removeprefix('choreograph_acceptance_').isalnum():raise ValueError('ACCEPTANCE_DATABASE_REQUIRED')
            url=url.set(database=args.database_name);settings=replace(settings,database_url=url.render_as_string(hide_password=False))
        if url.host not in {'localhost','127.0.0.1'} or url.port!=45862 or url.query:
            raise ValueError('LOCAL_ACCEPTANCE_DATABASE_REQUIRED')
        if args.lane=='ai' and not (url.database or '').startswith('choreograph_acceptance_'):
            raise ValueError('ACCEPTANCE_DATABASE_REQUIRED')
        engine=build_engine(settings)
        if args.lane=='ai':result=execute_ai(engine,settings,args.run_id,args.step,args.max_cost_micros)
        else:
            if args.workspace_id is None or not args.account_id:raise ValueError('EXACT_VISITOR_ACCOUNT_REQUIRED')
            result=execute_crm(engine,settings,args.run_id,args.workspace_id,args.account_id,args.step,uninstall=args.uninstall)
        print(json.dumps(result))
    except Exception as error:  # noqa: BLE001 - never log raw credentials, model payloads, contact data or provider text.
        print(json.dumps({'status':'failed','code':error.code if isinstance(error,DomainError) else 'ACCEPTANCE_CONFIGURATION_OR_EXECUTION_FAILED'}))
        raise SystemExit(1) from None
    finally:
        if engine:engine.dispose()


if __name__=='__main__':main()
