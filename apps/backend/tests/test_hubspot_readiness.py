"""No-account setup diagnostics and the checked-in OAuth contract."""
import json
from pathlib import Path

import httpx
import pytest
from test_live_crm import config_values

from choreograph.hubspot import CURRENCY_PATH, SCOPES, CRMFailure, HubSpotConfig, HubSpotTransport
from choreograph.readiness import hubspot_report
from choreograph.runtime_config import APPLICATION


def test_crm_readiness_is_independent_of_paid_ai_and_never_exposes_values(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('CRM-only diagnostics must not compose or validate paid AI')
    monkeypatch.setattr('choreograph.settings.Settings.parse',forbidden)
    synthetic=config_values()
    policy={**APPLICATION,**{key:value for key,value in synthetic.items() if key!='CHOREOGRAPH_HUBSPOT_CLIENT_SECRET'},
            'CHOREOGRAPH_AI_EXPIRES_AT':'2020-01-01T00:00:00Z'}
    values={'CHOREOGRAPH_HUBSPOT_CLIENT_SECRET':synthetic['CHOREOGRAPH_HUBSPOT_CLIENT_SECRET'],'CHOREOGRAPH_ORIGIN':'http://localhost:45860',
            'FAKE_MODE':'false','PAID_DEMO_ENABLED':'true','OPENAI_API_KEY':'private-ai-marker',
            }
    report=hubspot_report(values,application=policy)
    assert report['configuration_ready'] and report['ai_independent'] and report['provider_calls']==0
    assert 'private-ai-marker' not in json.dumps(report) and 'synthetic-secret' not in json.dumps(report)
    disabled=hubspot_report({})
    assert disabled['code']=='CRM_DISABLED' and not disabled['configuration_ready']
    assert 'CHOREOGRAPH_HUBSPOT_CLIENT_SECRET' in disabled['missing']
    assert 'CHOREOGRAPH_ORIGIN' in disabled['changes_required']


def test_oauth_app_manifest_matches_real_transport_and_contains_no_paid_feature_or_secret():
    root=Path(__file__).resolve().parents[3]
    manifest=json.loads((root/'infra/hubspot/app-hsmeta.json').read_text())
    config=manifest['config'];auth=config['auth']
    assert config['distribution']=='marketplace' and auth['type']=='oauth'
    assert set(auth['requiredScopes'])==set(SCOPES)
    assert auth['redirectUrls']==['http://localhost:45860/auth/hubspot/callback']
    assert not auth['optionalScopes'] and not auth['conditionallyRequiredScopes']
    assert not any(term in scope for scope in auth['requiredScopes'] for term in ('marketing','payment','workflow','custom','currencies.write'))
    assert not any(key in json.dumps(manifest).lower() for key in ('clientsecret','client_secret','access_token','refresh_token'))


@pytest.mark.parametrize('currency',[{}, {'id':'EGP'}, {'id':None}, {'id':840}])
def test_unknown_or_non_usd_currency_never_reaches_schema_writes(currency):
    calls=[]
    def respond(request):calls.append(request);return httpx.Response(200,json=currency)
    http=httpx.Client(transport=httpx.MockTransport(respond))
    provider=HubSpotTransport(HubSpotConfig('123','synthetic','private-marker','http://localhost:45860/auth/hubspot/callback',
        schema_setup_allowed=True),authorized=True,client=http)
    try:
        with pytest.raises(CRMFailure,match='CRM_CURRENCY_REQUIRED'):provider.preflight({'access_token':'private-token'},allow_schema=True)
        assert [(request.method,request.url.path) for request in calls]==[('GET',CURRENCY_PATH)]
        with pytest.raises(CRMFailure,match='CRM_ROUTE'):provider._request('PUT',CURRENCY_PATH,json={'currencyCode':'USD'})
        assert len(calls)==1
    finally:http.close()
