"""Native unattended SQL maintenance + task publication, without CRM clients."""
import base64
import json
import signal
import threading
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from uuid import uuid4

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from . import dispatch, jobs
from .db import build_engine
from .models import DispatcherHeartbeat, Outbox, TaskPublication
from .settings import Settings
from .task_enqueue import CloudTasks, TasksConfig


@contextmanager
def leadership(engine):
    # One checked-out connection owns a session advisory lock through the cycle;
    # the second pool connection serves short data transactions. Explicit unlock
    # is essential: returning a connection to a pool does not end its session.
    with engine.connect() as connection:
        acquired=connection.scalar(text('SELECT pg_try_advisory_lock(45870,1)'))
        connection.commit()
        try:yield acquired
        finally:
            if acquired:
                try:
                    connection.execute(text('SELECT pg_advisory_unlock(45870,1)'));connection.commit()
                except Exception:  # noqa: BLE001 - invalidate rather than returning a possibly locked session.
                    connection.invalidate()


def heartbeat(engine,instance,now,*,published=0,code=None):
    with Session(engine) as db,db.begin():
        row=db.get(DispatcherHeartbeat,'primary')
        if not row:
            row=DispatcherHeartbeat(id='primary',instance=instance,attempted_at=now,cycles=0,published=0);db.add(row)
        row.instance=instance;row.attempted_at=now;row.cycles+=1;row.published+=published;row.code=code
        if code is None:row.succeeded_at=now


def cycle(engine,transport,clock,instance,*,stopping=lambda:False):
    try:
        jobs.maintenance(engine,clock())
        dispatch.settle_terminal(engine)
        count=dispatch.tick(engine,transport,clock,stopping=stopping)
    except Exception:  # noqa: BLE001 - diagnostics retain only a fixed code; durable leases permit recovery.
        heartbeat(engine,instance,clock(),code='DISPATCH_CYCLE_FAILED')
        raise
    heartbeat(engine,instance,clock(),published=count)
    return count


def status(engine,now):
    with Session(engine) as db:
        row=db.get(DispatcherHeartbeat,'primary')
        states=dict(db.execute(select(TaskPublication.state,func.count()).group_by(TaskPublication.state)).all())
        codes=dict(db.execute(select(TaskPublication.code,func.count()).where(TaskPublication.code.is_not(None)).group_by(TaskPublication.code)).all())
        work=dict(db.execute(select(Outbox.state,func.count()).group_by(Outbox.state)).all())
        work_codes=dict(db.execute(select(Outbox.code,func.count()).where(Outbox.code.is_not(None)).group_by(Outbox.code)).all())
        oldest=db.scalar(select(func.min(Outbox.due_at)).where(Outbox.state.in_(['pending','retrying','reconciling'])))
        return {'code':row.code if row else 'DISPATCH_NOT_STARTED','cycles':row.cycles if row else 0,
            'published':row.published if row else 0,'cycle_age_seconds':int((now-row.attempted_at).total_seconds()) if row else None,
            'success_age_seconds':int((now-row.succeeded_at).total_seconds()) if row and row.succeeded_at else None,
            'publications':states,'publication_codes':codes,'work':work,'work_codes':work_codes,
            'oldest_due_seconds':max(0,int((now-oldest).total_seconds())) if oldest else None}


def settings_for_dispatcher(values):
    # These values are deliberately unused cryptographic placeholders. This role
    # never reads the bridge/token/provider secrets or constructs those clients.
    return Settings.parse({'CHOREOGRAPH_DATABASE_URL':values.get('CHOREOGRAPH_DATABASE_URL',''),
        'FAKE_MODE':'true','CHOREOGRAPH_CRM_PROVIDER':'disabled',
        'CHOREOGRAPH_BRIDGE_SECRET':'dispatcher-unused-'+'x'*32,
        'CHOREOGRAPH_TOKEN_KEY':base64.urlsafe_b64encode(bytes(32)).decode()})


def health_server(port,health,*,host='0.0.0.0'):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):super().setup();self.connection.settimeout(1)
        def do_GET(self):
            if self.path not in {'/health/live','/health/ready'}:self.send_error(404);return
            ready=health['ready'] if self.path.endswith('ready') else time.monotonic()-health['at']<90
            self.send_response(200 if ready else 503);self.send_header('content-length','0')
            self.send_header('cache-control','no-store');self.end_headers()
        def log_message(self,*args):pass
    server=HTTPServer((host,port),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    return server,thread


def run(values,*,once=False,inspect=False):
    config=None if inspect else TasksConfig.parse(values)
    settings=settings_for_dispatcher(values)
    engine=build_engine(settings,pool_size=2,max_overflow=0)
    transport=None;server=None;thread=None;instance=uuid4();stop=threading.Event()
    def clock():return datetime.now(UTC)
    health={'at':time.monotonic(),'ready':False}
    try:
        if inspect:
            print(json.dumps(status(engine,clock())));return
        transport=CloudTasks(config,authorized=True)
        if not once:
            port=int(values.get('CHOREOGRAPH_DISPATCH_HEALTH_PORT','8080'))
            if not 1<=port<=65535:raise ValueError('PORT_INVALID')
            server,thread=health_server(port,health)
            for name in ('SIGTERM','SIGINT'):
                if hasattr(signal,name):signal.signal(getattr(signal,name),lambda *_:stop.set())
        while not stop.is_set():
            try:
                with leadership(engine) as leader:
                    if leader:
                        count=cycle(engine,transport,clock,instance,stopping=stop.is_set)
                        print(json.dumps({'code':'DISPATCH_CYCLE_COMPLETED','published':count}),flush=True)
                        health['ready']=True
                    else:
                        snapshot=status(engine,clock())
                        health['ready']=snapshot['success_age_seconds'] is not None and snapshot['success_age_seconds']<90
            except Exception:  # noqa: BLE001 - keep bounded recovery alive without configuration/payload logging.
                health['ready']=False;print('{"code":"DISPATCH_CYCLE_FAILED"}',flush=True)
            health['at']=time.monotonic()
            if once:break
            stop.wait(2)
    finally:
        try:
            if server:server.shutdown();server.server_close()
            if thread:thread.join(timeout=2)
            if transport:transport.close()
        finally:engine.dispose()
