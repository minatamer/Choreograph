import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from queue import Queue
from time import monotonic
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from choreograph.api import create_app
from choreograph.errors import DomainError
from choreograph.models import DocumentVersion, Manifest, OAuthState, Reservation, Workspace
from choreograph.sessions import COOKIE, create_workspace

NOW = datetime(2026, 10, 22, 10, tzinfo=UTC)
CAPACITY = 256


@pytest.fixture
def admission_rows(database):
    engine, settings = database
    owned = []
    with Session(engine) as db:
        original_count = db.scalar(select(func.count()).select_from(Workspace))
    try:
        yield engine, settings, owned
    finally:
        # The suite shares this database. Remove only this test's rows, including
        # committed concurrent winners, rather than retaining a full-cap fixture.
        with Session(engine) as db, db.begin():
            db.execute(delete(Workspace).where(Workspace.id.in_(owned)))
            assert db.scalar(select(func.count()).select_from(Workspace)) == original_count


def retained_row(*, active=False):
    return Workspace(id=uuid4(), session_hash=uuid4().hex + uuid4().hex, timezone='UTC',
                     created_at=NOW-timedelta(hours=4), expires_at=NOW-timedelta(hours=2),
                     active=active, generation=1, revision=1, seeded=False, draft={}, messages=[])


def fill_to(engine, owned, target):
    with Session(engine) as db, db.begin():
        current = db.scalar(select(func.count()).select_from(Workspace))
        assert current <= target
        rows = [retained_row() for _ in range(target-current)]
        owned.extend(row.id for row in rows)
        db.add_all(rows)


def test_retired_unresolved_and_unflushed_rows_all_consume_admission(admission_rows):
    engine, _, owned = admission_rows
    unresolved = retained_row()
    owned.append(unresolved.id)
    state_hash = uuid4().hex+uuid4().hex
    with Session(engine) as db, db.begin():
        db.add(unresolved)
        db.flush()
        db.add(OAuthState(state_hash=state_hash, workspace_id=unresolved.id, generation=1,
                          expires_at=NOW-timedelta(hours=1), used=True, outcome='unknown'))
    fill_to(engine, owned, CAPACITY-1)
    pending = retained_row()
    owned.append(pending.id)
    with pytest.raises(DomainError) as rejected, Session(engine, autoflush=False) as db, db.begin():
        db.add(pending)
        create_workspace(db, 'UTC', NOW)
    assert (rejected.value.code, rejected.value.status) == ('DEMO_CAPACITY', 429)
    with Session(engine) as db, db.begin():
        assert db.scalar(select(func.count()).select_from(Workspace)) == CAPACITY-1
        workspace, _ = create_workspace(db, 'UTC', NOW)
        owned.append(workspace.id)
        # A second admission in this same transaction must see its first insert.
        with pytest.raises(DomainError) as repeated:
            create_workspace(db, 'UTC', NOW)
        assert (repeated.value.code, repeated.value.status) == ('DEMO_CAPACITY', 429)
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Workspace)) == CAPACITY
        assert db.get(OAuthState, state_hash).outcome == 'unknown'


def test_concurrent_final_slot_has_exactly_one_committed_winner(admission_rows):
    engine, _, owned = admission_rows
    fill_to(engine, owned, CAPACITY-1)
    inserted = threading.Event()
    release = threading.Event()
    contender_pid = Queue()

    def admit(first):
        try:
            with Session(engine) as db, db.begin():
                if not first:
                    contender_pid.put(db.scalar(text('SELECT pg_backend_pid()')))
                workspace, _ = create_workspace(db, 'UTC', NOW)
                owned.append(workspace.id)
                if first:
                    inserted.set()
                    assert release.wait(timeout=5)
            return 'committed'
        except DomainError as error:
            assert (error.code, error.status) == ('DEMO_CAPACITY', 429)
            return 'capacity'

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(admit, True)
        try:
            assert inserted.wait(timeout=5)
            contender = pool.submit(admit, False)
            pid = contender_pid.get(timeout=5)
            waiting = False
            deadline = monotonic()+2
            with engine.connect() as connection:
                while monotonic() < deadline:
                    waiting = connection.scalar(text("SELECT EXISTS (SELECT 1 FROM pg_locks "
                        "WHERE pid=:pid AND locktype='advisory' AND NOT granted)"), {'pid': pid})
                    if waiting or contender.done():
                        break
                    release.wait(.01)
            # The first insert remains uncommitted. The contender must wait,
            # then count that committed row instead of using the old snapshot.
            assert waiting
        finally:
            release.set()
        assert sorted([first.result(timeout=5), contender.result(timeout=5)]) == ['capacity', 'committed']
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Workspace)) == CAPACITY


def test_full_capacity_reset_rolls_back_and_existing_session_continues(admission_rows):
    engine, settings, owned = admission_rows
    headers = {'x-choreograph-bridge': settings.bridge_secret, 'origin': settings.origin}
    app = create_app(settings, engine, lambda: NOW)
    with TestClient(app) as existing, TestClient(app) as newcomer:
        started = existing.post('/v1/session', json={'timezone': 'Asia/Kathmandu'}, headers=headers)
        assert started.status_code == 200
        state = started.json()
        workspace_id = UUID(state['workspace_id'])
        owned.append(workspace_id)
        token = existing.cookies.get(COOKIE)
        source = b'Synthetic guest source retained after failed reset.'
        with Session(engine) as db, db.begin():
            workspace = db.get(Workspace, workspace_id)
            workspace.draft = {'service': 'regular', 'bedrooms': 1, 'oven': False}
            version = DocumentVersion(owner_id=workspace_id, slot='service', title='Synthetic source',
                version='1', media_type='text/plain', source=source, sha256=hashlib.sha256(source).hexdigest(),
                page_count=1, state='ready', created_at=NOW)
            db.add(version)
            db.flush()
            version_id = version.id
            db.merge(Manifest(workspace_id=workspace_id, slot='service', version_id=version_id))
        before = existing.get('/v1/session', headers=headers).json()
        fill_to(engine, owned, CAPACITY)
        refused = newcomer.post('/v1/session', json={'timezone': 'UTC'}, headers=headers)
        assert refused.status_code == 429 and refused.json() == {
            'code': 'DEMO_CAPACITY', 'message': 'The demo is busy. Please try again later.'}
        assert 'set-cookie' not in refused.headers
        reset = existing.post('/v1/reset', headers={**headers, 'x-csrf-token': before['csrf']},
            json={'timezone': 'UTC', 'generation': before['generation']})
        assert reset.status_code == 429 and reset.json()['code'] == 'DEMO_CAPACITY'
        assert 'set-cookie' not in reset.headers and existing.cookies.get(COOKIE) == token
        continued = existing.get('/v1/session', headers=headers)
        assert continued.status_code == 200 and continued.json() == before
        assert existing.post('/v1/session', json={'timezone': 'UTC'}, headers=headers).json() == before
        with Session(engine) as db:
            workspace = db.get(Workspace, workspace_id)
            assert workspace.active and workspace.generation == before['generation']
            assert workspace.revision == before['revision'] and workspace.purged_at is None
            assert db.get(DocumentVersion, version_id).source == source
            assert db.get(Manifest, (workspace_id, 'service')).version_id == version_id
            assert db.scalar(select(func.count()).select_from(Reservation).where(
                Reservation.workspace_id == workspace_id)) == len(before['calendar'])
            assert db.scalar(select(func.count()).select_from(Workspace)) == CAPACITY
