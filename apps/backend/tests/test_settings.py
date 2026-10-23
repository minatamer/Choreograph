import base64
import importlib
import os

import pytest

from choreograph.settings import Settings


def values():
    return {"CHOREOGRAPH_DATABASE_URL": "postgresql+psycopg://test:fake@127.0.0.1:45862/choreograph_test_config",
            "CHOREOGRAPH_BRIDGE_SECRET": "x" * 40, "CHOREOGRAPH_TOKEN_KEY": base64.urlsafe_b64encode(bytes(32)).decode()}


def test_explicit_config_does_not_inherit_live_environment(monkeypatch):
    monkeypatch.setenv("CHOREOGRAPH_PROFILE", "real")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-read")
    assert Settings.parse(values(), testing=True).profile == "fake"
    with pytest.raises(ValueError, match="TEST_PROVIDER_FORBIDDEN"):
        Settings.parse({**values(), "CHOREOGRAPH_PROFILE": "real"}, testing=True)


def test_test_database_guard_rejects_development_and_remote():
    for url in ["postgresql+psycopg://x:x@localhost/choreograph", "postgresql+psycopg://x:x@remote/choreograph_test_x"]:
        with pytest.raises(ValueError, match="ISOLATED_TEST_DATABASE_REQUIRED"):
            Settings.parse({**values(), "CHOREOGRAPH_DATABASE_URL": url}, testing=True)


def test_runtime_crm_defaults_disabled_while_isolated_tests_keep_fake():
    assert Settings.parse(values()).crm_provider == 'disabled'
    assert Settings.parse(values(), testing=True).crm_provider == 'fake'
    assert Settings.parse({**values(), 'CHOREOGRAPH_CRM_PROVIDER': 'disabled'}, testing=True).crm_provider == 'disabled'


def test_package_import_is_inert(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("import attempted configuration access")
    monkeypatch.setattr(os, "getenv", denied)
    importlib.reload(importlib.import_module("choreograph"))


def test_local_loader_uses_backend_file_without_inheriting_root_or_ambient(tmp_path, monkeypatch):
    from choreograph import settings
    backend = tmp_path / 'apps/backend'
    backend.mkdir(parents=True)
    local = {**values(), 'CHOREOGRAPH_DATABASE_URL': 'postgresql+psycopg://test:fake@127.0.0.1:45862/choreograph'}
    (backend / '.env.local').write_text(''.join(f'{key}={value}\n' for key, value in local.items()))
    (tmp_path / '.env.local').write_text('CHOREOGRAPH_PROFILE=live\n')
    monkeypatch.setenv('CHOREOGRAPH_PROFILE', 'live')
    monkeypatch.setattr(settings, '__file__', str(backend / 'choreograph/settings.py'))
    assert settings.load_local().profile == 'fake'
    (backend / '.env.local').unlink()
    with pytest.raises(ValueError, match='DATABASE_CONFIGURATION_INVALID'):
        settings.load_local()
