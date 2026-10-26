"""Private authenticated worker: Scheduler objects, optional legacy SQL tasks."""
import asyncio
import base64
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar, Literal
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import FastAPI, Request, Response
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from . import jobs
from .contracts import Contract
from .models import Outbox
from .persistence import Session


class Delivery(Contract):
    workspace_id: UUID
    event_id: UUID


class Maintenance(Contract):
    sweep: Literal[True]


@dataclass(frozen=True)
class TaskTarget:
    PATH: ClassVar[str]='/internal/tasks/crm'
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
        if (target.path!=self.PATH or audience.path or target.netloc!=audience.netloc or
                target.port not in {None,443} or audience.port not in {None,443}):
            raise ValueError('TASK_TARGET_INVALID')


class MaintenanceTarget(TaskTarget):
    PATH='/internal/maintenance'


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


def create_delivery_app(settings, engine, provider, target=None, *, verifier=verify_google_token, clock=None,close_provider=False,
                        maintenance_target=None,publisher=None,close_publisher=False):
    if target is None:
        from .persistence import is_object
        if not is_object(engine) or maintenance_target is None or publisher is not None:
            raise ValueError('SCHEDULER_TARGET_REQUIRED')
    @asynccontextmanager
    async def lifespan(_):
        try:yield
        finally:
            if close_publisher and publisher is not None:publisher.close()
            if close_provider:provider.close()
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None,lifespan=lifespan)
    clock = clock or (lambda: datetime.now(UTC))
    verification_slots = asyncio.Semaphore(4)

    async def authorized(request,identity):
        authorization = request.headers.get('authorization', '')
        if not authorization.startswith('Bearer ') or not 1 <= len(authorization[7:]) <= 8192:
            return False
        try:
            async with asyncio.timeout(6):
                async with verification_slots:
                    claims = await run_in_threadpool(verifier, authorization[7:], identity.audience)
            if (claims.get('iss') not in {'accounts.google.com', 'https://accounts.google.com'}
                    or claims.get('aud') != identity.audience or claims.get('email') != identity.service_email
                    or claims.get('email_verified') is not True):
                return False
        except Exception:  # noqa: BLE001 - every verifier failure must deny access without leaking token details.
            return False
        return True

    async def command_body(request,model):
        try:
            if request.headers.get('content-type', '').split(';')[0] != 'application/json':
                return Response(status_code=415)
            body = bytearray()
            async with asyncio.timeout(5):
                async for chunk in request.stream():
                    body.extend(chunk)
                    if len(body) > 1024:
                        return Response(status_code=413)
            return model.model_validate_json(body)
        except TimeoutError:
            return Response(status_code=408)
        except (ValidationError, ValueError):
            return Response(status_code=422)

    async def delivery(request: Request):
        if not await authorized(request,target):return Response(status_code=403)
        command=await command_body(request,Delivery)
        if isinstance(command,Response):return command

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

    if target is not None:app.post('/internal/tasks/crm')(delivery)

    if maintenance_target is not None and (publisher is not None or target is None):
        @app.post('/internal/maintenance')
        async def maintenance(request:Request):
            if not await authorized(request,maintenance_target):return Response(status_code=403)
            command=await command_body(request,Maintenance)
            if isinstance(command,Response):return command
            def sweep():
                if target is None:
                    return jobs.scheduled_tick(engine,settings,provider,clock)
                from . import dispatch
                jobs.maintenance(engine,clock())
                dispatch.settle_terminal(engine)
                dispatch.tick(engine,publisher,clock,limit=3)
            try:
                await run_in_threadpool(sweep)
                return Response(status_code=204)
            except Exception:  # noqa: BLE001 - Scheduler retries; durable claims and counters remain authoritative.
                return Response(status_code=503)

    return app
