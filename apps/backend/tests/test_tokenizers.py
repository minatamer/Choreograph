import hashlib
import json

import pytest
import tiktoken.load
import tiktoken_ext.openai_public

from choreograph.tokenizers import ASSET_DIRECTORY, ASSETS, load_tokenizer, verified_bytes


@pytest.mark.parametrize('name', ['cl100k_base', 'o200k_base'])
def test_bundled_tokenizer_is_hash_verified_and_never_uses_url_cache(monkeypatch, name):
    def denied(*args, **kwargs):
        raise AssertionError('Runtime must not use a fetchable tiktoken cache')
    monkeypatch.setattr(tiktoken.load, 'read_file', denied)
    monkeypatch.setattr(tiktoken.load, 'read_file_cached', denied)
    encoding = load_tokenizer(name)
    text = 'Juniper Cleaning — café. Supplies and pet safety: 123.\nSecond page.'
    assert encoding.decode(encoding.encode(text)) == text
    assert hashlib.sha256(verified_bytes(name)).hexdigest() == ASSETS[name]['sha256']
    item = next(item for item in json.loads((ASSET_DIRECTORY / 'manifest.json').read_text())['assets']
                if item['name'] == name)
    assert item['bytes'] == len(verified_bytes(name))
    assert item['sha256'] == ASSETS[name]['sha256']


@pytest.mark.parametrize('name', ['cl100k_base', 'o200k_base'])
def test_reserved_token_literals_remain_ordinary_untrusted_text(name):
    tokenizer = load_tokenizer(name)
    text = 'The visitor quoted: ' + ' '.join(ASSETS[name]['special_tokens'])
    tokens = tokenizer.encode(text)
    assert tokenizer.decode(tokens) == text
    assert set(tokens).isdisjoint(ASSETS[name]['special_tokens'].values())


def test_missing_tampered_or_unselected_vocabulary_fails_without_fallback(tmp_path, monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('Runtime attempted tokenizer network access')
    monkeypatch.setattr(tiktoken.load, 'read_file_cached', denied)
    with pytest.raises(ValueError, match='TOKENIZER_ASSET_UNAVAILABLE'):
        load_tokenizer('cl100k_base', tmp_path)
    (tmp_path / 'cl100k_base.tiktoken').write_bytes(b'c2FmZQ== 0\n')
    with pytest.raises(ValueError, match='TOKENIZER_ASSET_INVALID'):
        load_tokenizer('cl100k_base', tmp_path)
    with pytest.raises(ValueError, match='TOKENIZER_NOT_SUPPORTED'):
        load_tokenizer('../cl100k_base', tmp_path)


@pytest.mark.parametrize('name', ['cl100k_base', 'o200k_base'])
def test_offline_metadata_matches_pinned_vendor_constructor_without_fetch(monkeypatch, name):
    def local_only(url, *, expected_hash):
        assert url == ASSETS[name]['url']
        assert expected_hash == ASSETS[name]['sha256']
        return {}
    monkeypatch.setattr(tiktoken_ext.openai_public, 'load_tiktoken_bpe', local_only)
    metadata = getattr(tiktoken_ext.openai_public, name)()
    assert metadata['pat_str'] == ASSETS[name]['pattern']
    assert metadata['special_tokens'] == ASSETS[name]['special_tokens']
