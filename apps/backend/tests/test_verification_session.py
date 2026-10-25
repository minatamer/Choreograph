"""Recent human verification is scoped, finite and independent of AI authority."""
import json
from dataclasses import replace
from datetime import timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from test_requests import NOW, command

from choreograph import assistant, knowledge
from choreograph.api import create_app
from choreograph.models import Workspace
from choreograph.persistence import Session, is_object
from choreograph.verification import (
    CHAT_COOKIE,
    CHAT_VERIFICATION_SECONDS,
    TurnstileConfig,
    TurnstileVerifier,
)


@pytest.fixture
def protected(database):
    engine, base = database
    now = [NOW]
    proofs = {}
    calls = []
    used = set()
    config = TurnstileConfig('synthetic-site', 'synthetic-secret', '127.0.0.1')
    settings = replace(base, turnstile=config)
    with Session(engine) as db, db.begin():
        knowledge.prepare_samples(db, NOW)

    class Counted(assistant.FakeAssistant):
        count = 0

        def interpret(self, *args):
            self.count += 1
            return super().interpret(*args)

    provider = Counted()

    def siteverify(request):
        assert is_object(engine) or engine.pool.checkedout() == 0
        token = json.loads(request.content)['response']
        calls.append(token)
        if token not in proofs or token in used:
            return httpx.Response(200, json={'success': False})
        used.add(token)
        action, nonce = proofs[token]
        return httpx.Response(200, json={'success': True, 'hostname': config.hostname,
                                       'action': action, 'cdata': nonce})

    verifier = TurnstileVerifier(config, transport=httpx.MockTransport(siteverify))
    app = create_app(settings, engine, lambda: now[0], assistant_provider=provider, verification_provider=verifier)
    client = TestClient(app)
    headers = {'origin': settings.origin, 'x-choreograph-bridge': settings.bridge_secret}

    def proof(action):
        nonce, token = str(uuid4()), str(uuid4())
        proofs[token] = (action, nonce)
        return {'idempotency-key': nonce, 'x-turnstile-token': token}

    state = client.post('/v1/session', headers={**headers, **proof('workspace')}, json={'timezone': 'UTC'}).json()
    headers['x-csrf-token'] = state['csrf']
    try:
        yield client, headers, state, now, calls, provider, proof, app
    finally:
        client.close()
        verifier.close()


def test_successful_session_covers_later_chat_without_renewing_its_receipt(protected):
    client, headers, state, now, calls, provider, _, _ = protected
    stamp = client.cookies.get(CHAT_COOKIE)
    assert stamp and all(proof not in stamp for proof in calls)
    for _ in range(3):
        response = command(client, headers, state, {'text': 'Hello'}, '/v1/chat', method='post')
        assert response.status_code == 200
        assert not response.headers.get_list('set-cookie')
        state = response.json()['state']
    assert len(calls) == 1 and provider.count == 3
    assert client.cookies.get(CHAT_COOKIE) == stamp
    assert not client.get('/v1/session', headers=headers).headers.get_list('set-cookie')
    now[0] += timedelta(seconds=CHAT_VERIFICATION_SECONDS)
    response = command(client, headers, state, {'text': 'Hello'}, '/v1/chat', method='post')
    assert response.status_code == 403 and response.json()['code'] == 'VERIFICATION_REQUIRED'
    assert provider.count == 3 and len(calls) == 1


@pytest.mark.parametrize('value', ['forged', 'v1.1.999999999999.' + '0'*64, 'x'*111])
def test_tampered_or_oversized_receipts_fail_before_ai(protected, value):
    client, headers, state, _, calls, provider, _, _ = protected
    client.cookies.set(CHAT_COOKIE, value, domain='testserver.local', path='/')
    response = command(client, headers, state, {'text': 'Hello'}, '/v1/chat', method='post')
    assert response.status_code == 403 and response.json()['code'] == 'VERIFICATION_REQUIRED'
    assert provider.count == 0 and len(calls) == 1


def test_expired_receipt_can_renew_once_with_a_fresh_command_bound_proof(protected):
    client, headers, state, now, calls, provider, proof, _ = protected
    old = client.cookies.get(CHAT_COOKIE)
    now[0] += timedelta(seconds=CHAT_VERIFICATION_SECONDS)
    fresh = proof('assistant')
    failed = command(client, headers, state, {'text': 'Hello'}, '/v1/chat', fresh['idempotency-key'], method='post')
    assert failed.status_code == 403 and provider.count == 0
    accepted = command(client, {**headers, **fresh}, state, {'text': 'Hello'}, '/v1/chat', fresh['idempotency-key'], method='post')
    assert accepted.status_code == 200 and len(calls) == 2 and provider.count == 1
    receipt = accepted.headers.get_list('set-cookie')[0]
    assert 'HttpOnly' in receipt and 'SameSite=lax' in receipt and 'Max-Age=1800' in receipt
    assert client.cookies.get(CHAT_COOKIE) != old
    state = accepted.json()['state']
    assert command(client, headers, state, {'text': 'Hello'}, '/v1/chat', method='post').status_code == 200
    assert len(calls) == 2 and provider.count == 2


def test_valid_receipt_never_overrides_an_explicit_bad_proof_or_csrf(protected):
    client, headers, state, _, calls, provider, _, _ = protected
    rejected = command(client, {**headers, 'x-turnstile-token': 'unknown'}, state, {'text': 'Hello'}, '/v1/chat', method='post')
    assert rejected.status_code == 403 and rejected.json()['code'] == 'VERIFICATION_REQUIRED'
    assert provider.count == 0 and len(calls) == 2
    rejected = command(client, {**headers, 'x-csrf-token': 'wrong'}, state, {'text': 'Hello'}, '/v1/chat', method='post')
    assert rejected.status_code == 403 and rejected.json()['code'] == 'CSRF_REQUIRED'
    assert provider.count == 0 and len(calls) == 2
    client.cookies.delete('choreograph_guest')
    rejected = command(client, headers, state, {'text': 'Hello'}, '/v1/chat', method='post')
    assert rejected.status_code == 401 and rejected.json()['code'] == 'SESSION_REQUIRED'
    assert provider.count == 0 and len(calls) == 2


def test_receipt_is_bound_to_session_workspace_generation_and_current_keys(protected, database):
    client, headers, state, _, calls, provider, proof, app = protected
    old = client.cookies.get(CHAT_COOKIE)
    with TestClient(app) as other:
        second = other.post('/v1/session', headers={**headers, **proof('workspace')}, json={'timezone': 'UTC'}).json()
        other.cookies.set(CHAT_COOKIE, old, domain='testserver.local', path='/')
        rejected = command(other, {**headers, 'x-csrf-token': second['csrf']}, second,
                           {'text': 'Hello'}, '/v1/chat', method='post')
        assert rejected.status_code == 403 and provider.count == 0
    engine, _ = database
    with Session(engine) as db, db.begin():
        db.get(Workspace, UUID(state['workspace_id'])).generation += 1
    state['generation'] += 1
    assert command(client, headers, state, {'text': 'Hello'}, '/v1/chat', method='post').status_code == 403
    assert provider.count == 0 and len(calls) == 2
    with Session(engine) as db, db.begin():
        db.get(Workspace, UUID(state['workspace_id'])).generation -= 1
    state['generation'] -= 1
    settings = app.state.settings
    app.state.settings = replace(settings, turnstile=replace(settings.turnstile, secret_key='rotated'))
    assert command(client, headers, state, {'text': 'Hello'}, '/v1/chat', method='post').status_code == 403
    assert provider.count == 0


def test_renewed_receipt_cannot_outlive_its_guest_workspace(protected):
    client, headers, state, now, calls, provider, proof, _ = protected
    now[0] += timedelta(hours=2, seconds=-10)
    fresh = proof('assistant')
    accepted = command(client, {**headers, **fresh}, state, {'text': 'Hello'}, '/v1/chat', fresh['idempotency-key'], method='post')
    assert accepted.status_code == 200 and len(calls) == 2 and provider.count == 1
    assert 'Max-Age=10' in accepted.headers.get_list('set-cookie')[0]
    now[0] += timedelta(seconds=10)
    rejected = command(client, headers, accepted.json()['state'], {'text': 'Hello'}, '/v1/chat', method='post')
    assert rejected.status_code == 410 and provider.count == 1 and len(calls) == 2


def test_reset_and_document_upload_still_require_fresh_verification(protected):
    client, headers, state, _, calls, provider, proof, _ = protected
    old = client.cookies.get(CHAT_COOKIE)
    rejected = command(client, headers, state, {'kind': 'text', 'data': 'Tm8='},
                       '/v1/documents/preparation/replace', method='post')
    assert rejected.status_code == 403 and rejected.json()['code'] == 'VERIFICATION_REQUIRED'
    rejected = client.post('/v1/reset', headers=headers, json={'generation': state['generation'], 'timezone': 'UTC'})
    assert rejected.status_code == 403 and len(calls) == 1 and provider.count == 0
    reset = client.post('/v1/reset', headers={**headers, **proof('workspace')},
                        json={'generation': state['generation'], 'timezone': 'UTC'})
    assert reset.status_code == 200
    state = reset.json()
    headers['x-csrf-token'] = state['csrf']
    assert state['workspace_id'] and client.cookies.get(CHAT_COOKIE) != old
    client.cookies.set(CHAT_COOKIE, old, domain='testserver.local', path='/')
    assert command(client, headers, state, {'text': 'Hello'}, '/v1/chat', method='post').status_code == 403
    assert provider.count == 0 and len(calls) == 2
