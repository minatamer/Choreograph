"""Exercise the real SDK with only injected byte streams; never use the network."""
import gzip
import json

import httpx
import pytest
from openai import OpenAI

from choreograph.errors import DomainError
from choreograph.providers import RESPONSE_BYTES, RESPONSE_SECONDS, BoundedOpenAIClient, OpenAITransport


class CountedStream(httpx.SyncByteStream):
    def __init__(self, body, *, advance=None):
        self.body = body
        self.advance = advance
        self.read_bytes = 0
        self.closed = False

    def __iter__(self):
        for offset in range(0, len(self.body), 4096):
            if self.advance:
                self.advance()
            chunk = self.body[offset:offset + 4096]
            self.read_bytes += len(chunk)
            yield chunk

    def close(self):
        self.closed = True


def envelope():
    intent = {'intent': 'greeting', 'service': None, 'bedrooms': None, 'oven': None,
              'requested_date': None, 'requested_time': None, 'guide_question': None}
    return json.dumps({'id': 'resp_injected', 'object': 'response', 'created_at': 0,
                       'status': 'completed', 'output': [{'type': 'message', 'id': 'msg_injected',
                        'role': 'assistant', 'status': 'completed', 'content': [
                        {'type': 'output_text', 'text': json.dumps(intent), 'annotations': []}]}]}).encode()


def invoke(stream, *, status=200, headers=None, clock=None):
    calls = []

    def handle(request):
        calls.append(request)
        assert request.headers['accept-encoding'] == 'identity'
        assert request.extensions['timeout']['read'] == RESPONSE_SECONDS
        return httpx.Response(status, headers={'content-type': 'application/json', **(headers or {})}, stream=stream)

    client = BoundedOpenAIClient(transport=httpx.MockTransport(handle), **({'clock': clock} if clock else {}))
    sdk = OpenAI(api_key='injected-not-a-real-key', base_url='https://example.invalid/v1',
                 max_retries=0, http_client=client)
    adapter = OpenAITransport(model='injected-test-only', client=sdk, authorized=True)
    try:
        result = adapter.interpret('hello', {}, 'UTC', '2026-10-22')
        return result, calls
    finally:
        sdk.close()
        assert len(calls) == 1


@pytest.mark.parametrize('status', [200, 502])
def test_sdk_success_and_error_bodies_stop_before_full_materialization(status):
    stream = CountedStream(b'x' * (RESPONSE_BYTES * 4))
    with pytest.raises(DomainError) as error:
        invoke(stream, status=status)
    assert error.value.code == 'ASSISTANT_UNAVAILABLE'
    assert stream.closed and stream.read_bytes == RESPONSE_BYTES + 4096


def test_compressed_expansion_is_rejected_before_decoder_or_sdk():
    stream = CountedStream(gzip.compress(b'x' * (RESPONSE_BYTES * 100)))
    with pytest.raises(DomainError) as error:
        invoke(stream, headers={'content-encoding': 'gzip'})
    assert error.value.code == 'ASSISTANT_UNAVAILABLE'
    assert stream.closed and stream.read_bytes == 0


@pytest.mark.parametrize('length', [str(RESPONSE_BYTES + 1), 'invalid'])
def test_invalid_or_oversized_declared_response_is_closed_without_reading(length):
    stream = CountedStream(b'body')
    with pytest.raises(DomainError):
        invoke(stream, headers={'content-length': length})
    assert stream.closed and stream.read_bytes == 0


def test_response_budget_stops_slow_chunks_and_never_falls_back():
    now = [0]

    def advance():
        now[0] += 5

    stream = CountedStream(b'x' * (RESPONSE_BYTES * 4), advance=advance)
    with pytest.raises(DomainError) as error:
        invoke(stream, clock=lambda: now[0])
    assert error.value.code == 'ASSISTANT_TIMEOUT'
    assert stream.closed and stream.read_bytes == 3 * 4096


def test_bounded_sdk_response_still_uses_strict_envelope():
    stream = CountedStream(envelope())
    result, calls = invoke(stream)
    assert result.intent == 'greeting' and stream.closed
    payload = json.loads(calls[0].content)
    assert payload['store'] is False and payload['max_output_tokens'] == 1400
    assert payload['text']['format']['strict'] is True


def test_valid_envelope_with_late_eof_still_exceeds_response_budget():
    now = [0]

    class DelayedEOF(CountedStream):
        def __iter__(self):
            yield from super().__iter__()
            now[0] = 13

    stream = DelayedEOF(envelope())
    with pytest.raises(DomainError) as error:
        invoke(stream, clock=lambda: now[0])
    assert error.value.code == 'ASSISTANT_TIMEOUT' and stream.closed


def test_nonstreaming_first_byte_may_take_longer_than_one_second_within_budget():
    now=[0]
    def advance():now[0]+=2
    stream=CountedStream(envelope(),advance=advance)
    result,_=invoke(stream,clock=lambda:now[0])
    assert result.intent=='greeting' and 1<now[0]<RESPONSE_SECONDS and stream.closed


@pytest.mark.parametrize('status,code',[(401,'ASSISTANT_CREDENTIALS'),(403,'ASSISTANT_ACCESS_DENIED'),
    (404,'ASSISTANT_MODEL_UNAVAILABLE'),(400,'ASSISTANT_CONFIGURATION'),(429,'ASSISTANT_BUSY')])
def test_provider_http_failures_remain_fixed_private_diagnostics_without_retry(status,code):
    stream=CountedStream(b'{"error":{"message":"private-provider-body-marker","type":"invalid_request_error"}}')
    with pytest.raises(DomainError) as error:invoke(stream,status=status)
    assert error.value.code==code and 'private-provider-body-marker' not in error.value.message and stream.closed
