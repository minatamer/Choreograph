"""Actual isolated PostgreSQL. No live flags, provider keys or production database are inherited."""
import base64
from io import StringIO
from pathlib import Path
from uuid import uuid4

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from choreograph.db import build_engine
from choreograph.migrate import migrate
from choreograph.settings import Settings


@pytest.fixture(scope="session")
def postgres_database():
    root = Path(__file__).resolve().parents[3]
    # Read only the local DB setting, never model/account configuration.
    line = next(line for line in (root / 'apps/backend/.env.local').read_text().splitlines()
                if line.startswith('CHOREOGRAPH_DATABASE_URL='))
    try:
        source = make_url(dotenv_values(stream=StringIO(line), interpolate=False)['CHOREOGRAPH_DATABASE_URL'])
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
    settings = Settings.parse({'DATABASE_ENABLED':'true','CHOREOGRAPH_DATABASE_URL': url, 'FAKE_MODE':'true',
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


@pytest.fixture
def database(request,tmp_path):
    if getattr(request,'param','postgres')=='postgres':
        return request.getfixturevalue('postgres_database')

    from choreograph.object_store import FileObjects, ObjectEngine
    settings=Settings.parse({'DATABASE_ENABLED':'false','FAKE_MODE':'true',
        'CHOREOGRAPH_BRIDGE_SECRET':'test-only-'+'x'*40,
        'CHOREOGRAPH_TOKEN_KEY':base64.urlsafe_b64encode(bytes(32)).decode()},testing=True)
    engine=ObjectEngine(FileObjects(tmp_path/'private'),settings.token_key)
    engine.save(request.getfixturevalue('object_seed'),'0')
    request.addfinalizer(engine.dispose)
    return engine,settings


PORTABLE_MODULES={'test_storage_races','test_ai_admission','test_interactions','test_live_assistant','test_live_crm','test_task_delivery','test_storage_delivery','test_requests','test_customer_booking','test_booking','test_assistant','test_assistant_quality','test_crm','test_jobs','test_reservation_shortcut','test_knowledge','test_security_crm','test_provider_limits','test_verification_session'}


def pytest_generate_tests(metafunc):
    if metafunc.module.__name__.split('.')[-1] in PORTABLE_MODULES and 'database' in metafunc.fixturenames:
        metafunc.parametrize('database',['postgres'] if metafunc.function.__name__=='test_metadata_retrieval_and_attachment_omit_source_without_weakening_source_authorization' else ['postgres','objects'],indirect=True)


@pytest.fixture(scope='session')
def object_seed(tmp_path_factory):
    from test_requests import NOW

    from choreograph import knowledge
    from choreograph.object_store import FileObjects, ObjectEngine
    from choreograph.persistence import Session
    key=base64.urlsafe_b64encode(bytes(32)).decode()
    engine=ObjectEngine(FileObjects(tmp_path_factory.mktemp('object-seed')),key)
    with Session(engine) as db,db.begin():knowledge.prepare_samples(db,NOW)
    records,_=engine.load();engine.dispose()
    return records
