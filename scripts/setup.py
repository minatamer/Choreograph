"""Prepare app-local configuration; preserve existing credentials without printing them."""
import base64
import os
import re
import secrets
import sys
from io import StringIO
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/backend'))
from choreograph.runtime_config import APPLICATION, ENV_FIELDS, MOVED_FIELDS, REMOVED_ALIASES  # noqa: E402


def read_values(path):
    return {key: value for key, value in dotenv_values(path, interpolate=False).items() if value is not None}


def render(example, values):
    source = example.read_text(encoding='utf-8')
    for key, value in values.items():
        # Never add wrapping quotes. Refuse values that would be interpreted
        # differently by the Python, Node or Compose environment loaders.
        rendered = value
        if (any(char in value for char in '\r\n\0#$') or value != value.strip() or
                dotenv_values(stream=StringIO(f'{key}={value}\n'), interpolate=False).get(key) != value):
            raise ValueError('UNQUOTED_LOCAL_VALUE_UNSUPPORTED')
        source, count = re.subn(rf'^{re.escape(key)}=.*$', lambda _, key=key, rendered=rendered: f'{key}={rendered}', source, flags=re.M)
        if not count:
            source += f'\n{key}={rendered}\n'
    return source


def create(path, content):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', encoding='utf-8') as stream:
        stream.write(content)


def private_values(values):
    """Explicit one-time migration; runtime loaders never accept these aliases."""
    unknown = set(values) - ENV_FIELDS - MOVED_FIELDS - REMOVED_ALIASES
    if unknown:
        raise ValueError('UNRECOGNIZED_LOCAL_CONFIGURATION')
    result = {key: value for key, value in values.items() if key in ENV_FIELDS}
    if 'FAKE_MODE' not in result:
        profile = values.get('CHOREOGRAPH_PROFILE', 'fake')
        if profile not in {'fake', 'live'}:
            raise ValueError('LOCAL_MODE_MIGRATION_INVALID')
        result['FAKE_MODE'] = 'true' if profile == 'fake' else 'false'
    result.setdefault('PAID_DEMO_ENABLED', values.get('CHOREOGRAPH_AI_PAID_ENABLED', 'false'))
    if 'OPENAI_API_KEY' not in result:
        result['OPENAI_API_KEY'] = values.get('CHOREOGRAPH_OPENAI_API_KEY', '')
    elif (result['OPENAI_API_KEY'] and values.get('CHOREOGRAPH_OPENAI_API_KEY') and
          result['OPENAI_API_KEY'] != values['CHOREOGRAPH_OPENAI_API_KEY']):
        raise ValueError('LOCAL_SECRET_ALIAS_CONFLICT')
    if any(result[key] not in {'true', 'false'} for key in ('FAKE_MODE', 'PAID_DEMO_ENABLED')):
        raise ValueError('LOCAL_MODE_MIGRATION_INVALID')
    # Do not silently discard a deliberately different model, allowance or app ID.
    # Callback is derived from origin; old disabled flags are no longer switches.
    for key, expected in APPLICATION.items():
        if values.get(key) and values[key] != expected:
            raise ValueError('NONSECRET_CONFIGURATION_REQUIRES_CODE_MIGRATION')
    if values.get('CHOREOGRAPH_TASKS_ENABLED', 'false') != 'false':
        raise ValueError('LOCAL_TASKS_CONFIGURATION_INVALID')
    return result


def prepare(root=ROOT):
    legacy = root / '.env.local'
    backend = root / 'apps/backend/.env.local'
    frontend = root / 'apps/frontend/.env.local'
    if legacy.exists() and backend.exists() and read_values(legacy) != read_values(backend):
        raise ValueError('LOCAL_BACKEND_CONFIG_CONFLICT')
    source = backend if backend.exists() else legacy if legacy.exists() else None
    if source:
        backend_values = private_values(read_values(source))
    else:
        existing_frontend = read_values(frontend) if frontend.exists() else {}
        password = secrets.token_hex(24)
        backend_values = {
            'FAKE_MODE': 'true', 'PAID_DEMO_ENABLED': 'false',
            'CHOREOGRAPH_DB_PASSWORD': password,
            'CHOREOGRAPH_DATABASE_URL': f'postgresql+psycopg://choreograph:{password}@127.0.0.1:45862/choreograph',
            'CHOREOGRAPH_ORIGIN': existing_frontend.get('CHOREOGRAPH_ORIGIN', 'http://127.0.0.1:45860'),
            'CHOREOGRAPH_BRIDGE_SECRET': existing_frontend.get('CHOREOGRAPH_BRIDGE_SECRET', secrets.token_hex(32)),
            'CHOREOGRAPH_TOKEN_KEY': base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
        }
    backend_values = {**read_values(backend.with_name('.env.example')), **backend_values}
    backend_content = render(backend.with_name('.env.example'), backend_values)
    shared = {key: backend_values.get(key, '') for key in ('CHOREOGRAPH_ORIGIN', 'CHOREOGRAPH_BRIDGE_SECRET')}
    if (shared['CHOREOGRAPH_ORIGIN'] not in {'http://127.0.0.1:45860', 'http://localhost:45860'} or
            len(shared['CHOREOGRAPH_BRIDGE_SECRET']) < 32):
        raise ValueError('LOCAL_BRIDGE_CONFIG_INVALID')
    frontend_values = read_values(frontend) if frontend.exists() else {}
    if frontend.exists() and any(frontend_values.get(key) != value for key, value in shared.items()):
        raise ValueError('LOCAL_FRONTEND_CONFIG_CONFLICT')
    if set(frontend_values) - {'CHOREOGRAPH_API_URL', 'CHOREOGRAPH_API_AUTH', 'CHOREOGRAPH_API_AUDIENCE', *shared}:
        raise ValueError('LOCAL_FRONTEND_CONFIG_INVALID')
    if frontend_values.get('CHOREOGRAPH_API_AUTH', 'none') != 'none' or frontend_values.get('CHOREOGRAPH_API_AUDIENCE'):
        raise ValueError('LOCAL_FRONTEND_CONFIG_INVALID')
    frontend_content = render(frontend.with_name('.env.example'), {**read_values(frontend.with_name('.env.example')), **shared,
        **{key: value for key, value in frontend_values.items() if key == 'CHOREOGRAPH_API_URL'}})
    # All validation precedes either write; preserve the permissions of existing files.
    for path, content in ((backend, backend_content), (frontend, frontend_content)):
        if not path.exists():create(path, content)
        elif path.read_text(encoding='utf-8') != content:path.write_text(content, encoding='utf-8')
    if legacy.exists():
        if any(read_values(backend).get(key) != value for key,value in private_values(read_values(legacy)).items()):
            raise ValueError('LOCAL_CONFIG_MIGRATION_INCOMPLETE')
        legacy.unlink()
    print('Minimal app-local configuration ready; credentials and mode choices preserved, values omitted.')


def main():
    try:
        prepare()
    except ValueError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
