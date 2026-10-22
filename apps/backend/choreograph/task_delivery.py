"""Prepared private Cloud Tasks boundary; never mounted by the local guest API."""
import asyncio
import base64
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import FastAPI, Request, Response
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from . import jobs
from .contracts import Contract
from .models import Outbox


class Delivery(Contract):
    workspace_id: UUID
    event_id: UUID


@dataclass(frozen=True)
class TaskTarget:
    url: str
    audience: str
    service_email: str

    def __post_init__(self):
        for value in (self.url, self.audience):
            parsed = urlsplit(value)
            if len(value)>1024 or parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
                raise ValueError('TASK_TARGET_INVALID')
        if not re.fullmatch(r'[a-z][a-z0-9-]{4,28}[a-z0-9]@[a-z][a-z0-9-]{4,28}[a-z0-9]\.iam\.gserviceaccount\.com',self.service_email):
            raise ValueError('TASK_IDENTITY_INVALID')
        target,audience=urlsplit(self.url),urlsplit(self.audience)
        if (target.path!='/internal/tasks/crm' or audience.path or target.netloc!=audience.netloc or
                target.port not in {None,443} or audience.port not in {None,443}):
            raise ValueError('TASK_TARGET_INVALID')


def task_payload(target, workspace_id, event_id):
    """Build a REST task description only. Enqueue/IAM remain external checks."""
    body = Delivery(workspace_id=workspace_id, event_id=event_id).model_dump_json()
    return {'httpRequest': {'url': target.url, 'httpMethod': 'POST',
            'headers': {'Content-Type': 'application/json'},
            'body': base64.b64encode(body.encode()).decode(),
            'oidcToken': {'serviceAccountEmail': target.service_email, 'audience': target.audience}},
            'dispatchDeadline': '120s'}


def verify_google_token(token, audience):
    # Import/certificate fetching happen only for an explicitly configured
    # private handler request; tests inject a verifier and never contact Google.
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2.id_token import verify_oauth2_token
    from requests import Session as HTTPSession

    with HTTPSession() as session:
        transport = GoogleRequest(session=session)

        def bounded_request(url, method='GET', body=None, headers=None, **_):
            return transport(url, method=method, body=body, headers=headers, timeout=5)

        return verify_oauth2_token(token, bounded_request, audience=audience)


def create_delivery_app(settings, engine, provider, target, *, verifier=verify_google_token, clock=None,close_provider=False):
    @asynccontextmanager
    async def lifespan(_):
        try:yield
        finally:
            if close_provider:provider.close()
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None,lifespan=lifespan)
    clock = clock or (lambda: datetime.now(UTC))
    verification_slots = asyncio.Semaphore(4)

    @app.post('/internal/tasks/crm')
    async def delivery(request: Request):
        authorization = request.headers.get('authorization', '')
        if not authorization.startswith('Bearer ') or not 1 <= len(authorization[7:]) <= 8192:
            return Response(status_code=403)
        try:
            async with asyncio.timeout(6):
                async with verification_slots:
                    claims = await run_in_threadpool(verifier, authorization[7:], target.audience)
            if (claims.get('iss') not in {'accounts.google.com', 'https://accounts.google.com'}
                    or claims.get('aud') != target.audience or claims.get('email') != target.service_email
                    or claims.get('email_verified') is not True):
                return Response(status_code=403)
        except Exception:  # noqa: BLE001 - every verifier failure must deny access without leaking token details.
            return Response(status_code=403)
        try:
            if request.headers.get('content-type', '').split(';')[0] != 'application/json':
                return Response(status_code=415)
            body = bytearray()
            async with asyncio.timeout(5):
                async for chunk in request.stream():
                    body.extend(chunk)
                    if len(body) > 1024:
                        return Response(status_code=413)
            command = Delivery.model_validate_json(body)
        except TimeoutError:
            return Response(status_code=408)
        except (ValidationError, ValueError):
            return Response(status_code=422)

        def process():
            job = jobs.claim(engine, clock(), event_id=command.event_id, workspace_id=command.workspace_id)
            if job:
                jobs.deliver(engine, settings, provider, job, clock)
            with Session(engine) as db:
                row = db.get(Outbox, (command.workspace_id, command.event_id))
                return 503 if row and row.state in {'pending', 'processing', 'retrying', 'reconciling'} else 204

        try:
            return Response(status_code=await run_in_threadpool(process))
        except Exception:  # noqa: BLE001 - the private delivery boundary returns only a retry status.
            return Response(status_code=503)

    return app
