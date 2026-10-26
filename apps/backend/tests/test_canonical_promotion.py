"""Canonical-only operator promotion must never carry local private authority."""
import copy
import json
import runpy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from sqlalchemy.engine import Engine

from choreograph import knowledge
from choreograph.ai_admission import EmbeddingSpec
from choreograph.errors import DomainError
from choreograph.models import EmbeddingProfile
from choreograph.object_store import FileObjects, ObjectEngine, encode
from choreograph.runtime_config import APPLICATION
from choreograph.tokenizers import load_tokenizer

ROOT = Path(__file__).resolve().parents[3]
TOOL = runpy.run_path(str(ROOT / 'scripts/promote-canonical.py'))


@pytest.fixture(autouse=True)
def forbid_sql(monkeypatch):
    def forbidden(*_args, **_kwargs): raise AssertionError('SQL_FORBIDDEN')
    monkeypatch.setattr(Engine, 'connect', forbidden)


@pytest.fixture(scope='module')
def sample():
    spec = EmbeddingSpec('openai', APPLICATION['CHOREOGRAPH_AI_EMBEDDING_MODEL'],
                         int(APPLICATION['CHOREOGRAPH_AI_EMBEDDING_DIMENSIONS']),
                         APPLICATION['CHOREOGRAPH_AI_CHUNKER'], APPLICATION['CHOREOGRAPH_AI_EMBEDDING_TOKENIZER'])
    tokenizer = load_tokenizer(spec.tokenizer)

    class InjectedVectors:
        def __init__(self): self.spec = spec
        def get_text_embedding_batch(self, texts): return [[0.25] * spec.dimensions for _ in texts]

    def snapshot(row):
        return {column.name: getattr(row, column.name) for column in row.__table__.columns
                if column.computed is None}

    profile = EmbeddingProfile(id=spec.profile_id, provider=spec.provider, model=spec.model,
                               dimensions=spec.dimensions, chunker=spec.chunker, tokenizer=spec.tokenizer)
    source = {'embedding_profiles': [snapshot(profile)], 'document_versions': [], 'knowledge_chunks': []}
    for item in json.loads((ROOT / 'assets/knowledge/manifest.json').read_text()):
        if item['replacement']: continue
        raw = (ROOT / 'assets/knowledge' / item['file']).read_bytes()
        row, chunks = knowledge.build_version(raw, 'pdf' if item['file'].endswith('.pdf') else 'text',
            item['slot'], item['title'], item['version'], datetime(2026, 10, 26, tzinfo=UTC),
            spec=spec, tokenizer=tokenizer, embedder=InjectedVectors())
        source['document_versions'].append(snapshot(row))
        source['knowledge_chunks'].extend(snapshot(chunk) for chunk in chunks)
    return source, TOOL['canonical_records'](source)


def test_private_records_and_other_profiles_are_excluded(sample):
    source, expected = sample
    private = copy.deepcopy(source)
    marker = 'PRIVATE_GUEST_TOKEN_OUTBOX_MUST_NOT_LEAVE'
    for table in ('workspaces', 'crm_connections', 'outbox', 'ai_usage_grants', 'crm_installations'):
        private[table] = [{'private': marker}]
    private['embedding_profiles'].append({'id': 'unrelated-fake-profile', 'private': marker})
    private['document_versions'].append({'owner_id': 'guest', 'private': marker})
    actual = TOOL['canonical_records'](private)
    assert actual == expected and set(actual) == TOOL['TABLES']
    assert marker not in json.dumps(actual, default=encode)
    assert len(actual['document_versions']) == 6 and len(actual['knowledge_chunks']) == 23


@pytest.mark.parametrize('damage', ['source', 'passage', 'dimensions', 'nan', 'metadata', 'profile', 'missing', 'extra'])
def test_tampered_canonical_source_is_rejected_before_cloud_write(sample, damage):
    source = copy.deepcopy(sample[0])
    if damage == 'source': source['document_versions'][0]['source'] = b'private altered source'
    elif damage == 'passage': source['knowledge_chunks'][0]['content'] = 'private changed passage'
    elif damage == 'dimensions': source['knowledge_chunks'][0]['embedding'] = [0.0]
    elif damage == 'nan': source['knowledge_chunks'][0]['embedding'][0] = float('nan')
    elif damage == 'metadata': source['document_versions'][0]['title'] = 'private metadata'
    elif damage == 'profile': source['embedding_profiles'][0]['model'] = 'wrong-embedding-space'
    elif damage == 'missing': source['document_versions'].pop(0)
    else: source['knowledge_chunks'].append(copy.deepcopy(source['knowledge_chunks'][0]))
    with pytest.raises(ValueError, match='CANONICAL_'):
        TOOL['canonical_records'](source)


def fingerprint_files(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.iterdir() if path.is_file()}


def test_fresh_encrypted_promotion_and_replay_preserve_source(sample, tmp_path):
    source = ObjectEngine(FileObjects(tmp_path / 'source'), Fernet.generate_key().decode())
    target_key = Fernet.generate_key().decode()
    target = ObjectEngine(FileObjects(tmp_path / 'target'), target_key)
    try:
        source.save(sample[0], '0')
        before_source = fingerprint_files(tmp_path / 'source')
        assert TOOL['initialize_hosted'](target, sample[1]) == 'promoted'
        stored, _ = ObjectEngine(target.objects, target_key).load()
        assert stored == sample[1]
        target_files = fingerprint_files(tmp_path / 'target')
        assert all(b'%PDF' not in data and b'PRIVATE_' not in data for name, data in target_files.items() if name != '.lock')
        assert TOOL['initialize_hosted'](target, sample[1]) == 'already_promoted'
        assert fingerprint_files(tmp_path / 'target') == target_files
        assert fingerprint_files(tmp_path / 'source') == before_source
    finally:
        source.dispose(); target.dispose()


def test_existing_private_destination_is_never_replaced(sample, tmp_path):
    target = ObjectEngine(FileObjects(tmp_path / 'used'), Fernet.generate_key().decode())
    try:
        target.save({'private_existing_records': [{'do_not_overwrite': True}]}, '0')
        before = fingerprint_files(tmp_path / 'used')
        with pytest.raises(ValueError, match='HOSTED_STORE_ALREADY_INITIALIZED'):
            TOOL['initialize_hosted'](target, sample[1])
        assert fingerprint_files(tmp_path / 'used') == before
    finally:
        target.dispose()


def test_lost_write_acknowledgement_is_read_back_without_repeating_write(sample, tmp_path):
    target = ObjectEngine(FileObjects(tmp_path / 'ack'), Fernet.generate_key().decode())

    class UnknownAck:
        saves = 0
        def load(self): return target.load()
        def save(self, records, generation):
            self.saves += 1
            target.save(records, generation)
            raise DomainError('STORAGE_UNAVAILABLE', 'Injected lost acknowledgement', 503)

    uncertain = UnknownAck()
    try:
        assert TOOL['initialize_hosted'](uncertain, sample[1]) == 'verified_after_unknown_ack'
        assert uncertain.saves == 1 and target.load()[0] == sample[1]
    finally:
        target.dispose()


def test_existing_empty_state_generation_is_not_a_fresh_store(sample):
    class PreviouslyInitialized:
        def load(self): return {}, '123'
        def save(self, *_): raise AssertionError('EXISTING_STATE_MUST_NOT_BE_REPLACED')
    with pytest.raises(ValueError, match='HOSTED_STORE_ALREADY_INITIALIZED'):
        TOOL['initialize_hosted'](PreviouslyInitialized(), sample[1])
