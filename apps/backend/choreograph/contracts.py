from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True,
                             json_schema_serialization_defaults_required=True)


class Health(Contract):
    status: Literal["ok"] = "ok"
    profile: Literal["fake", "live"] = "fake"


class Problem(Contract):
    code: str
    message: str


class StartSession(Contract):
    timezone: str = Field(min_length=1, max_length=80)
    restart: bool = False


class ResetSession(StartSession):
    generation: int = Field(ge=1)


ServiceName = Literal['regular','deep','move-out']


class DraftView(Contract):
    service: ServiceName | None = None
    bedrooms: int | None = Field(default=None,ge=1,le=3)
    oven: bool = False
    preferred_at: datetime | None = None


class QuoteItem(Contract):
    name: str
    cents: int
    minutes: int


class QuoteView(Contract):
    currency: Literal['USD']
    cents: int
    minutes: int
    revision: int
    items: list[QuoteItem]


class Scenario(Contract):
    busy_date: date | None = None
    alternative_date: date | None = None
    week_start: date | None = None
    requested_date: date | None = None
    requested_time: str | None = None


class BookingView(Contract):
    id: UUID
    enquiry_id: UUID | None
    staff_id: str
    starts_at: datetime
    ends_at: datetime
    state: Literal['blocked','confirmed','completed','cancelled']
    label: str


class RequestView(Contract):
    id: UUID
    revision: int
    status: Literal['awaiting_review','confirmed','cancelled','completed']
    fields: DraftView
    quote: QuoteView
    preferred_at: datetime
    booking: BookingView | None = None
    crm_state: str = 'not_connected'
    crm_links:dict[str,str]=Field(default_factory=dict)
    crm_receipt:dict[str,str]|None=None


class Summary(Contract):
    requests_count: int = 0
    awaiting_count: int = 0
    confirmed_count: int = 0
    booked_cents: int = 0


class DocumentView(Contract):
    id: UUID
    slot: str
    title: str
    version: str
    pages: int
    media_type: str
    private: bool


class PassageView(Contract):
    id: UUID
    page: int
    section: str
    content: str


class DocumentDetail(Contract):
    document: DocumentView
    passages: list[PassageView]


class SourceClaim(Contract):
    version_id: UUID
    passage_id: UUID
    title: str
    version: str
    page: int
    section: str
    media_type: str
    excerpt: str


class Suggestion(Contract):
    label: str
    text: str


class ChatMessage(Contract):
    id: UUID
    role: Literal['user','assistant']
    text: str
    claims: list[SourceClaim] = Field(default_factory=list)
    cards: list[Literal['services','clarify','quote','week','review']] = Field(default_factory=list)
    suggestions: list[Suggestion] = Field(default_factory=list)
    requested_date: date | None = None
    revision: int


class CRMStage(Contract):
    id: str
    label: str


class CRMDestination(CRMStage):
    stages: list[CRMStage]


class CRMConnectionView(Contract):
    id: UUID
    label: str
    provider: Literal['fake','hubspot']
    state: str
    consented: bool
    can_uninstall: bool
    contact_name: str
    contact_email: str
    cleanup_state: str = 'not_requested'
    uninstall_state: str = 'not_requested'
    destinations: list[CRMDestination] = Field(default_factory=list)
    destination_label: str | None = None


class OAuthChallenge(Contract):
    state: str
    authorize_url: str | None
    simulated: bool


class SessionView(Contract):
    workspace_id: UUID
    timezone: str
    expires_at: datetime
    generation: int
    revision: int
    csrf: str
    profile: Literal["fake", "live"] = "fake"
    crm_provider: Literal['fake', 'hubspot', 'disabled'] = 'fake'
    crm_mode: str
    draft: DraftView
    messages: list[ChatMessage]
    quote: QuoteView | None = None
    scenario: Scenario = Field(default_factory=Scenario)
    requests: list[RequestView] = Field(default_factory=list)
    calendar: list[BookingView] = Field(default_factory=list)
    calendar_week_start: date | None = None
    calendar_last_week_start: date | None = None
    summary: Summary = Field(default_factory=Summary)
    documents: list[DocumentView] = Field(default_factory=list)
    replacements_left: int = 3
    connection: CRMConnectionView | None = None
    crm_available: bool = True
    crm_schema_setup_allowed: bool = False


class Command(Contract):
    generation: int = Field(ge=1,strict=True)
    revision: int = Field(ge=1,strict=True)


class DraftCommand(Command):
    service: ServiceName | None = None
    bedrooms: int | None = Field(default=None,ge=1,le=3,strict=True)
    oven: bool = False
    preferred_at: datetime | None = None


class SubmitCommand(Command):
    accept_quote: Literal[True]


class ChatCommand(Command):
    text: str = Field(min_length=1,max_length=1200)


class OAuthCallback(Command):
    state: str = Field(min_length=32,max_length=100)
    code: str = Field(default='',max_length=600)
    denied: bool = False


class CRMConsent(Command):
    connection_id: UUID
    confirm: Literal[True]


class CRMFinish(CRMConsent):
    cleanup: bool = False
    uninstall: bool = False


class CRMSetup(CRMConsent):
    pipeline_id: str = Field(min_length=1,max_length=100,pattern=r'^[A-Za-z0-9_-]+$')
    stage_id: str = Field(min_length=1,max_length=100,pattern=r'^[A-Za-z0-9_-]+$')
    allow_schema: bool = False


class ReplaceDocument(Command):
    kind: Literal['pdf','text']
    data: str = Field(min_length=1,max_length=2_796_204)


class ReplacementNotice(Contract):
    ready: bool
    code: str
    message: str


class BookingCommand(Command):
    request_revision: int = Field(ge=1,strict=True)
    confirm: Literal[True]
    staff_id: Literal['ada','noah'] | None = None
    preferred_at: datetime | None = None


class ActionReceipt(Contract):
    action: Literal['confirmed','rescheduled','cancelled','completed']
    status: Literal['accepted']
    booking_id: UUID | None
    enquiry_revision: int
    crm_state: str


class SlotView(Contract):
    start: datetime
    end: datetime
    staff_ids: list[str]


class OccupiedView(Contract):
    start: datetime
    end: datetime
    staff_id: str


class DayView(Contract):
    date: date
    weekday: str
    status: Literal['past','outside','closed','available','busy']
    slots: list[SlotView]
    occupied: list[OccupiedView]


class WeekView(Contract):
    week_start: date
    timezone: str
    minutes: int
    days: list[DayView]
    can_previous: bool
    can_next: bool


class MutationView(Contract):
    state: SessionView
    request_id: UUID | None
    applied_revision: int
    replayed: bool
    receipt: ActionReceipt | None = None
    document_notice: ReplacementNotice | None = None
    oauth: OAuthChallenge | None = None
    crm_notice: str | None = None
