"""Short authority transactions around bounded external assistant/document work."""
import base64
import binascii
import copy
import time
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, defer

from . import ai_admission, assistant, knowledge, service
from .assistant_context import bind_context, turn_context
from .contracts import MutationView
from .errors import DomainError
from .models import DocumentVersion, Manifest
from .verification import require_verification

OPERATION_SECONDS = 55


@dataclass(frozen=True)
class Snapshot:
    scope: ai_admission.AttemptScope
    request_hash: str
    profile: ai_admission.EmbeddingSpec
    manifest_ids: dict[str, str]
    timezone: str
    draft: dict = field(repr=False)
    local_date: str
    conversation: dict = field(repr=False,default_factory=dict)


def _deadline(deadline):
    if time.monotonic() >= deadline:
        raise DomainError('ASSISTANT_TIMEOUT', 'The operation took too long. Your request is unchanged; refresh before trying again.', 503)


def _profile(app, db, workspace):
    spec = knowledge.spec_for_workspace(db, workspace)
    current = app.state.ai_runtime.spec
    if spec.provider != current.provider or (spec.provider != 'fake' and spec.profile_id != current.profile_id):
        raise DomainError('ASSISTANT_CHANGED', 'Assistance has changed. Reset the demo before sending a new question or document.', 409)
    return spec


def _snapshot(app, db, workspace, body, request, operation, payload):
    key = request.headers.get('idempotency-key')
    fingerprint, previous = service.idempotency_status(db, workspace, key, operation, payload)
    if previous is not None:
        return None, previous
    service.require_revision(workspace, body.revision)
    profile = _profile(app, db, workspace)
    knowledge.attach_samples(db, workspace)
    manifest = {row.slot: str(row.version_id) for row in db.scalars(
        select(Manifest).where(Manifest.workspace_id == workspace.id))}
    if operation=='chat' and profile.provider!='fake' and len(manifest)!=len(knowledge.SLOTS):
        raise DomainError('KNOWLEDGE_NOT_READY','Juniper’s document library is not ready yet. Please try again shortly.',503)
    return Snapshot(ai_admission.AttemptScope(workspace.id, workspace.generation, key, workspace.revision),
                    fingerprint, profile, manifest, workspace.timezone, copy.deepcopy(workspace.draft),
                    app.state.clock().astimezone(ZoneInfo(workspace.timezone)).date().isoformat(),
                    turn_context(db,workspace) if operation=='chat' else {}), None


def _guard(app, request, body, claim, deadline):
    _deadline(deadline)
    with Session(app.state.engine) as db, db.begin():
        workspace, _ = app.state.authorize(request, db, body)
        ai_admission.check_interaction(db, claim, workspace, app.state.clock())
    _deadline(deadline)


def _failed(app, claim):
    ai_admission.finish_interaction(app.state.engine, claim, now=app.state.clock())


def chat(app, request, body):
    if app.state.engine is None:
        raise DomainError('STORAGE_UNAVAILABLE', 'Please try again in a moment.', 503)
    deadline = time.monotonic() + OPERATION_SECONDS
    payload = body.model_dump(mode='json')
    with Session(app.state.engine, expire_on_commit=False) as db, db.begin():
        workspace, token = app.state.authorize(request, db, body)
        snapshot, previous = _snapshot(app, db, workspace, body, request, 'chat', payload)
        if previous is not None:
            return MutationView(state=app.state.full_view(db, workspace, token), **previous)
        if len(workspace.messages) >= 60:
            raise DomainError('CHAT_LIMIT', 'This demo has reached its conversation limit. Start a new demo.', 429)
    require_verification(app,request,'assistant')
    claim = ai_admission.claim_interaction(app.state.engine, snapshot.scope, operation='chat',
        request_hash=snapshot.request_hash, profile_id=snapshot.profile.profile_id,
        manifest_ids=snapshot.manifest_ids, now=app.state.clock())
    try:
        scoped = app.state.ai_runtime.for_scope(snapshot.scope, clock=app.state.clock, deadline=deadline)
        provider = bind_context(scoped.assistant,snapshot.conversation)
        _guard(app, request, body, claim, deadline)
        intent = provider.interpret(body.text, snapshot.draft, snapshot.timezone, snapshot.local_date)
        _guard(app, request, body, claim, deadline)
        hits = []
        output = None
        if intent.guide_question and intent.intent != 'handoff':
            if len(snapshot.manifest_ids)!=len(knowledge.SLOTS):
                raise DomainError('KNOWLEDGE_NOT_READY','Juniper’s document library is not ready yet. Please try again shortly.',503)
            # No guest source or database connection is held while embedding.
            vector = knowledge.query_embedding(scoped.embedder, intent.guide_question)
            _guard(app, request, body, claim, deadline)
            with Session(app.state.engine) as db, db.begin():
                workspace, _ = app.state.authorize(request, db, body)
                ai_admission.check_interaction(db, claim, workspace, app.state.clock())
                hits = knowledge.retrieve(db, workspace, intent.guide_question,
                                          vector=vector, spec=snapshot.profile)
            output = provider.evidence(intent.guide_question, hits) if hits else assistant.GroundedOutput(status='insufficient',claims=[])
            _guard(app, request, body, claim, deadline)
        with Session(app.state.engine, expire_on_commit=False) as db, db.begin():
            workspace, token = app.state.authorize(request, db, body)
            ai_admission.check_interaction(db, claim, workspace, app.state.clock())
            result = service.idempotent(db, workspace, snapshot.scope.command_key, 'chat', payload,
                lambda: assistant.apply_chat(db, workspace, body.text, body.revision, app.state.clock(),
                                            intent=intent, hits=hits, output=output))
            _deadline(deadline)
            ai_admission.complete_interaction(db, claim, workspace, app.state.clock())
            return MutationView(state=app.state.full_view(db, workspace, token), **result)
    except BaseException:
        _failed(app, claim)
        raise


def replace_document(app, slot, body, request):
    if app.state.engine is None:
        raise DomainError('STORAGE_UNAVAILABLE', 'Please try again in a moment.', 503)
    deadline = time.monotonic() + OPERATION_SECONDS
    try:
        data = base64.b64decode(body.data, validate=True)
    except (ValueError, binascii.Error):
        raise DomainError('DOCUMENT_FORMAT', 'Choose a supported document.', 422) from None
    payload = {**body.model_dump(mode='json'), 'slot': slot}
    with Session(app.state.engine, expire_on_commit=False) as db, db.begin():
        workspace, token = app.state.authorize(request, db, body)
        snapshot, previous = _snapshot(app, db, workspace, body, request, 'document-replace', payload)
        if previous is not None:
            return MutationView(state=app.state.full_view(db, workspace, token), **previous)
        if slot not in knowledge.SLOTS:
            raise DomainError('DOCUMENT_SLOT', 'Choose a document to replace.', 422)
        if workspace.ingestion_attempts >= 3:
            raise DomainError('DOCUMENT_LIMIT', 'This demo has used its three document replacements.', 422)
        current = db.scalar(knowledge.authorized(db, workspace).where(DocumentVersion.slot == slot).options(
            defer(DocumentVersion.source, raiseload=True)))
        if current is None:
            raise DomainError('DOCUMENT_UNAVAILABLE', 'Prepare the sample pack first.', 503)
        title, expected = current.title, current.id
    require_verification(app,request,'documents')
    claim = ai_admission.claim_interaction(app.state.engine, snapshot.scope, operation='replace',
        request_hash=snapshot.request_hash, profile_id=snapshot.profile.profile_id,
        manifest_ids=snapshot.manifest_ids, now=app.state.clock())
    try:
        # Reserve the finite lifetime attempt independently of parse/network and
        # final business publication. Failure/reset does not replenish it.
        with Session(app.state.engine) as db, db.begin():
            workspace, _ = app.state.authorize(request, db, body)
            ai_admission.check_interaction(db, claim, workspace, app.state.clock())
            if workspace.ingestion_attempts >= 3:
                raise DomainError('DOCUMENT_LIMIT', 'This demo has used its three document replacements.', 422)
            workspace.ingestion_attempts += 1
            version = f'Guest {workspace.ingestion_attempts}'
        scoped = app.state.ai_runtime.for_scope(snapshot.scope, clock=app.state.clock, deadline=deadline)
        notice = None
        built = parsed = None
        try:
            _guard(app, request, body, claim, deadline)
            parsed = knowledge.parse_version(data, body.kind, slot, title, version, app.state.clock(),
                owner=snapshot.scope.workspace_id, generation=snapshot.scope.generation,
                spec=snapshot.profile, tokenizer=app.state.ai_runtime.tokenizer)
            _guard(app, request, body, claim, deadline)
            built = knowledge.embed_version(parsed, scoped.embedder)
            _guard(app, request, body, claim, deadline)
        except DomainError as error:
            # Parsing/provider failures are an honest failed replacement, with
            # the old ready manifest preserved and finite attempt accounted.
            notice = {'ready': False, 'code': error.code, 'message': error.message}
        with Session(app.state.engine, expire_on_commit=False) as db, db.begin():
            workspace, token = app.state.authorize(request, db, body)
            ai_admission.check_interaction(db, claim, workspace, app.state.clock())
            _deadline(deadline)
            def apply():
                if notice is None:
                    result = knowledge.publish_replacement(db, workspace, parsed, built,
                        expected_version_id=expected, expected_revision=body.revision, now=app.state.clock())
                else:
                    result = notice
                workspace.revision += 1
                return {'request_id': None, 'document_notice': result}
            result = service.idempotent(db, workspace, snapshot.scope.command_key, 'document-replace', payload, apply)
            ai_admission.complete_interaction(db, claim, workspace, app.state.clock())
            return MutationView(state=app.state.full_view(db, workspace, token), **result)
    except BaseException:
        _failed(app, claim)
        raise
