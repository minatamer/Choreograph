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


def test_package_import_is_inert(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("import attempted configuration access")
    monkeypatch.setattr(os, "getenv", denied)
    importlib.reload(importlib.import_module("choreograph"))
