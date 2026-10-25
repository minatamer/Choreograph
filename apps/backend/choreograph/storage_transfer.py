"""Explicit, stopped-writer local cutover. PostgreSQL is read-only and retained."""
import argparse
import json
import os
import socket
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from .models import Base
from .object_store import FileObjects, ObjectEngine
from .persistence import ObjectSession

ROOT=Path(__file__).resolve().parents[3]


def require_stopped(root=ROOT):
    receipt=root/'.runtime'/'services.json'
    services=json.loads(receipt.read_text()) if receipt.exists() else {}
    if any(name in services for name in ('api','runner')):
        raise ValueError('STOP_OWNED_WRITERS_BEFORE_TRANSFER')
    with socket.socket() as connection:
        connection.settimeout(.5)
        if connection.connect_ex(('127.0.0.1',45861))==0:
            raise ValueError('STOP_OWNED_WRITERS_BEFORE_TRANSFER')


def snapshot_postgres(engine):
    records={}
    with engine.connect().execution_options(isolation_level='REPEATABLE READ') as connection,connection.begin():
        connection.exec_driver_sql('SET TRANSACTION READ ONLY')
        for table in Base.metadata.sorted_tables:
            columns=[column for column in table.columns if column.computed is None]
            records[table.name]=[dict(row) for row in connection.execute(select(*columns)).mappings()]
    return records


def transfer(engine,target):
    if target.load()[0]:raise ValueError('OBJECT_STORE_ALREADY_INITIALIZED')
    snapshot=snapshot_postgres(engine)
    with ObjectSession(target) as destination,destination.begin():
        destination.data={name:[destination.models[name](**entry) for entry in entries]
                          for name,entries in snapshot.items()}
    with ObjectSession(target) as check:
        check.validate()
        counts={name:len(entries) for name,entries in check.data.items() if entries}
        if counts!={name:len(entries) for name,entries in snapshot.items() if entries}:
            raise ValueError('STORAGE_TRANSFER_VERIFICATION_FAILED')
    return counts


def write_receipt(root,counts):
    runtime=root/'.runtime';runtime.mkdir(exist_ok=True)
    payload={'from':'postgres','to':'objects','at':datetime.now(UTC).isoformat(),'counts':counts}
    handle,path=tempfile.mkstemp(dir=runtime,prefix='storage-transfer-')
    try:
        with os.fdopen(handle,'w',encoding='utf8') as stream:
            json.dump(payload,stream);stream.flush();os.fsync(stream.fileno())
        os.replace(path,runtime/'storage-transfer.json')
    finally:
        if os.path.exists(path):os.unlink(path)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--local-postgres-to-objects',action='store_true',required=True)
    parser.parse_args()
    require_stopped()
    from dotenv import dotenv_values

    from .db import build_engine
    from .runtime_config import LOCAL_MANUAL_AI_GRANT_ID, LOCAL_MANUAL_CRM_GRANT_ID, configuration_values
    from .settings import Settings, require_local_manual_target
    values={key:value for key,value in dotenv_values(ROOT/'apps/backend/.env.local',interpolate=False).items() if value is not None}
    # Preserve all provider values. This command composes no provider at all.
    settings=Settings.parse(configuration_values({**values,'DATABASE_ENABLED':'true'}),
        local_manual_grant_id=LOCAL_MANUAL_AI_GRANT_ID or None,local_manual_crm_grant_id=LOCAL_MANUAL_CRM_GRANT_ID or None)
    require_local_manual_target(settings.database_url,settings.origin,'OWNED_LOCAL_POSTGRES_REQUIRED')
    target=ObjectEngine(FileObjects(ROOT/'.runtime/private-state'),settings.token_key)
    source=build_engine(settings)
    try:
        counts=transfer(source,target)
        write_receipt(ROOT,counts)
        print(json.dumps({'code':'LOCAL_STORAGE_TRANSFER_VERIFIED','counts':counts}))
    finally:
        source.dispose();target.dispose()


if __name__=='__main__':main()
