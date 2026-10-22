"""Persistence only. Domain decisions live outside ORM and HTTP code."""
from datetime import datetime
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSTZRANGE, ExcludeConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .ai_admission import FAKE_SPEC


class Base(DeclarativeBase):
    pass


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_hash: Mapped[str] = mapped_column(String(64), unique=True)
    timezone: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    generation: Mapped[int] = mapped_column(Integer, default=1)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    seeded: Mapped[bool] = mapped_column(Boolean, default=False)
    scenario: Mapped[dict] = mapped_column(JSONB, default=dict)
    draft: Mapped[dict] = mapped_column(JSONB, default=dict)
    messages: Mapped[list] = mapped_column(JSONB, default=list)
    ingestion_attempts: Mapped[int] = mapped_column(Integer, default=0)
    purged_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    crm_mode: Mapped[str] = mapped_column(String(24), default="skipped")
    embedding_profile_id: Mapped[str] = mapped_column(ForeignKey('embedding_profiles.id'), default=FAKE_SPEC.profile_id)
    __table_args__ = (CheckConstraint("expires_at > created_at"), CheckConstraint("generation > 0"),)


class Catalogue(Base):
    __tablename__ = "catalogue"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    version: Mapped[int] = mapped_column(Integer)
    rules: Mapped[dict] = mapped_column(JSONB)


class Staff(Base):
    __tablename__ = "staff"
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(40))


class Enquiry(Base):
    __tablename__ = "enquiries"
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(24), default="awaiting_review")
    fields: Mapped[dict] = mapped_column(JSONB)
    quote: Mapped[dict] = mapped_column(JSONB)
    preferred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (CheckConstraint("revision > 0"), CheckConstraint("status IN ('awaiting_review','confirmed','cancelled','completed')"),)


class Reservation(Base):
    __tablename__ = "reservations"
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    staff_id: Mapped[str] = mapped_column(String(20))
    enquiry_id: Mapped[UUID | None] = mapped_column(nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period: Mapped[object] = mapped_column(TSTZRANGE, Computed("tstzrange(starts_at, ends_at, '[)')", persisted=True))
    state: Mapped[str] = mapped_column(String(24), default="confirmed")
    label: Mapped[str] = mapped_column(String(60), default="Cleaning appointment")
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "staff_id"], ["staff.workspace_id", "staff.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["workspace_id", "enquiry_id"], ["enquiries.workspace_id", "enquiries.id"], ondelete="CASCADE"),
        UniqueConstraint("workspace_id", "enquiry_id"),
        CheckConstraint("ends_at > starts_at"),
        CheckConstraint("state IN ('confirmed','blocked','completed','cancelled')"),
        ExcludeConstraint(("workspace_id", "="), ("staff_id", "="), ("period", "&&"),
                          where=text("state IN ('confirmed','blocked','completed')"), name="reservation_no_overlap", using="gist"),
    )


class Idempotency(Base):
    __tablename__ = "idempotency"
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    operation: Mapped[str] = mapped_column(String(40))
    request_hash: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSONB)


class Activity(Base):
    __tablename__ = "activity"
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    kind: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reference: Mapped[str] = mapped_column(String(64))


class EmbeddingProfile(Base):
    __tablename__ = 'embedding_profiles'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(16))
    model: Mapped[str] = mapped_column(String(100))
    dimensions: Mapped[int] = mapped_column(Integer)
    chunker: Mapped[str] = mapped_column(String(100))
    tokenizer: Mapped[str] = mapped_column(String(100))
    __table_args__ = (CheckConstraint("provider IN ('fake','openai')"),
                      CheckConstraint('dimensions BETWEEN 1 AND 3072'),)


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    generation: Mapped[int] = mapped_column(Integer, default=1)
    slot: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(120))
    version: Mapped[str] = mapped_column(String(40))
    media_type: Mapped[str] = mapped_column(String(80))
    source: Mapped[bytes] = mapped_column(LargeBinary)
    sha256: Mapped[str] = mapped_column(String(64))
    embedding_model: Mapped[str] = mapped_column(String(100), default=FAKE_SPEC.model)
    chunker_version: Mapped[str] = mapped_column(String(100), default=FAKE_SPEC.chunker)
    embedding_profile_id: Mapped[str] = mapped_column(ForeignKey('embedding_profiles.id'), default=FAKE_SPEC.profile_id)
    page_count: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(24), default="ready")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (CheckConstraint("octet_length(source) <= 2097152"), CheckConstraint("page_count BETWEEN 1 AND 10"),)


class Manifest(Base):
    __tablename__ = "document_manifest"
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    slot: Mapped[str] = mapped_column(String(50), primary_key=True)
    version_id: Mapped[UUID] = mapped_column(ForeignKey("document_versions.id"))


class Chunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    version_id: Mapped[UUID] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), index=True)
    page: Mapped[int] = mapped_column(Integer)
    section: Mapped[str] = mapped_column(String(180))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector())
    __table_args__ = (CheckConstraint("page BETWEEN 1 AND 10"), CheckConstraint("length(content) <= 6000"),)


class Connection(Base):
    __tablename__ = "crm_connections"
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[str] = mapped_column(String(80))
    generation: Mapped[int] = mapped_column(Integer, default=1)
    state: Mapped[str] = mapped_column(String(24), default="ready")
    provider: Mapped[str] = mapped_column(String(24), default="fake")
    app_id: Mapped[str] = mapped_column(String(80), default='choreograph-local-simulation')
    destination: Mapped[dict] = mapped_column(JSONB, default=dict)
    destination_options: Mapped[list] = mapped_column(JSONB, default=list)
    encrypted_tokens: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    export_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Installation(Base):
    __tablename__ = "crm_installations"
    app_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    state: Mapped[str] = mapped_column(String(24))
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OAuthState(Base):
    __tablename__ = "oauth_states"
    state_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    generation: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    outcome:Mapped[str]=mapped_column(String(24),default='pending')
    provider: Mapped[str] = mapped_column(String(24), default='fake')
    app_id: Mapped[str] = mapped_column(String(80), default='choreograph-local-simulation')


class CRMGrant(Base):
    __tablename__ = 'crm_http_grants'
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    app_id: Mapped[str] = mapped_column(String(80))
    spec_hash: Mapped[str] = mapped_column(String(64))
    requests: Mapped[int] = mapped_column(BigInteger, default=0)


class CRMCall(Base):
    __tablename__ = 'crm_http_calls'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    grant_id: Mapped[str] = mapped_column(ForeignKey('crm_http_grants.id'), index=True)
    scope_key: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Outbox(Base):
    __tablename__ = "outbox"
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    enquiry_id: Mapped[UUID | None] = mapped_column(nullable=True)
    connection_id: Mapped[UUID | None] = mapped_column(nullable=True)
    account_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    connection_generation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    workspace_generation: Mapped[int] = mapped_column(Integer)
    revision: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_token: Mapped[UUID | None] = mapped_column(nullable=True)
    code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    payload:Mapped[dict]=mapped_column(JSONB,default=dict)
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "enquiry_id"], ["enquiries.workspace_id", "enquiries.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["workspace_id", "connection_id"], ["crm_connections.workspace_id", "crm_connections.id"], ondelete="CASCADE"),
        UniqueConstraint("workspace_id", "enquiry_id", "revision", "connection_id", "kind"),
        CheckConstraint("attempts BETWEEN 0 AND 5"),
    )


class ExternalMapping(Base):
    __tablename__ = "external_mappings"
    workspace_id: Mapped[UUID] = mapped_column(primary_key=True)
    connection_id: Mapped[UUID] = mapped_column(primary_key=True)
    enquiry_id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[str] = mapped_column(String(80))
    revision: Mapped[int] = mapped_column(Integer)
    contact_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    deal_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    state: Mapped[str] = mapped_column(String(24))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "connection_id"], ["crm_connections.workspace_id", "crm_connections.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["workspace_id", "enquiry_id"], ["enquiries.workspace_id", "enquiries.id"], ondelete="CASCADE"),
    )


class SimulatedRecord(Base):
    """Durable fake external system; deliberately no guest FK cascade."""
    __tablename__='simulated_crm_records'
    account_id:Mapped[str]=mapped_column(String(80),primary_key=True)
    object_type:Mapped[str]=mapped_column(String(20),primary_key=True)
    external_key:Mapped[str]=mapped_column(String(64),primary_key=True)
    id:Mapped[str]=mapped_column(String(80),default=lambda:'sim-'+uuid4().hex,unique=True)
    properties:Mapped[dict]=mapped_column(JSONB)
    archived:Mapped[bool]=mapped_column(Boolean,default=False)


class AIGrant(Base):
    __tablename__ = 'ai_grants'
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    spec_hash: Mapped[str] = mapped_column(String(64))
    spec: Mapped[dict] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    requests: Mapped[int] = mapped_column(BigInteger, default=0)
    input_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    output_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    vectors: Mapped[int] = mapped_column(BigInteger, default=0)
    cost_micros: Mapped[int] = mapped_column(BigInteger, default=0)


class AIAttempt(Base):
    __tablename__ = 'ai_attempts'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    grant_id: Mapped[str] = mapped_column(ForeignKey('ai_grants.id'))
    workspace_id: Mapped[UUID | None] = mapped_column(ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True)
    scope_key: Mapped[str] = mapped_column(String(40))
    generation: Mapped[int] = mapped_column(Integer)
    command_key: Mapped[str] = mapped_column(String(36))
    phase: Mapped[str] = mapped_column(String(24))
    batch: Mapped[int] = mapped_column(Integer)
    model: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(16), default='reserved')
    lease_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    lease_token: Mapped[UUID] = mapped_column(default=uuid4)
    input_tokens: Mapped[int] = mapped_column(BigInteger)
    output_tokens: Mapped[int] = mapped_column(BigInteger)
    vectors: Mapped[int] = mapped_column(BigInteger)
    cost_micros: Mapped[int] = mapped_column(BigInteger)
    actual_input_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    actual_output_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    __table_args__ = (UniqueConstraint('scope_key', 'generation', 'command_key', 'phase', 'batch'),)


class AIInteraction(Base):
    __tablename__ = 'ai_interactions'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey('workspaces.id', ondelete='CASCADE'), index=True)
    generation: Mapped[int] = mapped_column(Integer)
    revision: Mapped[int] = mapped_column(Integer)
    command_key: Mapped[str] = mapped_column(String(36))
    request_hash: Mapped[str] = mapped_column(String(64))
    operation: Mapped[str] = mapped_column(String(16))
    profile_id: Mapped[str] = mapped_column(String(64))
    manifest_ids: Mapped[dict] = mapped_column(JSONB)
    state: Mapped[str] = mapped_column(String(16), default='active')
    lease_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    __table_args__ = (UniqueConstraint('workspace_id', 'generation', 'command_key'),)


class TaskPublication(Base):
    __tablename__ = 'task_publications'
    workspace_id: Mapped[UUID] = mapped_column(primary_key=True)
    event_id: Mapped[UUID] = mapped_column(primary_key=True)
    target_hash: Mapped[str] = mapped_column(String(64))
    epoch: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(500))
    state: Mapped[str] = mapped_column(String(24), default='new')
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_check: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_token: Mapped[UUID | None] = mapped_column(nullable=True)
    code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    __table_args__ = (ForeignKeyConstraint(['workspace_id','event_id'],['outbox.workspace_id','outbox.id'],ondelete='CASCADE'),
        CheckConstraint('attempts BETWEEN 0 AND 120'),CheckConstraint('epoch BETWEEN 0 AND 120'))


class DispatcherHeartbeat(Base):
    __tablename__ = 'dispatcher_heartbeats'
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    instance: Mapped[UUID] = mapped_column()
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    succeeded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cycles: Mapped[int] = mapped_column(BigInteger, default=0)
    published: Mapped[int] = mapped_column(BigInteger, default=0)
    code: Mapped[str | None] = mapped_column(String(40), nullable=True)


class AcceptanceRun(Base):
    __tablename__ = 'acceptance_runs'
    id: Mapped[UUID] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(16))
    config_hash: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16), default='running')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    counts: Mapped[dict] = mapped_column(JSONB, default=dict)
    workspace_ids: Mapped[list] = mapped_column(JSONB, default=list)
