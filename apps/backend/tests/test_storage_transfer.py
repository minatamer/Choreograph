"""Actual isolated SQL -> encrypted files; source rows stay unchanged."""
import hashlib
import json
from dataclasses import replace
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from conftest import postgres_database as postgres_fixture
from fastapi.testclient import TestClient
from test_jobs import connected_booking
from test_requests import NOW

from choreograph import jobs, knowledge
from choreograph.ai_admission import (
    Admission,
    AttemptScope,
    GrantSpec,
    ProviderResult,
    SafeUsage,
    claim_interaction,
)
from choreograph.api import create_app
from choreograph.hubspot import FakeHubSpot
from choreograph.models import AIGrant, Manifest, Outbox, Workspace
from choreograph.object_store import FileObjects, ObjectEngine, encode
from choreograph.persistence import Session, repo_rows
from choreograph.storage_transfer import snapshot_postgres, transfer


def fingerprint(records):
    return hashlib.sha256(json.dumps(records,default=encode,sort_keys=True).encode()).hexdigest()


def test_transfer_keeps_sessions_vectors_counters_pending_export_and_cleanup(tmp_path):
    fixture=postgres_fixture.__wrapped__();engine,settings=next(fixture)
    target=ObjectEngine(FileObjects(tmp_path/'private'),settings.token_key)
    client=None
    try:
        with Session(engine) as db,db.begin():knowledge.prepare_samples(db,NOW)
        client,headers,state,_,event=connected_booking((engine,settings))
        wid=UUID(state['workspace_id'])
        with Session(engine) as db:
            workspace=db.get(Workspace,wid)
            scope=AttemptScope(wid,workspace.generation,str(uuid4()),workspace.revision)
            manifests={row.slot:str(row.version_id) for row in repo_rows(db,Manifest,filters={'workspace_id':wid})}
        claim_interaction(engine,scope,operation='chat',request_hash=hashlib.sha256(b'injected').hexdigest(),
            profile_id=workspace.embedding_profile_id,manifest_ids=manifests,now=NOW)
        grant=GrantSpec(str(uuid4()),NOW+timedelta(hours=1),'synthetic-response','synthetic-embedding',
            20,100_000,100_000,100,100_000,20,100_000,100_000,100,100_000,1_000_000,1_000_000,1_000_000)
        gate=Admission(engine,grant,scope,lambda:NOW)
        assert gate.run('interpret',0,input_tokens=5,output_tokens=1,
                        invoke=lambda:ProviderResult('ok',SafeUsage(5,1)))=='ok'
        before=fingerprint(snapshot_postgres(engine))
        counts=transfer(engine,target)
        assert counts['workspaces']==1 and counts['document_versions']==6 and counts['outbox']==1
        assert fingerprint(snapshot_postgres(engine))==before
        with Session(target) as db:
            assert db.get(AIGrant,grant.grant_id).requests==1
            assert db.get(Outbox,(wid,event)).state=='pending'
        provider=FakeHubSpot(target);selected=replace(settings,database_enabled=False)
        assert jobs.tick(target,selected,provider,lambda:NOW)==1
        with TestClient(create_app(selected,target,lambda:NOW,crm_provider=provider),
                        cookies={'choreograph_guest':client.cookies.get('choreograph_guest')}) as restarted:
            current=restarted.get('/v1/session',headers=headers).json()
            assert current['workspace_id']==state['workspace_id'] and len(current['documents'])==6
            assert current['requests'][0]['booking']['id']==state['requests'][0]['booking']['id']
            assert current['requests'][0]['crm_state']=='simulated_synced'
        assert fingerprint(snapshot_postgres(engine))==before
        assert jobs.tick(target,selected,provider,lambda:NOW+timedelta(hours=2,seconds=1))==1
        assert 'archive-deals' in provider.calls and 'archive-contacts' in provider.calls
        assert 'uninstall' not in provider.calls
        assert fingerprint(snapshot_postgres(engine))==before
        with pytest.raises(ValueError,match='OBJECT_STORE_ALREADY_INITIALIZED'):transfer(engine,target)
    finally:
        if client is not None:client.close()
        target.dispose();fixture.close()
