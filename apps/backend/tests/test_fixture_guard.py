"""Unsafe test configuration must fail before admin-engine construction."""
from pathlib import Path

import conftest
import pytest


@pytest.mark.parametrize('url', [
    'postgresql+psycopg://fixture:fixture@127.0.0.1:45862/choreograph?host=remote.example.invalid',
    'postgresql+psycopg://fixture:fixture@127.0.0.1:45862/choreograph?hostaddr=192.0.2.1',
    'postgresql+psycopg://fixture:fixture@127.0.0.1:45862/choreograph?port=5432',
    'postgresql+psycopg://fixture:fixture@127.0.0.1:45862/choreograph?service=external',
    'postgresql+psycopg://fixture:fixture@127.0.0.1:45862/choreograph?host=localhost&host=remote.example.invalid',
    'postgresql+psycopg://fixture:fixture@127.0.0.1:45862/choreograph?sslmode=require',
    'postgresql+psycopg2://fixture:fixture@127.0.0.1:45862/choreograph',
    'postgresql+psycopg://fixture:fixture@remote.example.invalid:45862/choreograph',
    'postgresql+psycopg://fixture:fixture@127.0.0.1:5432/choreograph',
    'postgresql+psycopg://fixture:fixture@127.0.0.1:45862/other_database',
    'not-a-database-url',
])
def test_unsafe_source_is_rejected_before_admin_engine(monkeypatch, url):
    original_read = Path.read_text
    calls = []

    def fake_configuration(path, *args, **kwargs):
        if path.name == '.env.local':
            return f'CHOREOGRAPH_DATABASE_URL={url}\n'
        return original_read(path, *args, **kwargs)

    def forbidden_engine(*_args, **_kwargs):
        calls.append(True)
        raise AssertionError('UNSAFE_ADMIN_ENGINE_CONSTRUCTION')

    monkeypatch.setattr(Path, 'read_text', fake_configuration)
    monkeypatch.setattr(conftest, 'create_engine', forbidden_engine)
    fixture = conftest.database.__wrapped__()
    with pytest.raises(RuntimeError, match='OWNED_LOCAL_POSTGRES_REQUIRED'):
        next(fixture)
    assert calls == []
