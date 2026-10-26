"""Container composition. Local launchers keep their separate explicit loader."""
import argparse
import os
import signal
import threading
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text

from .ai_admission import AttemptScope
from .composition import compose_ai
from .crm_composition import compose_crm
from .db import build_engine
from .persistence import is_object
from .settings import load_environment


def application(role, settings, engine, values, *, ai_runtime=None,crm_provider=None):
    if role=='bootstrap':
        from fastapi import FastAPI
        app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
        @app.get('/health')
        @app.get('/healthz')
        def bootstrap_health():return {'status':'bootstrap','application_ready':False}
        return app
    publisher=None
    object_mode=is_object(engine)
    if object_mode and values.get('CHOREOGRAPH_TASKS_ENABLED')=='true':
        raise ValueError('OBJECT_TASKS_NOT_USED')
    if not object_mode and values.get('CHOREOGRAPH_TASKS_ENABLED')=='true':
        from .task_enqueue import CloudTasks, TasksConfig
        publisher=CloudTasks(TasksConfig.parse(values),authorized=True)
    if role == 'api':
        from .api import create_app
        try:
            return create_app(settings, engine, ai_runtime=ai_runtime,crm_provider=crm_provider,
                              publisher=publisher,close_publisher=publisher is not None)
        except BaseException:
            if publisher is not None:publisher.close()
            raise
    from .task_delivery import MaintenanceTarget, TaskTarget, create_delivery_app
    target = None if object_mode else TaskTarget(values.get('CHOREOGRAPH_TASK_URL', ''),
                        values.get('CHOREOGRAPH_TASK_AUDIENCE', ''),
                        values.get('CHOREOGRAPH_TASK_SERVICE_EMAIL', ''))
    maintenance=None
    if object_mode or publisher is not None:
        audience=values.get('CHOREOGRAPH_WORKER_AUDIENCE','') if object_mode else target.audience
        maintenance=MaintenanceTarget(audience+'/internal/maintenance',audience,
                                     values.get('CHOREOGRAPH_MAINTENANCE_SERVICE_EMAIL',''))
    provider=crm_provider if crm_provider is not None else compose_crm(settings,engine)
    app = create_delivery_app(settings, engine, provider, target,close_provider=crm_provider is None,
        maintenance_target=maintenance,publisher=publisher,close_publisher=publisher is not None)

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('role', choices=['api', 'worker', 'migrate', 'schema-downgrade', 'prepare-knowledge', 'maintenance', 'runner','dispatcher','dispatch-once','dispatch-status','bootstrap','readiness'])
    parser.add_argument('--target')
    parser.add_argument('--command-key', help='Explicit UUID for finite live sample preparation')
    args = parser.parse_args()
    if args.role=='bootstrap':
        import uvicorn
        port=int(os.environ.get('PORT','8080'))
        if not 1<=port<=65535:raise ValueError('PORT_INVALID')
        return uvicorn.run(application('bootstrap',None,None,{}),host='0.0.0.0',port=port,access_log=False,log_level='critical')
    if args.role in {'dispatcher','dispatch-once','dispatch-status'}:
        from .dispatcher import run
        return run(os.environ,once=args.role=='dispatch-once',inspect=args.role=='dispatch-status')
    settings = load_environment()
    engine = build_engine(settings)
    runtime = None
    crm_runtime = None
    try:
        if args.role=='readiness':
            import json

            from .readiness import report
            result=report(os.environ,engine=engine);print(json.dumps(result))
            if not all(result[key]['ready'] for key in ('configuration','corpus','database')):raise SystemExit(2)
            return
        if args.role in {'migrate', 'schema-downgrade'}:
            if is_object(engine):raise ValueError('DATABASE_DISABLED_NO_MIGRATIONS')
            from .migrate import downgrade, migrate
            if args.role == 'schema-downgrade':
                if not args.target:
                    raise ValueError('EXPLICIT_SCHEMA_TARGET_REQUIRED')
                downgrade(engine, args.target)
            else:
                migrate(engine, args.target or 'head')
            print('{"code":"SCHEMA_COMMAND_COMPLETED"}')
            return
        if is_object(engine):engine.load()
        else:
            with engine.connect() as connection:
                connection.execute(text('SELECT 1'))
        if args.role == 'prepare-knowledge':
            from .knowledge import prepare_pack, prepare_samples
            from .persistence import Session
            if settings.profile == 'fake':
                with Session(engine) as db, db.begin():
                    prepare_samples(db, datetime.now(UTC))
                print('{"code":"FAKE_KNOWLEDGE_PREPARED"}', flush=True)
            else:
                try:
                    if len(args.command_key or '') != 36:
                        raise ValueError()
                    UUID(args.command_key)
                except (ValueError, TypeError, AttributeError):
                    raise ValueError('EXPLICIT_PREPARATION_COMMAND_KEY_REQUIRED') from None
                runtime = compose_ai(settings, engine)
                scoped = runtime.for_scope(AttemptScope(None, 0, args.command_key))
                result = prepare_pack(engine, datetime.now(UTC), spec=scoped.spec,
                                      embedder=scoped.embedder, tokenizer=scoped.tokenizer)
                print(f'{{"code":"KNOWLEDGE_PREPARED","count":{result["prepared"]}}}', flush=True)
            return
        if args.role in {'maintenance', 'runner'}:
            from .jobs import tick
            if args.role == 'runner':
                runtime = compose_ai(settings, engine)
                crm_runtime=compose_crm(settings,engine)
            stop = threading.Event()
            for name in ('SIGTERM', 'SIGINT'):
                if hasattr(signal, name):
                    signal.signal(getattr(signal, name), lambda *_: stop.set())
            while not stop.is_set():
                if args.role=='runner':count=tick(engine,settings,crm_runtime,lambda:datetime.now(UTC))
                else:
                    from .jobs import maintenance
                    count=maintenance(engine,datetime.now(UTC))
                print(f'{{"code":"RELEASE_MAINTENANCE","count":{count}}}', flush=True)
                if args.role == 'maintenance':
                    break
                stop.wait(2)
            return
        import uvicorn
        port = int(os.environ.get('PORT', '8080'))
        if not 1 <= port <= 65535:
            raise ValueError('PORT_INVALID')
        if args.role == 'api':
            runtime = compose_ai(settings, engine)
        crm_runtime=compose_crm(settings,engine)
        uvicorn.run(application(args.role, settings, engine, os.environ, ai_runtime=runtime,crm_provider=crm_runtime),
                    host='0.0.0.0', port=port, access_log=False, log_level='critical')
    finally:
        try:
            try:
                if crm_runtime is not None:crm_runtime.close()
            finally:
                if runtime is not None:runtime.close()
        finally:
            engine.dispose()


if __name__ == '__main__':
    try:
        main()
    except Exception:  # noqa: BLE001 - composition diagnostics never expose configuration or provider payloads.
        print('{"code":"RELEASE_COMMAND_FAILED"}', flush=True)
        raise SystemExit(1) from None
