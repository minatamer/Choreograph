"""Durable publication. Database work, not queue history, owns completion."""
import base64
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import and_, or_, select, text
from sqlalchemy.orm import Session

from . import jobs
from .models import Outbox, TaskPublication
from .task_delivery import Delivery, task_payload
from .task_enqueue import PublishFailure


@dataclass(frozen=True)
class PublicationClaim:
    workspace_id: object
    event_id: object
    lease_token: object
    name: str
    action: str
    target_hash: str


def target_hash(config):
    return hashlib.sha256(json.dumps(asdict(config),sort_keys=True,separators=(',',':')).encode()).hexdigest()


def task_name(config,workspace_id,event_id,epoch):
    identity=f'{target_hash(config)}:{workspace_id}:{event_id}:{epoch}'
    return config.parent+'/tasks/'+hashlib.sha256(identity.encode()).hexdigest()


def eligible(row,now):
    return (row.attempts<5 and ((row.state in {'pending','retrying','reconciling'} and row.due_at<=now) or
        (row.state=='processing' and row.lease_until is not None and row.lease_until<=now)))


def claim(engine,config,now):
    fingerprint=target_hash(config)
    with Session(engine) as db,db.begin():
        db.execute(text('SELECT pg_advisory_xact_lock(45869,1)'))
        active=TaskPublication.lease_until>now
        if len(list(db.scalars(select(TaskPublication.event_id).where(active).limit(3))))>=3:return None
        due=or_(and_(Outbox.state.in_(['pending','retrying','reconciling']),Outbox.due_at<=now),
            and_(Outbox.state=='processing',Outbox.lease_until<=now))
        rows=db.scalars(select(Outbox).outerjoin(TaskPublication,
            (TaskPublication.workspace_id==Outbox.workspace_id)&(TaskPublication.event_id==Outbox.id)).where(
            due,Outbox.attempts<5,or_(TaskPublication.event_id.is_(None),and_(
                TaskPublication.next_check<=now,TaskPublication.state.not_in(['retired','attention']),
                or_(TaskPublication.lease_until.is_(None),TaskPublication.lease_until<=now))))
            .order_by(Outbox.due_at,Outbox.id).limit(20).with_for_update(of=Outbox,skip_locked=True))
        for row in rows:
            publication=db.get(TaskPublication,(row.workspace_id,row.id))
            if not jobs.window_open(db,row,now):
                row.state='needs_attention';row.code='CRM_WINDOW_EXPIRED'
                if publication:publication.state='attention';publication.code='TASK_WINDOW_EXPIRED'
                continue
            if not jobs.valid(db,row,now):
                row.state='retired';row.code='CRM_RETIRED'
                if publication:publication.state='retired';publication.lease_token=None;publication.lease_until=None
                continue
            if publication and publication.target_hash!=fingerprint:
                publication.state='attention';publication.code='TASK_TARGET_CHANGED';continue
            if publication and publication.attempts>=120:
                publication.state='attention';publication.code='TASK_ATTEMPTS_EXHAUSTED';continue
            if not publication:
                publication=TaskPublication(workspace_id=row.workspace_id,event_id=row.id,target_hash=fingerprint,
                    epoch=0,name=task_name(config,row.workspace_id,row.id,0),state='new',attempts=0,next_check=now)
                db.add(publication)
            action='create' if publication.state=='new' else 'get'
            publication.state='unknown';publication.attempts+=1
            publication.lease_token=uuid4();publication.lease_until=now+timedelta(seconds=30)
            return PublicationClaim(row.workspace_id,row.id,publication.lease_token,publication.name,action,fingerprint)
    return None


def current(engine,claim,now):
    with Session(engine) as db:
        row=db.get(Outbox,(claim.workspace_id,claim.event_id))
        publication=db.get(TaskPublication,(claim.workspace_id,claim.event_id))
        return bool(row and publication and publication.lease_token==claim.lease_token and
            publication.lease_until and publication.lease_until>now and publication.target_hash==claim.target_hash and
            eligible(row,now) and jobs.valid(db,row,now) and jobs.window_open(db,row,now))


def matches(task,claim,config):
    try:
        request=task['httpRequest'];target=config.target
        body=Delivery.model_validate_json(base64.b64decode(request['body'],validate=True))
        return (task['name']==claim.name and request['url']==target.url and request['httpMethod']=='POST' and
            request['oidcToken']=={'serviceAccountEmail':target.service_email,'audience':target.audience} and
            body.workspace_id==claim.workspace_id and body.event_id==claim.event_id and task['dispatchDeadline']=='120s')
    except (ValueError,KeyError,TypeError):return False


def finish(engine,config,claim,now,*,task=None,error=None):
    with Session(engine) as db,db.begin():
        row=db.scalar(select(Outbox).where(Outbox.workspace_id==claim.workspace_id,Outbox.id==claim.event_id).with_for_update())
        publication=db.get(TaskPublication,(claim.workspace_id,claim.event_id))
        if (not row or not publication or publication.lease_token!=claim.lease_token or
                not publication.lease_until or publication.lease_until<=now):return False
        publication.lease_token=None;publication.lease_until=None
        if row.state=='needs_attention':
            publication.state='attention';publication.code=row.code;return False
        if row.state in {'synced','completed','retired'} or not jobs.valid(db,row,now):
            publication.state='retired';publication.code=None;return False
        if publication.target_hash!=target_hash(config):
            publication.state='attention';publication.code='TASK_TARGET_CHANGED';return False
        if not jobs.window_open(db,row,now):
            row.state='needs_attention';row.code='CRM_WINDOW_EXPIRED'
            publication.state='attention';publication.code='TASK_WINDOW_EXPIRED';return False
        if error:
            publication.code=error.code
            publication.state='attention' if error.code in {'TASK_ACCESS_DENIED','TASK_IDENTITY_INVALID','TASK_PAYLOAD_INVALID','TASK_QUEUE_MISSING'} else 'unknown'
            publication.next_check=now+timedelta(seconds=min(300,2**min(publication.attempts,8)))
            return False
        if task is not None:
            if not matches(task,claim,config):
                publication.state='attention';publication.code='TASK_RECEIPT_MISMATCH';return False
            publication.state='accepted';publication.code=None;publication.next_check=now+timedelta(seconds=30)
            return True
        # NOT_FOUND is consistent with completion, deletion or exhausted retries.
        # Only a fresh DB read can decide whether another epoch is still needed.
        if eligible(row,now):
            publication.epoch+=1;publication.name=task_name(config,row.workspace_id,row.id,publication.epoch)
            publication.state='new';publication.code='TASK_NOT_FOUND';publication.next_check=now+timedelta(seconds=5)
        else:
            publication.state='unknown';publication.code='TASK_IN_FLIGHT'
            publication.next_check=row.lease_until if row.state=='processing' and row.lease_until else row.due_at
        return False


def settle_terminal(engine):
    with Session(engine) as db,db.begin():
        rows=db.execute(select(TaskPublication,Outbox).join(Outbox,
            (TaskPublication.workspace_id==Outbox.workspace_id)&(TaskPublication.event_id==Outbox.id)).where(
                Outbox.state.in_(['synced','completed','retired','needs_attention']),
                TaskPublication.state.not_in(['retired','attention'])).limit(20).with_for_update(of=TaskPublication,skip_locked=True))
        for publication,row in rows:
            publication.state='attention' if row.state=='needs_attention' else 'retired'
            publication.code=row.code;publication.lease_until=None;publication.lease_token=None


def publish(engine,transport,claim,clock):
    if not current(engine,claim,clock()):
        return finish(engine,transport.config,claim,clock())
    try:
        task=(transport.create(claim.name,task_payload(transport.config.target,claim.workspace_id,claim.event_id))
              if claim.action=='create' else transport.get(claim.name))
        return finish(engine,transport.config,claim,clock(),task=task)
    except PublishFailure as error:return finish(engine,transport.config,claim,clock(),error=error)


def tick(engine,transport,clock,*,limit=3,stopping=lambda:False):
    accepted=0
    for _ in range(min(3,max(0,limit))):
        if stopping():break
        item=claim(engine,transport.config,clock())
        if not item:break
        accepted+=bool(publish(engine,transport,item,clock))
    return accepted
