import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .errors import DomainError
from .models import Workspace
from .persistence import advisory, repo_first, repo_rows

COOKIE = "choreograph_guest"
MAX_RETAINED_WORKSPACES = 256


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def csrf_token(token: str, secret: str) -> str:
    return hmac.new(secret.encode(), ("csrf:" + token).encode(), hashlib.sha256).hexdigest()


def validate_zone(zone: str) -> str:
    try:
        ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        raise DomainError("TIMEZONE_REQUIRED", "Choose your timezone before scheduling.", 422) from None
    return zone


def find_workspace(db, token: str | None, now: datetime, *, lock: bool = False, allow_retired=False):
    if not token or len(token) > 128:
        raise DomainError("SESSION_REQUIRED", "Start a new demo to continue.", 401)
    workspace = repo_first(db,Workspace,filters={'session_hash':digest(token)},lock=lock)
    if workspace is None:
        raise DomainError("SESSION_REQUIRED", "Start a new demo to continue.", 401)
    if not allow_retired and (not workspace.active or workspace.expires_at <= now):
        raise DomainError("SESSION_EXPIRED", "This demo has ended. Start a new demo to continue.", 410)
    return workspace


def require_csrf(token: str, provided: str | None, secret: str):
    if not provided or not hmac.compare_digest(csrf_token(token, secret), provided):
        raise DomainError("CSRF_REQUIRED", "Refresh the demo and try again.", 403)


def create_workspace(db, zone: str, now: datetime, *, embedding_profile_id: str | None = None):
    validate_zone(zone)
    # Serialize every creation path until its caller commits or rolls back.
    # Retired rows still consume storage and may retain unresolved cleanup.
    advisory(db,45865,1)
    db.flush()
    if len(repo_rows(db, Workspace)) >= MAX_RETAINED_WORKSPACES:
        raise DomainError('DEMO_CAPACITY', 'The demo is busy. Please try again later.', 429)
    token = secrets.token_urlsafe(48)
    workspace = Workspace(session_hash=digest(token), timezone=zone, created_at=now,
                          expires_at=now + timedelta(hours=2), active=True, generation=1,
                          revision=1, seeded=False, draft={}, messages=[], crm_mode="skipped")
    if embedding_profile_id is not None:
        workspace.embedding_profile_id = embedding_profile_id
    db.add(workspace)
    db.flush()
    return workspace, token


def retire(workspace):
    workspace.active = False
    workspace.generation += 1
    workspace.revision += 1


def require_generation(workspace, generation: int):
    if generation != workspace.generation:
        raise DomainError("STALE_GENERATION", "This demo changed. Refresh before continuing.")
