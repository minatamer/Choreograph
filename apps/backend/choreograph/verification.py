"""Bounded operation-specific Turnstile verification; no IP or token logging."""
import hashlib
import hmac
import json
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import urlsplit
from uuid import UUID

import httpx

from .errors import DomainError
from .runtime_config import CHAT_VERIFICATION_SECONDS

CHAT_COOKIE = 'choreograph_human'
_RECEIPT = re.compile(r'v1\.([0-9]{1,12})\.([0-9]{1,12})\.([0-9a-f]{64})', re.ASCII)


@dataclass(frozen=True)
class TurnstileConfig:
    site_key:str
    secret_key:str=field(repr=False)
    hostname:str


def configuration(values,origin):
    site=values.get('TURNSTILE_SITE_KEY','');secret=values.get('TURNSTILE_SECRET_KEY','')
    if not site and not secret:return None
    if any(not isinstance(value,str) or not value or len(value)>512 or any(c.isspace() for c in value)
           for value in (site,secret)):
        raise ValueError('TURNSTILE_CONFIGURATION_INVALID')
    return TurnstileConfig(site,secret,urlsplit(origin).hostname)


class TurnstileVerifier:
    def __init__(self,config,*,transport=None,clock=time.monotonic):
        self.config=config;self.clock=clock
        self.client=httpx.Client(transport=transport,trust_env=False,follow_redirects=False,
            timeout=httpx.Timeout(connect=2,read=4,write=2,pool=1),
            limits=httpx.Limits(max_connections=4,max_keepalive_connections=2))

    def close(self):self.client.close()

    def verify(self,proof,action,binding):
        deadline=self.clock()+6
        try:
            with self.client.stream('POST','https://challenges.cloudflare.com/turnstile/v0/siteverify',
                headers={'accept-encoding':'identity'},json={'secret':self.config.secret_key,'response':proof}) as response:
                if response.status_code!=200 or response.headers.get('content-encoding','identity') not in {'','identity'}:return False
                length=response.headers.get('content-length')
                if length is not None and (not length.isdecimal() or len(length)>6 or int(length)>8192):return False
                data=bytearray()
                chunks=(response.content,) if response.is_stream_consumed else response.iter_raw()
                for chunk in chunks:
                    if self.clock()>=deadline or len(data)+len(chunk)>8192:return False
                    data.extend(chunk)
                if self.clock()>=deadline:return False
                result=json.loads(data)
                return (isinstance(result,dict) and result.get('success') is True and
                        result.get('hostname')==self.config.hostname and result.get('action')==action and
                        result.get('cdata')==binding)
        except (httpx.HTTPError,ValueError,TypeError):return False


def require_verification(app,request,action):
    verifier=app.state.verification
    if verifier is None:
        if app.state.settings.profile=='live':
            raise DomainError('VERIFICATION_UNAVAILABLE','Human verification is not configured. Please try again later.',503)
        return
    proof=request.headers.get('x-turnstile-token','')
    binding=request.headers.get('idempotency-key','')
    try:valid_binding=len(binding)==36 and str(UUID(binding))==binding
    except (ValueError,TypeError):valid_binding=False
    if not valid_binding or not proof or len(proof)>2048 or not proof.isascii() or any(c.isspace() for c in proof) or not verifier.verify(proof,action,binding):
        raise DomainError('VERIFICATION_REQUIRED','Please complete the quick human check and try again.',403)
    return True


def _receipt_mac(app, workspace, issued, until):
    config = app.state.settings.turnstile
    if config is None:
        return None
    # Separate purpose; rotating either verification key or the bridge key
    # invalidates receipts. Nothing here contains a reusable Cloudflare token.
    scope = json.dumps(['choreograph-chat-human-v1', config.site_key, config.secret_key, config.hostname,
                        str(workspace.id), workspace.generation, workspace.session_hash, issued, until],
                       separators=(',', ':')).encode()
    return hmac.new(app.state.settings.bridge_secret.encode(), scope, hashlib.sha256).hexdigest()


def _recent_chat_verification(app, request, workspace):
    value = request.cookies.get(CHAT_COOKIE, '')
    match = _RECEIPT.fullmatch(value) if isinstance(value, str) and len(value) <= 110 else None
    if match is None:
        return False
    issued, until = int(match[1]), int(match[2])
    now = app.state.clock().timestamp()
    if not (issued <= now < until <= min(issued + CHAT_VERIFICATION_SECONDS, workspace.expires_at.timestamp())):
        return False
    expected = _receipt_mac(app, workspace, issued, until)
    return expected is not None and hmac.compare_digest(match[3], expected)


def require_chat_verification(app, request, workspace):
    """Only the authenticated workspace can reuse a recent human check for chat.

    Explicit proofs are always checked, even alongside a valid receipt. Reset
    and document replacement continue through fresh require_verification calls.
    """
    if (app.state.verification is not None and not request.headers.get('x-turnstile-token') and
            _recent_chat_verification(app, request, workspace)):
        return None
    return app.state.clock() if require_verification(app, request, 'assistant') else None


def remember_verification(app, response, workspace, checked_at):
    """Mint only after genuine verification; ordinary chat never extends expiry."""
    if checked_at is None or app.state.verification is None:
        return
    issued = int(checked_at.timestamp())
    until = min(issued + CHAT_VERIFICATION_SECONDS, int(workspace.expires_at.timestamp()))
    signature = _receipt_mac(app, workspace, issued, until)
    if signature is None or until <= app.state.clock().timestamp():
        return
    response.set_cookie(CHAT_COOKIE, f'v1.{issued}.{until}.{signature}',
                        max_age=until-int(app.state.clock().timestamp()), expires=datetime.fromtimestamp(until, UTC),
                        httponly=True, secure=app.state.settings.origin.startswith('https://'), samesite='lax', path='/')
