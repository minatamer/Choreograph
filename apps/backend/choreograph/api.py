"""Inert application factory. Composition and configuration happen in the entry point."""
import asyncio
import hmac
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from . import domain, service
from .contracts import (
    BookingCommand,
    BookingView,
    ChatCommand,
    Command,
    DraftCommand,
    Health,
    MutationView,
    RequestView,
    ResetSession,
    SessionView,
    StartSession,
    SubmitCommand,
    Summary,
    VerificationView,
    WeekView,
)
from .errors import DomainError
from .models import Activity, Enquiry, Outbox, Reservation
from .sessions import (
    COOKIE,
    create_workspace,
    csrf_token,
    find_workspace,
    require_csrf,
    require_generation,
)
from .settings import Settings
from .verification import TurnstileVerifier, require_verification


class Boundary:
    def __init__(self, app, settings: Settings, body_timeout: float = 10):
        self.app = app
        self.settings = settings
        self.body_timeout = body_timeout

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        async def reject(status, code):
            await JSONResponse({"code": code, "message": "This request could not be accepted."}, status)(scope, receive, send)
        if scope["path"] != "/health":
            if not hmac.compare_digest(headers.get(b"x-choreograph-bridge", b""), self.settings.bridge_secret.encode()):
                return await reject(403, "BRIDGE_REQUIRED")
            if (scope["method"] not in {"GET", "HEAD"} and
                    headers.get(b"origin", b"").decode("latin1") != self.settings.origin):
                return await reject(403, "ORIGIN_REQUIRED")
        if scope["method"] in {"POST", "PUT", "PATCH"}:
            if headers.get(b"content-type", b"").split(b";")[0] != b"application/json":
                return await reject(415, "JSON_REQUIRED")
            limit = 2_850_000 if scope["path"].startswith("/v1/documents/") else 16_384
            body = bytearray()
            try:
                async with asyncio.timeout(self.body_timeout):
                    while True:
                        part = await receive()
                        if part["type"] == "http.disconnect":
                            return
                        body.extend(part.get("body", b""))
                        if len(body) > limit:
                            return await reject(413, "BODY_TOO_LARGE")
                        if not part.get("more_body", False):
                            break
            except TimeoutError:
                return await reject(408, "BODY_TIMEOUT")
            delivered = False
            async def bounded_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()
            return await self.app(scope, bounded_receive, send)
        return await self.app(scope, receive, send)


def create_app(settings: Settings, engine=None, clock=None,assistant_provider=None,crm_provider=None,ai_runtime=None,verification_provider=None) -> FastAPI:
    from .composition import compose_ai
    from .crm_composition import compose_crm
    runtime = ai_runtime or compose_ai(settings, engine, assistant_provider=assistant_provider, clock=clock)
    try:
        crm_runtime=crm_provider if crm_provider is not None else compose_crm(settings,engine,clock=clock)
    except BaseException:
        if ai_runtime is None:runtime.close()
        raise
    try:
        verifier=verification_provider if verification_provider is not None else TurnstileVerifier(settings.turnstile) if settings.turnstile else None
    except BaseException:
        if crm_provider is None:crm_runtime.close()
        if ai_runtime is None:runtime.close()
        raise
    @asynccontextmanager
    async def lifespan(_app):
        try:
            yield
        finally:
            try:
                if verification_provider is None and verifier is not None:verifier.close()
            finally:
                try:
                    if crm_provider is None:crm_runtime.close()
                finally:
                    if ai_runtime is None:runtime.close()
    app = FastAPI(title="Choreograph guest API", version="0.1.0", docs_url=None, redoc_url=None,
                  openapi_url=None, lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.clock = clock or (lambda: datetime.now(UTC))
    app.state.ai_runtime = runtime
    app.state.assistant = runtime.assistant
    app.state.crm=crm_runtime
    app.state.verification=verifier
    app.add_middleware(Boundary, settings=settings)

    def unit_of_work():
        if app.state.engine is None:
            raise DomainError("STORAGE_UNAVAILABLE", "Please try again in a moment.", 503)
        with Session(app.state.engine, expire_on_commit=False) as db, db.begin():
            yield db
    app.state.unit_of_work = unit_of_work

    @app.exception_handler(DomainError)
    async def domain_error(request, error):
        return JSONResponse({"code": error.code, "message": error.message}, error.status,
                            headers={"cache-control": "no-store"})

    @app.exception_handler(IntegrityError)
    async def database_conflict(request,error):
        if getattr(error.orig,'sqlstate',None)=='23P01':
            return JSONResponse({'code':'TIME_OCCUPIED','message':'That time was just reserved. Choose another time.'},409)
        return JSONResponse({'code':'WRITE_FAILED','message':'The change could not be saved. Refresh and try again.'},500)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        return JSONResponse({"code": "INPUT_INVALID", "message": "Check the highlighted details and try again."}, 422)

    @app.exception_handler(OperationalError)
    async def database_busy(request,error):
        if getattr(error.orig,'sqlstate',None) in {'40P01','40001','55P03','57014'}:
            return JSONResponse({'code':'WRITE_RETRY','message':'The demo is busy. Refresh the details and try again.'},409)
        return JSONResponse({'code':'STORAGE_UNAVAILABLE','message':'The change could not be saved. Try again shortly.'},503)

    @app.exception_handler(HTTPException)
    async def http_error(request, error):
        return JSONResponse({"code": "REQUEST_UNAVAILABLE", "message": "This request is unavailable."}, error.status_code)

    @app.exception_handler(Exception)
    async def unexpected_error(request, error):
        return JSONResponse({"code": "REQUEST_FAILED", "message": "Something went wrong. Please try again."}, 500)

    @app.get("/health", response_model=Health)
    def health():
        return Health(profile=settings.profile)

    def view(workspace, token):
        return SessionView(workspace_id=workspace.id, timezone=workspace.timezone,
                           expires_at=workspace.expires_at, generation=workspace.generation,
                           revision=workspace.revision, csrf=csrf_token(token, settings.bridge_secret), profile=settings.profile,
                           crm_provider=app.state.crm.provider,
                           crm_schema_setup_allowed=bool(getattr(getattr(app.state.crm,'config',None),'schema_setup_allowed',False)),
                           crm_mode=workspace.crm_mode, draft=workspace.draft, messages=workspace.messages,
                           quote=service.current_quote(workspace),scenario=workspace.scenario)

    def full_view(db,workspace,token):
        from . import knowledge
        knowledge.attach_samples(db,workspace)
        state=view(workspace,token)
        service.bind_booking_messages(db,workspace,state.messages)
        from .contracts import DocumentView
        state.documents=[DocumentView(**item) for item in knowledge.documents(db,workspace)]
        state.replacements_left=3-workspace.ingestion_attempts
        from . import crm
        from .contracts import CRMConnectionView
        events=list(db.scalars(select(Outbox).where(Outbox.workspace_id==workspace.id).order_by(Outbox.revision)))
        current_connection=crm.latest_connection(db,workspace)
        connection=crm.public_view(db,workspace,settings.bridge_secret,app.state.clock(),
                                   connection=current_connection,events=events,provider=app.state.crm)
        state.connection=CRMConnectionView(**connection) if connection else None
        state.crm_available=crm.available(db,app.state.crm,app.state.clock())
        rows=list(db.scalars(select(Reservation).where(Reservation.workspace_id==workspace.id).order_by(Reservation.starts_at)))
        all_bookings=[BookingView(id=row.id,enquiry_id=row.enquiry_id,staff_id=row.staff_id,starts_at=row.starts_at,
                                 ends_at=row.ends_at,state=row.state,label=row.label) for row in rows]
        cleared=set(db.scalars(select(Activity.reference).where(Activity.workspace_id==workspace.id,
                                                                Activity.kind=='calendar_cleared')))
        state.calendar=[row for row in all_bookings if row.state!='cancelled' or str(row.id) not in cleared]
        bookings={row.enquiry_id:row for row in all_bookings if row.enquiry_id}
        state.requests=[RequestView(id=row.id,revision=row.revision,status=row.status,fields=row.fields,
                                    quote=row.quote,preferred_at=row.preferred_at,booking=bookings.get(row.id))
                        for row in db.scalars(select(Enquiry).where(Enquiry.workspace_id==workspace.id).order_by(
                            Enquiry.created_at,Enquiry.quote['revision'].as_integer(),Enquiry.id))]
        state.calendar_week_start=domain.week_start(app.state.clock().astimezone(ZoneInfo(workspace.timezone)).date())
        state.calendar_first_week_start=state.calendar_week_start
        if state.calendar:
            state.calendar_first_week_start=min(state.calendar_week_start,domain.week_start(min(
                row.starts_at.astimezone(ZoneInfo(workspace.timezone)).date() for row in state.calendar)))
        state.calendar_last_week_start=domain.week_start(app.state.clock().astimezone(ZoneInfo(workspace.timezone)).date()+timedelta(days=29))
        state.summary=Summary(requests_count=len(state.requests),awaiting_count=sum(row.status=='awaiting_review' for row in state.requests),
                              confirmed_count=sum(row.status=='confirmed' for row in state.requests),
                              booked_cents=sum(row.quote.cents for row in state.requests if row.status in {'confirmed','completed'}))
        crm.apply_receipts(db,workspace,state,connection=current_connection,events=events,provider=app.state.crm)
        return state

    def cookie(response, token):
        response.set_cookie(COOKIE, token, max_age=7200, httponly=True, samesite="lax",
                            secure=settings.origin.startswith("https://"), path="/")
        response.headers['cache-control'] = 'no-store'

    def new_workspace(db, zone):
        from . import knowledge
        from .models import DocumentVersion
        if runtime.spec.provider != 'fake':
            slots = set(db.scalars(select(DocumentVersion.slot).where(DocumentVersion.owner_id.is_(None),
                DocumentVersion.embedding_profile_id == runtime.spec.profile_id, DocumentVersion.state == 'ready')))
            if not set(knowledge.SLOTS).issubset(slots):
                raise DomainError('KNOWLEDGE_NOT_READY', 'The front desk is being prepared. Please try again later.', 503)
        return create_workspace(db, zone, app.state.clock(), embedding_profile_id=runtime.spec.profile_id)

    @app.get('/v1/verification',response_model=VerificationView)
    def verification_config(response:Response):
        response.headers['cache-control']='no-store'
        return VerificationView(enabled=verifier is not None,site_key=settings.turnstile.site_key if settings.turnstile else None,
                                required=settings.profile=='live' or verifier is not None)

    @app.post('/v1/session', response_model=SessionView)
    def start_session(body: StartSession, request: Request, response: Response, db=Depends(unit_of_work, scope='function')):
        require_verification(app,request,'workspace')
        token = request.cookies.get(COOKIE)
        if token:
            try:
                workspace = find_workspace(db, token, app.state.clock(), lock=True,allow_retired=body.restart)
            except DomainError as error:
                if not body.restart or error.code!='SESSION_REQUIRED':
                    raise
                workspace,token=new_workspace(db,body.timezone)
                cookie(response,token)
                service.ensure_seeded(db,workspace,app.state.clock())
                return full_view(db,workspace,token)
            if body.restart:
                if workspace.active and workspace.expires_at>app.state.clock():
                    raise DomainError('RESET_REQUIRED','Use Reset demo to end an active workspace.')
                from .jobs import retire_workspace
                retire_workspace(db,workspace,app.state.clock())
                workspace,token=new_workspace(db,body.timezone)
                cookie(response,token)
        else:
            workspace, token = new_workspace(db, body.timezone)
            cookie(response, token)
        service.ensure_seeded(db,workspace,app.state.clock())
        return full_view(db,workspace,token)

    @app.get('/v1/session', response_model=SessionView)
    def get_session(request: Request, response: Response, db=Depends(unit_of_work, scope='function')):
        token = request.cookies.get(COOKIE)
        workspace = find_workspace(db, token, app.state.clock(),lock=True)
        service.ensure_seeded(db,workspace,app.state.clock())
        response.headers['cache-control'] = 'no-store'
        return full_view(db,workspace,token)

    @app.post('/v1/reset', response_model=SessionView)
    def reset_session(body: ResetSession, request: Request, response: Response, db=Depends(unit_of_work, scope='function')):
        require_verification(app,request,'workspace')
        token = request.cookies.get(COOKIE)
        workspace = find_workspace(db, token, app.state.clock(), lock=True, allow_retired=True)
        require_csrf(token, request.headers.get('x-csrf-token'), settings.bridge_secret)
        if not workspace.active:
            raise DomainError("SESSION_EXPIRED", "This demo has already ended.", 410)
        require_generation(workspace, body.generation)
        from .jobs import retire_workspace
        retire_workspace(db,workspace,app.state.clock())
        workspace, token = new_workspace(db, body.timezone)
        service.ensure_seeded(db,workspace,app.state.clock())
        cookie(response, token)
        return full_view(db,workspace,token)

    def authorize(request,db,body=None):
        token=request.cookies.get(COOKIE)
        workspace=find_workspace(db,token,app.state.clock(),lock=True)
        if body is not None:
            require_csrf(token,request.headers.get('x-csrf-token'),settings.bridge_secret)
            require_generation(workspace,body.generation)
        service.ensure_seeded(db,workspace,app.state.clock())
        return workspace,token
    app.state.authorize=authorize
    app.state.full_view=full_view

    @app.get('/v1/availability',response_model=WeekView)
    def get_availability(request:Request,week:date|None=None,db=Depends(unit_of_work,scope='function')):
        workspace,_=authorize(request,db)
        return service.week_view(db,workspace,app.state.clock(),week)

    @app.put('/v1/draft',response_model=MutationView)
    def edit_draft(body:DraftCommand,request:Request,db=Depends(unit_of_work,scope='function')):
        workspace,token=authorize(request,db,body)
        payload=body.model_dump(mode='json',exclude_unset=True)
        fields={key:value for key,value in payload.items() if key not in {'generation','revision'}}
        result=service.idempotent(db,workspace,request.headers.get('idempotency-key'),'draft',payload,
                                  lambda:service.update_draft(db,workspace,fields,body.revision,app.state.clock()))
        return MutationView(state=full_view(db,workspace,token),**result)

    @app.post('/v1/requests',response_model=MutationView)
    def send_request(body:SubmitCommand,request:Request,db=Depends(unit_of_work,scope='function')):
        workspace,token=authorize(request,db,body)
        result=service.idempotent(db,workspace,request.headers.get('idempotency-key'),'submit',body.model_dump(mode='json'),
                                  lambda:service.submit_request(db,workspace,body.revision,app.state.clock()))
        return MutationView(state=full_view(db,workspace,token),**result)

    @app.post('/v1/bookings',response_model=MutationView)
    def book_clean(body:SubmitCommand,request:Request,db=Depends(unit_of_work,scope='function')):
        workspace,token=authorize(request,db,body)
        result=service.idempotent(db,workspace,request.headers.get('idempotency-key'),'book',body.model_dump(mode='json'),
                                  lambda:service.book_from_chat(db,workspace,body.revision,app.state.clock()))
        return MutationView(state=full_view(db,workspace,token),**result)

    @app.post('/v1/chat',response_model=MutationView)
    def send_chat(body:ChatCommand,request:Request):
        from .interactions import chat
        return chat(app,request,body)

    @app.post('/v1/calendar/{booking_id}/clear',response_model=MutationView)
    def clear_calendar(booking_id:UUID,body:Command,request:Request,db=Depends(unit_of_work,scope='function')):
        workspace,token=authorize(request,db,body)
        payload={**body.model_dump(mode='json'),'booking_id':str(booking_id)}
        result=service.idempotent(db,workspace,request.headers.get('idempotency-key'),'calendar_clear',payload,
            lambda:service.clear_calendar_entry(db,workspace,booking_id,body.revision,app.state.clock()))
        return MutationView(state=full_view(db,workspace,token),**result)

    @app.get('/v1/requests/{request_id}/availability',response_model=WeekView)
    def request_availability(request_id:UUID,request:Request,week:date|None=None,db=Depends(unit_of_work,scope='function')):
        workspace,_=authorize(request,db)
        enquiry=service.owned_request(db,workspace,request_id)
        return service.request_week(db,workspace,enquiry,app.state.clock(),week)

    @app.post('/v1/requests/{request_id}/{action}',response_model=MutationView)
    def update_booking(request_id:UUID,action:str,body:BookingCommand,request:Request,db=Depends(unit_of_work,scope='function')):
        if action not in {'approve','reschedule','cancel','complete'}:
            raise DomainError('ACTION_UNAVAILABLE','That action is unavailable.',404)
        workspace,token=authorize(request,db,body)
        result=service.idempotent(db,workspace,request.headers.get('idempotency-key'),action,{**body.model_dump(mode='json'),'request_id':str(request_id)},
                                 lambda:service.booking_command(db,workspace,request_id,action,body,app.state.clock()))
        return MutationView(state=full_view(db,workspace,token),**result)

    from .knowledge_api import register
    register(app)
    from .crm_api import register as register_crm
    register_crm(app)
    return app
