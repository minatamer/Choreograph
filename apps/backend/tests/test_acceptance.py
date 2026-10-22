"""Operator tooling on actual isolated PG with explicitly metered fake providers."""
import json
import re
import time
from contextlib import ExitStack
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from conftest import database as database_fixture
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from choreograph import acceptance, knowledge, readiness, release
from choreograph.ai_admission import FAKE_SPEC, GrantSpec, ProviderResult, SafeUsage
from choreograph.assistant import FakeAssistant
from choreograph.composition import AIRuntime
from choreograph.errors import DomainError
from choreograph.models import AcceptanceRun, DocumentVersion, Workspace
from choreograph.providers import EvidenceQuote, GroundedOutput


@pytest.fixture
def database():
    fixture=database_fixture.__wrapped__()
    try:yield next(fixture)
    finally:fixture.close()


class MeteredAssistant(FakeAssistant):
    def __init__(self,gate=None):self.gate=gate
    def with_admission(self,gate):return MeteredAssistant(gate)
    def interpret(self,*args):
        return self.gate.run('interpret',0,input_tokens=100,output_tokens=100,
            invoke=lambda:ProviderResult(super(MeteredAssistant,self).interpret(*args),SafeUsage(100,100)))
    def evidence(self,*args):
        return self.gate.run('evidence',0,input_tokens=100,output_tokens=100,
            invoke=lambda:ProviderResult(self.fixture_evidence(*args),SafeUsage(100,100)))
    def fixture_evidence(self,question,hits):
        # Fixture decisions prove harness/source plumbing, never real model quality.
        if 'international flights' in question:return GroundedOutput(status='insufficient',claims=[])
        cases=json.loads((knowledge.PACK/'evaluation.json').read_text())
        expected=next((case for case in cases if case['question']==question),None)
        if expected:
            for hit in hits:
                for sentence in re.split(r'(?<=[.!?])\s+',hit.node.text):
                    if expected['contains'].lower() in sentence.lower() and hit.node.metadata['slot']==expected['slot'] and hit.node.metadata['page']==expected['page']:
                        return GroundedOutput(status='supported',claims=[EvidenceQuote(passage_id=hit.node.id_,excerpt=sentence)])
        return super().evidence(question,hits)


class MeteredEmbedding:
    spec=FAKE_SPEC
    def __init__(self,gate=None):self.gate=gate;self.fake=knowledge.FakeEmbedding();self.batch=0
    def with_admission(self,gate):return MeteredEmbedding(gate)
    def get_text_embedding_batch(self,values):
        result=[]
        for start in range(0,len(values),4):
            batch=values[start:start+4];number=self.batch;self.batch+=1
            result.extend(self.gate.run('ingest_embed',number,input_tokens=100,vectors=len(batch),
                invoke=lambda batch=batch:ProviderResult(self.fake.get_text_embedding_batch(batch),SafeUsage(100))))
        return result
    def get_query_embedding(self,value):
        return self.gate.run('query_embed',0,input_tokens=10,vectors=1,
            invoke=lambda:ProviderResult(self.fake.get_query_embedding(value),SafeUsage(10)))


def runtime_for(engine,now):
    grant=GrantSpec('acceptance-'+uuid4().hex,now+timedelta(hours=1),'metered-fake',FAKE_SPEC.model,
        78,336_864,42_000,88,1_000_000,78,336_864,42_000,88,1_000_000,1,1,1)
    return AIRuntime(MeteredAssistant(),MeteredEmbedding(),FAKE_SPEC,None,engine,grant,lambda:now,ExitStack())


def test_readiness_dry_run_and_bootstrap_do_not_construct_providers(monkeypatch):
    monkeypatch.setattr('choreograph.composition.compose_ai',lambda *_:pytest.fail('network composition'))
    result=readiness.report({'CHOREOGRAPH_PROFILE':'live'})
    assert result['provider_calls']==0 and 'CHOREOGRAPH_OPENAI_API_KEY' in result['missing']
    assert result['corpus']['ready']
    assert acceptance.dry_plan('ai','evaluate')['limits']['ingest_embed']==24
    client=TestClient(release.application('bootstrap',None,None,{}))
    assert client.get('/health').json()=={'status':'bootstrap','application_ready':False}
    assert client.get('/v1/session').status_code==404


def test_readiness_checks_actual_migration_and_shared_vectors(database):
    engine,_=database;now=datetime.now(UTC)
    assert readiness.database_status(engine,FAKE_SPEC)['code']=='KNOWLEDGE_NOT_READY'
    with Session(engine) as db,db.begin():knowledge.prepare_samples(db,now)
    assert readiness.database_status(engine,FAKE_SPEC)['ready']
    assert not readiness.database_status(engine,replace(FAKE_SPEC,model='other'))['ready']


def test_complete_injected_acceptance_retains_receipts_and_purges_private_sources(database):
    engine,settings=database;now=datetime(2026,10,22,9,tzinfo=UTC);runtime=runtime_for(engine,now)
    prepared=acceptance.execute_ai(engine,settings,uuid4(),'prepare',1_000_000,runtime=runtime,clock=lambda:now,injected=True)
    assert prepared['status']=='succeeded' and prepared['mode']=='injected'
    run_id=uuid4()
    try:result=acceptance.execute_ai(engine,settings,run_id,'evaluate',1_000_000,runtime=runtime,clock=lambda:now,injected=True)
    except DomainError:
        with Session(engine) as db:print('failed acceptance stage:',db.get(AcceptanceRun,run_id).counts.get('stage'))
        raise
    assert result['status']=='succeeded' and len(result['cases'])==24
    assert result['reserved']['query_embed']<=24 and result['reserved']['evidence']<=24
    with Session(engine) as db:
        row=db.get(AcceptanceRun,run_id)
        assert row.state=='succeeded' and len(row.counts['case_receipts'])==24
        ids=[UUID(value) for value in row.workspace_ids]
        assert len(ids)==2 and all(not db.get(Workspace,wid).active for wid in ids)
        assert not db.scalar(select(func.count()).select_from(DocumentVersion).where(DocumentVersion.owner_id.in_(ids)))
    with pytest.raises(DomainError,match='ACCEPTANCE_RUN_USED'):
        acceptance.execute_ai(engine,settings,run_id,'evaluate',1_000_000,runtime=runtime,clock=lambda:now,injected=True)


def test_failed_call_is_charged_and_replay_or_over_limit_never_invokes(database):
    engine,_=database;now=datetime.now(UTC);run_id=uuid4()
    acceptance.reserve_run(engine,run_id,'ai_evaluate','0'*64,now)
    class Inner:
        grant=runtime_for(engine,now)._grant
        def run(self,*args,**kwargs):raise RuntimeError('unknown outcome')
    meter=acceptance.RunAdmission(engine,run_id,Inner(),time.monotonic()+60,1_000_000)
    with pytest.raises(RuntimeError):meter.run('interpret',0,input_tokens=100,output_tokens=100,invoke=lambda:None)
    with Session(engine) as db:assert db.get(AcceptanceRun,run_id).counts['interpret']==1
    with pytest.raises(DomainError):meter.run('interpret',0,input_tokens=300_001,output_tokens=100,invoke=lambda:pytest.fail('unbounded'))
    acceptance.finish_run(engine,run_id,state='failed',clock=lambda:now)
    with pytest.raises(DomainError):meter.run('interpret',0,input_tokens=100,output_tokens=100,invoke=lambda:pytest.fail('replay'))


def test_initializer_rejects_remote_and_libpq_overrides_without_connection(monkeypatch):
    monkeypatch.setattr('sqlalchemy.create_engine',lambda *_args,**_kwargs:pytest.fail('unsafe connection'))
    for url in ['postgresql+psycopg://u:p@elsewhere:45862/choreograph',
                'postgresql+psycopg://u:p@127.0.0.1:45862/choreograph?host=elsewhere']:
        with pytest.raises(ValueError):acceptance.initialize_database({'CHOREOGRAPH_DATABASE_URL':url},uuid4())


def test_dry_cli_reads_no_env_file(monkeypatch,capsys):
    monkeypatch.setattr('sys.argv',['acceptance','crm','sync','--env-file','missing-file'])
    acceptance.main()
    assert json.loads(capsys.readouterr().out)['provider_calls']==0


def test_usage_reporting_failure_cannot_leave_success(database):
    engine,_=database;now=datetime.now(UTC);run_id=uuid4();grant=runtime_for(engine,now)._grant
    acceptance.reserve_run(engine,run_id,'ai_prepare','0'*64,now)
    def fail_usage(_connection,_cursor,statement,_params,_context,_many):
        if statement.lstrip().startswith('SELECT ai_attempts.'):raise RuntimeError('fixture database failure')
    event.listen(engine,'before_cursor_execute',fail_usage)
    try:
        with pytest.raises(DomainError,match='ACCEPTANCE_RECEIPT_FAILED'):
            acceptance.complete_ai_run(engine,run_id,grant,lambda:now)
    finally:event.remove(engine,'before_cursor_execute',fail_usage)
    with Session(engine) as db:
        row=db.get(AcceptanceRun,run_id)
        assert row.state=='failed' and row.counts['failure_code']=='ACCEPTANCE_RECEIPT_FAILED'
