from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .settings import Settings


def build_engine(settings: Settings, *, pool_size=5, max_overflow=2) -> Engine:
    return create_engine(settings.database_url, pool_size=pool_size, max_overflow=max_overflow, pool_timeout=5,
                         pool_pre_ping=True, hide_parameters=True,
                         connect_args={"connect_timeout": 5, "options": "-c statement_timeout=8000 -c lock_timeout=3000"})
