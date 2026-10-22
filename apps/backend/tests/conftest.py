"""Actual isolated PostgreSQL. No live flags, provider keys or production database are inherited."""
import base64
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from choreograph.db import build_engine
from choreograph.migrate import migrate
from choreograph.settings import Settings


@pytest.fixture(scope="session")
def database():
    root = Path(__file__).resolve().parents[3]
    # Read only the local DB setting, never model/account configuration.
    line = next(line for line in (root / '.env.local').read_text().splitlines()
                if line.startswith('CHOREOGRAPH_DATABASE_URL='))
    try:
        source = make_url(line.split('=', 1)[1])
    except (ArgumentError, ValueError):
        raise RuntimeError('OWNED_LOCAL_POSTGRES_REQUIRED') from None
    # libpq query parameters override authority fields. Validate before even
    # constructing the privileged admin engine, including on parsing failures.
    if (source.drivername != 'postgresql+psycopg' or source.query or
            source.host not in {'127.0.0.1', 'localhost'} or source.port != 45862 or source.database != 'choreograph'):
        raise RuntimeError('OWNED_LOCAL_POSTGRES_REQUIRED')
    name = 'choreograph_test_' + uuid4().hex
    admin = create_engine(source.set(database='postgres'), isolation_level='AUTOCOMMIT', hide_parameters=True)
    with admin.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
    url = source.set(database=name).render_as_string(hide_password=False)
    settings = Settings.parse({'CHOREOGRAPH_DATABASE_URL': url, 'CHOREOGRAPH_PROFILE': 'fake',
                               'CHOREOGRAPH_BRIDGE_SECRET': 'test-only-' + 'x'*40,
                               'CHOREOGRAPH_TOKEN_KEY': base64.urlsafe_b64encode(bytes(32)).decode()}, testing=True)
    engine = build_engine(settings)
    try:
        migrate(engine)
        yield engine, settings
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE "{name}"')
        admin.dispose()
