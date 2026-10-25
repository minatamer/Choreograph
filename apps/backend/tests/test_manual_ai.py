"""Owner manual local policy uses injected providers and isolated PostgreSQL."""
import hashlib
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from test_ai_config import live_values
from test_composition import CountingTransport

from choreograph import settings
from choreograph.ai_admission import (
    FAKE_SPEC,
    Admission,
    AttemptScope,
    ManualGrantSpec,
    ProviderResult,
    SafeUsage,
    claim_interaction,
)
from choreograph.composition import compose_ai
from choreograph.errors import DomainError
from choreograph.models import AIAttempt, AIGrant, Workspace
from choreograph.runtime_config import ENV_FIELDS, LOCAL_MANUAL_AI_GRANT_ID, configuration_values
from choreograph.sessions import create_workspace


def local_values():
    return {'DATABASE_ENABLED':'true',**live_values(),'CHOREOGRAPH_DATABASE_URL':
            'postgresql+psycopg://fixture:fixture@127.0.0.1:45862/choreograph'}


def test_actual_local_loader_selects_manual_but_environment_stays_finite(tmp_path,monkeypatch):
    backend=tmp_path/'backend'
    backend.mkdir()
    private={key:value for key,value in local_values().items() if key in ENV_FIELDS}
    path=backend/'.env.local'
    path.write_text('\n'.join(f'{key}={value}' for key,value in private.items()))
    monkeypatch.setattr(settings,'__file__',str(backend/'choreograph/settings.py'))
    manual=settings.load_local()
    assert isinstance(manual.live_ai.grant,ManualGrantSpec)
    assert manual.live_ai.grant.grant_id==LOCAL_MANUAL_AI_GRANT_ID
    assert manual.live_ai.grant.expires_at is None
    assert manual.live_ai.spec.profile_id=='43374774b0d3a0b95aac6083cd3d2720ed3d4eb809e540c32af27eb9628fdd9b'
    from choreograph.readiness import report
    assert report(private,local_manual_grant_id=LOCAL_MANUAL_AI_GRANT_ID)['configuration']['ai_policy']=='local_owner_manual'
    assert report(private)['configuration']['code']=='LIVE_AI_GRANT_EXPIRED'
    with pytest.raises(ValueError,match='LIVE_AI_GRANT_EXPIRED'):
        settings.load_environment(private)
    with pytest.raises(ValueError,match='LIVE_AI_NOT_ENABLED'):
        settings.Settings.parse(configuration_values({**private,'PAID_DEMO_ENABLED':'false'}),
                                local_manual_grant_id=LOCAL_MANUAL_AI_GRANT_ID)
    with pytest.raises(ValueError,match='LIVE_AI_CONFIGURATION_INVALID'):
        settings.Settings.parse(configuration_values({**private,'OPENAI_API_KEY':''}),
                                local_manual_grant_id=LOCAL_MANUAL_AI_GRANT_ID)
    assert settings.Settings.parse(configuration_values({**private,'FAKE_MODE':'true'}),
                                   local_manual_grant_id=LOCAL_MANUAL_AI_GRANT_ID).live_ai is None


@pytest.mark.parametrize('changes',[
    {'CHOREOGRAPH_ORIGIN':'https://example.invalid'},
    {'DATABASE_ENABLED':'true','CHOREOGRAPH_DATABASE_URL':'postgresql+psycopg://fixture:fixture@database.example.invalid:45862/choreograph'},
    {'DATABASE_ENABLED':'true','CHOREOGRAPH_DATABASE_URL':'postgresql+psycopg://fixture:fixture@127.0.0.1:5432/choreograph'},
    {'DATABASE_ENABLED':'true','CHOREOGRAPH_DATABASE_URL':'postgresql+psycopg://fixture:fixture@127.0.0.1:45862/another_database'},
])
def test_manual_policy_is_rejected_outside_owned_loopback(changes):
    with pytest.raises(ValueError,match='LOCAL_MANUAL_AI_ONLY'):
        settings.Settings.parse({**local_values(),**changes},local_manual_grant_id='synthetic-manual')


def test_manual_composition_constructs_clients_without_requests_and_keeps_admission():
    from choreograph.acceptance import execute_ai
    response,embedding=CountingTransport(),CountingTransport()
    config=settings.Settings.parse(local_values(),local_manual_grant_id='synthetic-manual')
    runtime=compose_ai(config,object(),response_transport=response,embedding_transport=embedding,
                       clock=lambda:datetime(2091,1,1,tzinfo=UTC))
    try:
        assert not response.requests and not embedding.requests
        scoped=runtime.for_scope(AttemptScope(uuid4(),1,str(uuid4()),1))
        assert isinstance(scoped.admission.grant,ManualGrantSpec)
        assert scoped.assistant.admission is scoped.admission
        assert scoped.embedder._admission is scoped.admission
        with pytest.raises(DomainError,match='ACCEPTANCE_GRANT_INVALID'):
            execute_ai(object(),config,uuid4(),'evaluate',1,runtime=runtime,injected=True)
    finally:runtime.close()
    assert response.closes==embedding.closes==1


def test_manual_accounting_has_no_ceiling_or_expiry_but_replay_and_downgrade_are_fenced(database):
    from choreograph.migrate import downgrade
    engine,_=database
    # A date beyond both historical grants and ordinary fixture grants proves
    # this policy has no expiry, rather than a replacement future deadline.
    now=datetime(2091,1,1,tzinfo=UTC)
    policy=ManualGrantSpec('synthetic-manual-'+uuid4().hex,'synthetic-response','synthetic-embedding',
                           2_500_000,10_000_000,20_000)
    with Session(engine) as db,db.begin():
        workspace,_=create_workspace(db,'UTC',now)
        workspace_id=workspace.id
        scope=AttemptScope(workspace.id,workspace.generation,str(uuid4()),workspace.revision)
    claim_interaction(engine,scope,operation='chat',request_hash=hashlib.sha256(b'manual').hexdigest(),
                      profile_id=FAKE_SPEC.profile_id,manifest_ids={},now=now)
    try:
        gate=Admission(engine,policy,scope,lambda:now)
        assert gate.run('interpret',0,input_tokens=1_000_000,output_tokens=10_000,
                        invoke=lambda:ProviderResult('ok',SafeUsage(10,2)))=='ok'
        with Session(engine) as db,db.begin():
            row=db.get(AIGrant,policy.grant_id)
            assert row.expires_at is None and row.cost_micros==2_600_000
            assert row.spec['policy']=='local_owner_manual'
            assert not any(key in row.spec for key in ('requests','cost_micros','workspace_requests'))
            row.requests=1_000_000
        assert Admission(engine,policy,scope,lambda:now).run('evidence',0,input_tokens=1_000_000,output_tokens=10_000,
                    invoke=lambda:ProviderResult('next',SafeUsage(10,2)))=='next'
        with Session(engine) as db:
            row=db.get(AIGrant,policy.grant_id)
            assert row.requests==1_000_001 and row.cost_micros==5_200_000
            assert len(list(db.scalars(select(AIAttempt).where(AIAttempt.grant_id==row.id))))==2
        with pytest.raises(DomainError,match='AI_ATTEMPT_USED'):
            Admission(engine,policy,scope,lambda:now).reserve('interpret',0,input_tokens=1,output_tokens=1)
        with pytest.raises(DomainError,match='AI_MANUAL_WORKSPACE_REQUIRED'):
            Admission(engine,policy,AttemptScope(None,0,str(uuid4())),lambda:now).reserve(
                'ingest_embed',0,input_tokens=1,vectors=1)
        with pytest.raises(RuntimeError,match='MANUAL_AI_POLICY_DOWNGRADE_FORBIDDEN'):
            downgrade(engine,'0010')
    finally:
        with Session(engine) as db,db.begin():
            db.execute(delete(Workspace).where(Workspace.id==workspace_id))
            db.execute(delete(AIAttempt).where(AIAttempt.grant_id==policy.grant_id))
            db.execute(delete(AIGrant).where(AIGrant.id==policy.grant_id))
