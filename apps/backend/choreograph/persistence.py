"""Shared explicit repositories for PostgreSQL and private object units of work.

Object units store typed domain records, never parse or execute SQL expressions.
Predicates below are ordinary Python; SQL filters narrow the PostgreSQL read.
"""
import copy
import time
from contextlib import contextmanager, suppress
from functools import wraps

from sqlalchemy import UniqueConstraint, select
from sqlalchemy.orm import Session as SQLSession

from .errors import DomainError


def is_object(value):
    return bool(getattr(value, 'object_storage', False))


def storage_retry(function):
    """Retry explicitly pure claim/accounting transactions, never provider calls."""
    @wraps(function)
    def run(*args,**kwargs):
        target=args[0] if args else kwargs.get('engine')
        engine=getattr(target,'engine',target)
        if not is_object(engine):return function(*args,**kwargs)
        for attempt in range(4):
            try:return function(*args,**kwargs)
            except DomainError as error:
                if error.code!='WRITE_RETRY' or attempt==3:raise
                time.sleep(.01*(attempt+1))
        raise AssertionError('UNREACHABLE')
    return run


def Session(engine, **kwargs):
    return ObjectSession(engine) if is_object(engine) else SQLSession(engine, **kwargs)


def repo_rows(db, model, *, filters=None, predicate=None, order=None, reverse=False, limit=None, lock=False):
    from uuid import UUID
    filters = dict(filters or {})
    for name,value in filters.items():
        if value is not None and isinstance(value,str) and model.__table__.columns[name].type.python_type is UUID:
            filters[name]=UUID(value)
    if is_object(db):
        result = db.records(model, filters=filters)
    else:
        query = select(model).where(*(getattr(model, key) == value for key, value in filters.items()))
        if lock: query = query.with_for_update()
        result = list(db.scalars(query))
    if predicate is not None: result = [row for row in result if predicate(row)]
    if order is not None: result.sort(key=order, reverse=reverse)
    return result if limit is None else result[:limit]


def repo_first(db, model, **kwargs):
    kwargs["limit"] = 1
    return next(iter(repo_rows(db, model, **kwargs)), None)


def repo_values(db, model, field, **kwargs):
    return [getattr(row, field) for row in repo_rows(db, model, **kwargs)]


def repo_value(db, model, field, **kwargs):
    row = repo_first(db, model, **kwargs)
    return getattr(row, field) if row is not None else None


class repo_desc:
    def __init__(self, value): self.value = value
    def __lt__(self, other): return self.value > other.value
    def __eq__(self, other): return self.value == other.value


def try_advisory(db, key, slot):
    if is_object(db): return True
    from sqlalchemy import text
    return db.scalar(text('SELECT pg_try_advisory_xact_lock(:key,:slot)'), {'key': key, 'slot': slot})


def remove(db, model, **kwargs):
    for row in repo_rows(db, model, **kwargs): db.delete(row)


def change(db, model, values, **kwargs):
    for row in repo_rows(db, model, **kwargs):
        for key, value in values.items(): setattr(row, key, value)


def advisory(db, key, slot):
    # Object transactions are fenced by one durable generation. A CAS loser
    # cannot commit bookings, consent, counters, claims or idempotent receipts.
    if not is_object(db):
        from sqlalchemy import text
        db.execute(text('SELECT pg_advisory_xact_lock(:key,:slot)'), {'key': key, 'slot': slot})


def workspace_lock(db,workspace):
    """Match the SQL caller's workspace row lock for external CRM commands.

    Pure assistant network work stays outside this short authority transaction.
    The lock is acquired by the shared idempotent mutation boundary, so reset or
    another edit cannot discard an OAuth exchange whose response is in flight.
    """
    if is_object(db):db.hold_lease('workspace-'+str(workspace.id))


class ObjectSession:
    object_storage = True

    def __init__(self, engine):
        from .models import Base
        self.engine = engine
        self.models = {mapper.class_.__tablename__: mapper.class_ for mapper in Base.registry.mappers}
        stored, self.generation = engine.load()
        self.data = {name: [self.models[name](**item) for item in entries] for name, entries in stored.items()
                     if name in self.models}
        if set(stored) - set(self.models): raise ValueError('STORAGE_SCHEMA_INVALID')
        self.initial = copy.deepcopy(self.snapshot())
        self.read_sets = []
        self.leases = {}

    def __enter__(self): return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        # Match SQL Session.close even for a read-only context without begin().
        # Unknown release acknowledgements leave only a bounded expiring lease.
        for lease in self.leases.values():
            with suppress(Exception):self.engine.release(lease)
        self.leases.clear()

    @contextmanager
    def begin(self):
        try:
            yield self
            self.commit()
        finally:
            self.close()

    def hold_lease(self, name):
        if name in self.leases:return
        lease=self.engine.acquire(name)
        self.leases[name]=lease
        current,generation=self.engine.load()
        if generation!=self.generation:self.rebase(current,generation)

    def records(self, model, *, filters=None):
        filters=filters or {}
        self.read_sets.append((model.__tablename__,filters))
        return [row for row in self.data.get(model.__tablename__, [])
                if all(getattr(row,key)==value for key,value in filters.items())]

    def get(self, model, identity, **_kwargs):
        columns = list(model.__table__.primary_key.columns)
        identity = identity if isinstance(identity, tuple) else (identity,)
        if len(columns) != len(identity): raise ValueError('STORAGE_IDENTITY_INVALID')
        from uuid import UUID
        normalized={}
        for column,value in zip(columns,identity,strict=True):
            if value is not None and column.type.python_type is UUID and isinstance(value,str):value=UUID(value)
            normalized[column.name]=value
        return repo_first(self, model, filters=normalized)

    def adopt_committed(self,model,identity,fields):
        """Acknowledge a narrow independently durable external-attempt marker."""
        row=self.get(model,identity)
        keys=[column.name for column in model.__table__.primary_key.columns]
        before=next(item for item in self.initial[model.__tablename__]
                    if all(item[key]==getattr(row,key) for key in keys))
        for key,value in fields.items():
            setattr(row,key,value);before[key]=copy.deepcopy(value)

    def add(self, row):
        for column in row.__table__.columns:
            if column.computed is not None: continue
            if getattr(row, column.name) is None and column.default is not None:
                default = column.default
                value = default.arg(None) if default.is_callable else copy.deepcopy(default.arg)
                setattr(row, column.name, value)
        target = self.data.setdefault(row.__tablename__, [])
        if not any(item is row for item in target): target.append(row)

    def add_all(self, entries):
        for row in entries: self.add(row)

    def delete(self, row):
        table = row.__table__
        target = self.data.get(table.name, [])
        target[:] = [item for item in target if item is not row]
        # Apply the same explicit CASCADE relationships as the SQL schema.
        for model in self.models.values():
            for constraint in model.__table__.foreign_key_constraints:
                if constraint.ondelete != 'CASCADE' or constraint.referred_table is not table: continue
                for child in self.records(model):
                    if all(getattr(child, element.parent.name) == getattr(row, element.column.name)
                           for element in constraint.elements): self.delete(child)

    def flush(self):
        # IDs/defaults are assigned by add; no partial durable writes exist.
        pass

    def snapshot(self):
        return {name: [{column.name: getattr(row, column.name) for column in row.__table__.columns
                        if column.computed is None} for row in sorted(entries,key=lambda item:tuple(
                            str(getattr(item,column.name)) for column in item.__table__.primary_key.columns))]
                for name, entries in self.data.items() if entries}

    def validate(self):
        import hashlib
        import math

        from .models import (
            Chunk,
            Connection,
            DocumentVersion,
            EmbeddingProfile,
            Manifest,
            Reservation,
            Workspace,
        )
        for name, entries in self.data.items():
            table = self.models[name].__table__
            unique = [list(table.primary_key.columns)] + [list(item.columns) for item in table.constraints
                                                          if isinstance(item, UniqueConstraint)]
            for columns in unique:
                seen = set()
                for row in entries:
                    key = tuple(getattr(row, column.name) for column in columns)
                    if any(value is None for value in key): continue
                    if key in seen: raise DomainError('WRITE_RETRY', 'The demo changed. Please try again.', 409)
                    seen.add(key)
            for row in entries:
                for column in table.columns:
                    if column.computed is None and not column.nullable and getattr(row, column.name) is None:
                        raise ValueError('STORAGE_RECORD_INVALID')
                for constraint in table.foreign_key_constraints:
                    values = [(element.column.name, getattr(row, element.parent.name)) for element in constraint.elements]
                    if any(value is None for _, value in values): continue
                    parents = self.data.get(constraint.referred_table.name, [])
                    if not any(all(getattr(parent, key) == value for key, value in values) for parent in parents):
                        raise ValueError('STORAGE_REFERENCE_INVALID')
        profiles={row.id:row for row in self.data.get(EmbeddingProfile.__tablename__,[])}
        documents={row.id:row for row in self.data.get(DocumentVersion.__tablename__,[])}
        workspaces={row.id:row for row in self.data.get(Workspace.__tablename__,[])}
        initial_profiles={row['id']:row for row in self.initial.get(EmbeddingProfile.__tablename__,[])}
        for profile in self.data.get(EmbeddingProfile.__tablename__,[]):
            old=initial_profiles.get(profile.id)
            if old and any(getattr(profile,key)!=value for key,value in old.items()):
                raise ValueError('EMBEDDING_PROFILE_IMMUTABLE')
        for old in self.initial.get(Workspace.__tablename__,[]):
            current=workspaces.get(old['id'])
            if current and current.embedding_profile_id!=old['embedding_profile_id']:
                raise ValueError('EMBEDDING_PROFILE_IMMUTABLE')
        for document in documents.values():
            if (len(document.source)>2_097_152 or not 1<=document.page_count<=10 or
                    hashlib.sha256(document.source).hexdigest()!=document.sha256):
                raise ValueError('STORAGE_DOCUMENT_INVALID')
        for old in self.initial.get(DocumentVersion.__tablename__,[]):
            document=documents.get(old['id'])
            if document is not None and any(getattr(document,key)!=value for key,value in old.items() if key!='state'):
                raise ValueError('DOCUMENT_IDENTITY_IMMUTABLE')
        initial_connections={(row['workspace_id'],row['id']):row for row in self.initial.get(Connection.__tablename__,[])}
        for connection in self.data.get(Connection.__tablename__,[]):
            old=initial_connections.get((connection.workspace_id,connection.id))
            if not old:continue
            if any(getattr(connection,key)!=old[key] for key in ('app_id','provider','account_id')):
                raise ValueError('CRM_IDENTITY_IMMUTABLE')
            if connection.destination!=old['destination'] and connection.generation<=old['generation']:
                raise ValueError('CRM_DESTINATION_GENERATION_REQUIRED')
        for chunk in self.data.get(Chunk.__tablename__,[]):
            document=documents[chunk.version_id];profile=profiles[document.embedding_profile_id]
            if len(chunk.embedding)!=profile.dimensions or any(not math.isfinite(value) for value in chunk.embedding):
                raise ValueError('EMBEDDING_DIMENSIONS_INVALID')
        for manifest in self.data.get(Manifest.__tablename__,[]):
            document=documents[manifest.version_id];workspace=workspaces[manifest.workspace_id]
            profile=profiles[document.embedding_profile_id]
            legacy=(profiles[workspace.embedding_profile_id].model=='legacy-mixed-fake64' and
                    profile.provider=='fake' and profile.dimensions==64)
            if (document.state!='ready' or document.slot!=manifest.slot or document.owner_id not in {None,workspace.id} or
                    (document.owner_id is not None and document.generation!=workspace.generation) or
                    (document.embedding_profile_id!=workspace.embedding_profile_id and not legacy)):
                raise ValueError('DOCUMENT_SCOPE_INVALID')
        if len(self.data.get(Workspace.__tablename__,[]))>256:
            raise DomainError('DEMO_CAPACITY','The demo is busy. Please try again later.',429)
        active = [row for row in self.data.get(Reservation.__tablename__,[]) if row.state in {'confirmed', 'blocked', 'completed'}]
        for index, row in enumerate(active):
            if row.ends_at <= row.starts_at: raise ValueError('STORAGE_PERIOD_INVALID')
            if any(other.workspace_id == row.workspace_id and other.staff_id == row.staff_id and
                   row.starts_at < other.ends_at and row.ends_at > other.starts_at for other in active[index + 1:]):
                raise DomainError('TIME_OCCUPIED', 'That time was just reserved. Choose another time.', 409)

    def rebase(self,current,generation):
        document=self.snapshot()
        for name,entries in current.items():
            keys=[column.name for column in self.models[name].__table__.primary_key.columns]
            entries.sort(key=lambda item,keys=keys:tuple(str(item[key]) for key in keys))
        for name,filters in self.read_sets:
            def matching(entries,filters=filters):
                return [row for row in entries if all(row[key]==value for key,value in filters.items())]
            before_read=matching(self.initial.get(name,[]));after_read=matching(current.get(name,[]))
            if after_read==before_read:continue
            if name=='workspaces' and len(before_read)==len(after_read)==1 and before_read[0]['id']==after_read[0]['id']:
                if before_read[0]['generation']!=after_read[0]['generation']:
                    raise DomainError('STALE_GENERATION','This demo changed. Refresh before continuing.',409)
                if before_read[0]['revision']!=after_read[0]['revision']:
                    raise DomainError('STALE_REVISION','The request changed. Review its current details.',409)
            raise DomainError('WRITE_RETRY','The demo changed. Please try again.',409)
        merged=copy.deepcopy(current)
        for name in set(document)|set(self.initial):
            columns=[column.name for column in self.models[name].__table__.primary_key.columns]
            def keyed(entries,columns=columns):
                return {tuple(row[key] for key in columns):row for row in entries}
            before=keyed(self.initial.get(name,[]));after=keyed(document.get(name,[]))
            present=keyed(current.get(name,[]))
            for key in set(before)|set(after):
                if before.get(key)==after.get(key):continue
                if present.get(key)!=before.get(key):
                    raise DomainError('WRITE_RETRY','The demo changed. Please try again.',409)
                if key in after:present[key]=after[key]
                else:present.pop(key,None)
            merged[name]=list(present.values())
        # Keep already-authorized Workspace/Connection/OAuth object identities.
        # A holder waiting for account uninstall sees the committed registry
        # before its single exchange, without losing its own pending changes.
        for name,entries in merged.items():
            model=self.models[name];columns=[column.name for column in model.__table__.primary_key.columns]
            existing={tuple(getattr(row,key) for key in columns):row for row in self.data.get(name,[])}
            adopted=[]
            for entry in entries:
                row=existing.get(tuple(entry[key] for key in columns))
                if row is None:row=model(**entry)
                else:
                    for key,value in entry.items():setattr(row,key,value)
                adopted.append(row)
            self.data[name]=adopted
        self.initial=copy.deepcopy(current);self.generation=generation
        self.validate()

    def commit(self):
        document=self.snapshot()
        if document==self.initial:return
        self.validate()
        # Retry only a conditional storage write; provider calls never repeat.
        for attempt in range(4):
            try:
                self.generation=self.engine.save(document,self.generation)
                self.initial=copy.deepcopy(document)
                return
            except DomainError as error:
                if error.code!='WRITE_RETRY' or attempt==3:raise
                self.rebase(*self.engine.load())
                document=self.snapshot()
