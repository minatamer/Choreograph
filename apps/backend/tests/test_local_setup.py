"""Synthetic app-local setup/migration; no checkout credentials are read."""
import importlib.util
from pathlib import Path

import pytest
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('local_setup', ROOT / 'scripts/setup.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


@pytest.fixture
def checkout(tmp_path):
    for service in ('backend', 'frontend'):
        app = tmp_path / 'apps' / service
        app.mkdir(parents=True)
        (app / '.env.example').write_bytes((ROOT / 'apps' / service / '.env.example').read_bytes())
    return tmp_path


def test_new_setup_uses_fake_ai_disabled_crm_and_is_repeatable(checkout):
    setup.prepare(checkout)
    backend = checkout / 'apps/backend/.env.local'
    frontend = checkout / 'apps/frontend/.env.local'
    values = dotenv_values(backend, interpolate=False)
    public = dotenv_values(frontend, interpolate=False)
    assert values['CHOREOGRAPH_PROFILE'] == 'fake'
    assert values['CHOREOGRAPH_CRM_PROVIDER'] == 'disabled'
    assert values['CHOREOGRAPH_AI_PAID_ENABLED'] == 'false'
    assert values['CHOREOGRAPH_BRIDGE_SECRET'] == public['CHOREOGRAPH_BRIDGE_SECRET']
    assert set(public) == {'CHOREOGRAPH_API_URL', 'CHOREOGRAPH_API_AUTH',
                           'CHOREOGRAPH_ORIGIN', 'CHOREOGRAPH_BRIDGE_SECRET'}
    originals = (backend.read_bytes(), frontend.read_bytes())
    setup.prepare(checkout)
    assert (backend.read_bytes(), frontend.read_bytes()) == originals
    assert not (checkout / '.env.local').exists()


def test_legacy_migration_preserves_values_and_keeps_backend_secrets_private(checkout, capsys):
    legacy = checkout / '.env.local'
    content = ('CHOREOGRAPH_PROFILE=fake\nCHOREOGRAPH_ORIGIN=http://127.0.0.1:45860\n'
               'CHOREOGRAPH_BRIDGE_SECRET=synthetic-bridge-' + 'x' * 40 + '\n'
               'CHOREOGRAPH_DATABASE_URL=synthetic-database-marker\n'
               'CHOREOGRAPH_OPENAI_API_KEY=synthetic-provider-marker\n')
    legacy.write_text(content)
    setup.prepare(checkout)
    assert not legacy.exists()
    assert (checkout / 'apps/backend/.env.local').read_text() == content
    frontend = (checkout / 'apps/frontend/.env.local').read_text()
    assert 'synthetic-database-marker' not in frontend
    assert 'synthetic-provider-marker' not in frontend
    assert 'synthetic-' not in capsys.readouterr().out


def test_conflicting_existing_frontend_prevents_migration_without_changes(checkout):
    legacy = checkout / '.env.local'
    legacy.write_text('CHOREOGRAPH_ORIGIN=http://127.0.0.1:45860\nCHOREOGRAPH_BRIDGE_SECRET=' + 'x' * 40)
    frontend = checkout / 'apps/frontend/.env.local'
    frontend.write_text('CHOREOGRAPH_BRIDGE_SECRET=' + 'y' * 40)
    original = legacy.read_bytes(), frontend.read_bytes()
    with pytest.raises(ValueError, match='LOCAL_FRONTEND_CONFIG_CONFLICT'):
        setup.prepare(checkout)
    assert (legacy.read_bytes(), frontend.read_bytes()) == original
    assert not (checkout / 'apps/backend/.env.local').exists()
