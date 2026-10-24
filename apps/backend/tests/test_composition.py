from dataclasses import FrozenInstanceError
from uuid import uuid4

import httpx
import pytest
from test_ai_config import live_values

from choreograph import composition
from choreograph.ai_admission import FAKE_SPEC, AttemptScope
from choreograph.errors import DomainError
from choreograph.settings import Settings


class BorrowedClient:
    def __init__(self):
        self.closes = 0

    def close(self):
        self.closes += 1


def test_fake_composition_is_inert_and_preserves_explicit_assistant_override(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('Fake composition must not read vocabularies or construct clients')
    monkeypatch.setattr(composition, 'load_tokenizer', denied)
    monkeypatch.setattr(composition, '_client', denied)
    settings = Settings.parse({**live_values(), 'FAKE_MODE':'true'}, testing=True)
    assistant = object()
    runtime = composition.compose_ai(settings, object(), assistant_provider=assistant)
    scoped = runtime.for_scope(AttemptScope(uuid4(), 1, str(uuid4())))
    assert scoped.assistant is assistant
    assert scoped.spec == FAKE_SPEC
    assert scoped.tokenizer is None and scoped.admission is None
    runtime.close()
    runtime.close()


def test_scopes_have_separate_admission_and_borrowed_clients_remain_caller_owned():
    response, embedding = BorrowedClient(), BorrowedClient()
    engine = object()
    runtime = composition.compose_ai(Settings.parse(live_values()), engine,
                                     response_client=response, embedding_client=embedding)
    first_scope = AttemptScope(uuid4(), 1, str(uuid4()), 3)
    second_scope = AttemptScope(first_scope.workspace_id, 2, str(uuid4()), 4)
    first = runtime.for_scope(first_scope)
    second = runtime.for_scope(second_scope)
    assert first.admission is not second.admission
    assert first.admission.scope == first_scope and second.admission.scope == second_scope
    assert first.admission.engine is engine
    assert first.assistant.admission is first.admission
    assert second.assistant.admission is second.admission
    assert runtime.assistant.admission is None
    assert first.embedder is not second.embedder
    assert first.tokenizer is runtime.tokenizer
    with pytest.raises(FrozenInstanceError):
        first.admission = None
    runtime.close()
    runtime.close()
    assert response.closes == embedding.closes == 0
    with pytest.raises(ValueError, match='AI_RUNTIME_CLOSED'):
        runtime.for_scope(first_scope)


class CountingTransport(httpx.MockTransport):
    def __init__(self):
        super().__init__(self.respond)
        self.requests = []
        self.closes = 0

    def respond(self, request):
        self.requests.append(request)
        return httpx.Response(200, json={
            'id': 'synthetic-response', 'object': 'response', 'created_at': 0,
            'status': 'completed', 'model': 'operator-response-model',
            'output': [{'type': 'message', 'id': 'synthetic-message', 'role': 'assistant', 'status':'completed',
                        'content': [{'type': 'output_text', 'text': '{"status":"insufficient","claims":[]}',
                                     'annotations': []}]}],
            'usage': {'input_tokens': 10, 'output_tokens': 10, 'total_tokens': 20},
        })

    def close(self):
        self.closes += 1


def test_injected_http_uses_fixed_endpoint_no_ambient_auth_and_closes_once(monkeypatch):
    from choreograph.providers import GroundedOutput

    monkeypatch.setenv('OPENAI_BASE_URL', 'https://ambient.example.invalid')
    monkeypatch.setenv('OPENAI_CUSTOM_HEADERS', 'Authorization: Bearer ambient-secret\nOpenAI-Project: ambient-project')
    monkeypatch.setenv('OPENAI_ORG_ID', 'ambient-org')
    response, embedding = CountingTransport(), CountingTransport()
    runtime = composition.compose_ai(Settings.parse(live_values()), object(),
                                     response_transport=response, embedding_transport=embedding)
    # Raw composed adapters cannot invoke external work before scope admission.
    with pytest.raises(DomainError, match='LIVE_NOT_CONFIGURED'):
        runtime.assistant.structured(GroundedOutput, 'synthetic instructions', {'question': 'supplies'})
    assert not response.requests
    gate = runtime.for_scope(AttemptScope(uuid4(), 1, str(uuid4()))).admission
    # The durable implementation is covered by actual PostgreSQL admission tests;
    # this hermetic seam exercises SDK routing and envelope handling only.
    gate.run = lambda phase, batch, **kwargs: kwargs['invoke']().value
    assistant = runtime.assistant.with_admission(gate)
    assert assistant.structured(GroundedOutput, 'synthetic instructions', {}).status == 'insufficient'
    assert len(response.requests) == 1
    request = response.requests[0]
    assert str(request.url) == 'https://api.openai.com/v1/responses'
    assert request.headers['authorization'] == 'Bearer synthetic-key-never-used-externally'
    assert request.headers.get('openai-project', '') == ''
    assert request.headers.get('openai-organization', '') == ''
    assert runtime.assistant.client.max_retries == 0
    assert runtime.embedder._client._client.response_bytes == 524_288
    runtime.close()
    runtime.close()
    assert response.closes == embedding.closes == 1


def test_partial_construction_failure_closes_created_client_only(monkeypatch):
    response = CountingTransport()
    original = composition._client

    def fail_second(key, **kwargs):
        if kwargs['response_bytes'] == 524_288:
            raise ValueError('synthetic-construction-failure')
        return original(key, **kwargs)
    monkeypatch.setattr(composition, '_client', fail_second)
    with pytest.raises(ValueError, match='synthetic-construction-failure'):
        composition.compose_ai(Settings.parse(live_values()), object(), response_transport=response)
    assert response.closes == 1


def test_scope_forwards_one_absolute_deadline_to_shared_admission(monkeypatch):
    captured = []
    def admission(engine, grant, scope, clock, **kwargs):
        captured.append(kwargs)
        return object()
    monkeypatch.setattr(composition, 'Admission', admission)
    runtime = composition.compose_ai(Settings.parse(live_values()), object(),
                                     response_client=BorrowedClient(), embedding_client=BorrowedClient())
    scoped = runtime.for_scope(AttemptScope(uuid4(), 1, str(uuid4())), deadline=123.5)
    assert captured == [{'monotonic_deadline': 123.5}]
    assert scoped.assistant.admission is scoped.admission
    runtime.close()
