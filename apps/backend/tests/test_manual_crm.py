"""Local owner CRM policy; synthetic HTTP and isolated PostgreSQL only."""
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from test_live_crm import config_values
from test_settings import values

from choreograph import runtime_config, settings
from choreograph.acceptance import execute_crm
from choreograph.crm_admission import CRMAdmission, ManualCRMAllowance
from choreograph.crm_composition import compose_crm
from choreograph.errors import DomainError
from choreograph.hubspot import CRMFailure
from choreograph.models import CRMCall, CRMGrant
from choreograph.readiness import hubspot_report


def local_values():
    return {'DATABASE_ENABLED':'true',**values(),**config_values(),'FAKE_MODE':'true','PAID_DEMO_ENABLED':'false',
            'CHOREOGRAPH_ORIGIN':'http://localhost:45860','CHOREOGRAPH_CRM_PROVIDER':'hubspot',
            'CHOREOGRAPH_DATABASE_URL':'postgresql+psycopg://fixture:fixture@localhost:45862/choreograph'}


def test_local_loader_selects_manual_but_environment_and_acceptance_remain_finite(tmp_path,monkeypatch):
    fixture=local_values()
    policy={**runtime_config.APPLICATION,**{k:v for k,v in fixture.items() if k not in runtime_config.ENV_FIELDS},
            **{k:'' for k in ('CHOREOGRAPH_CRM_GRANT_ID','CHOREOGRAPH_CRM_EXPIRES_AT',
                             'CHOREOGRAPH_CRM_REQUESTS','CHOREOGRAPH_CRM_WORKSPACE_REQUESTS')}}
    policy.pop('CHOREOGRAPH_CRM_PROVIDER')
    policy.pop('CHOREOGRAPH_HUBSPOT_REDIRECT_URI')
    monkeypatch.setattr(runtime_config,'APPLICATION',policy)
    private={k:v for k,v in fixture.items() if k in runtime_config.ENV_FIELDS}
    backend=tmp_path/'backend';backend.mkdir()
    (backend/'.env.local').write_text('\n'.join(f'{k}={v}' for k,v in private.items()))
    monkeypatch.setattr(settings,'__file__',str(backend/'choreograph/settings.py'))
    configured=settings.load_local()
    assert isinstance(configured.live_crm.allowance,ManualCRMAllowance)
    assert configured.live_crm.allowance.expires_at is configured.live_crm.allowance.requests is None
    assert configured.live_crm.allowance.grant_id==runtime_config.LOCAL_MANUAL_CRM_GRANT_ID
    with pytest.raises(ValueError,match='CRM_CONFIGURATION_INVALID'):settings.load_environment(private)
    report=hubspot_report(private,application=policy,local_manual_crm_grant_id='synthetic-manual')
    assert report['configuration_ready'] and not report['missing'] and report['provider_calls']==0
    assert report['crm_policy']=='local_owner_manual'
    calls=[]
    http=httpx.Client(transport=httpx.MockTransport(lambda request:calls.append(request)))
    provider=compose_crm(configured,object(),client=http,clock=lambda:datetime(2091,1,1,tzinfo=UTC))
    try:
        assert provider.requires_admission and not calls
        with pytest.raises(DomainError,match='ACCEPTANCE_GRANT_INVALID'):
            execute_crm(object(),configured,uuid4(),uuid4(),'456','sync',provider=provider,injected=True)
    finally:http.close()
    assert not calls


@pytest.mark.parametrize('changes',[
    {'DATABASE_ENABLED':'true','CHOREOGRAPH_DATABASE_URL':'postgresql+psycopg://fixture:fixture@remote.invalid:45862/choreograph'},
    {'DATABASE_ENABLED':'true','CHOREOGRAPH_DATABASE_URL':'postgresql+psycopg://fixture:fixture@localhost:5432/choreograph'},
    {'DATABASE_ENABLED':'true','CHOREOGRAPH_DATABASE_URL':'postgresql+psycopg://fixture:fixture@localhost:45862/another_database'},
    {'CHOREOGRAPH_ORIGIN':'https://example.invalid'},
])
def test_manual_crm_cannot_escape_owned_local_target(changes):
    with pytest.raises(ValueError,match='LOCAL_MANUAL_CRM_ONLY'):
        settings.Settings.parse({**local_values(),**changes},local_manual_crm_grant_id='synthetic-manual')


def test_manual_crm_keeps_durable_counts_and_app_binding_without_ceiling_or_expiry(database):
    engine,_=database
    policy=ManualCRMAllowance('synthetic-manual-'+uuid4().hex,'123')
    scope=uuid4()
    def clock():return datetime(2091,1,1,tzinfo=UTC)
    try:
        CRMAdmission(engine,policy,scope,clock).reserve()
        with Session(engine) as db,db.begin():db.get(CRMGrant,policy.grant_id).requests=1_000_000
        CRMAdmission(engine,policy,scope,clock).reserve()
        with Session(engine) as db:
            assert db.get(CRMGrant,policy.grant_id).requests==1_000_001
            assert db.scalar(select(func.count()).select_from(CRMCall).where(CRMCall.grant_id==policy.grant_id))==2
        with pytest.raises(CRMFailure,match='CRM_ALLOWANCE_CHANGED'):
            CRMAdmission(engine,replace(policy,app_id='124'),scope,clock).reserve()
    finally:
        with Session(engine) as db,db.begin():
            db.execute(delete(CRMCall).where(CRMCall.grant_id==policy.grant_id))
            db.execute(delete(CRMGrant).where(CRMGrant.id==policy.grant_id))
