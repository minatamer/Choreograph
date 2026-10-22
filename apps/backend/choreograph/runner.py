"""Owned local durable runner. No listener, cloud identity or external provider needed."""
import argparse
import json
import os
import signal
import threading
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from .composition import compose_ai
from .crm_composition import compose_crm
from .db import build_engine
from .jobs import tick
from .settings import load_local


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
    settings=load_local();engine=build_engine(settings);provider=None
    ai_runtime=None
    stop=threading.Event()
    for name in ('SIGTERM','SIGINT'):
        if hasattr(signal,name):signal.signal(getattr(signal,name),lambda *_:stop.set())
    root=Path(__file__).resolve().parents[3];runtime=root/'.runtime';runtime.mkdir(exist_ok=True)
    path=runtime/'runner-ready.json'
    instance=os.environ.get('CHOREOGRAPH_RUNNER_INSTANCE','manual')
    def ready():
        payload={'pid':os.getpid(),'instance':instance,'profile':settings.profile,'at':datetime.now(UTC).isoformat(),'status':'ready'}
        temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(payload),encoding='utf-8');temporary.replace(path)
    try:
        ai_runtime=compose_ai(settings,engine)
        provider=compose_crm(settings,engine)
        with engine.connect() as db:db.execute(text('SELECT 1'))
        ready()
        while not stop.is_set():
            try:
                count=tick(engine,settings,provider,lambda:datetime.now(UTC));ready()
                if count:print(json.dumps({'code':'RUNNER_TICK','count':count}),flush=True)
            except Exception:  # noqa: BLE001 - a failed bounded tick must keep recovery alive without logging private data.
                print('{"code":"RUNNER_TICK_FAILED"}',flush=True)
            if args.once:break
            stop.wait(2)
    finally:
        try:
            try:
                try:
                    if provider is not None:provider.close()
                finally:
                    if ai_runtime is not None:ai_runtime.close()
            finally:engine.dispose()
        finally:
            try:
                if json.loads(path.read_text()).get('pid')==os.getpid():path.unlink()
            except (OSError,ValueError):pass


if __name__=='__main__':main()
