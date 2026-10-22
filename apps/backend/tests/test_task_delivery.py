import base64
import json
from uuid import uuid4

from fastapi.testclient import TestClient
from test_jobs import connected_booking
from test_requests import NOW

from choreograph.task_delivery import TaskTarget, create_delivery_app, task_payload

TARGET = TaskTarget('https://worker.example.invalid/internal/tasks/crm',
                    'https://worker.example.invalid', 'delivery@test-project.iam.gserviceaccount.com')
CLAIMS = {'iss': 'https://accounts.google.com', 'aud': TARGET.audience,
          'email': TARGET.service_email, 'email_verified': True}
HEADERS = {'authorization': 'Bearer injected-test-identity'}


def test_identity_required_before_body_or_database():
    checks = []

    def verify(token, audience):
        checks.append((token, audience))
        return CLAIMS

    client = TestClient(create_delivery_app(None, None, None, TARGET, verifier=verify))
    assert client.post('/internal/tasks/crm', content=b'bad').status_code == 403
    assert checks == []
    for change in ({'email': 'other@test-project.iam.gserviceaccount.com'},
                   {'aud': 'https://other.example.invalid'}, {'email_verified': False}, {'iss': 'untrusted'}):
        app = create_delivery_app(None, None, None, TARGET, verifier=lambda *_, change=change: {**CLAIMS, **change})
        with TestClient(app) as wrong:
            assert wrong.post('/internal/tasks/crm', headers=HEADERS, json={}).status_code == 403
    assert client.post('/internal/tasks/crm', headers=HEADERS, json={'arbitrary': 'command'}).status_code == 422
    assert client.post('/internal/tasks/crm', headers=HEADERS, json={'content': 'x' * 1100}).status_code == 413
    assert client.post('/internal/tasks/crm', headers=HEADERS, content='text').status_code == 415
    client.close()


def test_authenticated_task_uses_persisted_destination_and_replays_safely(database):
    engine, settings = database
    client, headers, state, provider, event = connected_booking(database)
    app = create_delivery_app(settings, engine, provider, TARGET, verifier=lambda *_: CLAIMS, clock=lambda: NOW)
    try:
        body = {'workspace_id': state['workspace_id'], 'event_id': str(event)}
        with TestClient(app) as worker:
            assert worker.post('/internal/tasks/crm', headers=HEADERS,
                               json={**body, 'workspace_id': str(uuid4())}).status_code == 204
            assert 'upsert-contacts' not in provider.calls
            assert worker.post('/internal/tasks/crm', headers=HEADERS, json=body).status_code == 204
            calls = list(provider.calls)
            assert worker.post('/internal/tasks/crm', headers=HEADERS, json=body).status_code == 204
            assert provider.calls == calls
        assert client.get('/v1/session', headers=headers).json()['requests'][0]['crm_state'] == 'simulated_synced'
        task = task_payload(TARGET, state['workspace_id'], event)
        assert json.loads(base64.b64decode(task['httpRequest']['body'])) == body
        assert task['httpRequest']['oidcToken'] == {'serviceAccountEmail': TARGET.service_email,
                                                  'audience': TARGET.audience}
        assert 'access_token' not in json.dumps(task)
    finally:
        client.close()
