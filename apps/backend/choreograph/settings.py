"""Explicit configuration boundary. Imports never read files or environment variables."""
import base64
import binascii
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .ai_config import LiveAIConfig, parse_live_ai, runtime_values
from .crm_config import LiveCRMConfig, parse_live_crm
from .verification import TurnstileConfig
from .verification import configuration as turnstile_configuration


def require_local_manual_target(database_url, origin, code):
    """Manual policies cannot escape the owned loopback development stack."""
    try:
        parsed=urlsplit(database_url)
        valid=(parsed.scheme=='postgresql+psycopg' and parsed.hostname in {'localhost','127.0.0.1'} and
               parsed.port==45862 and parsed.path=='/choreograph' and not parsed.query and
               origin in {'http://localhost:45860','http://127.0.0.1:45860'})
    except ValueError:valid=False
    if not valid:raise ValueError(code)


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
    turnstile: TurnstileConfig | None = field(default=None, repr=False)

    @classmethod
    def parse(cls, values: Mapping[str, str], *, testing: bool = False,
              local_manual_grant_id: str | None = None,
              local_manual_crm_grant_id: str | None = None) -> "Settings":
        values=runtime_values(values)
        profile = 'fake' if values.get('FAKE_MODE', 'true') == 'true' else 'live'
        if testing and profile != "fake":
            raise ValueError("TEST_PROVIDER_FORBIDDEN")
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
        if local_manual_grant_id is not None and profile=='live':
            require_local_manual_target(db,origin,'LOCAL_MANUAL_AI_ONLY')
        if local_manual_crm_grant_id is not None and crm_provider=='hubspot':
            require_local_manual_target(db,origin,'LOCAL_MANUAL_CRM_ONLY')
        live_ai = parse_live_ai(values,manual_grant_id=local_manual_grant_id) if profile == 'live' else None
        live_crm=parse_live_crm(values,origin,manual_grant_id=local_manual_crm_grant_id) if crm_provider=='hubspot' else None
        return cls(db, origin, secret, key, profile, testing, live_ai, crm_provider, live_crm,turnstile_configuration(values,origin))


def load_local() -> Settings:
    from dotenv import dotenv_values
    backend = Path(__file__).resolve().parents[1]
    values = {key: value for key, value in dotenv_values(backend / ".env.local",interpolate=False).items() if value is not None}
    from .runtime_config import LOCAL_MANUAL_AI_GRANT_ID, LOCAL_MANUAL_CRM_GRANT_ID, configuration_values
    settings=Settings.parse(configuration_values(values),local_manual_grant_id=LOCAL_MANUAL_AI_GRANT_ID or None,
                            local_manual_crm_grant_id=LOCAL_MANUAL_CRM_GRANT_ID or None)
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
    from .runtime_config import configuration_values
    return Settings.parse(configuration_values(values))
