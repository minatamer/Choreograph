"""Actual PostgreSQL admission persists independently of business transactions."""
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from choreograph.ai_admission import (
    FAKE_SPEC,
    Admission,
    AttemptScope,
    GrantSpec,
    ProviderResult,
    SafeUsage,
    check_interaction,
    claim_interaction,
    finish_interaction,
)
from choreograph.errors import DomainError
from choreograph.models import AIAttempt, AIGrant, AIInteraction, Workspace
from choreograph.persistence import Session, remove, repo_first
from choreograph.sessions import create_workspace

NOW=datetime(2026,10,22,10,tzinfo=UTC)


@pytest.fixture
def setup_admission(database):
    engine,_=database
    owned=[];grants=[]
    def grant(**changes):
        spec=GrantSpec(str(uuid4()),NOW+timedelta(hours=1),'synthetic-response','synthetic-embedding',
            20,100_000,100_000,100,100_000,20,100_000,100_000,100,100_000,1_000_000,1_000_000,1_000_000)
        spec=replace(spec,**changes);grants.append(spec.grant_id);return spec
    def scope(workspace_id=None,operation='chat'):
        with Session(engine) as db,db.begin():
            if workspace_id is None:
                workspace,_=create_workspace(db,'UTC',NOW);owned.append(workspace.id)
            else:workspace=db.get(Workspace,workspace_id)
            result=AttemptScope(workspace.id,workspace.generation,str(uuid4()),workspace.revision)
        claim=claim_interaction(engine,result,operation=operation,request_hash=hashlib.sha256(b'synthetic').hexdigest(),
            profile_id=FAKE_SPEC.profile_id,manifest_ids={},now=NOW)
        return result,claim
    try:yield engine,grant,scope
    finally:
        with Session(engine) as db,db.begin():
            remove(db,Workspace,predicate=lambda row:row.id in owned)
            remove(db,AIAttempt,predicate=lambda row:row.grant_id in grants)
            remove(db,AIGrant,predicate=lambda row:row.id in grants)


def test_concurrent_last_allowance_has_one_external_call(setup_admission):
    engine,grant,scope=setup_admission
    allowance=grant(requests=1,workspace_requests=1)
    scopes=[scope()[0],scope()[0]];barrier=threading.Barrier(2);calls=[]
    def run(current):
        barrier.wait(timeout=5)
        gate=Admission(engine,allowance,current,lambda:NOW)
        def invoke():calls.append(1);return ProviderResult('ok',SafeUsage(5,1),'resp_fixture')
        try:return gate.run('interpret',0,input_tokens=5,output_tokens=1,invoke=invoke)
        except DomainError as error:return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(run,scopes))==['AI_BUDGET_LIMIT','ok']
    assert calls==[1]
    with Session(engine) as db:
        row=db.get(AIGrant,allowance.grant_id)
        assert (row.requests,row.input_tokens,row.output_tokens,row.cost_micros)==(1,5,1,6)


def test_uncertain_call_replay_business_rollback_and_purge_keep_spend(setup_admission):
    engine,grant,scope=setup_admission
    allowance=grant();current,claim=scope();gate=Admission(engine,allowance,current,lambda:NOW);calls=[]
    def failed():calls.append(1);raise DomainError('SYNTHETIC_FAILURE','Unavailable.',503)
    with pytest.raises(DomainError):gate.run('interpret',0,input_tokens=9,output_tokens=4,invoke=failed)
    with pytest.raises(DomainError) as replay:
        Admission(engine,allowance,current,lambda:NOW).run('interpret',0,input_tokens=9,output_tokens=4,invoke=failed)
    assert replay.value.code=='AI_ATTEMPT_USED' and calls==[1]
    with pytest.raises(RuntimeError),Session(engine) as db,db.begin():
        db.get(Workspace,current.workspace_id).draft={'service':'deep'}
        raise RuntimeError('synthetic rollback')
    with Session(engine) as db:
        attempt=repo_first(db, AIAttempt, filters={'workspace_id': current.workspace_id})
        assert attempt.state=='unknown' and attempt.actual_input_tokens is None
        assert db.get(Workspace,current.workspace_id).draft=={}
    finish_interaction(engine,claim,now=NOW)
    with Session(engine) as db,db.begin():remove(db,Workspace,filters={'id':current.workspace_id})
    with Session(engine) as db:assert db.get(AIGrant,allowance.grant_id).requests==1
    operator=AttemptScope(None,0,str(uuid4()))
    with pytest.raises(DomainError) as changed:
        Admission(engine,replace(allowance,requests=21),operator,lambda:NOW).reserve('interpret',0,input_tokens=1,output_tokens=1)
    assert changed.value.code=='AI_GRANT_CHANGED'


def test_guest_limit_and_expiry_precede_provider_work(setup_admission):
    engine,grant,scope=setup_admission
    allowance=grant(workspace_requests=1)
    first,claim=scope();gate=Admission(engine,allowance,first,lambda:NOW)
    assert gate.run('interpret',0,input_tokens=1,output_tokens=1,invoke=lambda:ProviderResult('ok'))=='ok'
    finish_interaction(engine,claim,now=NOW)
    retry,_=scope(first.workspace_id)
    with pytest.raises(DomainError) as exhausted:
        Admission(engine,allowance,retry,lambda:NOW).reserve('interpret',0,input_tokens=1,output_tokens=1)
    assert exhausted.value.code=='AI_BUDGET_LIMIT'
    with pytest.raises(DomainError) as expired:
        Admission(engine,allowance,retry,lambda:NOW+timedelta(hours=2)).reserve('interpret',0,input_tokens=1,output_tokens=1)
    assert expired.value.code=='AI_BUDGET_EXPIRED'


def test_interaction_limits_and_generation_fence_include_failures(setup_admission):
    engine,_,scope=setup_admission
    current,claim=scope()
    with Session(engine) as db,db.begin():
        workspace=db.get(Workspace,current.workspace_id);check_interaction(db,claim,workspace,NOW)
        workspace.generation+=1
    with Session(engine) as db,pytest.raises(DomainError):
        check_interaction(db,claim,db.get(Workspace,current.workspace_id),NOW)
    finish_interaction(engine,claim,now=NOW)
    with Session(engine) as db,db.begin():
        workspace=db.get(Workspace,current.workspace_id)
        for _ in range(199):
            db.add(AIInteraction(workspace_id=workspace.id,generation=workspace.generation,revision=workspace.revision,
                command_key=str(uuid4()),request_hash='0'*64,operation='chat',profile_id=FAKE_SPEC.profile_id,
                manifest_ids={},state='failed',lease_until=NOW))
    with pytest.raises(DomainError) as limited:scope(current.workspace_id)
    assert limited.value.code=='DEMO_LIMIT'


def test_four_turn_and_two_ingestion_admission_are_shared(setup_admission):
    engine,_,scope=setup_admission
    claims=[scope(operation='replace')[1],scope(operation='replace')[1]]
    with pytest.raises(DomainError) as ingestion:scope(operation='replace')
    assert ingestion.value.code=='ASSISTANT_BUSY'
    claims.extend([scope()[1],scope()[1]])
    with pytest.raises(DomainError) as turns:scope()
    assert turns.value.code=='ASSISTANT_BUSY'
    for claim in claims:finish_interaction(engine,claim,now=NOW)
    assert scope()[1]


def test_usage_overrun_blocks_grant_without_refunding_or_repeating(setup_admission):
    engine,grant,scope=setup_admission
    allowance=grant();current,_=scope();gate=Admission(engine,allowance,current,lambda:NOW)
    with pytest.raises(DomainError) as overrun:
        gate.run('interpret',0,input_tokens=1,output_tokens=1,invoke=lambda:ProviderResult('unusable',SafeUsage(2,1)))
    assert overrun.value.code=='AI_GRANT_REVIEW'
    with Session(engine) as db:
        row=db.get(AIGrant,allowance.grant_id)
        assert row.blocked and row.requests==1 and row.cost_micros==2
        attempt=repo_first(db, AIAttempt, filters={'grant_id': row.id})
        assert attempt.state=='unknown' and attempt.actual_input_tokens==2
    with pytest.raises(DomainError) as blocked:gate.reserve('evidence',0,input_tokens=1,output_tokens=1)
    assert blocked.value.code=='AI_GRANT_REVIEW'


def test_absolute_deadline_stops_next_phase_but_records_late_usage(setup_admission):
    engine,grant,scope=setup_admission
    allowance=grant();current,_=scope();monotonic=[0.];calls=[]
    gate=Admission(engine,allowance,current,lambda:NOW,monotonic_deadline=5.,monotonic_clock=lambda:monotonic[0])
    def late():
        calls.append(1);monotonic[0]=6.;return ProviderResult('late',SafeUsage(1,1))
    with pytest.raises(DomainError) as expired:gate.run('interpret',0,input_tokens=1,output_tokens=1,invoke=late)
    assert expired.value.code=='ASSISTANT_TIMEOUT'
    with pytest.raises(DomainError):gate.run('evidence',0,input_tokens=1,output_tokens=1,invoke=late)
    assert calls==[1]
    with Session(engine) as db:
        assert db.get(AIGrant,allowance.grant_id).requests==1
        attempt=repo_first(db, AIAttempt, filters={'grant_id': allowance.grant_id})
        assert attempt.state=='completed' and attempt.actual_input_tokens==1


def test_operator_preparation_has_finite_global_not_guest_vector_allowance(setup_admission):
    engine,grant,_=setup_admission
    allowance=grant(vectors=2,workspace_vectors=1)
    gate=Admission(engine,allowance,AttemptScope(None,0,str(uuid4())),lambda:NOW)
    assert gate.run('ingest_embed',0,input_tokens=2,vectors=2,invoke=lambda:ProviderResult('prepared'))=='prepared'
    with pytest.raises(DomainError) as exhausted:
        gate.reserve('ingest_embed',1,input_tokens=1,vectors=1)
    assert exhausted.value.code=='AI_BUDGET_LIMIT'
