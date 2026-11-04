"""Reviewed, nonsecret application policy. No file/environment/network access.

Env files hold credentials, connection addresses and the three mode switches.
These values are code configuration, not additional runtime switches.
"""
from types import MappingProxyType

# One-time Choreograph OAuth app registration, shared by the Connect button.
# Public identifiers, NOT a visitor account ID or personal CRM API token.
# Private object bucket; provision only through the reviewed deployment runbook.
OBJECT_BUCKET = 'choreograph-512713-private-state'

HUBSPOT_APP_ID = '58593051'
HUBSPOT_CLIENT_ID = 'e797c71e-5806-4b02-ac65-a1e7c64fd539'

# Owner25 October2026: a genuine human check covers subsequent chat in the
# same guest workspace briefly. This is separate from AI spending authority.
CHAT_VERIFICATION_SECONDS = 30 * 60

# Owner instruction25 October2026: local manual UI use has no budget/deadline.
# Selected ONLY by load_local; containers and automated acceptance stay finite.
# This does not authorize agent-run paid requests or operator sample ingestion.
LOCAL_MANUAL_AI_GRANT_ID = 'owner-manual-local-20261025'
LOCAL_MANUAL_CRM_GRANT_ID = 'owner-manual-hubspot-local-20261025'

# Owner26 October2026: normal hosted AI spending is controlled on the provider
# dashboard. These stable accounting identities have no app aggregate budget or
# expiry; historical finite test grants below are not renewed or repurposed.
# Owner4 November2026: canonical custom domain; retired run.app is not an
# alternate provider-policy origin. Durable accounting identities stay unchanged.
HOSTED_FRONTEND_ORIGIN = 'https://trychoreograph.com'
HOSTED_DASHBOARD_AI_GRANT_ID = 'owner-dashboard-hosted-20261026'
HOSTED_VISITOR_CRM_GRANT_ID = 'visitor-hubspot-hosted-20261026'


def container_policy_ids(values):
    """Only the selected no-database deployment uses normal hosted policies."""
    if (values.get('CHOREOGRAPH_ORIGIN') != HOSTED_FRONTEND_ORIGIN or
            values.get('DATABASE_ENABLED', 'false') != 'false'):
        return None, None
    ai = HOSTED_DASHBOARD_AI_GRANT_ID if values.get('FAKE_MODE', 'true') == 'false' else None
    return ai, HOSTED_VISITOR_CRM_GRANT_ID

# Reviewed24 October2026; preserve the prepared1536-dimensional source profile.
# The input rate includes conservative cache-write headroom ($2.50/M tokens).
APPLICATION = MappingProxyType({
    'CHOREOGRAPH_AI_RESPONSE_MODEL': 'gpt-6.1-sol',
    'CHOREOGRAPH_AI_REASONING_EFFORT': 'low',
    'CHOREOGRAPH_AI_EMBEDDING_MODEL': 'text-embedding-3-small',
    'CHOREOGRAPH_AI_RESPONSE_TOKENIZER': 'utf8-upper-v1',
    'CHOREOGRAPH_AI_EMBEDDING_TOKENIZER': 'cl100k_base',
    'CHOREOGRAPH_AI_EMBEDDING_DIMENSIONS': '1536',
    'CHOREOGRAPH_AI_CHUNKER': 'llama-token-section-v4',
    'CHOREOGRAPH_AI_RESPONSE_INPUT_RATE': '2500000',
    'CHOREOGRAPH_AI_RESPONSE_OUTPUT_RATE': '10000000',
    'CHOREOGRAPH_AI_EMBEDDING_INPUT_RATE': '20000',
    # Historical owner authorization, not a rolling allowance. It is expired.
    # Change this block ONLY after a new specific finite owner authorization.
    # Reusing the ID retains durable counters; restart never replenishes them.
    'CHOREOGRAPH_AI_GRANT_ID': 'sbs023-9847f916-cfe7-4454-97e5-b3fc4eb50fcd',
    'CHOREOGRAPH_AI_EXPIRES_AT': '2026-10-24T13:28:49.844016+00:00',
    'CHOREOGRAPH_AI_REQUESTS': '60',
    'CHOREOGRAPH_AI_INPUT_TOKENS': '250000',
    'CHOREOGRAPH_AI_OUTPUT_TOKENS': '40000',
    'CHOREOGRAPH_AI_VECTORS': '40',
    'CHOREOGRAPH_AI_COST_MICROS': '1000000',
    'CHOREOGRAPH_AI_WORKSPACE_REQUESTS': '60',
    'CHOREOGRAPH_AI_WORKSPACE_INPUT_TOKENS': '250000',
    'CHOREOGRAPH_AI_WORKSPACE_OUTPUT_TOKENS': '40000',
    'CHOREOGRAPH_AI_WORKSPACE_VECTORS': '40',
    'CHOREOGRAPH_AI_WORKSPACE_COST_MICROS': '1000000',
    'CHOREOGRAPH_HUBSPOT_APP_ID': HUBSPOT_APP_ID,
    'CHOREOGRAPH_HUBSPOT_CLIENT_ID': HUBSPOT_CLIENT_ID,
    'CHOREOGRAPH_HUBSPOT_DISTRIBUTION': 'marketplace_unlisted',
    'CHOREOGRAPH_HUBSPOT_CAPACITY': '25',
    # Schema changes still require the visitor's separate explicit setup consent.
    'CHOREOGRAPH_HUBSPOT_SCHEMA_SETUP_ALLOWED': 'true',
    # Automated/hosted acceptance still needs its own finite authorization.
    'CHOREOGRAPH_CRM_GRANT_ID': '',
    'CHOREOGRAPH_CRM_EXPIRES_AT': '',
    'CHOREOGRAPH_CRM_REQUESTS': '',
    'CHOREOGRAPH_CRM_WORKSPACE_REQUESTS': '',
})

ENV_FIELDS = frozenset({
    'DATABASE_ENABLED',
    'FAKE_MODE', 'PAID_DEMO_ENABLED', 'OPENAI_API_KEY',
    'TURNSTILE_SITE_KEY', 'TURNSTILE_SECRET_KEY',
    'CHOREOGRAPH_DB_PASSWORD', 'CHOREOGRAPH_DATABASE_URL', 'CHOREOGRAPH_ORIGIN',
    'CHOREOGRAPH_BRIDGE_SECRET', 'CHOREOGRAPH_TOKEN_KEY',
    'CHOREOGRAPH_HUBSPOT_CLIENT_SECRET',
})
REMOVED_ALIASES = frozenset({'CHOREOGRAPH_PROFILE', 'CHOREOGRAPH_AI_PAID_ENABLED', 'CHOREOGRAPH_OPENAI_API_KEY'})
MOVED_FIELDS = frozenset(APPLICATION) | {'CHOREOGRAPH_CRM_PROVIDER', 'CHOREOGRAPH_CRM_ENABLED',
    'CHOREOGRAPH_HUBSPOT_REDIRECT_URI', 'CHOREOGRAPH_AI_TOKENIZER_DIRECTORY', 'CHOREOGRAPH_TASKS_ENABLED'}


def configuration_values(values, *, application=None):
    """External loader boundary; fixed policy cannot be overridden by environment.

    Tests may explicitly inject synthetic code policy; never inherit a checkout's
    enabled providers or credentials. Settings.parse remains a pure internal parser.
    """
    if REMOVED_ALIASES.intersection(values):
        raise ValueError('LEGACY_CONFIGURATION_REMOVED')
    if (MOVED_FIELDS - {'CHOREOGRAPH_TASKS_ENABLED'}).intersection(values):
        raise ValueError('FIXED_CONFIGURATION_MOVED_TO_CODE')
    fixed = APPLICATION if application is None else application
    result = {**fixed, **{key: value for key, value in values.items() if key in ENV_FIELDS}}
    origin = result.get('CHOREOGRAPH_ORIGIN', 'http://127.0.0.1:45860')
    result['CHOREOGRAPH_HUBSPOT_REDIRECT_URI'] = origin + '/auth/hubspot/callback'
    ready = all(result.get(name) for name in ('CHOREOGRAPH_HUBSPOT_APP_ID',
        'CHOREOGRAPH_HUBSPOT_CLIENT_ID', 'CHOREOGRAPH_HUBSPOT_CLIENT_SECRET'))
    result['CHOREOGRAPH_CRM_PROVIDER'] = 'hubspot' if ready else 'disabled'
    return result
