"""Selected CRM security regressions use isolated PostgreSQL and fake transports."""
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_crm import begin, connect
from test_requests import NOW, command

from choreograph import crm, jobs
from choreograph.hubspot import CRMFailure, FakeHubSpot
from choreograph.models import Connection, Installation, OAuthState, Outbox


def provider_for(engine, provider_type=FakeHubSpot):
    provider = provider_type(engine, account_id='security-account-' + uuid4().hex)
    provider.app_id = 'security-app-' + uuid4().hex
    return provider


def uninstall_job(engine, client, headers, state):
    response = command(client, headers, state,
                       {'connection_id': state['connection']['id'], 'confirm': True,
                        'cleanup': False, 'uninstall': True}, '/v1/crm/finish', method='post')
    assert response.status_code == 200, response.text
    state = response.json()['state']
    with Session(engine) as db:
        event = db.scalar(select(Outbox.id).where(Outbox.workspace_id == state['workspace_id'],
                                                Outbox.kind == 'crm_cleanup'))
    job = jobs.claim(engine, NOW, event_id=event, workspace_id=UUID(state['workspace_id']))
    assert job
    return state, job


def test_uninstall_registry_commit_precedes_new_callback_and_old_completion(database, monkeypatch):
    engine, settings = database
    entered = threading.Event()
    release = threading.Event()
    callback_waiting = threading.Event()
    registry_seen_by_callback = []

    class Controlled(FakeHubSpot):
        next_workspace = None

        def exchange(self, code, workspace_id):
            if workspace_id == self.next_workspace:
                with Session(engine) as db:
                    registry_seen_by_callback.append(db.get(Installation, (self.app_id, self.account_id)).state)
            return super().exchange(code, workspace_id)

        def uninstall(self, tokens):
            entered.set()
            assert release.wait(5), 'controlled uninstall was not released'
            return super().uninstall(tokens)

    provider = provider_for(engine, Controlled)
    old, old_headers, old_state, _ = begin(database, provider)
    new, new_headers, new_state, _ = begin(database, provider)
    original_lock = crm.account_lock

    def observe_lock(db):
        if entered.is_set():
            callback_waiting.set()
        return original_lock(db)

    try:
        old_state, _ = connect(old, old_headers, old_state)
        challenge = command(new, new_headers, new_state, {}, '/v1/crm/connect', method='post').json()
        provider.next_workspace = UUID(new_state['workspace_id'])
        old_state, job = uninstall_job(engine, old, old_headers, old_state)
        data = jobs.prepare(engine, settings, provider, job, lambda: NOW)
        monkeypatch.setattr(crm, 'account_lock', observe_lock)
        with ThreadPoolExecutor(max_workers=2) as pool:
            removal = pool.submit(jobs.perform, engine, provider, job, data, lambda: NOW,
                                  time.monotonic() + 90)
            try:
                assert entered.wait(2), 'uninstall did not reach the provider'
                callback = pool.submit(command, new, new_headers, challenge['state'],
                                       {'state': challenge['oauth']['state'], 'code': 'approved'},
                                       '/v1/crm/callback', method='post')
                assert callback_waiting.wait(2), 'new callback did not reach account serialization'
                assert not removal.done() and not callback.done()
                release.set()
                result = removal.result(timeout=5)
                connected = callback.result(timeout=5)
            finally:
                release.set()
        assert connected.status_code == 200, connected.text
        assert connected.json()['state']['crm_mode'] == 'connected'
        assert registry_seen_by_callback == ['uninstalled']
        assert jobs.finish_job(engine, provider, job, lambda: NOW, result=result)
        with Session(engine) as db:
            assert db.get(Installation, (provider.app_id, provider.account_id)).state == 'installed'
            assert db.get(Outbox, (job['workspace_id'], job['event_id'])).state == 'completed'
            assert db.get(Connection, (job['workspace_id'], UUID(old_state['connection']['id']))).state == 'finished'
            assert db.get(Connection, (provider.next_workspace,
                                      UUID(connected.json()['state']['connection']['id']))).state == 'ready'
        assert provider.calls.count('uninstall') == 1
    finally:
        release.set()
        old.close()
        new.close()


@pytest.mark.parametrize(('code', 'retryable', 'ambiguous', 'expected_state'), [
    ('CRM_TIMEOUT', True, True, 'reconciling'),
    ('CRM_AUTH_REQUIRED', False, False, 'needs_attention'),
])
def test_failed_uninstall_keeps_installation_capacity(database, code, retryable, ambiguous, expected_state):
    engine, settings = database

    class Failed(FakeHubSpot):
        def uninstall(self, tokens):
            self.calls.append('uninstall')
            raise CRMFailure(code, retryable, ambiguous)

    provider = provider_for(engine, Failed)
    client, headers, state, _ = begin(database, provider)
    try:
        state, _ = connect(client, headers, state)
        _, job = uninstall_job(engine, client, headers, state)
        assert jobs.deliver(engine, settings, provider, job, lambda: NOW)
        with Session(engine) as db:
            assert db.get(Installation, (provider.app_id, provider.account_id)).state == 'installed'
            event = db.get(Outbox, (job['workspace_id'], job['event_id']))
            assert event.state == expected_state and event.code == code
            assert event.payload['result']['uninstall'] == 'not_requested'
    finally:
        client.close()


def test_repeated_definitive_fake_denial_does_not_reserve_capacity(database):
    engine, _ = database
    provider = provider_for(engine)
    client, headers, state, _ = begin(database, provider)
    try:
        for _ in range(25):
            attempt = command(client, headers, state, {}, '/v1/crm/connect', method='post')
            assert attempt.status_code == 200 and attempt.json()['oauth']
            challenge = attempt.json()
            denied = command(client, headers, challenge['state'],
                             {'state': challenge['oauth']['state'], 'code': 'invalid-code'},
                             '/v1/crm/callback', method='post')
            assert denied.status_code == 200, denied.text
            state = denied.json()['state']
            assert state['crm_mode'] == 'skipped' and state['crm_available']
        with Session(engine) as db:
            outcomes = list(db.scalars(select(OAuthState.outcome).where(OAuthState.workspace_id == state['workspace_id'])))
            assert outcomes == ['denied'] * 25
            assert crm.installed_count(db, provider.app_id) == 0
            assert db.scalar(select(func.count()).select_from(Connection).where(Connection.workspace_id == state['workspace_id'])) == 0
            assert db.scalar(select(func.count()).select_from(Outbox).where(Outbox.workspace_id == state['workspace_id'])) == 0
            assert crm.available(db, provider, NOW + timedelta(days=1))
        assert command(client, headers, state, {}, '/v1/crm/connect', method='post').json()['oauth']
    finally:
        client.close()


@pytest.mark.parametrize('previous_state', [None, 'uninstalled'])
def test_identified_preflight_failure_reserves_one_registry_installation(database, previous_state):
    engine, _ = database

    class Unverified(FakeHubSpot):
        provider = 'hubspot'

        def destinations(self, tokens):
            raise CRMFailure('CRM_SCOPES_REQUIRED')

    provider = provider_for(engine, Unverified)
    if previous_state:
        with Session(engine) as db, db.begin():
            db.add(Installation(app_id=provider.app_id, account_id=provider.account_id,
                                state=previous_state, checked_at=NOW - timedelta(days=1)))
    client, headers, state, _ = begin(database, provider)
    try:
        challenge = command(client, headers, state, {}, '/v1/crm/connect', method='post').json()
        response = command(client, headers, challenge['state'],
                           {'state': challenge['oauth']['state'], 'code': 'approved'},
                           '/v1/crm/callback', method='post')
        assert response.status_code == 200, response.text
        assert response.json()['state']['crm_mode'] == 'skipped'
        with Session(engine) as db:
            installation = db.get(Installation, (provider.app_id, provider.account_id))
            assert installation.state == 'unknown' and installation.checked_at == NOW
            assert crm.installed_count(db, provider.app_id) == 1
            outcome = db.scalar(select(OAuthState).where(OAuthState.workspace_id == state['workspace_id']))
            assert outcome.used and outcome.outcome == 'installed'
            assert db.scalar(select(func.count()).select_from(Connection).where(Connection.workspace_id == state['workspace_id'])) == 0
    finally:
        client.close()


def test_capacity_failure_restores_known_previously_uninstalled_account(database):
    engine, _ = database
    provider = provider_for(engine)
    client, headers, state, _ = begin(database, provider)
    try:
        challenge = command(client, headers, state, {}, '/v1/crm/connect', method='post').json()
        with Session(engine) as db, db.begin():
            db.add(Installation(app_id=provider.app_id, account_id=provider.account_id,
                                state='uninstalled', checked_at=NOW - timedelta(days=1)))
            for number in range(25):
                db.add(Installation(app_id=provider.app_id, account_id=str(number),
                                    state='installed', checked_at=NOW))
        response = command(client, headers, challenge['state'],
                           {'state': challenge['oauth']['state'], 'code': 'approved'},
                           '/v1/crm/callback', method='post')
        assert response.status_code == 200, response.text
        assert response.json()['state']['crm_mode'] == 'skipped'
        with Session(engine) as db:
            installation = db.get(Installation, (provider.app_id, provider.account_id))
            assert installation.state == 'unknown' and installation.checked_at == NOW
            assert crm.installed_count(db, provider.app_id) == 26
            assert db.scalar(select(OAuthState.outcome).where(OAuthState.workspace_id == state['workspace_id'])) == 'installed'
    finally:
        client.close()


def test_nonfake_denial_keeps_unidentified_installation_uncertain(database):
    engine, _ = database

    class Unidentified(FakeHubSpot):
        provider = 'hubspot'

        def exchange(self, code, workspace_id):
            raise CRMFailure('CRM_DENIED')

    provider = provider_for(engine, Unidentified)
    client, headers, state, _ = begin(database, provider)
    try:
        challenge = command(client, headers, state, {}, '/v1/crm/connect', method='post').json()
        response = command(client, headers, challenge['state'],
                           {'state': challenge['oauth']['state'], 'code': 'invalid-code'},
                           '/v1/crm/callback', method='post')
        assert response.status_code == 200, response.text
        with Session(engine) as db:
            outcome = db.scalar(select(OAuthState).where(OAuthState.workspace_id == state['workspace_id']))
            assert outcome.used and outcome.outcome == 'unknown' and outcome.expires_at < NOW + timedelta(days=1)
            assert crm.installed_count(db, provider.app_id) == 0
    finally:
        client.close()
