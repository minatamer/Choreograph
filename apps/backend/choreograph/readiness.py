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
from .ai_config import POSITIVE_GRANT_FIELDS, runtime_values
from .models import Chunk, DocumentVersion
from .runtime_config import configuration_values
from .settings import Settings, require_local_manual_target

ROOT=Path(__file__).resolve().parents[3]
BASE_FIELDS=('CHOREOGRAPH_DATABASE_URL','CHOREOGRAPH_BRIDGE_SECRET','CHOREOGRAPH_TOKEN_KEY')
AI_FIELDS=('OPENAI_API_KEY','CHOREOGRAPH_AI_RESPONSE_MODEL','CHOREOGRAPH_AI_EMBEDDING_MODEL',
    'CHOREOGRAPH_AI_RESPONSE_TOKENIZER','CHOREOGRAPH_AI_EMBEDDING_TOKENIZER','CHOREOGRAPH_AI_EMBEDDING_DIMENSIONS',
    'CHOREOGRAPH_AI_CHUNKER','CHOREOGRAPH_AI_GRANT_ID','CHOREOGRAPH_AI_EXPIRES_AT',
    *('CHOREOGRAPH_AI_'+field.upper() for field in POSITIVE_GRANT_FIELDS))
CRM_FIELDS=('CHOREOGRAPH_HUBSPOT_APP_ID','CHOREOGRAPH_HUBSPOT_CLIENT_ID','CHOREOGRAPH_HUBSPOT_CLIENT_SECRET',
    'CHOREOGRAPH_HUBSPOT_REDIRECT_URI','CHOREOGRAPH_HUBSPOT_DISTRIBUTION','CHOREOGRAPH_HUBSPOT_CAPACITY',
    'CHOREOGRAPH_CRM_GRANT_ID','CHOREOGRAPH_CRM_EXPIRES_AT','CHOREOGRAPH_CRM_REQUESTS','CHOREOGRAPH_CRM_WORKSPACE_REQUESTS')
CRM_FINITE_FIELDS=frozenset(name for name in CRM_FIELDS if name.startswith('CHOREOGRAPH_CRM_'))


def hubspot_report(values, *, application=None, local_manual_crm_grant_id=None):
    """CRM configuration only: an expired paid-AI grant cannot hide its diagnosis."""
    from .crm_config import parse_live_crm
    try:values=configuration_values(values,application=application)
    except ValueError as error:
        return {'mode':'read-only-hubspot-readiness','provider_calls':0,'configuration_ready':False,
                'ai_independent':True,'missing':[],'changes_required':[],'code':str(error)}
    origin=values.get('CHOREOGRAPH_ORIGIN','http://127.0.0.1:45860')
    changes=[]
    if values.get('CHOREOGRAPH_CRM_PROVIDER','disabled')!='hubspot':changes.append('REGISTER_CHOREOGRAPH_OAUTH_APP')
    if origin=='http://127.0.0.1:45860':changes.append('CHOREOGRAPH_ORIGIN')
    result={'mode':'read-only-hubspot-readiness','provider_calls':0,'configuration_ready':False,
            'ai_independent':True,'missing':[name for name in CRM_FIELDS if not values.get(name) and
                (local_manual_crm_grant_id is None or name not in CRM_FINITE_FIELDS)],
            'changes_required':changes,'local_callback':'http://localhost:45860/auth/hubspot/callback',
            'settings_file':'choreograph/runtime_config.py'}
    if 'REGISTER_CHOREOGRAPH_OAUTH_APP' in changes:result['code']='CRM_DISABLED';return result
    try:
        if local_manual_crm_grant_id is not None:
            require_local_manual_target(values.get('CHOREOGRAPH_DATABASE_URL',''),origin,'LOCAL_MANUAL_CRM_ONLY')
        parse_live_crm(values,origin,manual_grant_id=local_manual_crm_grant_id)
    except ValueError as error:
        result['code']=str(error) if re.fullmatch(r'[A-Z_]{3,80}',str(error)) else 'CRM_CONFIGURATION_INVALID'
        return result
    result['configuration_ready']=True;result['code']='CRM_CONFIGURATION_VALID'
    result['crm_policy']='local_owner_manual' if local_manual_crm_grant_id is not None else 'finite'
    return result


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


def report(values,*,engine=None,local_manual_grant_id=None,local_manual_crm_grant_id=None):
    try:values=runtime_values(configuration_values(values))
    except ValueError as error:return {'mode':'read-only-readiness','provider_calls':0,'missing':[],
        'configuration':{'ready':False,'code':str(error)},'corpus':corpus_status(),
        'database':{'ready':False,'code':'DATABASE_NOT_CHECKED'}}
    required=list(BASE_FIELDS)
    if values.get('FAKE_MODE','true')=='false':
        finite_fields={'CHOREOGRAPH_AI_GRANT_ID','CHOREOGRAPH_AI_EXPIRES_AT',
            *('CHOREOGRAPH_AI_'+name.upper() for name in POSITIVE_GRANT_FIELDS if not name.endswith('_rate'))}
        required.extend(name for name in AI_FIELDS if local_manual_grant_id is None or name not in finite_fields)
    if values.get('CHOREOGRAPH_CRM_PROVIDER','fake')=='hubspot':
        required.extend(name for name in CRM_FIELDS if local_manual_crm_grant_id is None or name not in CRM_FINITE_FIELDS)
    missing=[name for name in required if not values.get(name)]
    result={'mode':'read-only-readiness','provider_calls':0,'missing':missing,'configuration':{'ready':False},
            'corpus':corpus_status(),'database':{'ready':False,'code':'DATABASE_NOT_CHECKED'}}
    try:settings=Settings.parse(values,local_manual_grant_id=local_manual_grant_id,
                                local_manual_crm_grant_id=local_manual_crm_grant_id)
    except ValueError as error:
        result['configuration']['code']=str(error) if re.fullmatch(r'[A-Z][A-Z_]{2,79}',str(error)) else 'CONFIGURATION_INVALID'
        return result
    result['configuration']={'ready':True,'code':'CONFIGURATION_VALID','ai':settings.profile,'crm':settings.crm_provider}
    if settings.live_crm:
        result['configuration']['crm_policy']='local_owner_manual' if local_manual_crm_grant_id is not None else 'finite'
    if settings.live_ai:
        result['configuration']['ai_policy']='local_owner_manual' if local_manual_grant_id is not None else 'finite'
    if settings.live_ai:
        from .tokenizers import RESPONSE_COUNTER, verified_bytes
        try:
            for name in {settings.live_ai.response_tokenizer,settings.live_ai.spec.tokenizer}:
                if name!=RESPONSE_COUNTER:verified_bytes(name,settings.live_ai.tokenizer_directory)
        except ValueError:result['configuration']={'ready':False,'code':'TOKENIZER_ASSET_INVALID'}
    if engine is not None:result['database']=database_status(engine,settings.live_ai.spec if settings.live_ai else FAKE_SPEC)
    return result


def main():
    from dotenv import dotenv_values
    parser=argparse.ArgumentParser(description='Offline by default; never constructs a provider client.')
    parser.add_argument('--env-file',type=Path,default=ROOT/'apps/backend/.env.example')
    parser.add_argument('--database',action='store_true',help='Explicit read-only SQL check')
    parser.add_argument('--require-ready',action='store_true')
    parser.add_argument('--hubspot-only',action='store_true',help='CRM configuration only; no AI grant, provider or SQL access')
    args=parser.parse_args();values={key:value for key,value in dotenv_values(args.env_file,interpolate=False).items() if value is not None}
    from .runtime_config import LOCAL_MANUAL_AI_GRANT_ID, LOCAL_MANUAL_CRM_GRANT_ID
    local=args.env_file.resolve()==(ROOT/'apps/backend/.env.local').resolve()
    manual_id=(LOCAL_MANUAL_AI_GRANT_ID or None) if local else None
    crm_manual_id=(LOCAL_MANUAL_CRM_GRANT_ID or None) if local else None
    if args.hubspot_only:
        if args.database:parser.error('--hubspot-only cannot be combined with --database')
        result=hubspot_report(values,local_manual_crm_grant_id=crm_manual_id);print(json.dumps(result))
        if args.require_ready and not result['configuration_ready']:raise SystemExit(2)
        return
    engine=None
    try:
        if args.database:
            from .db import build_engine
            engine=build_engine(Settings.parse(configuration_values(values),local_manual_grant_id=manual_id,
                                               local_manual_crm_grant_id=crm_manual_id))
        result=report(values,engine=engine,local_manual_grant_id=manual_id,
                      local_manual_crm_grant_id=crm_manual_id);print(json.dumps(result))
        if args.require_ready and not (result['configuration']['ready'] and result['corpus']['ready'] and
                (not args.database or result['database']['ready'])):raise SystemExit(2)
    except ValueError:
        print('{"mode":"read-only-readiness","provider_calls":0,"code":"CONFIGURATION_INVALID"}')
        raise SystemExit(2) from None
    finally:
        if engine:engine.dispose()


if __name__=='__main__':main()
