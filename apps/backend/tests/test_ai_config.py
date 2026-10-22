import base64
from datetime import UTC, datetime, timedelta

import pytest

from choreograph.ai_config import POSITIVE_GRANT_FIELDS, parse_live_ai
from choreograph.settings import Settings
from choreograph.tokenizers import ASSET_DIRECTORY

NOW = datetime(2026, 10, 22, tzinfo=UTC)


def live_values():
    values = {
        'CHOREOGRAPH_PROFILE': 'live', 'CHOREOGRAPH_AI_PAID_ENABLED': 'true',
        'CHOREOGRAPH_DATABASE_URL': 'postgresql+psycopg://fixture:fixture@127.0.0.1:45862/choreograph_test_config',
        'CHOREOGRAPH_BRIDGE_SECRET': 'synthetic-bridge-' + 'x' * 40,
        'CHOREOGRAPH_TOKEN_KEY': base64.urlsafe_b64encode(bytes(32)).decode(),
        'CHOREOGRAPH_OPENAI_API_KEY': 'synthetic-key-never-used-externally',
        'CHOREOGRAPH_AI_EXPIRES_AT': '2090-01-01T00:00:00Z',
        'CHOREOGRAPH_AI_RESPONSE_MODEL': 'operator-response-model',
        'CHOREOGRAPH_AI_EMBEDDING_MODEL': 'operator-embedding-model',
        'CHOREOGRAPH_AI_RESPONSE_TOKENIZER': 'cl100k_base',
        'CHOREOGRAPH_AI_EMBEDDING_TOKENIZER': 'o200k_base',
        'CHOREOGRAPH_AI_CHUNKER': 'llama-token-section-v4',
        'CHOREOGRAPH_AI_EMBEDDING_DIMENSIONS': '128',
        'CHOREOGRAPH_AI_GRANT_ID': 'synthetic-finite-grant',
    }
    values.update({'CHOREOGRAPH_AI_' + name.upper(): '100' for name in POSITIVE_GRANT_FIELDS})
    return values


def test_explicit_live_configuration_has_no_model_price_or_allowance_defaults():
    values = live_values()
    config = parse_live_ai(values, now=NOW)
    assert config.spec.model == values['CHOREOGRAPH_AI_EMBEDDING_MODEL']
    assert config.grant.response_model == values['CHOREOGRAPH_AI_RESPONSE_MODEL']
    assert config.spec.dimensions == 128
    assert config.tokenizer_directory == str(ASSET_DIRECTORY)
    required = [key for key in values if key.startswith('CHOREOGRAPH_AI_')]
    required.append('CHOREOGRAPH_OPENAI_API_KEY')
    for key in required:
        missing = values.copy()
        del missing[key]
        with pytest.raises(ValueError):
            parse_live_ai(missing, now=NOW)


@pytest.mark.parametrize('bad', ['0', '-1', '1.5', 'true', '100000000000000000000', ' 10'])
def test_prices_and_allowances_are_strict_positive_integers(bad):
    for name in POSITIVE_GRANT_FIELDS:
        with pytest.raises(ValueError):
            parse_live_ai({**live_values(), 'CHOREOGRAPH_AI_' + name.upper(): bad}, now=NOW)


def test_expiry_scope_and_embedding_identity_fail_closed():
    for name, value in [
        ('CHOREOGRAPH_AI_EXPIRES_AT', NOW.isoformat()),
        ('CHOREOGRAPH_AI_EXPIRES_AT', (NOW - timedelta(seconds=1)).isoformat()),
        ('CHOREOGRAPH_AI_EXPIRES_AT', '2090-01-01T00:00:00'),
        ('CHOREOGRAPH_AI_WORKSPACE_REQUESTS', '101'),
        ('CHOREOGRAPH_AI_EMBEDDING_DIMENSIONS', '3073'),
        ('CHOREOGRAPH_AI_CHUNKER', 'llama-token-section-v3'),
        ('CHOREOGRAPH_AI_RESPONSE_TOKENIZER', 'implicit-model-tokenizer'),
        ('CHOREOGRAPH_AI_EMBEDDING_TOKENIZER', 'implicit-model-tokenizer'),
        ('CHOREOGRAPH_AI_TOKENIZER_DIRECTORY', 'https://example.invalid/vocabulary'),
        ('CHOREOGRAPH_AI_PAID_ENABLED', 'True'),
    ]:
        with pytest.raises(ValueError):
            parse_live_ai({**live_values(), name: value}, now=NOW)


def test_settings_preserve_fake_test_guard_and_hide_live_credentials(monkeypatch):
    values = live_values()
    monkeypatch.setenv('OPENAI_API_KEY', 'ambient-key-must-not-be-used')
    config = Settings.parse(values)
    assert config.live_ai.api_key == values['CHOREOGRAPH_OPENAI_API_KEY']
    assert values['CHOREOGRAPH_OPENAI_API_KEY'] not in repr(config)
    assert values['CHOREOGRAPH_OPENAI_API_KEY'] not in repr(config.live_ai)
    with pytest.raises(ValueError, match='TEST_PROVIDER_FORBIDDEN'):
        Settings.parse(values, testing=True)
    fake = Settings.parse({**values, 'CHOREOGRAPH_PROFILE': 'fake'}, testing=True)
    assert fake.live_ai is None


def test_explicit_live_mapping_cannot_use_ambient_sdk_key(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'ambient-key-must-not-be-used')
    values = live_values()
    del values['CHOREOGRAPH_OPENAI_API_KEY']
    with pytest.raises(ValueError, match='LIVE_AI_CONFIGURATION_INVALID'):
        Settings.parse(values)
