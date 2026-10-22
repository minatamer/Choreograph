"""Prepare the immutable sample vectors once with explicitly fake embeddings."""
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from choreograph.db import build_engine
from choreograph.knowledge import prepare_samples
from choreograph.settings import load_local

engine=build_engine(load_local())
try:
    with Session(engine) as db,db.begin():prepare_samples(db,datetime.now(UTC))
    print('Six sample guides prepared with fake-hash-64-v2; no provider calls.')
finally:
    engine.dispose()
