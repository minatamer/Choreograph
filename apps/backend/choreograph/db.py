from urllib.parse import urlsplit

from sqlalchemy import create_engine

from .settings import Settings


def build_engine(settings: Settings, *, pool_size=5, max_overflow=2):
    from pathlib import Path
    root=Path(__file__).resolve().parents[3]
    if not settings.database_enabled:
        if settings.testing:
            raise ValueError('EXPLICIT_ISOLATED_OBJECT_STORE_REQUIRED')
        from .object_store import FileObjects, GCSObjects, ObjectEngine
        from .runtime_config import OBJECT_BUCKET
        objects=GCSObjects(OBJECT_BUCKET) if settings.object_backend=='gcs' else FileObjects(
            root/'.runtime'/'private-state')
        return ObjectEngine(objects,settings.token_key)
    if (not settings.testing and settings.object_backend=='local' and
            urlsplit(settings.database_url).path=='/choreograph' and
            (root/'.runtime/storage-transfer.json').exists()):
        raise ValueError('REVERSE_STORAGE_TRANSFER_REQUIRED')
    return create_engine(settings.database_url, pool_size=pool_size, max_overflow=max_overflow, pool_timeout=5,
                         pool_pre_ping=True, hide_parameters=True,
                         connect_args={"connect_timeout": 5, "options": "-c statement_timeout=8000 -c lock_timeout=3000"})
