"""Promote only verified fictional canonical RAG data; no ingestion/provider clients."""
import argparse
import base64
import copy
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/backend'))
PROJECT = 'choreograph-512713'
TABLES = {'embedding_profiles', 'document_versions', 'knowledge_chunks'}


def signature(records):
    from choreograph.object_store import encode
    return hashlib.sha256(json.dumps(records, default=encode, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def canonical_records(source):
    from choreograph.ai_admission import EmbeddingSpec
    from choreograph.knowledge import parse_version
    from choreograph.runtime_config import APPLICATION
    from choreograph.tokenizers import load_tokenizer

    spec = EmbeddingSpec('openai', APPLICATION['CHOREOGRAPH_AI_EMBEDDING_MODEL'],
                         int(APPLICATION['CHOREOGRAPH_AI_EMBEDDING_DIMENSIONS']),
                         APPLICATION['CHOREOGRAPH_AI_CHUNKER'], APPLICATION['CHOREOGRAPH_AI_EMBEDDING_TOKENIZER'])
    profile = {'id': spec.profile_id, **asdict(spec)}
    profiles = [row for row in source.get('embedding_profiles', []) if row.get('id') == spec.profile_id]
    if profiles != [profile]:
        raise ValueError('CANONICAL_PROFILE_MISMATCH')
    tokenizer = load_tokenizer(spec.tokenizer)
    manifest = [item for item in json.loads((ROOT / 'assets/knowledge/manifest.json').read_text())
                if not item['replacement']]
    if len(manifest) != 6 or len({item['slot'] for item in manifest}) != 6:
        raise ValueError('CANONICAL_MANIFEST_INVALID')
    output = {'embedding_profiles': [profile], 'document_versions': [], 'knowledge_chunks': []}
    for item in manifest:
        raw = (ROOT / 'assets/knowledge' / item['file']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('CANONICAL_SOURCE_MISMATCH')
        matches = [row for row in source.get('document_versions', [])
                   if row.get('owner_id') is None and row.get('state') == 'ready'
                   and row.get('slot') == item['slot'] and row.get('sha256') == item['sha256']
                   and row.get('embedding_profile_id') == spec.profile_id]
        if len(matches) != 1:
            raise ValueError('CANONICAL_SOURCE_NOT_READY')
        original = matches[0]
        version_id = uuid5(NAMESPACE_URL, 'choreograph:' + item['slot'] + ':' + item['sha256'] + ':' + spec.profile_id)
        if original.get('id') != version_id or original.get('source') != raw:
            raise ValueError('CANONICAL_SOURCE_MISMATCH')
        created = original['created_at']
        if created.tzinfo is None:
            raise ValueError('CANONICAL_TIME_INVALID')
        kind = 'pdf' if item['file'].endswith('.pdf') else 'text'
        parsed = parse_version(raw, kind, item['slot'], item['title'], item['version'], created,
                               spec=spec, tokenizer=tokenizer)
        expected = {'id': version_id, 'owner_id': None, 'generation': 1, 'slot': item['slot'],
                    'title': item['title'], 'version': item['version'],
                    'media_type': 'application/pdf' if kind == 'pdf' else 'text/plain',
                    'source': raw, 'sha256': item['sha256'], 'embedding_model': spec.model,
                    'chunker_version': spec.chunker, 'embedding_profile_id': spec.profile_id,
                    'page_count': max(chunk.page for chunk in parsed.chunks), 'state': 'ready', 'created_at': created}
        if original != expected:
            raise ValueError('CANONICAL_METADATA_MISMATCH')
        available = defaultdict(list)
        for chunk in source.get('knowledge_chunks', []):
            if chunk.get('version_id') == version_id:
                available[(chunk['page'], chunk['section'], chunk['content'])].append(chunk['embedding'])
        for index, chunk in enumerate(parsed.chunks):
            key = (chunk.page, chunk.section, chunk.content)
            if not available[key]:
                raise ValueError('CANONICAL_PASSAGE_MISMATCH')
            vector = available[key].pop()
            if len(vector) != spec.dimensions or any(type(value) not in {int, float} or not math.isfinite(value)
                                                     for value in vector):
                raise ValueError('CANONICAL_VECTOR_INVALID')
            output['knowledge_chunks'].append({'id': uuid5(version_id, 'canonical-chunk:' + str(index)),
                'version_id': version_id, 'page': chunk.page, 'section': chunk.section,
                'content': chunk.content, 'embedding': list(vector)})
        if any(available.values()):
            raise ValueError('CANONICAL_PASSAGE_MISMATCH')
        output['document_versions'].append(expected)
    validate_records(output)
    return output


def validate_records(records):
    from choreograph.persistence import ObjectSession
    if set(records) != TABLES:
        raise ValueError('CANONICAL_ONLY_RECORDS_REQUIRED')

    class Snapshot:
        def load(self): return copy.deepcopy(records), '0'

    with ObjectSession(Snapshot()) as session:
        session.validate()
    if (len(records['embedding_profiles']) != 1 or len(records['document_versions']) != 6
            or not records['knowledge_chunks'] or any(row['owner_id'] is not None for row in records['document_versions'])):
        raise ValueError('CANONICAL_ONLY_RECORDS_REQUIRED')


def initialize_hosted(engine, records):
    from choreograph.errors import DomainError
    validate_records(records)
    expected = signature(records)
    current, generation = engine.load()
    if current:
        if signature(current) == expected:
            return 'already_promoted'
        raise ValueError('HOSTED_STORE_ALREADY_INITIALIZED')
    if generation != '0':
        raise ValueError('HOSTED_STORE_ALREADY_INITIALIZED')
    try:
        engine.save(records, generation)
    except DomainError as error:
        if error.code not in {'STORAGE_UNAVAILABLE', 'WRITE_RETRY'}:
            raise
        current, _ = engine.load()
        if signature(current) != expected:
            raise
        return 'verified_after_unknown_ack'
    current, _ = engine.load()
    if signature(current) != expected:
        raise ValueError('HOSTED_PROMOTION_READBACK_MISMATCH')
    return 'promoted'


def cli_output(args):
    executable = shutil.which('gcloud.cmd') or shutil.which('gcloud')
    if not executable:
        raise ValueError('GCLOUD_REQUIRED')
    result = subprocess.run([executable, *args, '--quiet'], capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError('CLOUD_COMMAND_FAILED')
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--key-version', choices=['1'], default='1')
    args = parser.parse_args()
    from choreograph.db import build_engine
    from choreograph.settings import load_local
    settings = load_local()
    if settings.database_enabled or settings.object_backend != 'local':
        raise ValueError('LOCAL_OBJECT_SOURCE_REQUIRED')
    source = build_engine(settings)
    try:
        original, _ = source.load()
        before = signature(original)
        records = canonical_records(original)
        result = {'mode': 'canonical-only-promotion', 'apply': args.apply, 'provider_calls': 0,
                  'profile_id': records['embedding_profiles'][0]['id'], 'sources': 6,
                  'chunks': len(records['knowledge_chunks']), 'dimensions': records['embedding_profiles'][0]['dimensions'],
                  'snapshot_sha256': signature(records), 'private_tables_exported': 0,
                  'source_hashes': {row['slot']: row['sha256'] for row in records['document_versions']}}
        if args.apply:
            from google.auth.transport.requests import AuthorizedSession
            from google.oauth2.credentials import Credentials

            from choreograph.object_store import GCSObjects, ObjectEngine
            from choreograph.runtime_config import OBJECT_BUCKET
            # CLI formatter base64 is stripped; decoded credential bytes are never trimmed or written.
            encoded = cli_output(['secrets', 'versions', 'access', args.key_version,
                                  '--secret=CHOREOGRAPH_TOKEN_KEY', '--project=' + PROJECT,
                                  '--format=get(payload.data)']).strip()
            key = base64.b64decode(encoded, altchars=b'-_', validate=True).decode('ascii')
            if (not re.fullmatch(r'[A-Za-z0-9_-]{43}=', key)
                    or len(base64.b64decode(key, altchars=b'-_', validate=True)) != 32):
                raise ValueError('DEPLOYMENT_KEY_FORMAT_INVALID')
            token = cli_output(['auth', 'print-access-token']).decode('ascii').strip()
            session = AuthorizedSession(Credentials(token=token), refresh_timeout=5)
            session.trust_env = False
            objects = GCSObjects(OBJECT_BUCKET, session=session)
            target = ObjectEngine(objects, key)
            try:
                result['outcome'] = initialize_hosted(target, records)
                # A new engine has no cached canonical pack: download and decrypt actual target bytes.
                verified = ObjectEngine(objects, key)
                stored, generation = verified.load()
                validate_records(stored)
                if signature(stored) != signature(records):
                    raise ValueError('HOSTED_PROMOTION_READBACK_MISMATCH')
                result.update({'bucket': OBJECT_BUCKET, 'state_generation': generation,
                               'canonical_sha256': next(iter(verified.packs)), 'key_secret_version': args.key_version,
                               'fresh_engine_readback': True})
            finally:
                target.dispose()
            # The running local app may legitimately advance its state; the operator writes no source bytes.
            result['source_snapshot_writes'] = 0
            del key, encoded, token
        if signature(original) != before:
            raise ValueError('SOURCE_SNAPSHOT_MUTATED')
        print(json.dumps(result))
    finally:
        source.dispose()


if __name__ == '__main__':
    try:
        main()
    except Exception:  # noqa: BLE001 - never echo credential/HTTP/source payloads or tracebacks.
        print('{"mode":"canonical-only-promotion","code":"CANONICAL_PROMOTION_FAILED"}')
        raise SystemExit(1) from None
