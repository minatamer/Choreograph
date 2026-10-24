"""Reviewed, nonsecret application policy. No file/environment/network access.

Env files hold credentials, connection addresses and the two mode switches.
These values are code configuration, not additional runtime switches.
"""
from types import MappingProxyType

# One-time Choreograph OAuth app registration, shared by the Connect button.
# Public identifiers, NOT a visitor account ID or personal CRM API token.
HUBSPOT_APP_ID = ''
HUBSPOT_CLIENT_ID = ''

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
    'CHOREOGRAPH_HUBSPOT_SCHEMA_SETUP_ALLOWED': 'false',
    # No real HubSpot API acceptance has been authorized/configured yet.
    'CHOREOGRAPH_CRM_GRANT_ID': '',
    'CHOREOGRAPH_CRM_EXPIRES_AT': '',
    'CHOREOGRAPH_CRM_REQUESTS': '',
    'CHOREOGRAPH_CRM_WORKSPACE_REQUESTS': '',
})

ENV_FIELDS = frozenset({
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
