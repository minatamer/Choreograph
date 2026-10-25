"""Explicit operator-supplied AI configuration; no environment or client access."""
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .ai_admission import EmbeddingSpec, GrantSpec, ManualGrantSpec
from .tokenizers import ASSET_DIRECTORY, RESPONSE_COUNTER

POSITIVE_GRANT_FIELDS = (
    'requests', 'input_tokens', 'output_tokens', 'vectors', 'cost_micros',
    'workspace_requests', 'workspace_input_tokens', 'workspace_output_tokens',
    'workspace_vectors', 'workspace_cost_micros', 'response_input_rate',
    'response_output_rate', 'embedding_input_rate',
)
SUPPORTED_TOKENIZERS = frozenset({'cl100k_base', 'o200k_base'})
LIVE_CHUNKER = 'llama-token-section-v4'


def runtime_values(values:Mapping[str,str]):
    """Validate the only two public mode controls; no legacy aliases."""
    result=dict(values)
    for name in ('FAKE_MODE','PAID_DEMO_ENABLED'):
        if name in result and result[name] not in {'true','false'}:
            raise ValueError('AI_MODE_SWITCH_INVALID')
    return result


@dataclass(frozen=True)
class LiveAIConfig:
    api_key: str = field(repr=False)
    response_tokenizer: str
    tokenizer_directory: str
    spec: EmbeddingSpec
    grant: GrantSpec | ManualGrantSpec
    reasoning_effort:str|None=None


def _identifier(values, name, *, maximum=100):
    value = values.get(name, '')
    if (not isinstance(value, str) or not value or len(value) > maximum
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]*', value)):
        raise ValueError('LIVE_AI_CONFIGURATION_INVALID')
    return value


def _positive(values, name):
    value = values.get(name, '')
    if not isinstance(value, str) or not re.fullmatch(r'[1-9][0-9]{0,18}', value):
        raise ValueError('LIVE_AI_CONFIGURATION_INVALID')
    number = int(value)
    if number > 2**63 - 1:
        raise ValueError('LIVE_AI_CONFIGURATION_INVALID')
    return number


def parse_live_ai(values: Mapping[str, str], *, now: datetime | None = None,
                  manual_grant_id: str | None = None) -> LiveAIConfig:
    """Require every spending input; flags or inherited SDK defaults are insufficient."""
    if values.get('PAID_DEMO_ENABLED') != 'true':
        raise ValueError('LIVE_AI_NOT_ENABLED')
    key = values.get('OPENAI_API_KEY', '')
    if not isinstance(key, str) or not key or len(key) > 512 or any(char.isspace() for char in key):
        raise ValueError('LIVE_AI_CONFIGURATION_INVALID')
    expires = None
    if manual_grant_id is None:
        try:
            expires = datetime.fromisoformat(values.get('CHOREOGRAPH_AI_EXPIRES_AT', '').replace('Z', '+00:00'))
            if expires.tzinfo is None or expires.utcoffset() is None:
                raise ValueError()
            expires = expires.astimezone(UTC)
        except (ValueError, TypeError, AttributeError, OverflowError):
            raise ValueError('LIVE_AI_CONFIGURATION_INVALID') from None
        if expires <= (now or datetime.now(UTC)):
            raise ValueError('LIVE_AI_GRANT_EXPIRED')
    response_model = _identifier(values, 'CHOREOGRAPH_AI_RESPONSE_MODEL')
    embedding_model = _identifier(values, 'CHOREOGRAPH_AI_EMBEDDING_MODEL')
    response_tokenizer = _identifier(values, 'CHOREOGRAPH_AI_RESPONSE_TOKENIZER')
    embedding_tokenizer = _identifier(values, 'CHOREOGRAPH_AI_EMBEDDING_TOKENIZER')
    chunker = _identifier(values, 'CHOREOGRAPH_AI_CHUNKER')
    directory = values.get('CHOREOGRAPH_AI_TOKENIZER_DIRECTORY', str(ASSET_DIRECTORY))
    if (response_tokenizer not in SUPPORTED_TOKENIZERS|{RESPONSE_COUNTER} or embedding_tokenizer not in SUPPORTED_TOKENIZERS
            or chunker != LIVE_CHUNKER or not isinstance(directory, str) or not directory
            or len(directory) > 4096 or '://' in directory or '\x00' in directory):
        raise ValueError('LIVE_AI_CONFIGURATION_INVALID')
    spec = EmbeddingSpec(
        provider='openai', model=embedding_model,
        dimensions=_positive(values, 'CHOREOGRAPH_AI_EMBEDDING_DIMENSIONS'),
        chunker=chunker, tokenizer=embedding_tokenizer,
    )
    if manual_grant_id is not None:
        rates={name:_positive(values,'CHOREOGRAPH_AI_'+name.upper()) for name in
               ('response_input_rate','response_output_rate','embedding_input_rate')}
        grant=ManualGrantSpec(manual_grant_id,response_model,embedding_model,**rates)
    else:
        limits = {name: _positive(values, 'CHOREOGRAPH_AI_' + name.upper())
                  for name in POSITIVE_GRANT_FIELDS}
        if any(limits['workspace_' + name] > limits[name]
               for name in ('requests', 'input_tokens', 'output_tokens', 'vectors', 'cost_micros')):
            raise ValueError('LIVE_AI_CONFIGURATION_INVALID')
        grant = GrantSpec(
            grant_id=_identifier(values, 'CHOREOGRAPH_AI_GRANT_ID', maximum=80),
            expires_at=expires, response_model=response_model, embedding_model=embedding_model, **limits,
        )
    reasoning=values.get('CHOREOGRAPH_AI_REASONING_EFFORT') or None
    if reasoning is not None and reasoning not in {'none','low','medium','high','xhigh','max'}:
        raise ValueError('LIVE_AI_CONFIGURATION_INVALID')
    return LiveAIConfig(api_key=key, response_tokenizer=response_tokenizer,
                        tokenizer_directory=directory, spec=spec, grant=grant,reasoning_effort=reasoning)
