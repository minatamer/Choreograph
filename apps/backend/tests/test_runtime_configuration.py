"""External configuration cannot grow switches or override reviewed provider policy."""
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from test_ai_config import live_values
from test_settings import values as private_values

from choreograph import runtime_config
from choreograph.ai_config import parse_live_ai
from choreograph.runtime_config import APPLICATION, ENV_FIELDS, configuration_values
from choreograph.settings import Settings, load_environment


def test_no_key_ci_generator_and_job_environment_load_fake_only(tmp_path, monkeypatch):
    """Run the checked-in CI generator, never a copied fixture or checkout env."""
    from dotenv import dotenv_values

    from choreograph import settings
    root=Path(__file__).resolve().parents[3]
    job=yaml.safe_load((root/'.github/workflows/ci.yml').read_text())['jobs']['verify']
    step=next(step for step in job['steps'] if step['name']=='Create disposable fake-only configuration')
    generator=re.search(r"python - <<'PY'\n(.*?)\nPY",step['run'],re.S).group(1)
    backend=tmp_path/'apps/backend'
    backend.mkdir(parents=True)
    completed=subprocess.run([sys.executable,'-I','-c',generator],cwd=tmp_path,capture_output=True,check=True)
    values=dotenv_values(backend/'.env.local',interpolate=False)
    # Job-level values also reach container/migration commands. Both boundaries
    # must reject accidental live mode even when the developer has live keys.
    configured=load_environment({**values,**job['env']})
    monkeypatch.setattr(settings,'__file__',str(backend/'choreograph/settings.py'))
    local=settings.load_local()
    assert configured.profile==local.profile=='fake'
    assert configured.live_ai is local.live_ai is None
    assert configured.crm_provider==local.crm_provider=='disabled'
    assert not values.get('OPENAI_API_KEY') and values['PAID_DEMO_ENABLED']=='false'
    assert values['FAKE_MODE']=='true'
    assert b'values omitted' in completed.stdout
    assert values['CHOREOGRAPH_BRIDGE_SECRET'].encode() not in completed.stdout


def test_external_loaders_use_fixed_code_policy_with_only_private_values(monkeypatch):
    fixture=live_values()
    monkeypatch.setattr(runtime_config,'APPLICATION',{key:value for key,value in fixture.items() if key not in ENV_FIELDS})
    private={key:value for key,value in fixture.items() if key in ENV_FIELDS}
    monkeypatch.setenv('CHOREOGRAPH_AI_EMBEDDING_DIMENSIONS','3072')
    configured=load_environment(private)
    assert configured.profile=='live' and configured.live_ai.spec.dimensions==128
    assert configured.live_ai.api_key==private['OPENAI_API_KEY']
    assert configured.crm_provider=='disabled'


@pytest.mark.parametrize('name',['CHOREOGRAPH_PROFILE','CHOREOGRAPH_AI_PAID_ENABLED','CHOREOGRAPH_OPENAI_API_KEY',
    'CHOREOGRAPH_AI_EMBEDDING_DIMENSIONS','CHOREOGRAPH_AI_RESPONSE_MODEL','CHOREOGRAPH_AI_EXPIRES_AT',
    'CHOREOGRAPH_CRM_PROVIDER','CHOREOGRAPH_CRM_ENABLED','CHOREOGRAPH_HUBSPOT_CLIENT_ID',
    'CHOREOGRAPH_HUBSPOT_REDIRECT_URI'])
def test_external_env_cannot_restore_aliases_or_change_fixed_policy(name):
    with pytest.raises(ValueError,match='CONFIGURATION'):
        load_environment({**private_values(),name:'override-marker'})


def test_moving_policy_preserves_live_vectors_and_expired_grant_without_renewal():
    config=configuration_values({'FAKE_MODE':'false','PAID_DEMO_ENABLED':'true','OPENAI_API_KEY':'synthetic'})
    approved=parse_live_ai(config,now=datetime(2026,10,24,13,tzinfo=UTC))
    assert approved.spec.profile_id=='43374774b0d3a0b95aac6083cd3d2720ed3d4eb809e540c32af27eb9628fdd9b'
    assert approved.grant.grant_id=='sbs023-9847f916-cfe7-4454-97e5-b3fc4eb50fcd'
    assert approved.grant.cost_micros==1_000_000
    assert approved.grant.expires_at==datetime(2026,10,24,13,28,49,844016,tzinfo=UTC)
    for _ in range(2):
        with pytest.raises(ValueError,match='LIVE_AI_GRANT_EXPIRED'):
            parse_live_ai(configuration_values({'PAID_DEMO_ENABLED':'true','OPENAI_API_KEY':'synthetic'}),
                now=datetime(2026,10,24,14,tzinfo=UTC))


def test_hubspot_auto_availability_needs_app_registration_and_its_secret_not_a_visitor_key():
    from test_live_crm import config_values
    synthetic=config_values()
    policy={**APPLICATION,**{key:value for key,value in synthetic.items() if key!='CHOREOGRAPH_HUBSPOT_CLIENT_SECRET'}}
    private={**private_values(),'FAKE_MODE':'true','PAID_DEMO_ENABLED':'false',
             'CHOREOGRAPH_ORIGIN':'http://localhost:45860','CHOREOGRAPH_HUBSPOT_CLIENT_SECRET':'synthetic-secret'}
    ready=configuration_values(private,application=policy)
    configured=Settings.parse(ready)
    assert configured.profile=='fake' and configured.crm_provider=='hubspot'
    assert configured.live_crm.transport.redirect_uri=='http://localhost:45860/auth/hubspot/callback'
    assert Settings.parse(configuration_values({**private,'CHOREOGRAPH_HUBSPOT_CLIENT_SECRET':''},application=policy)).crm_provider=='disabled'
    assert Settings.parse(configuration_values(private,application={**APPLICATION,
        'CHOREOGRAPH_HUBSPOT_APP_ID':'','CHOREOGRAPH_HUBSPOT_CLIENT_ID':''})).crm_provider=='disabled'
