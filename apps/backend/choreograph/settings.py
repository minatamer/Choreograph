"""Explicit configuration boundary. Imports never read files or environment variables."""
import base64
import binascii
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .ai_config import LiveAIConfig, parse_live_ai
from .crm_config import LiveCRMConfig, parse_live_crm


@dataclass(frozen=True)
class Settings:
    database_url: str = field(repr=False)
    origin: str
    bridge_secret: str = field(repr=False)
    token_key: str = field(repr=False)
    profile: str = "fake"
    testing: bool = False
    live_ai: LiveAIConfig | None = field(default=None, repr=False)
    crm_provider: str = 'disabled'
    live_crm: LiveCRMConfig | None = field(default=None, repr=False)

    @classmethod
    def parse(cls, values: Mapping[str, str], *, testing: bool = False) -> "Settings":
        profile = values.get("CHOREOGRAPH_PROFILE", "fake")
        if testing and profile != "fake":
            raise ValueError("TEST_PROVIDER_FORBIDDEN")
        if profile not in {"fake", "live"}:
            raise ValueError("LIVE_ACCEPTANCE_NOT_CONFIGURED")
        db = values.get("CHOREOGRAPH_DATABASE_URL", "")
        parsed = urlsplit(db)
        query = parse_qs(parsed.query, keep_blank_values=True)
        socket_hosts = query.get('host', [])
        cloud_socket = (not parsed.hostname and set(query) == {'host'} and len(socket_hosts) == 1 and
                        len(socket_hosts[0] + '/.s.PGSQL.5432') < 108 and
                        re.fullmatch(r'/cloudsql/[a-z0-9-]+:[a-z0-9-]+:[a-z0-9-]+', socket_hosts[0]) is not None)
        if parsed.scheme != "postgresql+psycopg" or not (parsed.hostname or cloud_socket) or not parsed.path:
            raise ValueError("DATABASE_CONFIGURATION_INVALID")
        # libpq query parameters can override the authority, including the test
        # host guard. Only the explicitly validated Cloud SQL socket may use one.
        if query and not cloud_socket:
            raise ValueError("DATABASE_CONFIGURATION_INVALID")
        if testing and (parsed.hostname not in {"127.0.0.1", "localhost"} or
                        not parsed.path.removeprefix("/").startswith("choreograph_test_")):
            raise ValueError("ISOLATED_TEST_DATABASE_REQUIRED")
        origin = values.get("CHOREOGRAPH_ORIGIN", "http://127.0.0.1:45860")
        origin_parts = urlsplit(origin)
        if (origin_parts.scheme not in {"http", "https"} or not origin_parts.hostname or
                origin_parts.path or origin_parts.query or origin_parts.fragment or origin_parts.username):
            raise ValueError("ORIGIN_CONFIGURATION_INVALID")
        secret = values.get("CHOREOGRAPH_BRIDGE_SECRET", "")
        key = values.get("CHOREOGRAPH_TOKEN_KEY", "")
        try:
            valid_key = len(key) == 44 and len(base64.b64decode(key, altchars=b'-_', validate=True)) == 32
        except (ValueError, binascii.Error):
            valid_key = False
        if len(secret) < 32 or not valid_key:
            raise ValueError("SERVER_SECRET_CONFIGURATION_INVALID")
        crm_provider=values.get('CHOREOGRAPH_CRM_PROVIDER','fake' if testing else 'disabled')
        if crm_provider not in {'fake','hubspot','disabled'}:raise ValueError('CRM_CONFIGURATION_INVALID')
        if testing and crm_provider=='hubspot':raise ValueError('TEST_PROVIDER_FORBIDDEN')
        live_ai = parse_live_ai(values) if profile == 'live' else None
        live_crm=parse_live_crm(values,origin) if crm_provider=='hubspot' else None
        return cls(db, origin, secret, key, profile, testing, live_ai, crm_provider, live_crm)


def load_local() -> Settings:
    from dotenv import dotenv_values
    backend = Path(__file__).resolve().parents[1]
    values = {key: value for key, value in dotenv_values(backend / ".env.local",interpolate=False).items() if value is not None}
    settings=Settings.parse(values)
    from sqlalchemy.engine import make_url
    url=make_url(settings.database_url)
    if (url.host not in {'localhost','127.0.0.1'} or url.port!=45862 or url.database!='choreograph' or url.query or
            settings.origin not in {'http://localhost:45860','http://127.0.0.1:45860'}):
        raise ValueError('LOCAL_CONFIGURATION_REQUIRED')
    return settings


def load_environment(values: Mapping[str, str] | None = None) -> Settings:
    """Explicit container composition only; never read a checkout's env file."""
    if values is None:
        import os
        values = os.environ
    return Settings.parse(values)
