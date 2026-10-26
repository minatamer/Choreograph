# SBS-012 — Complete live-capable AI and versioned retrieval

> **Deployment supersession,26 October2026:** the selected deployment is **no database** (`DATABASE_ENABLED=false`), using private GCS objects, Cloud Tasks and authenticated minute Scheduler maintenance. SQL/pgvector/migration/WorkerPool requirements in this dated packet are historical or optional true-mode evidence. They do not authorize or require database provisioning. See [the current setup inventory](../../infra/README.md#verified-cloud-inventory-and-remaining-setup-26-october2026).

Status: **Complete local**  
Owning phase: **07-build continuation**  
Depends on: existing SBS-005/005A and security baseline  
Owner authorization: 22 October 2026, “keep going … you have my approval” and “do all coding needed like all possible coding needed”.

## Outcome

Wire real Responses and embedding adapters through the same guest application, without making a paid call during implementation. A live configuration must be explicit, finite and paid-off by default. Preserve fake development, current data, actual source authorization and exact booking authority. Missing credentials are not a reason to leave the source path unimplemented.

## Confirmed gaps and scope

- Settings rejects every nonfake profile; API/server/release never compose real assistance. Ingestion and retrieval instantiate FakeEmbedding internally. Vector(64), sample(slot,sha) uniqueness and in-place preparation cannot safely coexist with real embedding spaces.
- The application holds the workspace row lock during provider work. Business rollback erases ordinary idempotency while provider spend survives. Real activation therefore needs durable, content-free admission/attempt receipts and short preparation/application transactions.
- Add immutable embedding identity (provider/model/dimensions/chunker/tokenizer), pin guest/document scope, and support validated dimensions in the existing PostgreSQL vector table. Migrate/backfill existing fake data safely; never rewrite a ready pack into another profile or silently retarget an existing workspace.
- Implement bounded real embeddings through explicit per-request LlamaIndex adapters. Parse/tokenize/chunk all input before any call; enforce batch/vector/input/dimension/finite-float bounds and a separate bounded embedding response allowance. Semantic retrieval must not require lexical overlap. Preserve manifest/ready/owner authorization before search and exact passage validation afterward.
- Persist a finite configured grant and per-workspace/global request, token and conservative currency reservations before external work. Require explicit model/rates/allowance/expiry; select no live model, dimension or price default. Key attempts by workspace/generation/command/phase/batch. Failures and uncertain outcomes keep reservations; replay/restart must not repeat ambiguous paid work. Bound concurrent active attempts with durable leases, without keeping database connections around network waits.
- Refactor chat and replacement into authenticated snapshot → admitted external work → short locked domain application. Revalidate generation, revision, actual expiry, embedding profile and manifest identities before publishing. Reset/expiry/edits must remain reachable while work waits; stale responses cannot publish. Keep one domain application path for fake and live results, explicit Send/approval, strict schemas, no model-authorized actions or fake fallback.
- Wire explicit local/server/container composition and shutdown cleanup. Guest creation/source reading never embeds the sample pack; preparation is a separate finite command. Public mode labels must reflect the configured assistant without conflating CRM choice.

## File allocation

- AI/RAG owner: `providers.py`, `knowledge.py`, new `ai_admission.py`, `models.py`, migration `0007`, focused transport/profile/budget tests. Publish small explicit interfaces before integration: immutable EmbeddingSpec, finite grant configuration and reserve/start/finish attempt receipts; parse/embed/publish knowledge stages.
- Integration owner: `settings.py`, a narrow composition/configuration module, `sessions.py`, `assistant.py`, `api.py`, `knowledge_api.py`, `contracts.py`, generated types, `server.py`/`release.py`/`runner.py` as needed, minimal accurate mode labels and integration regressions. Coordinate interfaces; no simultaneous writes to shared owners.
- Integration suballocation: configuration owner handles `settings.py`, new `composition.py` (and explicit narrow config module if needed), `server.py`/`release.py`/`runner.py` and config/composition regressions; root handles `sessions.py`, `assistant.py`, `api.py`, `knowledge_api.py`, contracts/generated types, mode label and two-phase integration regressions. AI owner publishes EmbeddingSpec/GrantSpec/admission APIs first. No other provider, task or migration ownership overlaps.
- Assistant suballocation: pure assistant domain owner refactors `assistant.py` and focused direct-domain regressions into explicit resolved intent/hits/output followed by one shared application function; root owns API/network orchestration and does not edit that file concurrently.
- Root may extract the existing idempotency preflight in `service.py` for reuse before external work and add `interactions.py` as narrow chat/document orchestration. The domain action and final idempotent write remain shared with ordinary commands; no second booking implementation.
- Existing approved UI/copy/layout remains; no new vector service, agent framework, ORM or broad refactor. Git allocations are review plans only, not staging/commit authorization.
- Root integration also owns the BFF's bounded operation timeout, `use-guest.ts` cancellation/retry handling, reachable Reset, and Docker tokenizer asset inclusion. The configuration owner prepares explicitly downloaded, hash-verified public BPE assets and their offline loader; runtime never downloads a tokenizer.

## Acceptance and checks

- [x] Real-capable composition exists; incomplete/expired/paid-off configuration fails before network and tests never inherit live credentials.
- [x] Actual isolated PostgreSQL proves fake/live profile coexistence, dimensional validation, scoped retrieval, immutable preparation and preservation of existing fake data.
- [x] Injected real-SDK HTTP success/error/compressed/oversized/invalid vector and output cases have bounded work, safe diagnostics and no automatic retry/fallback.
- [x] Concurrent final-grant admission has one winner; rollback/restart/replay cannot erase spending or repeat ambiguous requests.
- [x] Delayed interpretation/embedding/evidence plus actual reset/expiry/edit/replacement rejects stale publication, preserves old reservations/ready source and retains usage accounting.
- [x] Original 18-case evaluation, quotes/calendar/booking/CRM skip and responsive source reader continue working. No paid model quality result is claimed.
- [x] Focused checks, settled required suite/contracts/type/build, read-only validation and independently confirmed fixes pass; changed source invalidates previous release proof.

## References and limits

Blueprint sections 9, 10.1, 13–14 and17; [existing external plan](SBS-011-external-acceptance.md). Primary API references: [embeddings](https://developers.openai.com/api/reference/resources/embeddings/methods/create), [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses). Verify actual selected model support/pricing before separately authorized funded activation. No account/key entry, paid call, cloud/deployment, metadata export, outreach or Git permission is added. Preserve hidden local services, ports45860/45861/45862 and all siblings.

## Evidence

Implemented explicit paid-off composition, hash-verified offline tokenizers, immutable embedding profiles/migration0007, durable grants/attempts and two-phase chat/replacement authority. New runtime mode labels distinguish AI from CRM. No live credentials or network provider calls were used.

Read-only validation V1 found four concrete issues: legacy fake replacements could target an incompatible profile; reported usage beyond reservations was discarded; raw tokenizer special-token literals could fail as control syntax; and a multi-batch replacement could continue issuing calls after the operation deadline. Independent checks confirmed each. The settled remedies preserve legacy bytes and request a fresh demo for replacement, block an overrun grant while retaining observed usage, encode special-looking strings as ordinary text, and carry one absolute deadline through all admitted batches. API/reset/draft/expiry guards retain one domain application path.

Actual focused evidence: 39 admission/embedding/profile/migration/knowledge/transport checks passed on isolated PostgreSQL; six orchestration regressions passed, including all three delayed phases and replacement; original 18-case grounded retrieval evaluation remains in the passing suite. Generated contracts, TypeScript and a Windows production frontend build passed. The frontend was restored on45860 after its build. An initial complete suite passed157 with only two stale schema-head assertions failing; the migration owner corrected these to inspect the real Alembic head. The final settled full-suite and read-only revalidation are pending below. Source changes invalidate the prior Linux release receipt; SBS-015 owns fresh final images/smoke.

External acceptance remains genuine model compatibility/pricing/funded grant approval, one explicit sample preparation, semantic answer quality and hosted behavior. None is inferred from injected vectors/SDK replies.


Final settled gate: **167 backend tests passed in47.12s** on isolated PostgreSQL, plus **11 Node checks**, generated contracts, TypeScript, whole-repository Ruff and a successful Windows production build. A final independently reviewed direct-constructor hardening change pins both SDK utility branches to the official endpoint and clears ambient SDK configuration; its **10 focused checks passed in6.34s**. No actionable local finding remains in SBS-012 scope after revalidation. This is implemented/local evidence; paid model quality, hosted behavior, affected integrated browser review and source-fresh Linux release remain the named later acceptance gates. Nothing was staged or committed.
