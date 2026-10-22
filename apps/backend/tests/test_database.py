import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from choreograph.api import create_app
from choreograph.models import DocumentVersion, Manifest, Reservation, Staff, Workspace
from choreograph.sessions import create_workspace, digest

NOW = datetime(2026, 10, 22, 10, tzinfo=UTC)
HEAD = ScriptDirectory.from_config(Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))).get_current_head()


def test_actual_extensions_vector_and_schema(database):
    engine, _ = database
    with engine.connect() as c:
        extensions = dict(c.execute(text("select extname, extversion from pg_extension where extname in ('vector','btree_gist')")).all())
        assert extensions == {'vector': '0.8.5', 'btree_gist': '1.7'}
        assert c.scalar(text("select ('[1,0,0]'::vector <=> '[1,0,0]'::vector)")) == 0
        assert c.scalar(text('select version_num from alembic_version')) == HEAD
        assert c.scalar(text("select format_type(atttypid,atttypmod) from pg_attribute where attrelid='knowledge_chunks'::regclass and attname='embedding'")) == 'vector'


def test_migration_roundtrip_on_isolated_database(database):
    from pathlib import Path

    from alembic import command
    from alembic.config import Config
    engine, _ = database
    config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    with engine.begin() as connection:
        config.attributes['connection'] = connection
        command.downgrade(config, 'base')
        assert connection.scalar(text("select to_regclass('reservations')")) is None
        command.upgrade(config, 'head')
        assert connection.scalar(text('select version_num from alembic_version')) == HEAD


def test_cookie_scope_fixed_expiry_reset_and_no_browser_id_authority(database):
    engine, settings = database
    clock = [NOW]
    app = create_app(settings, engine, lambda: clock[0])
    headers = {'x-choreograph-bridge': settings.bridge_secret, 'origin': settings.origin}
    with TestClient(app) as a, TestClient(app) as b:
        first = a.post('/v1/session', json={'timezone': 'Asia/Kathmandu'}, headers=headers)
        assert first.status_code == 200
        assert 'HttpOnly' in first.headers['set-cookie'] and 'SameSite=lax' in first.headers['set-cookie']
        state = first.json()
        token = a.cookies.get('choreograph_guest')
        with Session(engine) as db:
            row = db.get(Workspace, state['workspace_id'])
            assert row.session_hash == digest(token) and token not in row.session_hash
        other = b.post('/v1/session', json={'timezone': 'Africa/Cairo'}, headers=headers).json()
        assert state['workspace_id'] != other['workspace_id']
        assert b.get('/v1/session?workspace_id='+state['workspace_id'], headers=headers).json()['workspace_id'] == other['workspace_id']
        retry = a.post('/v1/session', json={'timezone': 'America/New_York'}, headers=headers).json()
        assert retry['timezone'] == 'Asia/Kathmandu' and retry['expires_at'] == state['expires_at']
        body = {'timezone': 'Asia/Kathmandu', 'generation': state['generation']}
        assert a.post('/v1/reset', json=body, headers=headers).status_code == 403
        reset = a.post('/v1/reset', json=body, headers={**headers, 'x-csrf-token': state['csrf']})
        assert reset.status_code == 200 and reset.json()['workspace_id'] != state['workspace_id']
        a.cookies.set('choreograph_guest', token, domain='testserver.local', path='/')
        assert a.get('/v1/session', headers=headers).status_code == 410
        clock[0] = NOW + timedelta(hours=2)
        assert b.get('/v1/session', headers=headers).status_code == 410
        renewed=b.post('/v1/session',json={'timezone':'Africa/Cairo','restart':True},headers=headers)
        assert renewed.status_code==200 and renewed.json()['workspace_id']!=other['workspace_id']


def test_invalid_zone_and_stale_generation_do_not_create_or_reset(database):
    engine, settings = database
    headers = {'x-choreograph-bridge': settings.bridge_secret, 'origin': settings.origin}
    with TestClient(create_app(settings, engine, lambda: NOW)) as c:
        assert c.post('/v1/session', json={'timezone': 'Not/AZone'}, headers=headers).status_code == 422
        state = c.post('/v1/session', json={'timezone': 'Europe/Berlin'}, headers=headers).json()
        result = c.post('/v1/reset', json={'timezone': 'Europe/Berlin', 'generation': 100}, headers={**headers,'x-csrf-token':state['csrf']})
        assert result.status_code == 409
        assert c.get('/v1/session', headers=headers).json()['workspace_id'] == state['workspace_id']
        c.cookies.set('choreograph_guest','invalid-cookie',domain='testserver.local',path='/')
        assert c.post('/v1/session',json={'timezone':'UTC'},headers=headers).status_code==401
        assert c.post('/v1/session',json={'timezone':'UTC','restart':True},headers=headers).status_code==200


def test_postgres_rejects_concurrent_partial_overlap_and_allows_adjacent(database):
    engine, _ = database
    with Session(engine) as db, db.begin():
        ws, _ = create_workspace(db, 'Africa/Cairo', NOW)
        wid = ws.id
        db.add(Staff(workspace_id=wid, id='ada', name='Ada'))
    barrier = threading.Barrier(2)
    def reserve(offset):
        try:
            with Session(engine) as db, db.begin():
                barrier.wait(timeout=3)
                db.add(Reservation(workspace_id=wid, staff_id='ada', starts_at=NOW+timedelta(minutes=offset),
                                   ends_at=NOW+timedelta(minutes=offset+120), state='confirmed'))
                db.flush()
            return 'committed'
        except (IntegrityError,OperationalError) as error:
            assert error.orig.sqlstate in {'23P01','40P01'}
            return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(reserve, [0, 30])) == ['committed', 'conflict']
    with Session(engine) as db, db.begin():
        current = db.scalar(select(Reservation).where(Reservation.workspace_id == wid))
        db.add(Reservation(workspace_id=wid, staff_id='ada', starts_at=current.ends_at,
                           ends_at=current.ends_at+timedelta(minutes=30), state='confirmed'))


def test_scoped_foreign_key_rejects_another_workspaces_staff(database):
    engine, _ = database
    with Session(engine) as db, db.begin():
        a,_=create_workspace(db,'UTC',NOW);b,_=create_workspace(db,'UTC',NOW)
        aid,bid=a.id,b.id
        db.add(Staff(workspace_id=aid,id='only-a',name='Ada'))
    with pytest.raises(IntegrityError), Session(engine) as db, db.begin():
        db.add(Reservation(workspace_id=bid,staff_id='only-a',starts_at=NOW,ends_at=NOW+timedelta(hours=1)))


def test_manifest_cannot_select_another_guests_document_or_unready_version(database):
    engine, _ = database
    with Session(engine) as db, db.begin():
        a,_=create_workspace(db,'UTC',NOW);b,_=create_workspace(db,'UTC',NOW)
        aid,bid=a.id,b.id
        version=DocumentVersion(owner_id=aid,slot='service',title='Private',version='1',media_type='text/plain',
                                source=b'private',sha256='0'*64,page_count=1,state='ready',created_at=NOW)
        db.add(version);db.flush();vid=version.id
    with pytest.raises(IntegrityError), Session(engine) as db, db.begin():
        db.add(Manifest(workspace_id=bid,slot='service',version_id=vid))
    with Session(engine) as db, db.begin():
        db.add(Manifest(workspace_id=aid,slot='service',version_id=vid));db.flush()
        version=db.get(DocumentVersion,vid)
        with pytest.raises(IntegrityError), db.begin_nested():
            version.owner_id=bid;db.flush()
