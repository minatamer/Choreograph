"""Explicit fake-only browser test control for one freshly created guest workspace."""
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'apps' / 'backend'))
from sqlalchemy.orm import Session

from choreograph.db import build_engine
from choreograph.models import Workspace
from choreograph.settings import load_local


def main():
    settings = load_local()
    if settings.profile != 'fake':
        raise RuntimeError('BROWSER_FIXTURE_REQUIRES_FAKE')
    workspace_id = UUID(sys.argv[1])
    engine = build_engine(settings)
    try:
        with Session(engine) as db, db.begin():
            workspace = db.get(Workspace, workspace_id, with_for_update=True)
            now = datetime.now(UTC)
            if not workspace or not workspace.active or workspace.created_at < now - timedelta(minutes=10):
                raise RuntimeError('FRESH_BROWSER_FIXTURE_REQUIRED')
            workspace.expires_at = now - timedelta(seconds=1)
        print('BROWSER_FIXTURE_EXPIRED')
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
