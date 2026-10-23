"""Prepare app-local configuration; preserve existing credentials without printing them."""
import base64
import os
import re
import secrets
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def read_values(path):
    return {key: value for key, value in dotenv_values(path, interpolate=False).items() if value is not None}


def render(example, values):
    source = example.read_text(encoding='utf-8')
    for key, value in values.items():
        quoted = "'" + value.replace('\\', '\\\\').replace("'", "\\'") + "'"
        source, count = re.subn(rf'^{re.escape(key)}=.*$', lambda _, key=key, quoted=quoted: f'{key}={quoted}', source, flags=re.M)
        if not count:
            source += f'\n{key}={quoted}\n'
    return source


def create(path, content):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', encoding='utf-8') as stream:
        stream.write(content)


def prepare(root=ROOT):
    legacy = root / '.env.local'
    backend = root / 'apps/backend/.env.local'
    frontend = root / 'apps/frontend/.env.local'
    if legacy.exists() and backend.exists() and read_values(legacy) != read_values(backend):
        raise ValueError('LOCAL_BACKEND_CONFIG_CONFLICT')
    source = backend if backend.exists() else legacy if legacy.exists() else None
    if source:
        backend_values = read_values(source)
        backend_content = source.read_text(encoding='utf-8')
    else:
        existing_frontend = read_values(frontend) if frontend.exists() else {}
        password = secrets.token_hex(24)
        backend_values = {
            'CHOREOGRAPH_PROFILE': 'fake',
            'CHOREOGRAPH_DB_PASSWORD': password,
            'CHOREOGRAPH_DATABASE_URL': f'postgresql+psycopg://choreograph:{password}@127.0.0.1:45862/choreograph',
            'CHOREOGRAPH_ORIGIN': existing_frontend.get('CHOREOGRAPH_ORIGIN', 'http://127.0.0.1:45860'),
            'CHOREOGRAPH_BRIDGE_SECRET': existing_frontend.get('CHOREOGRAPH_BRIDGE_SECRET', secrets.token_hex(32)),
            'CHOREOGRAPH_TOKEN_KEY': base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
        }
        backend_content = render(backend.with_name('.env.example'), backend_values)
    shared = {key: backend_values.get(key, '') for key in ('CHOREOGRAPH_ORIGIN', 'CHOREOGRAPH_BRIDGE_SECRET')}
    if (shared['CHOREOGRAPH_ORIGIN'] not in {'http://127.0.0.1:45860', 'http://localhost:45860'} or
            len(shared['CHOREOGRAPH_BRIDGE_SECRET']) < 32):
        raise ValueError('LOCAL_BRIDGE_CONFIG_INVALID')
    if frontend.exists() and any(read_values(frontend).get(key) != value for key, value in shared.items()):
        raise ValueError('LOCAL_FRONTEND_CONFIG_CONFLICT')
    frontend_content = render(frontend.with_name('.env.example'), shared)
    if not backend.exists():
        create(backend, backend_content)
    if not frontend.exists():
        create(frontend, frontend_content)
    if legacy.exists():
        if read_values(legacy) != read_values(backend):
            raise ValueError('LOCAL_CONFIG_MIGRATION_INCOMPLETE')
        legacy.unlink()
    print('App-local backend/frontend configuration ready; existing values preserved, secrets omitted.')


def main():
    try:
        prepare()
    except ValueError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
