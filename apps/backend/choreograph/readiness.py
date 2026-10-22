"""No-provider readiness checks. Offline by default; SQL reads are explicit."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .ai_admission import FAKE_SPEC
from .ai_config import POSITIVE_GRANT_FIELDS
from .models import Chunk, DocumentVersion
from .settings import Settings

ROOT=Path(__file__).resolve().parents[3]
BASE_FIELDS=('CHOREOGRAPH_DATABASE_URL','CHOREOGRAPH_BRIDGE_SECRET','CHOREOGRAPH_TOKEN_KEY')
AI_FIELDS=('CHOREOGRAPH_OPENAI_API_KEY','CHOREOGRAPH_AI_RESPONSE_MODEL','CHOREOGRAPH_AI_EMBEDDING_MODEL',
    'CHOREOGRAPH_AI_RESPONSE_TOKENIZER','CHOREOGRAPH_AI_EMBEDDING_TOKENIZER','CHOREOGRAPH_AI_EMBEDDING_DIMENSIONS',
    'CHOREOGRAPH_AI_CHUNKER','CHOREOGRAPH_AI_GRANT_ID','CHOREOGRAPH_AI_EXPIRES_AT',
    *('CHOREOGRAPH_AI_'+field.upper() for field in POSITIVE_GRANT_FIELDS))
CRM_FIELDS=('CHOREOGRAPH_HUBSPOT_APP_ID','CHOREOGRAPH_HUBSPOT_CLIENT_ID','CHOREOGRAPH_HUBSPOT_CLIENT_SECRET',
    'CHOREOGRAPH_HUBSPOT_REDIRECT_URI','CHOREOGRAPH_HUBSPOT_DISTRIBUTION','CHOREOGRAPH_HUBSPOT_CAPACITY',
    'CHOREOGRAPH_CRM_GRANT_ID','CHOREOGRAPH_CRM_EXPIRES_AT','CHOREOGRAPH_CRM_REQUESTS','CHOREOGRAPH_CRM_WORKSPACE_REQUESTS')


def expected_head():
    return ScriptDirectory.from_config(Config(str(ROOT/'apps/backend/alembic.ini'))).get_current_head()


def corpus_status():
    pack=ROOT/'assets/knowledge'
    try:
        items=[item for item in json.loads((pack/'manifest.json').read_text()) if not item['replacement']]
        if len(items)!=6:raise ValueError()
        for item in items:
            data=(pack/item['file']).read_bytes()
            if len(data)>2_097_152 or hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError()
        return {'ready':True,'source_slots':len(items),'code':'CORPUS_HASHES_VERIFIED'}
    except (OSError,ValueError,KeyError,TypeError):
        return {'ready':False,'code':'CORPUS_NOT_READY'}


def database_status(engine,spec):
    try:
        with engine.connect() as connection:
            actual=connection.scalar(text('SELECT version_num FROM alembic_version'))
            version=connection.scalar(text('SHOW server_version_num'))
            extensions=dict(connection.execute(text("SELECT extname,extversion FROM pg_extension WHERE extname IN ('vector','btree_gist')")).all())
        if actual!=expected_head():return {'ready':False,'code':'SCHEMA_NOT_CURRENT','head':actual,'expected_head':expected_head()}
        if not 170000<=int(version)<180000 or extensions!={'vector':'0.8.5','btree_gist':'1.7'}:
            return {'ready':False,'code':'DATABASE_CAPABILITY_MISMATCH'}
        manifest=[item for item in json.loads((ROOT/'assets/knowledge/manifest.json').read_text()) if not item['replacement']]
        ready=0
        with Session(engine) as db:
            for item in manifest:
                version_id=db.scalar(select(DocumentVersion.id).where(DocumentVersion.owner_id.is_(None),
                    DocumentVersion.slot==item['slot'],DocumentVersion.sha256==item['sha256'],
                    DocumentVersion.embedding_profile_id==spec.profile_id,DocumentVersion.state=='ready'))
                if version_id is None:continue
                count,minimum,maximum=db.execute(select(func.count(),func.min(func.vector_dims(Chunk.embedding)),
                    func.max(func.vector_dims(Chunk.embedding))).where(Chunk.version_id==version_id)).one()
                if count and minimum==maximum==spec.dimensions:ready+=1
        return {'ready':ready==6,'code':'DATABASE_READY' if ready==6 else 'KNOWLEDGE_NOT_READY',
            'head':actual,'ready_slots':ready,'profile_id':spec.profile_id,'extensions':extensions}
    except Exception:  # noqa: BLE001 - diagnostic output must never contain the DB URL, credentials or SQL parameters.
        return {'ready':False,'code':'DATABASE_CHECK_FAILED'}


def report(values,*,engine=None):
    required=list(BASE_FIELDS)
    if values.get('CHOREOGRAPH_PROFILE','fake')=='live':required.extend(AI_FIELDS)
    if values.get('CHOREOGRAPH_CRM_PROVIDER','fake')=='hubspot':required.extend(CRM_FIELDS)
    missing=[name for name in required if not values.get(name)]
    result={'mode':'read-only-readiness','provider_calls':0,'missing':missing,'configuration':{'ready':False},
            'corpus':corpus_status(),'database':{'ready':False,'code':'DATABASE_NOT_CHECKED'}}
    try:settings=Settings.parse(values)
    except ValueError as error:
        result['configuration']['code']=str(error) if re.fullmatch(r'[A-Z][A-Z_]{2,79}',str(error)) else 'CONFIGURATION_INVALID'
        return result
    result['configuration']={'ready':True,'code':'CONFIGURATION_VALID','ai':settings.profile,'crm':settings.crm_provider}
    if settings.live_ai:
        from .tokenizers import verified_bytes
        try:
            for name in {settings.live_ai.response_tokenizer,settings.live_ai.spec.tokenizer}:
                verified_bytes(name,settings.live_ai.tokenizer_directory)
        except ValueError:result['configuration']={'ready':False,'code':'TOKENIZER_ASSET_INVALID'}
    if engine is not None:result['database']=database_status(engine,settings.live_ai.spec if settings.live_ai else FAKE_SPEC)
    return result


def main():
    from dotenv import dotenv_values
    parser=argparse.ArgumentParser(description='Offline by default; never constructs a provider client.')
    parser.add_argument('--env-file',type=Path,default=ROOT/'.env.example')
    parser.add_argument('--database',action='store_true',help='Explicit read-only SQL check')
    parser.add_argument('--require-ready',action='store_true')
    args=parser.parse_args();values={key:value for key,value in dotenv_values(args.env_file,interpolate=False).items() if value is not None}
    engine=None
    try:
        if args.database:
            from .db import build_engine
            engine=build_engine(Settings.parse(values))
        result=report(values,engine=engine);print(json.dumps(result))
        if args.require_ready and not (result['configuration']['ready'] and result['corpus']['ready'] and
                (not args.database or result['database']['ready'])):raise SystemExit(2)
    except ValueError:
        print('{"mode":"read-only-readiness","provider_calls":0,"code":"CONFIGURATION_INVALID"}')
        raise SystemExit(2) from None
    finally:
        if engine:engine.dispose()


if __name__=='__main__':main()
