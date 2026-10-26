"""Unchanged canonical vectors need no repeated serialization; changed data still persists."""
import copy
from uuid import UUID

from cryptography.fernet import Fernet

from choreograph import object_store
from choreograph.object_store import FileObjects, ObjectEngine


def records():
    return {'document_versions':[{'id':UUID(int=1),'owner_id':None,'source':b'Fictional guide'}],
            'knowledge_chunks':[{'id':UUID(int=2),'version_id':UUID(int=1),'embedding':[0.25]*1536}],
            'private_counter':[{'value':0}]}


def test_unchanged_pack_reuses_immutable_bytes_across_private_writes_and_restart(tmp_path,monkeypatch):
    key=Fernet.generate_key().decode();engine=ObjectEngine(FileObjects(tmp_path),key)
    snapshot=records();generation=engine.save(snapshot,'0')
    pack_files={path.name:path.read_bytes() for path in tmp_path.iterdir() if path.is_file() and path.name!='.lock'}
    original=object_store.json.dumps;serializations=[]
    def counted(value,*args,**kwargs):
        if isinstance(value,dict) and set(value)=={'document_versions','knowledge_chunks'}:
            serializations.append(True)
        return original(value,*args,**kwargs)
    monkeypatch.setattr(object_store.json,'dumps',counted)
    for value in (1,2):
        snapshot=copy.deepcopy(snapshot);snapshot['private_counter'][0]['value']=value
        generation=engine.save(snapshot,generation)
    restarted=ObjectEngine(engine.objects,key);snapshot,generation=restarted.load()
    snapshot['private_counter'][0]['value']=3;restarted.save(snapshot,generation)
    assert restarted.load()[0]['private_counter'][0]['value']==3
    assert serializations==[]
    # The canonical file remains identical; only the mutable state file changes.
    unchanged=[name for name,data in pack_files.items() if (tmp_path/name).read_bytes()==data]
    assert len(unchanged)==1
    engine.dispose()


def test_mutating_caller_owned_canonical_data_cannot_reuse_stale_pack_digest(tmp_path):
    key=Fernet.generate_key().decode();engine=ObjectEngine(FileObjects(tmp_path),key)
    snapshot=records();generation=engine.save(snapshot,'0')
    first=next(iter(engine.packs))
    snapshot['knowledge_chunks'][0]['embedding'][0]=0.75
    generation=engine.save(snapshot,generation)
    second=next(iter(engine.packs))
    assert second!=first
    fresh=ObjectEngine(engine.objects,key)
    assert fresh.load()[0]['knowledge_chunks'][0]['embedding'][0]==0.75
    snapshot['document_versions'][0]['source']=b'Fictional amended guide'
    engine.save(snapshot,generation)
    assert next(iter(engine.packs))!=second
    assert ObjectEngine(engine.objects,key).load()[0]['document_versions'][0]['source']==b'Fictional amended guide'
    engine.dispose()
