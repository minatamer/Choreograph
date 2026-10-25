"""Actual authority transactions around delayed injected external work."""
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from test_requests import NOW, command

from choreograph import assistant, knowledge
from choreograph.api import create_app
from choreograph.composition import compose_ai
from choreograph.errors import DomainError
from choreograph.models import AIInteraction, Manifest, Workspace
from choreograph.persistence import Session, is_object, repo_first


def start(database, provider=None, embedder=None):
    engine, settings = database
    with Session(engine) as db, db.begin():
        knowledge.prepare_samples(db, NOW)
    time = [NOW]
    runtime = compose_ai(settings, engine, assistant_provider=provider)
    if embedder is not None:
        runtime.embedder = embedder
    app = create_app(settings, engine, lambda: time[0], ai_runtime=runtime)
    client = TestClient(app)
    headers = {'x-choreograph-bridge': settings.bridge_secret, 'origin': settings.origin}
    state = client.post('/v1/session', headers=headers, json={'timezone': 'UTC'}).json()
    headers['x-csrf-token'] = state['csrf']
    return client, headers, state, time


@pytest.mark.parametrize('phase,change', [('interpret', 'reset'), ('embedding', 'edit'), ('evidence', 'expiry')])
def test_delayed_external_work_keeps_reset_edit_reachable_and_rejects_stale_results(database, phase, change):
    entered, release = Event(), Event()
    engine, _ = database

    def wait():
        # Neither a checked-out connection nor a workspace lock spans external work.
        assert is_object(engine) or engine.pool.checkedout() == 0
        entered.set()
        assert release.wait(8)

    class SlowAssistant(assistant.FakeAssistant):
        def interpret(self, *args):
            if phase == 'interpret':
                wait()
            return super().interpret(*args)

        def evidence(self, *args):
            if phase == 'evidence':
                wait()
            return super().evidence(*args)

    class SlowEmbedding(knowledge.FakeEmbedding):
        def _get_query_embedding(self, text):
            if phase == 'embedding':
                wait()
            return super()._get_query_embedding(text)

    client, headers, state, clock = start(database, SlowAssistant(), SlowEmbedding())
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(command, client, headers.copy(), state,
                                 {'text': 'Two bedrooms. What cleaning supplies do you bring?'},
                                 '/v1/chat', str(uuid4()), 'post')
            try:
                assert entered.wait(8)
                if change == 'reset':
                    changed = client.post('/v1/reset', headers={**headers, 'idempotency-key': str(uuid4())},
                        json={'generation': state['generation'], 'timezone': 'UTC'})
                elif change == 'edit':
                    changed = command(client, headers, state, {'service': 'deep'})
                else:
                    clock[0] += timedelta(hours=3)
                    changed = client.get('/v1/session', headers=headers)
                assert changed.status_code == (410 if change == 'expiry' else 200)
            finally:
                release.set()
            response = result.result(timeout=8)
            assert response.status_code in {401, 409, 410}
        with Session(engine) as db:
            workspace = db.get(Workspace, UUID(state['workspace_id']))
            assert not workspace.messages
            assert workspace.draft.get('bedrooms') is None
            interaction = repo_first(db, AIInteraction, filters={'workspace_id': workspace.id})
            assert interaction.state != 'completed'
    finally:
        release.set()
        client.close()


def test_failed_provider_key_cannot_repeat_but_completed_chat_replays_without_provider(database):
    class Counted(assistant.FakeAssistant):
        calls = 0
        broken = True

        def interpret(self, *args):
            self.calls += 1
            if self.broken:
                raise DomainError('ASSISTANT_UNAVAILABLE', 'Please try again later.', 503)
            return super().interpret(*args)

    provider = Counted()
    client, headers, state, _ = start(database, provider)
    key = str(uuid4())
    try:
        args = (client, headers, state, {'text': 'Hello'}, '/v1/chat', key, 'post')
        assert command(*args).status_code == 503
        assert command(*args).json()['code'] == 'AI_INTERACTION_USED'
        assert provider.calls == 1
        assert not client.get('/v1/session', headers=headers).json()['messages']
        provider.broken = False
        args = (*args[:5], str(uuid4()), 'post')
        first = command(*args)
        assert first.status_code == 200
        replay = command(*args).json()
        assert replay['replayed'] is True and provider.calls == 2
        assert len(replay['state']['messages']) == 2
    finally:
        client.close()


def test_failed_replacement_preserves_ready_source_and_consumes_durable_attempt(database):
    client, headers, state, _ = start(database)
    slot = 'preparation'
    try:
        before = next(item['id'] for item in state['documents'] if item['slot'] == slot)
        result = command(client, headers, state, {'kind': 'pdf', 'data': base64.b64encode(b'not a pdf').decode()},
                         f'/v1/documents/{slot}/replace', method='post')
        assert result.status_code == 200
        payload = result.json()
        assert payload['document_notice']['ready'] is False
        assert payload['state']['replacements_left'] == 2
        assert payload['state']['revision'] == state['revision'] + 1
        with Session(database[0]) as db:
            workspace = db.get(Workspace, UUID(state['workspace_id']))
            assert workspace.ingestion_attempts == 1
            assert str(db.get(Manifest, (workspace.id, slot)).version_id) == before
        assert client.get(f'/v1/documents/{before}', headers=headers).status_code == 200
    finally:
        client.close()


def test_delayed_replacement_cannot_publish_over_an_edit_and_does_not_refund_attempt(database):
    entered, release = Event(), Event()

    class SlowEmbedding(knowledge.FakeEmbedding):
        def _get_text_embedding(self, text):
            assert is_object(database[0]) or database[0].pool.checkedout() == 0
            entered.set()
            assert release.wait(8)
            return super()._get_text_embedding(text)

    client, headers, state, _ = start(database, embedder=SlowEmbedding())
    before = next(item['id'] for item in state['documents'] if item['slot'] == 'preparation')
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(command, client, headers.copy(), state,
                {'kind': 'text', 'data': base64.b64encode(
                    b'Fictional Juniper preparation guide. Please keep pets safely outside the cleaning rooms.').decode()},
                '/v1/documents/preparation/replace', str(uuid4()), 'post')
            try:
                assert entered.wait(8)
                changed = command(client, headers, state, {'service': 'deep'})
                assert changed.status_code == 200
            finally:
                release.set()
            assert result.result(timeout=8).status_code == 409
        with Session(database[0]) as db:
            workspace = db.get(Workspace, UUID(state['workspace_id']))
            assert workspace.ingestion_attempts == 1
            assert workspace.draft['service'] == 'deep'
            assert str(db.get(Manifest, (workspace.id, 'preparation')).version_id) == before
    finally:
        release.set()
        client.close()
