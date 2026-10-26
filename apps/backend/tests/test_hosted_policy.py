"""Owner dashboard hosting policy; injected providers and encrypted objects only."""
import base64
import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from choreograph.ai_admission import (
    FAKE_SPEC,
    Admission,
    AttemptScope,
    DashboardGrantSpec,
    ProviderResult,
    SafeUsage,
    claim_interaction,
)
from choreograph.crm_admission import CRMAdmission, HostedVisitorCRMAllowance
from choreograph.errors import DomainError
from choreograph.hubspot import CRMFailure
from choreograph.models import AIGrant, CRMGrant
from choreograph.object_store import FileObjects, ObjectEngine
from choreograph.persistence import Session
from choreograph.readiness import report
from choreograph.runtime_config import (
    HOSTED_DASHBOARD_AI_GRANT_ID,
    HOSTED_FRONTEND_ORIGIN,
    HOSTED_VISITOR_CRM_GRANT_ID,
    configuration_values,
    container_policy_ids,
)
from choreograph.sessions import create_workspace
from choreograph.settings import Settings, load_environment


def hosted_values():
    return {'DATABASE_ENABLED':'false','FAKE_MODE':'false','PAID_DEMO_ENABLED':'true',
        'CHOREOGRAPH_ORIGIN':HOSTED_FRONTEND_ORIGIN,
        'CHOREOGRAPH_BRIDGE_SECRET':'synthetic-bridge-'+'x'*40,
        'CHOREOGRAPH_TOKEN_KEY':base64.urlsafe_b64encode(bytes(32)).decode(),
        'OPENAI_API_KEY':'synthetic-no-network-key',
        'CHOREOGRAPH_HUBSPOT_CLIENT_SECRET':'synthetic-no-network-secret'}


def test_container_uses_distinct_hosted_policies_without_renewing_finite_or_local_grants():
    values=hosted_values();configured=load_environment(values)
    assert configured.object_backend=='gcs' and not configured.database_enabled
    assert isinstance(configured.live_ai.grant,DashboardGrantSpec)
    assert configured.live_ai.grant.grant_id==HOSTED_DASHBOARD_AI_GRANT_ID
    assert configured.live_ai.grant.expires_at is None
    assert isinstance(configured.live_crm.allowance,HostedVisitorCRMAllowance)
    assert configured.live_crm.allowance.grant_id==HOSTED_VISITOR_CRM_GRANT_ID
    assert configured.live_crm.allowance.expires_at is None
    assert configured.live_crm.transport.redirect_uri==HOSTED_FRONTEND_ORIGIN+'/auth/hubspot/callback'
    ai_id,crm_id=container_policy_ids(values)
    readiness=report(values,hosted_ai_grant_id=ai_id,hosted_crm_grant_id=crm_id)
    assert readiness['configuration']['ready'] and not readiness['missing']
    assert readiness['configuration']['ai_policy']=='owner_dashboard_hosted'
    assert readiness['configuration']['crm_policy']=='hosted_visitor'
    assert readiness['provider_calls']==0
    with pytest.raises(ValueError,match='LIVE_AI_GRANT_EXPIRED'):
        Settings.parse(configuration_values(values))
    with pytest.raises(ValueError,match='LOCAL_MANUAL_STORAGE_ONLY'):
        Settings.parse(configuration_values(values),local_manual_grant_id='synthetic-manual')


@pytest.mark.parametrize('changes',[
    {'CHOREOGRAPH_ORIGIN':'https://another.example'},
    {'CHOREOGRAPH_ORIGIN':'http://localhost:45860'},
    {'DATABASE_ENABLED':'true','CHOREOGRAPH_DATABASE_URL':
        'postgresql+psycopg://fixture:fixture@127.0.0.1:45862/choreograph_test_config'},
])
def test_hosted_policy_is_not_exported_to_another_origin_or_storage(changes):
    values={**hosted_values(),**changes}
    assert container_policy_ids(values)==(None,None)
    with pytest.raises(ValueError,match='LIVE_AI_GRANT_EXPIRED'):
        load_environment(values)
    with pytest.raises(ValueError,match='HOSTED_POLICY_TARGET_INVALID'):
        Settings.parse(configuration_values(values),hosted_ai_grant_id=HOSTED_DASHBOARD_AI_GRANT_ID)


def test_hosted_policy_keeps_test_mode_key_and_paid_switch_validation():
    values=hosted_values();ai_id,crm_id=container_policy_ids(values)
    with pytest.raises(ValueError,match='TEST_PROVIDER_FORBIDDEN'):
        Settings.parse(configuration_values(values),testing=True,hosted_ai_grant_id=ai_id,hosted_crm_grant_id=crm_id)
    with pytest.raises(ValueError,match='LIVE_AI_NOT_ENABLED'):
        load_environment({**values,'PAID_DEMO_ENABLED':'false'})
    with pytest.raises(ValueError,match='LIVE_AI_CONFIGURATION_INVALID'):
        load_environment({**values,'OPENAI_API_KEY':''})
    with pytest.raises(ValueError,match='HOSTED_POLICY_TARGET_INVALID'):
        Settings.parse(configuration_values(values),hosted_ai_grant_id=ai_id,local_manual_grant_id='synthetic')
    worker=load_environment({**values,'FAKE_MODE':'true','PAID_DEMO_ENABLED':'false'})
    assert worker.live_ai is None and isinstance(worker.live_crm.allowance,HostedVisitorCRMAllowance)


def test_hosted_accounting_survives_restart_without_app_budget_but_fences_replay_and_operator(tmp_path):
    from choreograph.knowledge import prepare_samples
    values=hosted_values();settings=load_environment(values);key=values['CHOREOGRAPH_TOKEN_KEY']
    path=tmp_path/'private';engine=ObjectEngine(FileObjects(path),key)
    now=datetime(2091,1,1,tzinfo=UTC)
    with Session(engine) as db,db.begin():
        prepare_samples(db,now)
        workspace,_=create_workspace(db,'UTC',now)
        scope=AttemptScope(workspace.id,workspace.generation,str(uuid4()),workspace.revision)
    claim_interaction(engine,scope,operation='chat',request_hash=hashlib.sha256(b'hosted').hexdigest(),
        profile_id=FAKE_SPEC.profile_id,manifest_ids={},now=now)
    grant=settings.live_ai.grant
    assert Admission(engine,grant,scope,lambda:now).run('interpret',0,input_tokens=1_000_000,output_tokens=10_000,
        invoke=lambda:ProviderResult('ok',SafeUsage(10,2)))=='ok'
    CRMAdmission(engine,settings.live_crm.allowance,scope.workspace_id,lambda:now).reserve()
    with Session(engine) as db,db.begin():
        ai=db.get(AIGrant,grant.grant_id)
        assert ai.expires_at is None and ai.spec['policy']=='owner_dashboard_hosted'
        assert ai.cost_micros>1_000_000
        ai.requests=1_000_000
        db.get(CRMGrant,settings.live_crm.allowance.grant_id).requests=1_000_000
    engine.dispose();engine=ObjectEngine(FileObjects(path),key)
    try:
        assert Admission(engine,grant,scope,lambda:now).run('evidence',0,input_tokens=1,output_tokens=1,
            invoke=lambda:ProviderResult('next',SafeUsage(1,1)))=='next'
        CRMAdmission(engine,settings.live_crm.allowance,scope.workspace_id,lambda:now).reserve()
        with Session(engine) as db:
            assert db.get(AIGrant,grant.grant_id).requests==1_000_001
            assert db.get(CRMGrant,settings.live_crm.allowance.grant_id).requests==1_000_001
        with pytest.raises(DomainError,match='AI_ATTEMPT_USED'):
            Admission(engine,grant,scope,lambda:now).reserve('interpret',0,input_tokens=1,output_tokens=1)
        with pytest.raises(DomainError,match='AI_WORKSPACE_REQUIRED'):
            Admission(engine,grant,AttemptScope(None,0,str(uuid4())),lambda:now).reserve(
                'ingest_embed',0,input_tokens=1,vectors=1)
        with pytest.raises(CRMFailure,match='CRM_ALLOWANCE_CHANGED'):
            CRMAdmission(engine,replace(settings.live_crm.allowance,app_id='another'),scope.workspace_id,lambda:now).reserve()
    finally:engine.dispose()
