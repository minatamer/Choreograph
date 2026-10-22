import asyncio

from fastapi.testclient import TestClient
from test_settings import values

from choreograph.api import Boundary, create_app
from choreograph.settings import Settings


def client():
    return TestClient(create_app(Settings.parse(values(), testing=True)), raise_server_exceptions=False)


def test_health_is_content_free_and_routes_require_bridge():
    with client() as c:
        assert c.get('/health').json() == {'status': 'ok', 'profile': 'fake'}
        assert c.get('/v1/session').status_code == 403
        assert c.post('/v1/session', headers={'x-choreograph-bridge': 'x'*40}, json={}).status_code == 403


def test_body_is_bounded_before_parsing_and_errors_do_not_echo():
    headers = {'x-choreograph-bridge': 'x'*40, 'origin': 'http://127.0.0.1:45860'}
    with client() as c:
        r = c.post('/v1/session', headers=headers, json={'private': 'z'*17000})
        assert r.status_code == 413 and 'zzz' not in r.text
        r = c.post('/v1/session', headers=headers, content='secret-not-json')
        assert r.status_code == 415 and 'secret' not in r.text


def test_total_body_deadline_stops_a_slow_trickle():
    async def run():
        settings = Settings.parse(values(), testing=True)
        sent = []
        async def downstream(*args):
            raise AssertionError('slow body reached parsing')
        async def receive():
            await asyncio.sleep(.004)
            return {'type': 'http.request', 'body': b'x', 'more_body': True}
        async def send(message):
            sent.append(message)
        scope = {'type': 'http', 'path': '/v1/session', 'method': 'POST', 'headers': [
            (b'x-choreograph-bridge', b'x'*40), (b'origin', settings.origin.encode()),
            (b'content-type', b'application/json')]}
        await Boundary(downstream, settings, body_timeout=.015)(scope, receive, send)
        assert sent[0]['status'] == 408
    asyncio.run(run())
