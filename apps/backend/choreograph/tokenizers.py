"""Pinned local BPE assets. Runtime loading never calls tiktoken's URL cache.

Patterns, special tokens, URLs and digests match tiktoken 0.14.0's
``tiktoken_ext/openai_public.py`` (MIT; license retained with the assets).
"""
import base64
import binascii
import hashlib
from dataclasses import dataclass, field
from importlib.metadata import version
from pathlib import Path

TOKENIZER_VERSION = '0.14.0'
ASSET_DIRECTORY = Path(__file__).resolve().parents[3] / 'assets' / 'tokenizers'
MAX_ASSET_BYTES = 4_194_304
RESPONSE_COUNTER = 'utf8-upper-v1'
ASSETS = {
    'cl100k_base': {
        'url': 'https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken',
        'sha256': '223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7',
        'pattern': r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}++|\p{N}{1,3}+| ?[^\s\p{L}\p{N}]++[\r\n]*+|\s++$|\s*[\r\n]|\s+(?!\S)|\s""",
        'special_tokens': {'<|endoftext|>': 100257, '<|fim_prefix|>': 100258,
                           '<|fim_middle|>': 100259, '<|fim_suffix|>': 100260,
                           '<|endofprompt|>': 100276},
    },
    'o200k_base': {
        'url': 'https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken',
        'sha256': '446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d',
        'pattern': '|'.join([
            r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*[\p{Ll}\p{Lm}\p{Lo}\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?""",
            r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+[\p{Ll}\p{Lm}\p{Lo}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?""",
            r'\p{N}{1,3}', r' ?[^\s\p{L}\p{N}]+[\r\n/]*',
            r'\s*[\r\n]+', r'\s+(?!\S)', r'\s+',
        ]),
        'special_tokens': {'<|endoftext|>': 199999, '<|endofprompt|>': 200018},
    },
}


@dataclass(frozen=True)
class LocalTokenizer:
    _encoding: object = field(repr=False)

    @property
    def name(self):
        return self._encoding.name

    def encode(self, text):
        # Visitor/source text may quote any reserved-token spelling. Those
        # spellings remain ordinary text, never control tokens or input errors.
        return self._encoding.encode(text, disallowed_special=())

    def decode(self, tokens, *, errors='replace'):
        return self._encoding.decode(tokens, errors=errors)


class UTF8Counter:
    """Conservative response admission, without guessing a model's BPE mapping."""
    name=RESPONSE_COUNTER
    def encode(self,text):return text.encode('utf-8')


def verified_bytes(name, directory=ASSET_DIRECTORY):
    if name not in ASSETS:
        raise ValueError('TOKENIZER_NOT_SUPPORTED')
    try:
        with (Path(directory) / (name + '.tiktoken')).open('rb') as stream:
            data = stream.read(MAX_ASSET_BYTES + 1)
    except OSError:
        raise ValueError('TOKENIZER_ASSET_UNAVAILABLE') from None
    if len(data) > MAX_ASSET_BYTES or hashlib.sha256(data).hexdigest() != ASSETS[name]['sha256']:
        raise ValueError('TOKENIZER_ASSET_INVALID')
    return data


def load_tokenizer(name, directory=ASSET_DIRECTORY):
    """Only the selected, SHA-verified local vocabulary can construct an encoding."""
    if name==RESPONSE_COUNTER:return UTF8Counter()
    data = verified_bytes(name, directory)
    if version('tiktoken') != TOKENIZER_VERSION:
        raise ValueError('TOKENIZER_VERSION_UNSUPPORTED')
    from tiktoken import Encoding

    try:
        ranks = {}
        for line in data.splitlines():
            token, rank = line.split()
            ranks[base64.b64decode(token, validate=True)] = int(rank)
        metadata = ASSETS[name]
        return LocalTokenizer(Encoding(name=name, pat_str=metadata['pattern'], mergeable_ranks=ranks,
                                       special_tokens=metadata['special_tokens']))
    except (ValueError, binascii.Error):
        raise ValueError('TOKENIZER_ASSET_INVALID') from None
