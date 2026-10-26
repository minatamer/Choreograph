"""The retained fake preparation entry uses the same persistence as its selected engine."""
import runpy
from pathlib import Path

from cryptography.fernet import Fernet
from sqlalchemy.engine import Engine

from choreograph import db, settings
from choreograph.object_store import FileObjects, ObjectEngine


def test_fake_preparation_command_works_with_default_no_database(tmp_path,monkeypatch,capsys):
    key=Fernet.generate_key().decode()
    selected=settings.Settings.parse({'DATABASE_ENABLED':'false','FAKE_MODE':'true','PAID_DEMO_ENABLED':'false',
        'CHOREOGRAPH_BRIDGE_SECRET':'test-only-'+'b'*40,'CHOREOGRAPH_TOKEN_KEY':key},testing=True)
    engine=ObjectEngine(FileObjects(tmp_path),key)
    monkeypatch.setattr(settings,'load_local',lambda:selected)
    monkeypatch.setattr(db,'build_engine',lambda actual:engine if actual is selected else None)
    def forbidden(*_args,**_kwargs):raise AssertionError('SQL_FORBIDDEN')
    monkeypatch.setattr(Engine,'connect',forbidden)
    runpy.run_path(str(Path(__file__).resolve().parents[3]/'scripts/prepare-knowledge.py'),run_name='__main__')
    assert 'no provider calls' in capsys.readouterr().out
    records,_=ObjectEngine(FileObjects(tmp_path),key).load()
    assert len(records['document_versions'])==6 and len(records['knowledge_chunks'])>0
    assert records['embedding_profiles'][0]['provider']=='fake'
