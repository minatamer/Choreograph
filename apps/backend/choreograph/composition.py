"""Explicit AI ownership and immutable per-command admission bindings."""
from contextlib import ExitStack
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .ai_admission import FAKE_SPEC, Admission, EmbeddingSpec
from .tokenizers import load_tokenizer


@dataclass(frozen=True)
class ScopedAI:
    assistant: object = field(repr=False)
    embedder: object = field(repr=False)
    spec: EmbeddingSpec
    tokenizer: object = field(repr=False)
    admission: Admission | None = field(repr=False)


@dataclass
class AIRuntime:
    assistant: object = field(repr=False)
    embedder: object = field(repr=False)
    spec: EmbeddingSpec
    tokenizer: object = field(repr=False)
    _engine: object = field(repr=False)
    _grant: object = field(repr=False)
    _clock: object = field(repr=False)
    _owned: ExitStack = field(repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    def admission(self, scope, *, clock=None, deadline=None):
        if self._closed:
            raise ValueError('AI_RUNTIME_CLOSED')
        if self._grant is None:
            return None
        options = {'monotonic_deadline': deadline} if deadline is not None else {}
        return Admission(self._engine, self._grant, scope, clock or self._clock, **options)

    def for_scope(self, scope, *, clock=None, deadline=None):
        gate = self.admission(scope, clock=clock, deadline=deadline)
        if gate is None:
            return ScopedAI(self.assistant, self.embedder, self.spec, self.tokenizer, None)
        return ScopedAI(self.assistant.with_admission(gate), self.embedder.with_admission(gate),
                        self.spec, self.tokenizer, gate)

    def close(self):
        if not self._closed:
            self._closed = True
            self._owned.close()


def _client(key, *, transport, response_bytes, owned):
    from openai import OpenAI

    from .providers import PROVIDER_TIMEOUT, BoundedOpenAIClient

    bounded = BoundedOpenAIClient(transport=transport, response_bytes=response_bytes)
    constructed = False
    try:
        client = OpenAI(api_key=key, base_url='https://api.openai.com/v1', max_retries=0,
                        organization='', project='', admin_api_key='', webhook_secret='',
                        timeout=PROVIDER_TIMEOUT, http_client=bounded)
        # Pinned SDK 3.36.1 reads OPENAI_CUSTOM_HEADERS even with explicit client
        # options. Drop that ambient override before the first request; only
        # SDK-generated headers and the explicitly supplied key are permitted.
        client._custom_headers = {}
        constructed = True
        owned.callback(client.close)
        return client
    finally:
        if not constructed:
            bounded.close()


def compose_ai(settings, engine, *, assistant_provider=None, response_client=None,
               embedding_client=None, response_transport=None, embedding_transport=None, clock=None):
    """Fake composition creates no HTTP clients; borrowed clients stay caller-owned."""
    from .assistant import FakeAssistant
    from .knowledge import FakeEmbedding, OpenAIEmbedding
    from .providers import OpenAITransport

    current_time = clock or (lambda: datetime.now(UTC))
    owned = ExitStack()
    if settings.profile == 'fake':
        return AIRuntime(assistant_provider if assistant_provider is not None else FakeAssistant(),
                         FakeEmbedding(FAKE_SPEC), FAKE_SPEC, None, engine, None, current_time, owned)
    config = settings.live_ai
    if settings.profile != 'live' or config is None or assistant_provider is not None:
        raise ValueError('LIVE_AI_CONFIGURATION_INVALID')
    if settings.testing:
        raise ValueError('TEST_PROVIDER_FORBIDDEN')
    if config.grant.expires_at <= current_time():
        raise ValueError('LIVE_AI_GRANT_EXPIRED')
    if (response_client is not None and response_transport is not None or
            embedding_client is not None and embedding_transport is not None):
        raise ValueError('AI_CLIENT_CONFIGURATION_INVALID')
    response_tokenizer = load_tokenizer(config.response_tokenizer, config.tokenizer_directory)
    embedding_tokenizer = (response_tokenizer if config.response_tokenizer == config.spec.tokenizer else
                           load_tokenizer(config.spec.tokenizer, config.tokenizer_directory))
    try:
        if response_client is None:
            response_client = _client(config.api_key, transport=response_transport,
                                      response_bytes=65_536, owned=owned)
        if embedding_client is None:
            embedding_client = _client(config.api_key, transport=embedding_transport,
                                       response_bytes=524_288, owned=owned)
        assistant = OpenAITransport(model=config.grant.response_model, client=response_client,
                                    authorized=True, tokenizer=response_tokenizer,reasoning_effort=config.reasoning_effort)
        # Even an injected SDK client needs durable admission in composed live mode.
        assistant.requires_admission = True
        embedder = OpenAIEmbedding(config.spec, client=embedding_client, authorized=True,
                                   tokenizer=embedding_tokenizer)
        return AIRuntime(assistant, embedder, config.spec, embedding_tokenizer,
                         engine, config.grant, current_time, owned)
    except BaseException:
        owned.close()
        raise
