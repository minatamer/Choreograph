"""Explicit embedding identities and durable, content-free provider admission."""
import hashlib
import json
import re
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Generic, Literal, TypeVar
from uuid import UUID, uuid4

from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

from .errors import DomainError

T = TypeVar('T')


@dataclass(frozen=True)
class EmbeddingSpec:
    provider: Literal['fake', 'openai']
    model: str
    dimensions: int
    chunker: str
    tokenizer: str

    def __post_init__(self):
        if (self.provider not in {'fake', 'openai'} or type(self.dimensions) is not int or not 1 <= self.dimensions <= 3072 or
                any(not isinstance(value, str) or not value or len(value) > 100
                    for value in (self.model, self.chunker, self.tokenizer))):
            raise ValueError('EMBEDDING_SPEC_INVALID')
        if self.provider == 'fake' and self.dimensions != 64:
            raise ValueError('EMBEDDING_SPEC_INVALID')

    @property
    def profile_id(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True, separators=(',', ':')).encode()).hexdigest()


FAKE_SPEC = EmbeddingSpec('fake', 'fake-hash-64-v2', 64, 'llama-token-section-v3', 'whitespace-v1')


@dataclass(frozen=True)
class GrantSpec:
    grant_id: str
    expires_at: datetime
    response_model: str
    embedding_model: str
    requests: int
    input_tokens: int
    output_tokens: int
    vectors: int
    cost_micros: int
    workspace_requests: int
    workspace_input_tokens: int
    workspace_output_tokens: int
    workspace_vectors: int
    workspace_cost_micros: int
    response_input_rate: int
    response_output_rate: int
    embedding_input_rate: int

    def __post_init__(self):
        numbers = [value for key, value in asdict(self).items()
                   if key not in {'grant_id', 'expires_at', 'response_model', 'embedding_model'}]
        if (not self.grant_id or len(self.grant_id) > 80 or not self.expires_at.tzinfo or
                not self.response_model or not self.embedding_model or
                any(type(value) is not int or not 0 < value <= 10**12 for value in numbers) or
                len(self.response_model)>100 or len(self.embedding_model)>100 or
                any(getattr(self,'workspace_'+key)>getattr(self,key)
                    for key in ('requests','input_tokens','output_tokens','vectors','cost_micros'))):
            raise ValueError('AI_GRANT_INVALID')


@dataclass(frozen=True)
class AttemptScope:
    workspace_id: UUID | None
    generation: int
    command_key: str
    revision: int | None = None


@dataclass(frozen=True)
class SafeUsage:
    input_tokens: int
    output_tokens: int = 0


@dataclass(frozen=True)
class ProviderResult(Generic[T]):
    value: T
    usage: SafeUsage | None = None
    reference: str | None = None


@dataclass(frozen=True)
class AttemptClaim:
    id: UUID
    lease_token: UUID


@dataclass(frozen=True)
class InteractionClaim:
    id: UUID
    workspace_id: UUID
    generation: int
    revision: int
    profile_id: str
    manifest_ids: dict[str, str]
    lease_until: datetime


def _scope(scope):
    try:
        UUID(scope.command_key)
    except (ValueError, TypeError, AttributeError):
        raise DomainError('IDEMPOTENCY_REQUIRED', 'Refresh the action and try again.', 422) from None
    if len(scope.command_key)!=36 or (scope.workspace_id is not None and scope.generation<1):
        raise DomainError('IDEMPOTENCY_REQUIRED', 'Refresh the action and try again.', 422)


def _workspace(db, scope, now):
    from .models import Workspace
    workspace=db.get(Workspace,scope.workspace_id)
    if not workspace or not workspace.active or workspace.expires_at<=now:
        raise DomainError('SESSION_EXPIRED','This demo has ended.',410)
    if workspace.generation!=scope.generation:
        raise DomainError('STALE_GENERATION','This demo changed. Refresh before continuing.')
    if scope.revision is not None and workspace.revision!=scope.revision:
        raise DomainError('STALE_REVISION','The demo changed. Refresh before continuing.')
    return workspace


def claim_interaction(engine, scope: AttemptScope, *, operation, request_hash, profile_id, manifest_ids, now):
    from .models import AIInteraction, Manifest
    _scope(scope)
    if (scope.workspace_id is None or scope.revision is None or operation not in {'chat','replace'} or
            re.fullmatch(r'[a-f0-9]{64}', request_hash) is None):
        raise ValueError('AI_INTERACTION_INVALID')
    with Session(engine) as db, db.begin():
        db.execute(text('SELECT pg_advisory_xact_lock(45866,1)'))
        workspace=_workspace(db,scope,now)
        expected={row.slot:str(row.version_id) for row in db.scalars(select(Manifest).where(
            Manifest.workspace_id==workspace.id))}
        if workspace.embedding_profile_id!=profile_id or expected!=manifest_ids:
            raise DomainError('DOCUMENT_CHANGED','The documents changed. Refresh before continuing.')
        previous=db.scalar(select(AIInteraction).where(AIInteraction.workspace_id==workspace.id,
            AIInteraction.generation==scope.generation,AIInteraction.command_key==scope.command_key))
        if previous:
            code='AI_INTERACTION_USED' if previous.request_hash==request_hash and previous.operation==operation else 'IDEMPOTENCY_MISMATCH'
            raise DomainError(code,'That action has already been processed. Refresh before sending again.',409)
        if db.scalar(select(func.count()).select_from(AIInteraction).where(AIInteraction.workspace_id==workspace.id))>=200:
            raise DomainError('DEMO_LIMIT','This demo has reached its action limit.',429)
        active=(AIInteraction.state=='active') & (AIInteraction.lease_until>now)
        if (db.scalar(select(func.count()).select_from(AIInteraction).where(active))>=4 or
                (operation=='replace' and db.scalar(select(func.count()).select_from(AIInteraction).where(
                    active,AIInteraction.operation=='replace'))>=2) or
                db.scalar(select(AIInteraction.id).where(active,AIInteraction.workspace_id==workspace.id).limit(1))):
            raise DomainError('ASSISTANT_BUSY','The front desk is busy. Try again shortly.',429)
        row=AIInteraction(id=uuid4(),workspace_id=workspace.id,generation=scope.generation,revision=scope.revision,
            command_key=scope.command_key,request_hash=request_hash,operation=operation,profile_id=profile_id,
            manifest_ids=dict(manifest_ids),state='active',lease_until=now+timedelta(seconds=120))
        db.add(row)
        return InteractionClaim(row.id,workspace.id,scope.generation,scope.revision,profile_id,dict(manifest_ids),row.lease_until)


def check_interaction(db, claim, workspace, now):
    from .models import AIInteraction, Manifest
    row=db.get(AIInteraction,claim.id)
    if (not row or row.state!='active' or row.lease_until<=now or workspace.id!=claim.workspace_id or
            not workspace.active or workspace.expires_at<=now or workspace.generation!=claim.generation):
        raise DomainError('SESSION_EXPIRED','This operation is no longer active.',410)
    current={item.slot:str(item.version_id) for item in db.scalars(select(Manifest).where(Manifest.workspace_id==workspace.id))}
    if workspace.revision!=claim.revision or workspace.embedding_profile_id!=claim.profile_id or current!=claim.manifest_ids:
        raise DomainError('STALE_REVISION','The demo or documents changed. Refresh before continuing.')


def complete_interaction(db, claim, workspace, now):
    # Call check_interaction before domain application, whose revision may change.
    from .models import AIInteraction
    row=db.get(AIInteraction,claim.id)
    if (not row or row.state!='active' or row.lease_until<=now or workspace.id!=claim.workspace_id or
            not workspace.active or workspace.expires_at<=now or workspace.generation!=claim.generation):
        raise DomainError('SESSION_EXPIRED','This operation is no longer active.',410)
    row.state='completed'


def finish_interaction(engine, claim, *, now, state='failed'):
    from .models import AIInteraction
    if state not in {'failed','retired'}:raise ValueError('AI_INTERACTION_STATE_INVALID')
    with Session(engine) as db,db.begin():
        db.execute(update(AIInteraction).where(AIInteraction.id==claim.id,AIInteraction.state=='active').values(state=state))


class Admission:
    """One command scope; each phase/batch is admitted at most once, ever.

    Rates are integer microcurrency units per million tokens. Reservations are
    deliberately never refunded; observed usage is diagnostic, not permission
    to repeat a request whose external completion may be uncertain.
    """
    def __init__(self, engine, grant: GrantSpec, scope: AttemptScope, clock: Callable[[], datetime], *,
                 monotonic_deadline=None, monotonic_clock=time.monotonic):
        self.engine, self.grant, self.scope, self.clock = engine, grant, scope, clock
        self.monotonic_deadline,self.monotonic_clock=monotonic_deadline,monotonic_clock

    def _deadline(self):
        if self.monotonic_deadline is not None and self.monotonic_clock()>=self.monotonic_deadline:
            raise DomainError('ASSISTANT_TIMEOUT','The front desk took too long. Your request is unchanged.',503)

    def run(self, phase: str, batch: int, *, input_tokens: int, output_tokens: int = 0,
            vectors: int = 0, invoke: Callable[[], ProviderResult[T]]) -> T:
        claim = self.reserve(phase, batch, input_tokens=input_tokens, output_tokens=output_tokens, vectors=vectors)
        try:
            self.start(claim)
            self._deadline()
            result = invoke()
            self.finish(claim, result=result)
            self._deadline()
            return result.value
        except BaseException:
            self.finish(claim)
            raise

    def reserve(self, phase, batch, *, input_tokens, output_tokens=0, vectors=0):
        from .models import AIAttempt, AIGrant, AIInteraction
        _scope(self.scope)
        self._deadline()
        embedding=phase in {'query_embed','ingest_embed'}
        if (phase not in {'interpret','evidence','query_embed','ingest_embed'} or type(batch) is not int or not 0<=batch<384 or
                any(type(v) is not int or v<0 for v in (input_tokens,output_tokens,vectors)) or not input_tokens or
                (embedding and (not 1<=vectors<=4 or output_tokens)) or (not embedding and (vectors or output_tokens<1))):
            raise ValueError('AI_ATTEMPT_INVALID')
        now=self.clock()
        if self.grant.expires_at<=now:raise DomainError('AI_BUDGET_EXPIRED','Live assistance is unavailable.',429)
        values=asdict(self.grant);values['expires_at']=self.grant.expires_at.isoformat()
        digest=hashlib.sha256(json.dumps(values,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        cost=(input_tokens*(self.grant.embedding_input_rate if embedding else self.grant.response_input_rate)+
              output_tokens*(0 if embedding else self.grant.response_output_rate)+999_999)//1_000_000
        requested=dict(requests=1,input_tokens=input_tokens,output_tokens=output_tokens,vectors=vectors,cost_micros=cost)
        scope_key=str(self.scope.workspace_id) if self.scope.workspace_id else 'operator'
        with Session(self.engine) as db,db.begin():
            db.execute(text('SELECT pg_advisory_xact_lock(45867,1)'))
            self._deadline()
            if self.scope.workspace_id:
                workspace=_workspace(db,self.scope,now)
                interaction=db.scalar(select(AIInteraction).where(AIInteraction.workspace_id==workspace.id,
                    AIInteraction.generation==self.scope.generation,AIInteraction.command_key==self.scope.command_key))
                if not interaction or interaction.state!='active' or interaction.lease_until<=now:
                    raise DomainError('AI_INTERACTION_REQUIRED','Start the action again.',409)
            grant=db.get(AIGrant,self.grant.grant_id)
            if grant and grant.spec_hash!=digest:raise DomainError('AI_GRANT_CHANGED','Live allowance needs review.',503)
            if grant and grant.blocked:raise DomainError('AI_GRANT_REVIEW','Live allowance needs review.',503)
            if not grant:
                grant=AIGrant(id=self.grant.grant_id,spec_hash=digest,spec=values,expires_at=self.grant.expires_at,
                    requests=0,input_tokens=0,output_tokens=0,vectors=0,cost_micros=0)
                db.add(grant)
            if db.scalar(select(AIAttempt.id).where(AIAttempt.scope_key==scope_key,AIAttempt.generation==self.scope.generation,
                AIAttempt.command_key==self.scope.command_key,AIAttempt.phase==phase,AIAttempt.batch==batch)):
                raise DomainError('AI_ATTEMPT_USED','That provider action cannot be repeated. Refresh the demo.',409)
            active=AIAttempt.state.in_(['reserved','started']) & (AIAttempt.lease_until>now)
            if db.scalar(select(func.count()).select_from(AIAttempt).where(active))>=4:
                raise DomainError('ASSISTANT_BUSY','The front desk is busy. Try again shortly.',429)
            for key,amount in requested.items():
                used=getattr(grant,key)
                aggregate=func.count(AIAttempt.id) if key=='requests' else func.coalesce(func.sum(getattr(AIAttempt,key)),0)
                guest=db.scalar(select(aggregate).where(
                    AIAttempt.grant_id==grant.id,AIAttempt.scope_key==scope_key))
                if used+amount>getattr(self.grant,key) or (self.scope.workspace_id is not None and
                        guest+amount>getattr(self.grant,'workspace_'+key)):
                    raise DomainError('AI_BUDGET_LIMIT','This live allowance has been used. Use the request controls.',429)
                setattr(grant,key,used+amount)
            row=AIAttempt(id=uuid4(),grant_id=grant.id,workspace_id=self.scope.workspace_id,scope_key=scope_key,
                generation=self.scope.generation,command_key=self.scope.command_key,phase=phase,batch=batch,
                model=self.grant.embedding_model if embedding else self.grant.response_model,state='reserved',
                lease_until=min(now+timedelta(seconds=120),self.grant.expires_at),lease_token=uuid4(),
                input_tokens=input_tokens,output_tokens=output_tokens,vectors=vectors,cost_micros=cost)
            db.add(row)
            return AttemptClaim(row.id,row.lease_token)

    def start(self, claim):
        from .models import AIAttempt, AIGrant
        self._deadline()
        with Session(self.engine) as db,db.begin():
            row=db.scalar(select(AIAttempt).where(AIAttempt.id==claim.id).with_for_update())
            if not row or row.lease_token!=claim.lease_token or row.state!='reserved' or row.lease_until<=self.clock():
                raise DomainError('AI_ATTEMPT_USED','That provider action cannot be repeated.',409)
            if db.get(AIGrant,row.grant_id).blocked:
                raise DomainError('AI_GRANT_REVIEW','Live allowance needs review.',503)
            if self.scope.workspace_id:_workspace(db,self.scope,self.clock())
            row.state='started'

    def finish(self, claim, *, result=None):
        from .models import AIAttempt, AIGrant
        overrun=False
        with Session(self.engine) as db,db.begin():
            db.execute(text('SELECT pg_advisory_xact_lock(45867,1)'))
            row=db.scalar(select(AIAttempt).where(AIAttempt.id==claim.id).with_for_update())
            if not row or row.lease_token!=claim.lease_token or row.state not in {'reserved','started'}:return
            row.state='completed' if result is not None else 'unknown'
            if result and result.usage:
                usage=result.usage
                if type(usage.input_tokens) is int and type(usage.output_tokens) is int:
                    overrun=not (0<=usage.input_tokens<=row.input_tokens and 0<=usage.output_tokens<=row.output_tokens)
                    if overrun:
                        row.state='unknown';db.get(AIGrant,row.grant_id).blocked=True
                if (type(usage.input_tokens) is int and type(usage.output_tokens) is int and
                        0<=usage.input_tokens<=10**12 and 0<=usage.output_tokens<=10**12):
                    row.actual_input_tokens=usage.input_tokens;row.actual_output_tokens=usage.output_tokens
            if result and result.reference and re.fullmatch(r'[A-Za-z0-9_-]{1,100}',result.reference):
                row.reference=result.reference
        if overrun:raise DomainError('AI_GRANT_REVIEW','Provider usage exceeded its allowance. Live assistance needs review.',503)
