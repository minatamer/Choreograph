import base64

import pytest
from fastapi.testclient import TestClient

from choreograph.release import application
from choreograph.settings import load_environment


def values():
    return {'CHOREOGRAPH_DATABASE_URL': 'postgresql+psycopg://fixture:fixture@127.0.0.1:45862/choreograph_test_release',
            'FAKE_MODE':'true', 'CHOREOGRAPH_BRIDGE_SECRET': 'x' * 40,
            'CHOREOGRAPH_TOKEN_KEY': base64.urlsafe_b64encode(bytes(32)).decode()}


def test_container_configuration_is_explicit_and_live_fails_closed(monkeypatch):
    monkeypatch.setenv('CHOREOGRAPH_PROFILE', 'real')
    assert load_environment(values()).profile == 'fake'
    with pytest.raises(ValueError, match='AI_MODE_SWITCH_INVALID'):
        load_environment({**values(), 'FAKE_MODE':'invalid'})
    socket = 'postgresql+psycopg://fixture:fixture@/choreograph?host=/cloudsql/test-project:us-central1:test-instance'
    assert load_environment({**values(), 'CHOREOGRAPH_DATABASE_URL': socket}).database_url == socket
    for suffix in ('/tmp/socket', '/cloudsql/../../socket', '/cloudsql/project:region:instance/extra'):
        with pytest.raises(ValueError, match='DATABASE_CONFIGURATION_INVALID'):
            load_environment({**values(), 'CHOREOGRAPH_DATABASE_URL': socket.split('?')[0] + '?host=' + suffix})
    for url in (values()['CHOREOGRAPH_DATABASE_URL'] + '?host=remote.example.invalid',
                values()['CHOREOGRAPH_DATABASE_URL'] + '?port=5432',
                values()['CHOREOGRAPH_DATABASE_URL'] + '?service=other',
                socket + '&host=/cloudsql/other:region:instance',
                socket + '&port=5433',
                socket.replace('test-project', 'p' * 80)):
        with pytest.raises(ValueError, match='DATABASE_CONFIGURATION_INVALID'):
            load_environment({**values(), 'CHOREOGRAPH_DATABASE_URL': url})


def test_worker_configuration_is_required_and_guest_routes_are_absent(database):
    engine, settings = database
    with pytest.raises(ValueError, match='TASK_TARGET_INVALID'):
        application('worker', settings, engine, {})
    app = application('worker', settings, engine, {
        'CHOREOGRAPH_TASK_URL': 'https://worker.example.invalid/internal/tasks/crm',
        'CHOREOGRAPH_TASK_AUDIENCE': 'https://worker.example.invalid',
        'CHOREOGRAPH_TASK_SERVICE_EMAIL': 'delivery@test-project.iam.gserviceaccount.com'})
    with TestClient(app) as client:
        assert client.get('/health').json() == {'status': 'ok'}
        assert client.post('/v1/session', json={'timezone': 'UTC'}).status_code == 404
        assert client.post('/internal/tasks/crm', json={}).status_code == 403
