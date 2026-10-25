"""Private encrypted object persistence. No SQL engine, browser authority or volatile fallback.

The small demo uses one versioned state shard: a conditional replacement commits
domain changes and delivery intent together, including global admission counters.
This deliberately trades throughput for a single honest atomic boundary. Canonical
source packs are separately immutable. Conflicts never rerun provider side effects.
"""
import base64
import copy
import gzip
import hashlib
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from cryptography.fernet import Fernet, InvalidToken

from .errors import DomainError

MAX_BYTES = 32 * 1024 * 1024


def _busy():
    return DomainError('WRITE_RETRY', 'The demo changed. Please try that action again.', 409)


def _key(name):
    if not re.fullmatch(r'[a-z0-9][a-z0-9/._-]{0,180}', name) or '..' in name:
        raise ValueError('STORAGE_KEY_INVALID')
    return name


class FileObjects:
    """Process-safe local store; a stable lock inode and atomic fsync/replace."""
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def _path(self, name):
        return self.root / (_key(name).replace('/', '_') + '.bin')

    @contextmanager
    def lock(self):
        path = self.root / '.lock'
        with path.open('a+b') as handle:
            # Do not read the byte before obtaining its Windows range lock:
            # another process may currently own it. Append initializes an empty
            # lock file without reading an already locked range.
            if path.stat().st_size == 0:
                handle.write(b'0'); handle.flush()
            started = time.monotonic()
            while True:
                try:
                    handle.seek(0)
                    if os.name == 'nt':
                        import msvcrt
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() - started > 8:
                        raise _busy() from None
                    time.sleep(.02)
            try:
                yield
            finally:
                handle.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def read(self, name):
        # Windows readers can deny replacement of their open file handle. Use
        # the same short process lock for reads and CAS replacement; decryption
        # and domain/provider work happen after releasing it.
        with self.lock():return self._read(name)

    def _read(self, name):
        try:
            data = self._path(name).read_bytes()
        except FileNotFoundError:
            return None, '0'
        if len(data) > MAX_BYTES:
            raise ValueError('STORAGE_SIZE_INVALID')
        return data, hashlib.sha256(data).hexdigest()

    def replace(self, name, data, generation):
        if len(data) > MAX_BYTES:
            raise DomainError('STORAGE_CAPACITY', 'The demo is busy. Try again later.', 503)
        with self.lock():
            if self._read(name)[1] != generation:
                raise _busy()
            target = self._path(name)
            descriptor, temporary = tempfile.mkstemp(dir=self.root, prefix='.write-')
            try:
                with os.fdopen(descriptor, 'wb') as handle:
                    handle.write(data); handle.flush(); os.fsync(handle.fileno())
                os.replace(temporary, target)
                if os.name != 'nt':
                    directory = os.open(self.root, os.O_RDONLY)
                    try: os.fsync(directory)
                    finally: os.close(directory)
            finally:
                if os.path.exists(temporary): os.unlink(temporary)
        return hashlib.sha256(data).hexdigest()

    def close(self):
        pass


class GCSObjects:
    """GCS JSON API with runtime identity, exact private bucket and generation CAS."""
    def __init__(self, bucket, *, session=None):
        if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]', bucket):
            raise ValueError('STORAGE_BUCKET_INVALID')
        self.bucket = bucket
        if session is None:
            import google.auth
            from google.auth.transport.requests import AuthorizedSession
            credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/devstorage.read_write'])
            session = AuthorizedSession(credentials,refresh_timeout=5)
            session.trust_env=False
        self.session = session
        try:
            response=session.get(f'https://storage.googleapis.com/storage/v1/b/{bucket}',timeout=10,
                params={'fields':'iamConfiguration,versioning,softDeletePolicy,retentionPolicy'},allow_redirects=False)
            policy=response.json() if response.status_code==200 else {}
            iam=policy.get('iamConfiguration',{})
            if (iam.get('publicAccessPrevention')!='enforced' or
                    iam.get('uniformBucketLevelAccess',{}).get('enabled') is not True or
                    policy.get('versioning',{}).get('enabled') is True or policy.get('retentionPolicy') or
                    str(policy.get('softDeletePolicy',{}).get('retentionDurationSeconds',0))!='0'):
                raise ValueError('PRIVATE_STORAGE_POLICY_REQUIRED')
        except BaseException:
            self.session.close()
            raise

    def read(self, name):
        from urllib.parse import quote
        path = f'https://storage.googleapis.com/storage/v1/b/{self.bucket}/o/{quote(_key(name), safe="")}'
        metadata = self.session.get(path, timeout=10, allow_redirects=False)
        if metadata.status_code == 404: return None, '0'
        if metadata.status_code != 200: raise DomainError('STORAGE_UNAVAILABLE', 'Please try again shortly.', 503)
        info = metadata.json(); generation = str(int(info['generation']))
        if int(info['size']) > MAX_BYTES: raise ValueError('STORAGE_SIZE_INVALID')
        response = self.session.get(path, params={'alt': 'media', 'generation': generation}, timeout=10,
                                    allow_redirects=False)
        if response.status_code != 200 or len(response.content) > MAX_BYTES:
            raise DomainError('STORAGE_UNAVAILABLE', 'Please try again shortly.', 503)
        return response.content, generation

    def replace(self, name, data, generation):
        if len(data) > MAX_BYTES: raise ValueError('STORAGE_SIZE_INVALID')
        for attempt in range(4):
            response = self.session.post(f'https://storage.googleapis.com/upload/storage/v1/b/{self.bucket}/o',
                params={'uploadType': 'media', 'name': _key(name), 'ifGenerationMatch': str(int(generation))},
                data=data, headers={'Content-Type': 'application/octet-stream'}, timeout=10, allow_redirects=False)
            if response.status_code not in {429, 503}: break
            if attempt < 3: time.sleep(.4 * 2**attempt)
        if response.status_code in {409, 412, 429}: raise _busy()
        if response.status_code not in {200, 201}:
            raise DomainError('STORAGE_UNAVAILABLE', 'Please try again shortly.', 503)
        return str(int(response.json()['generation']))

    def close(self):
        self.session.close()


def encode(value):
    if isinstance(value, UUID): return {'$uuid': str(value)}
    if isinstance(value, datetime): return {'$time': value.isoformat()}
    if isinstance(value, bytes): return {'$bytes': base64.b64encode(value).decode()}
    if hasattr(value, 'tolist'): return value.tolist()
    raise TypeError('STORAGE_VALUE_INVALID')


def decode(value):
    if set(value) == {'$uuid'}: return UUID(value['$uuid'])
    if set(value) == {'$time'}: return datetime.fromisoformat(value['$time'])
    if set(value) == {'$bytes'}: return base64.b64decode(value['$bytes'], validate=True)
    return value


class ObjectEngine:
    """A durable unit-of-work factory; intentionally has no SQL connection API."""
    object_storage = True

    def __init__(self, objects, key, *, name='state/v1'):
        self.objects = objects
        self.cipher = Fernet(key.encode())
        self.name = _key(name)
        self.packs = {}

    def _open(self, blob):
        import io
        with gzip.GzipFile(fileobj=io.BytesIO(self.cipher.decrypt(blob))) as handle:
            data=handle.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES:raise ValueError('STORAGE_SIZE_INVALID')
        return data

    def load(self):
        blob, generation = self.objects.read(self.name)
        if blob is None: return {}, generation
        try:
            document = json.loads(self._open(blob), object_hook=decode)
            if document['schema'] != 1: raise ValueError('STORAGE_SCHEMA_INVALID')
            records=document['records']
            digest=document.get('canonical')
            if digest:
                if not re.fullmatch(r'[a-f0-9]{64}',digest):raise ValueError('STORAGE_PACK_INVALID')
                if digest not in self.packs:
                    packed,_=self.objects.read('canonical/'+digest)
                    if packed is None:raise ValueError('STORAGE_PACK_MISSING')
                    raw=self._open(packed)
                    if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('STORAGE_PACK_INVALID')
                    self.packs={digest:json.loads(raw,object_hook=decode)}
                for name,entries in self.packs[digest].items():records.setdefault(name,[]).extend(copy.deepcopy(entries))
            return records, generation
        except (InvalidToken, KeyError, ValueError, OSError, TypeError):
            raise DomainError('STORAGE_UNAVAILABLE', 'Private storage could not be opened.', 503) from None

    def save(self, records, generation):
        canonical=[row for row in records.get('document_versions',[]) if row['owner_id'] is None]
        ids={row['id'] for row in canonical}
        packed={'document_versions':canonical,'knowledge_chunks':[
            row for row in records.get('knowledge_chunks',[]) if row['version_id'] in ids]}
        digest=None
        if canonical:
            raw=json.dumps(packed,default=encode,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
            if len(raw)>MAX_BYTES:raise ValueError('STORAGE_SIZE_INVALID')
            digest=hashlib.sha256(raw).hexdigest()
            if digest not in self.packs:
                name='canonical/'+digest
                existing,version=self.objects.read(name)
                if existing is None:
                    try:self.objects.replace(name,self.cipher.encrypt(gzip.compress(raw,mtime=0)),version)
                    except DomainError as error:
                        if error.code!='WRITE_RETRY':raise
                        existing,_=self.objects.read(name)
                        if existing is None or self._open(existing)!=raw:raise
                elif self._open(existing)!=raw:raise ValueError('STORAGE_PACK_INVALID')
                self.packs={digest:packed}
        private={**records,'document_versions':[row for row in records.get('document_versions',[]) if row['id'] not in ids],
                 'knowledge_chunks':[row for row in records.get('knowledge_chunks',[]) if row['version_id'] not in ids]}
        data = json.dumps({'schema': 1, 'records': private,'canonical':digest}, default=encode, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode()
        if len(data) > MAX_BYTES:
            raise DomainError('STORAGE_CAPACITY', 'The demo is busy. Please try again later.', 503)
        return self.objects.replace(self.name, self.cipher.encrypt(gzip.compress(data, mtime=0)), generation)

    def dispose(self):
        self.objects.close()

    def acquire(self, name, *, seconds=180):
        name='leases/'+_key(name)
        deadline=time.monotonic()+4
        while True:
            data,generation=self.objects.read(name)
            now=datetime.now(UTC)
            try:
                previous=json.loads(self.cipher.decrypt(data)) if data else None
                available=not previous or datetime.fromisoformat(previous['until'])<=now
            except (InvalidToken,ValueError,KeyError):
                raise DomainError('STORAGE_UNAVAILABLE','Private storage could not be opened.',503) from None
            if available:
                owner=uuid4().hex
                document={'owner':owner,'until':(now+timedelta(seconds=seconds)).isoformat()}
                try:
                    self.objects.replace(name,self.cipher.encrypt(json.dumps(document).encode()),generation)
                    return name,owner
                except DomainError as error:
                    if error.code!='WRITE_RETRY':raise
            if time.monotonic()>=deadline:raise _busy()
            time.sleep(.02)

    def release(self, lease):
        name,owner=lease
        data,generation=self.objects.read(name)
        if not data:return
        document=json.loads(self.cipher.decrypt(data))
        if document['owner']!=owner:return
        document['until']=datetime.now(UTC).isoformat()
        self.objects.replace(name,self.cipher.encrypt(json.dumps(document).encode()),generation)
