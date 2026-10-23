"""Bounded host/ASGI measurements against one disposable fake PostgreSQL database."""
import hashlib
import json
import math
import platform
import subprocess
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import median
from time import perf_counter
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'apps/backend'), str(ROOT / 'apps/backend/tests')]

from conftest import database as database_fixture  # noqa: E402
from sqlalchemy import event, func, or_, select  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import Session, aliased  # noqa: E402
from test_booking import add_request, book, prepare  # noqa: E402
from test_jobs import connected_booking  # noqa: E402
from test_requests import NOW, begin  # noqa: E402

from choreograph import jobs, knowledge  # noqa: E402
from choreograph.models import (  # noqa: E402
    Chunk,
    DocumentVersion,
    Manifest,
    Outbox,
    Reservation,
    SimulatedRecord,
    Workspace,
)

SAMPLES = 8
CONCURRENCIES = (1, 4, 8)
stage = 'configuration'


def fingerprints():
    code = "import {sourceFingerprint} from './scripts/release-fingerprint.mjs';const s=await sourceFingerprint();console.log(JSON.stringify({sha256:s.sha256,file_count:Object.keys(s.files).length}));"
    result = subprocess.run(['node', '--input-type=module', '-e', code], cwd=ROOT,
                            capture_output=True, text=True, check=True, timeout=30)
    source = json.loads(result.stdout)
    names = ['scripts/measure-performance.py', 'assets/knowledge/evaluation.json']
    names += ['apps/backend/tests/' + name + '.py' for name in
              ('conftest', 'test_booking', 'test_requests', 'test_jobs', 'test_crm')]
    source['harness_files'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(names)}
    return source


class Statements:
    def __init__(self):
        self.lock = threading.Lock()
        self.count = self.source_selects = 0

    def before(self, _connection, _cursor, statement, _parameters, _context, _many):
        with self.lock:
            self.count += 1
            self.source_selects += int(statement.lstrip().upper().startswith('SELECT') and
                                       'document_versions.source' in statement)

    def snapshot(self):
        with self.lock:
            return self.count, self.source_selects


def measure(name, concurrency, operation, statements, samples=SAMPLES):
    before = statements.snapshot()
    started = perf_counter()

    def attempt(index):
        tick = perf_counter()
        outcome = operation(index)
        return (perf_counter() - tick) * 1000, outcome

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(attempt, range(samples)))
    wall = (perf_counter() - started) * 1000
    after = statements.snapshot()
    durations = sorted(row[0] for row in results)
    return {'operation': name, 'concurrency': concurrency, 'attempts': samples,
            'outcomes': dict(sorted(Counter(row[1] for row in results).items())),
            'p50_ms': round(median(durations), 3), 'p95_ms': round(durations[math.ceil(.95 * samples) - 1], 3),
            'max_ms': round(durations[-1], 3), 'wall_ms': round(wall, 3),
            'sql_statements': after[0] - before[0],
            'sql_per_attempt': (after[0] - before[0]) / samples,
            'source_blob_selects': after[1] - before[1]}


def main():
    global stage
    # Validate routing before reusing the fixture's CREATE/DROP database path.
    with (ROOT / 'apps/backend/.env.local').open(encoding='utf-8') as stream:
        line = next(line for line in stream if line.startswith('CHOREOGRAPH_DATABASE_URL='))
    from io import StringIO

    from dotenv import dotenv_values
    source_url = make_url(dotenv_values(stream=StringIO(line), interpolate=False)['CHOREOGRAPH_DATABASE_URL'])
    if (source_url.host not in {'127.0.0.1', 'localhost'} or source_url.port != 45862 or
            source_url.database != 'choreograph' or source_url.query):
        raise RuntimeError('OWNED_LOCAL_POSTGRES_REQUIRED')
    source = fingerprints()
    fixture = database_fixture.__wrapped__()
    clients = []
    setup = {}
    started = perf_counter()
    stage = 'isolated-database-migration'
    database = next(fixture)
    engine, settings = database
    setup['database_and_migrations_ms'] = round((perf_counter() - started) * 1000, 3)
    assert settings.testing and settings.profile == 'fake'
    assert make_url(settings.database_url).database.startswith('choreograph_test_')
    statements = Statements()
    event.listen(engine, 'before_cursor_execute', statements.before)
    try:
        stage = 'canonical-fake-preparation'
        started = perf_counter()
        with Session(engine) as db, db.begin():
            knowledge.prepare_samples(db, NOW)
        setup['once_corpus_preparation_ms'] = round((perf_counter() - started) * 1000, 3)
        cases = json.loads((knowledge.PACK / 'evaluation.json').read_text(encoding='utf-8'))[:8]
        client, headers, state = begin(database, 'UTC')
        clients.append(client)
        workspace_id = UUID(state['workspace_id'])

        def retrieval(index):
            case = cases[index % len(cases)]
            with Session(engine) as db:
                workspace = db.get(Workspace, workspace_id)
                hits = knowledge.retrieve(db, workspace, case['question'])
                assert 1 <= len(hits) <= 4
                assert any(hit.node.metadata['slot'] == case['slot'] and hit.node.metadata['page'] == case['page']
                           and case['contains'] in hit.node.text for hit in hits)
                for hit in hits:
                    assert knowledge.source(db, workspace, UUID(hit.node.metadata['version_id'])).state == 'ready'
            return 'supported'

        stage = 'warmup-and-source-diagnostic'
        started = perf_counter()
        for index in range(SAMPLES):
            retrieval(index)
        setup['retrieval_warmup_ms'] = round((perf_counter() - started) * 1000, 3)
        with Session(engine) as db:
            workspace = db.get(Workspace, workspace_id)
            sizes = list(db.scalars(knowledge.authorized(db, workspace).with_only_columns(func.octet_length(DocumentVersion.source))))
            vector = knowledge.FakeEmbedding().get_query_embedding(cases[0]['question'])
            candidates = select(func.octet_length(DocumentVersion.source).label('bytes')).select_from(Chunk).join(
                DocumentVersion, DocumentVersion.id == Chunk.version_id).join(Manifest, Manifest.version_id == DocumentVersion.id).where(
                    Manifest.workspace_id == workspace.id, DocumentVersion.state == 'ready',
                    or_(DocumentVersion.owner_id.is_(None), DocumentVersion.owner_id == workspace.id)).order_by(
                        Chunk.embedding.cosine_distance(vector)).limit(64).subquery()
            rows, byte_count = db.execute(select(func.count(), func.sum(candidates.c.bytes))).one()
            diagnostic = {'ready_documents': len(sizes), 'canonical_source_bytes': sum(sizes),
                          'scoped_candidate_rows': rows, 'candidate_source_bytes_if_full_entities_selected': byte_count}
        print(json.dumps({'stage': 'source-diagnostic', 'counts': diagnostic}), flush=True)
        results = []
        for concurrency in CONCURRENCIES:
            stage = f'retrieval-{concurrency}'
            results.append(measure('warm_scoped_retrieval_and_source_authorization', concurrency, retrieval, statements))

        skipped_ids = []
        for concurrency in CONCURRENCIES:
            stage = f'booking-fixtures-{concurrency}'
            started = perf_counter()
            fixtures = [prepare(database) for _ in range(SAMPLES)]
            clients.extend(row[0] for row in fixtures)
            skipped_ids.extend(UUID(row[2]['workspace_id']) for row in fixtures)
            setup[f'booking_fixtures_concurrency_{concurrency}_ms'] = round((perf_counter() - started) * 1000, 3)

            def approval(index,fixtures=fixtures):
                guest, h, s, _ = fixtures[index]
                response = book(guest, h, s, s['requests'][0]['id'], fields={'staff_id': 'ada'})
                assert response.status_code == 200
                payload = response.json()
                assert payload['receipt']['action'] == 'confirmed'
                assert payload['state']['requests'][0]['status'] == 'confirmed'
                assert payload['state']['requests'][0]['booking']['staff_id'] == 'ada'
                assert payload['state']['crm_mode'] == 'skipped' and not guest.app.state.crm.calls
                return 'confirmed'

            stage = f'booking-{concurrency}'
            results.append(measure('independent_guest_approval', concurrency, approval, statements))

        stage = 'session-fixtures'
        for request_count in (1, 10):
            started = perf_counter()
            guest, h, s, start = prepare(database)
            clients.append(guest)
            skipped_ids.append(UUID(s['workspace_id']))
            for _ in range(request_count - 1):
                s = add_request(guest, h, s, start)
            setup[f'session_{request_count}_request_fixture_ms'] = round((perf_counter() - started) * 1000, 3)

            def session_read(_index,guest=guest,h=h,request_count=request_count):
                response = guest.get('/v1/session', headers=h)
                assert response.status_code == 200
                current = response.json()
                assert len(current['requests']) == request_count
                assert all(row['status'] == 'awaiting_review' and row['crm_state'] == 'not_connected'
                           and row['crm_receipt'] is None and not row['crm_links'] for row in current['requests'])
                return 'current'

            stage = f'session-read-{request_count}'
            results.append(measure(f'session_read_{request_count}_requests', 1, session_read, statements))

        worker_fixtures = []
        for concurrency in CONCURRENCIES:
            stage = f'worker-fixtures-{concurrency}'
            started = perf_counter()
            fixtures = [connected_booking(database) for _ in range(SAMPLES)]
            clients.extend(row[0] for row in fixtures)
            worker_fixtures.extend(fixtures)
            setup[f'worker_fixtures_concurrency_{concurrency}_ms'] = round((perf_counter() - started) * 1000, 3)
            delivered = {}
            lock = threading.Lock()

            def delivery(index,fixtures=fixtures,lock=lock,delivered=delivered):
                _guest, _headers, s, provider, event_id = fixtures[index]
                job = jobs.claim(engine, NOW, event_id=event_id, workspace_id=UUID(s['workspace_id']))
                if not job:
                    return 'admission_deferred'
                assert jobs.deliver(engine, settings, provider, job, lambda: NOW)
                with lock:
                    delivered[index] = job
                return 'delivered'

            stage = f'worker-{concurrency}'
            results.append(measure('targeted_worker_claim_and_fake_delivery', concurrency, delivery, statements))
            started = perf_counter()
            for index in range(SAMPLES):
                if index not in delivered:
                    assert delivery(index) == 'delivered'
                assert not jobs.deliver(engine, settings, fixtures[index][3], delivered[index], lambda: NOW)
            setup[f'worker_untimed_drain_and_stale_lease_checks_{concurrency}_ms'] = round((perf_counter() - started) * 1000, 3)

        stage = 'duplicate-worker-claim-probe'
        duplicate = connected_booking(database)
        clients.append(duplicate[0])
        _guest, _headers, s, provider, event_id = duplicate
        barrier = threading.Barrier(8)

        def duplicate_claim(_index):
            barrier.wait(timeout=10)
            return jobs.claim(engine, NOW, event_id=event_id, workspace_id=UUID(s['workspace_id']))

        with ThreadPoolExecutor(max_workers=8) as pool:
            claims = [item for item in pool.map(duplicate_claim, range(8)) if item]
        assert len(claims) == 1
        assert jobs.deliver(engine, settings, provider, claims[0], lambda: NOW)
        worker_fixtures.append(duplicate)
        stage = 'final-database-invariants'
        with Session(engine) as db:
            left, right = aliased(Reservation), aliased(Reservation)
            overlap_count = db.scalar(select(func.count()).select_from(left).join(right,
                (left.workspace_id == right.workspace_id) & (left.staff_id == right.staff_id) &
                (left.id < right.id) & (left.starts_at < right.ends_at) & (right.starts_at < left.ends_at)).where(
                    left.state != 'cancelled', right.state != 'cancelled'))
            assert overlap_count == 0
            assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.workspace_id.in_(skipped_ids))) == 0
            for _guest, _h, s, provider, event_id in worker_fixtures:
                row = db.get(Outbox, (UUID(s['workspace_id']), event_id))
                assert row.state == 'synced' and row.attempts == 1
                assert provider.calls.count('upsert-contacts') == provider.calls.count('upsert-deals') == 1
                assert db.scalar(select(func.count()).select_from(SimulatedRecord).where(
                    SimulatedRecord.account_id == 'simulated-' + s['workspace_id'], SimulatedRecord.archived.is_(False))) == 2
        assert fingerprints() == source
        return {'passed': True, 'profile': 'host-asgi-isolated-postgresql-pgvector-fake',
                'python': platform.python_version(), 'platform': sys.platform, 'source': source,
                'bounds': {'samples_per_group': SAMPLES, 'concurrency': CONCURRENCIES,
                           'sql_pool_size': 5, 'sql_max_overflow': 2, 'worker_admission': 4},
                'timing': 'monotonic per-operation service time; executor queue wait excluded; p95 nearest rank',
                'setup_excluded': setup, 'source_diagnostic_untimed': diagnostic, 'measurements': results,
                'invariants': {'reservation_overlaps': 0, 'skipped_crm_outbox': 0, 'duplicate_claims_admitted': 1,
                               'worker_events_verified_once': len(worker_fixtures)},
                'limits': ['Eight samples per group do not establish capacity or a latency SLO.',
                           'Host in-process ASGI; no browser, deployed networking, Cloud SQL, paid provider or live CRM evidence.',
                           'Migration, corpus preparation, fixture creation and worker drain are outside operation timings.']}
    finally:
        operation_stage = stage
        for client in clients:
            client.close()
        event.remove(engine, 'before_cursor_execute', statements.before)
        stage = 'isolated-database-cleanup'
        try:
            next(fixture)
        except StopIteration:
            stage = operation_stage


if __name__ == '__main__':
    try:
        print(json.dumps(main(), sort_keys=True), flush=True)
    except Exception as error:  # noqa: BLE001 - measurement diagnostics omit SQL, configuration, payloads and exception text.
        import traceback
        print(json.dumps({'passed': False, 'code': 'PERFORMANCE_MEASUREMENT_FAILED', 'stage': stage,
                          'exception_type': type(error).__name__,
                          'last_line': traceback.extract_tb(error.__traceback__)[-1].lineno}), flush=True)
        raise SystemExit(1) from None
