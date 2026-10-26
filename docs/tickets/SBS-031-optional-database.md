# SBS-031 â€” Optional PostgreSQL and database-free deployment

Status: **Complete local —26 October2026. Owner confirms no-database mode is working as intended; separately scoped native-account and hosted acceptance remain outstanding.**

## Owner instruction and scope

The owner replaces mandatory PostgreSQL hosting with a database-free default, while retaining the implemented PostgreSQL path for practice/testing. They first requested a thorough plan and sibling comparison, then explicitly authorized implementation: add **`DATABASE_ENABLED=true`** to the ignored backend `.env.local`, leave the current services/data working, implement the alternative, and tell them when they can set it to **false** and restart. The later owner continuation authorizes restarting with their chosen false setting after implementation, exhaustive isolated validation/fixes, a file-level commit plan and multiple ticket-prefixed local commits. Preserve the development database and account records; no cloud deployment/provisioning, real-provider agent spending or push is authorized. A one-time private local snapshot transfer must be explicit, read-only at the SQL source, and performed with owned writers stopped. Earlier instructions limiting env to two switches and mandating Cloud SQL are superseded for this continuation. Provider mode remains independent: `FAKE_MODE` / `PAID_DEMO_ENABLED` keep their values.

Portfolio wording must describe the real work: PostgreSQL/pgvector were implemented and tested, remain an optional mode, and the selected public deployment uses a different storage mode. Do not imply the public deployment uses PostgreSQL when disabled.

## Audit: what the database currently does

Inspected `models.py`, API/session/booking/domain functions, source/retrieval/replacement paths, AI/CRM admission, OAuth/account registry, jobs/publication/delivery, readiness/operator/acceptance, launch/setup and frontend guest orchestration. Static inventory found **25 tables,24 modules importing SQLAlchemy/models and24 decorated routes** across API, document, CRM and task boundaries. Health/verification are not themselves business storage; startup and ordinary guest flows currently construct/use the SQL engine. A flag around just `db.py` cannot make the app work.

| Existing model/table | Responsibility | Database-free owner |
| --- | --- | --- |
| Workspace / workspaces | Scoped session, token hash, fixed expiry, timezone, revision, messages/draft/seed/profile | Server-owned workspace object; browser keeps a sanitized UI cache |
| Catalogue / catalogue | Exact fictional service policy/rates | Existing immutable code/catalogue, server authoritative |
| Staff / staff | Eligible fictional staff | Existing immutable roster plus workspace projection |
| Enquiry / enquiries | Reviewed request, quote, status, revision, selected time | Workspace aggregate |
| Reservation / reservations | Authoritative reserved instants, cleaner, overlap exclusion | Same aggregate; server domain eligibility plus conditional atomic commit |
| Idempotency / idempotency | Key/body/operation binding and committed receipt replay | Same aggregate, preserving existing200-action bound |
| Activity / activity | History/seed/calendar-clear markers | Same aggregate, bounded |
| EmbeddingProfile / embedding_profiles | Immutable model/dimension/chunker/tokenizer identity | Hashed prepared-pack metadata |
| DocumentVersion / document_versions | Actual source bytes and ready/source metadata | Immutable canonical pack; private guest objects plus ready manifest |
| Manifest / document_manifest | Server-owned authorization/ready source selection | Workspace manifest; never caller-provided search filters |
| Chunk / knowledge_chunks | Original page/section passages and vectors | Prepared/private packs, bounded in-memory retrieval |
| Connection / crm_connections | Destination, consent, generation and encrypted OAuth tokens | Private server workspace/connection object; never browser cache |
| Installation / crm_installations | Distinct account installs/capacity/shared active uses | App/account registry with conditional updates and fenced removal |
| OAuthState / oauth_states | One-use callback/session/app/state binding | Private workspace/registry state, expiry and replay protection |
| CRMGrant / crm_http_grants | Shared grant identity/spec and reserved request count | Private code-grant ledger |
| CRMCall / crm_http_calls | Accounted per-workspace HTTP attempts | Ledger reservations, bounded private diagnostics |
| Outbox / outbox | Destination/version-bound durable sync/cleanup intent | Included atomically with the booking/lifecycle change |
| ExternalMapping / external_mappings | Verified native IDs, revision/readback | Private workspace receipt; public links only after verification |
| SimulatedRecord / simulated_crm_records | Injected fake CRM system, distinct from public skip | Explicit fake transport store, test-only isolation |
| AIGrant / ai_grants | Aggregate finite/manual policy and conservative accounting | Private grant ledger, no reset on process restart |
| AIAttempt / ai_attempts | One-use phase/batch reservations, actual/unknown usage | Ledger claims; charge before provider work and retain uncertainty |
| AIInteraction / ai_interactions | In-flight/revision/source ownership around external calls | Workspace interaction lease/fence |
| TaskPublication / task_publications | Queue create/get ambiguity, epoch/lease/backoff | Durable publication journal, correlated with workspace outbox |
| DispatcherHeartbeat / dispatcher_heartbeats | Private recovery liveness/oldest-due diagnostics | Scheduled-sweep status object; no continuously billed process |
| AcceptanceRun / acceptance_runs | Explicit bounded acceptance IDs/outcomes/replay prevention | Private acceptance ledger; modes labelled separately |

## Sibling patterns actually inspected

- Roomedy `apps/frontend/src/features/session/lifecycle.ts` and `persistence.ts`: real **sessionStorage**, strict version/expiry recovery,250ms debounced accepted-state saves, pagehide/visibility flush, generation fences and storage-denied memory fallback. It does not store a server OAuth token in browser storage.
- Retailor `features/session/context.tsx` / `controller.ts`: versioned projected sessionStorage recovery, fixed expiry, pagehide/pageshow restoration and no resumption of uncertain provider work. `features/photos/cache.ts` uses IndexedDB for bounded blobs with transactions, leases/fencing and cross-tab ownership. Copy behavior, not credentials, settings or an entire controller.
- Retailor private checkout-photo storage: real private GCS with resource-scoped identity/public-access prevention and an asynchronous lifecycle backstop. Its guide explicitly does not promise durable background checkout fulfilment. That limitation cannot silently replace this app's real HubSpot cleanup.

## Selected design and boundaries

**False means no PostgreSQL, SQLite, Firestore, Redis or other database service.** It does not mean placing server credentials or authoritative bookings in an editable browser object. Use local browser storage as a UI recovery/cache, and private Google Cloud Storage objects for durable server authority, encrypted OAuth custody and work journals. Local false mode uses an ignored, permission-restricted file object store with no Google prerequisite; hosted false mode uses GCS via the assigned service identity. Never treat Cloud Run's temporary filesystem or process memory as hosted durable storage. Tests inject temporary stores/HTTP; no real service is inferred from fake evidence.

Keep a small explicit storage boundary, immutable domain inputs and the existing public Pydantic API. Do not emulate arbitrary SQLAlchemy queries or introduce a general transaction framework. Preserve the true-mode SQLAlchemy/Alembic implementation. Share exact quote/time/eligibility/seed/source/receipt rules rather than create different fake/live booking behavior. No paid AI fallback or operator CRM fallback.

### Flag and operational cutover

- Backend-only `DATABASE_ENABLED` accepts exactly unquoted `true`/`false`. Final code default is false. The owner-local file stays explicitly **true** until this ticket passes; frontend has no duplicate switch. Three switches then exist, independently controlling persistence, fake AI and paid AI.
- Update the runtime env allowlist, Python/Node/setup loaders and ambient filtering together. False requires no database URL/password and creates/connects/migrates no SQL engine; malformed unused SQL configuration must not accidentally select SQL. True validates the existing target normally. Unknown/invalid storage configuration fails honestly; there is no silent backend fallback.
- Compose API, worker, admissions, document retrieval, readiness, operator and maintenance through the same selected backend. False startup must not launch Docker/PostgreSQL or a SQL runner. Keep current PostgreSQL volume and ignored credentials intact. Explicit schema commands require true.
- Switching invalidates old storage-mode guest cookies/cache identities. Do not import arbitrary browser snapshots, re-embed sources or automatically migrate encrypted visitor tokens. First inspect/drain old-mode pending cleanup, preserve native-install accounting and verify a fresh session. Do not run the same account concurrently across independent mode/deployment registries and then claim account-wide uninstall protection. A documented export/reconcile step is required before a real deployment registry cutover.
- Preserve all existing local config values byte-for-byte apart from the newly authorized key; never add wrapping quotes. Do not restart/flip false for the owner until specifically requested after the handoff.

### Browser storage

Use one bounded versioned Choreograph localStorage projection: accepted visible workspace data, composer draft, perspective/page and selection, with workspace/generation/expiry binding. Exclude cookies, CSRF/header values, OAuth code/state/access/refresh tokens, encryption keys, server leases, spend authority, raw uploaded sources and authoritative CRM success/consent. Validate schema/size/expiry before display; GET the server session before enabling commands or native links. Stored bytes are untrusted and never authorize a booking, price, destination or provider action.

Restore reload/OAuth navigation without resetting expiry. Handle denied/quota/corrupt storage with usable memory UI and an honest recovery limit; server booking/cleanup must continue. Use storage events/BroadcastChannel or the existing controller model to refresh other tabs; backend revisions remain the final concurrency control. Clear only this app's cache after acknowledged Reset and on expired recovery. Browser JavaScript cannot physically erase a closed browser's disk at exactly two hours; expired cached data must be discarded before use on return. Do not claim otherwise.

### Atomic bookings and receipts

Store the reservation/request transition, workspace revision, action receipt and destination-bound outbox intent in **one conditional workspace-object write**. Use generation preconditions/create-if-absent for competing updates; one reviewed revision wins, the other gets the existing stale/occupied response. The server recomputes exact cents/minutes, full-duration staff eligibility and overlap against the current aggregate before commit. A failed reschedule leaves the old booking untouched. Historical seed entries never export. An uncertain object write is reconciled using its committed idempotency key, not replayed blindly or reported as success.

Google guarantees atomic individual-object writes and strong object/list consistency; **batch/multi-object writes are not transactions**. Do not split booking and outbox into unrelated objects and call that atomic. Cross-object grant/account/asset work requires explicit intents and conservative reconciliation, not a pretend foreign-key/SQL transaction. GCS also limits writes to the same object name to about **one per second**: prototype/test pacing and contention for workspace and global ledgers before claiming latency parity. Do not put all visitors into one hot JSON object. Preserve bounded admission, body/history/receipt counts and deadlines.

### Real AI/RAG and documents

Keep six actual PDFs/FAQ, original source/page mapping, manifest authorization and yellow source highlights. Canonical parsed passages and prepared vectors are immutable hashed packs, distinct for fake64 and the current live1536 profile. Export only the existing ready **canonical fictional** live profile from PostgreSQL once under a read-only explicit operator step; do not copy guest documents/tokens or make a new embedding call. Validate original hashes/model/dimensions/chunker/tokenizer before serving. An absent incompatible live pack is unavailable, not fake success.

Object mode performs bounded actual vector/passage retrieval from the authorized prepared/private pack in memory, retaining the LlamaIndex adapter/tool vocabulary. Query embeddings and evidence still use the selected provider/admission. Guest replacement stages bytes/chunks/vectors first, then atomically switches the ready manifest; failure keeps the prior version. Enforce current2MiB/10-page/64-chunk/three-replacement limits. Source endpoints resolve through the current server-owned manifest; guessed blob/version IDs reveal nothing. Expiry retires private access immediately and deletes bytes/vectors independently of remote CRM cleanup.

Global AI/CRM ledgers reserve cost/attempts **before** external work and bind app/grant/workspace/phase/idempotency. A crash between ledger reservation and workspace commit consumes conservatively; never refund unknown provider work or reset counters on a cold start. No manually enabled real keys/mode are inherited by tests. Historical finite grants stay expired; local manual authority remains local.

### OAuth, sync, uninstall and cleanup

Keep OAuth state/session/app binding, one-use outcomes, encrypted tokens server-side, locked/conditionally persisted refresh, explicit schema/destination/sharing consent, account-bound USD verification and real readback. Account registry claims serialize distinct capacity and active uses; uninstall fences new bindings, protects other active uses, preserves partial cleanup receipts and does not free a slot after an unknown native result. A lost lease cannot safely continue an external effect merely because it once held a process mutex. Retain scoped unknown outcomes for reconciliation.

The public skip path makes no HubSpot call/outbox work. Bookings and lifecycle changes publish existing fixed-target Cloud Tasks after durable commit; missed enqueue/ambiguous acknowledgement remains in the journal. A private authenticated minute sweep scans bounded due work/expiry, continues without visitors, and updates real liveness diagnostics. Keep task payloads opaque IDs only, exact OIDC identity/audience, five delivery attempts/three-hour window and explicit cleanup/uninstall choices. Never store OAuth secrets in task bodies or the browser. Local false-mode runner uses the same handlers against local objects; no hosted in-process timer/always-running WorkerPool is required.

Reset/two-hour expiry denies access, clears chat/private sources/cache on acknowledged client handling and schedules app-owned contact/deal removal while authorized. Keep enough protected state for unresolved work; tokens disappear only after appropriate verified cleanup or retirement. Reset's old-workspace retirement/new-workspace creation is an idempotent recoverable transition, not an assumed atomic pair of blob writes. Native admin-notification disclosure and the single designed Uninstall dialog remain unchanged.

Private hosted buckets require uniform access, enforced public-access prevention, narrowly scoped identities and no browser write/signed bearer route for authority objects. Source/custody/journal object classes must have explicit retention. Disable the default seven-day soft-delete/version history for short-lived guest bytes unless separately disclosed; a generic age lifecycle is only an orphan backstop and cannot perform OAuth cleanup. Keep canonical packs and minimal receipts separate from expiring bytes. All transport failures retain fixed codes without content/credentials.

## Implementation sequence / owning files

1. **Record the flag safely:** `runtime_config.py`, `settings.py`, `db.py`, `scripts/setup.py`, `scripts/local.mjs`, env example and ignored local env. Add explicit true without changing provider values; false must never fall through to SQL during development. Finish false/default wiring with actual storage composition before declaring it usable.
2. **Storage primitives:** planned `object_store.py` / `object_storage.py` for bounded serialization, local atomic files, injected test transport and GCS conditional operations; domain aggregate schemas/leases/receipts, private path authorization and no hidden SQL. Reuse pinned HTTP/auth capabilities where appropriate; verify/pin any genuinely necessary new dependency.
3. **Server workflow:** selected storage composition in `api.py` / `server.py` / `release.py`; shared business rules from `domain.py`, `service.py`, `sessions.py`, `assistant_context.py`; parity routes/receipts for availability, quote, request, reserve, move/cancel/complete, calendar and Reset. Preserve PG mode without duplicating pricing/time policy.
4. **Sources/AI:** `knowledge.py`, `knowledge_api.py`, `composition.py`, `interactions.py`, `ai_admission.py`, `readiness.py`, source pack export/preparation and new object implementations. Keep existing SQL retrieval/admission when true.
5. **CRM/work:** `crm.py`, `crm_api.py`, `crm_composition.py`, `hubspot.py`, `crm_admission.py`, `jobs.py`, `dispatch.py`, `dispatcher.py`, `task_delivery.py`, `runner.py`, `operator.py`, acceptance handlers and object counterparts. Audit every ORM role, not just browser endpoints.
6. **Browser:** planned projection/controller helper plus `use-guest.ts` / `demo-guest.tsx`; existing shared UI/entry/booking/source/confirmation behavior stays. Pydantic remains public contract owner; regenerate narrow types only for real contract changes.
7. **Launch/deploy/CI:** mode-aware local service inventory/README, cloud plan/role/IAM examples, no SQL/VM resource in default object deployment, private bucket/Tasks/Scheduler configuration, dependency/release fingerprints, dual-mode test/build jobs and operations docs. SQL migrations remain available only for true mode. Do not delete old examples/receipts or pretend the current hosted path has been tested.
8. **Validate and handoff:** settle the matrix below, inspect permitted real UI states, report exact changed files/checks and remaining hosted gates. Leave owner `DATABASE_ENABLED=true`. Then explicitly tell them when false+restart is supported; no premature readiness claim or automatic restart.

## Required evidence before recommending false

- True-mode regression suite on isolated PostgreSQL; fake/live and CRM skip/injected/real-transport composition stay independent.
- False mode starts/serves with missing/unreachable SQL URL and traps every engine/connect/migration call. Local false requires neither Docker nor GCP; hosted false never uses ephemeral files as durability.
- Shared API transcripts for seeds/timezones/DST, exact quotes, both booking paths, concurrency/duplicate commands, failed moves, complete/cancel, perspectives/calendar, reload/OAuth return and Reset. Two processes/tabs/overlapping revisions cannot double-book one staff slot.
- Original source reader/highlights, all six fake/live prepared packs, retrieval support/absence, guest replacement atomicity and authorized byte deletion.
- Fake/injected provider transport tests with actual admissions, unknown response reservations and real-mode fail-closed behavior. No new paid request as an implementation test.
- Explicit OAuth/share/setup/skip, shared-account uninstall, queue-loss/retries/crash/lease recovery, late revision/destination/expiry, truthful links/receipts and closed-browser cleanup. No real uninstall/reset against the owner's account as a test.
- Corrupt/oversized/denied browser cache, expired cache before display, no token/CSRF persistence, cross-tab conflict and failed reset preserving live UI.
- GCS conditional failure/412/429/timeout/lost acknowledgement, permission/path/size fences, contention/backlog pacing and soft-delete/retention configuration. Mock/local evidence is distinct from later authorized real bucket/IAM/Tasks/Scheduler acceptance.
- Settled types/Ruff/contracts/appropriate suites and fresh isolated Linux builds/smoke for both modes. Benchmark storage/cold-start/retrieval memory/latency and count operations before quoting a near-zero bill.

## Current evidence / limits

Audit and sibling/source research are complete; production implementation and object-mode tests are not yet complete. Existing376 backend/160 Node checks validate the previous PostgreSQL implementation, not this future mode. Current API/runner still use PostgreSQL; the user's services/data and real-mode flags are preserved. No GCS bucket/Scheduler/VM/SQL deployment or new provider call is authorized or performed by this implementation request. Any later cloud acceptance/provisioning needs its concrete cost/resource scope.

Official references verified25 October2026: [GCS generation preconditions](https://docs.cloud.google.com/storage/docs/request-preconditions), [strong consistency and single-object atomicity](https://docs.cloud.google.com/storage/docs/consistency), [one-write-per-second object limit](https://docs.cloud.google.com/storage/quotas), [public-access prevention](https://docs.cloud.google.com/storage/docs/public-access-prevention), [soft-delete defaults](https://docs.cloud.google.com/storage/docs/soft-delete), [storage operation/free-tier pricing](https://cloud.google.com/storage/pricing). These support the design, not a tested deployed service.


## Implementation refinement and progress

The initial per-workspace-object sketch is refined to one bounded mutable encrypted shard for this low-traffic demo, giving booking/outbox, counters and account registry one real atomic boundary. This avoids pretending that GCS has multi-object transactions. Immutable canonical source bytes/passages/vectors are separate content-addressed encrypted packs cached by hash. Mutable JSON has a32 MiB uncompressed ceiling and256 retained-workspace cap. GCS's same-object write quota is a deliberate throughput limit: conditional throttled writes have bounded retries, while hosted contention and latency still require measurement. This does not claim high-throughput readiness.

Explicit repositories run the same domain commands in either mode. The object unit of work never evaluates ORM statements or opens SQL connections; PostgreSQL retains native overlap constraints/advisory locks and optimized manifest/pgvector queries. Object writes validate relationships, uniqueness and overlaps; scoped read/write sets fence competing edits and merge only disjoint changes without replaying provider calls. Short durable leases protect OAuth exchange, rotating tokens and account-wide uninstall. Explicitly pure claims/accounting may retry; external calls do not.

Local storage is `.runtime/private-state`, encrypted using the existing server token key, with process-safe file locks, fsync and atomic replacement. Container composition explicitly selects GCS and cannot fall back to volatile files. GCS startup checks enforced public-access prevention, uniform IAM and disabled versioning/soft-delete/retention before any object write. Its fixed bucket is `choreograph-512713-private-state`; no bucket or IAM has been created. Runtime identities need exact-bucket object operations and read-only bucket-policy access.

Request-bound task publication now preserves accepted bookings through queue failures. The private OIDC-authenticated `/internal/maintenance` endpoint expires guests, purges private sources and publishes pending cleanup/retries even after the browser closes. Scheduler and task delivery use different identities. Actual GCS/Scheduler/Tasks/IAM operation remains unprovisioned and unverified. No hosted WorkerPool is needed for this object path.

`python -m choreograph.storage_transfer --local-postgres-to-objects` is the explicit local cutover command. It requires owned API/runner stopped, reads a repeatable read-only SQL snapshot, writes/validates encrypted object state and verifies counts. It preserves ready vectors, expiries, guest cookies, existing reservations/cleanup identities, installation state and cumulative provider counters. It composes no provider, changes no PostgreSQL record and renews no grant. Reverse cutover needs its own reviewed transfer to prevent stale SQL outbox replay.

The owner's later instruction authorizes the false-mode restart and multiple ticket-prefixed local commits after continued repairs. Their env was observed as `DATABASE_ENABLED=false`, with real/manual AI flags preserved. A focused cohesive gate passed39 tests across both modes. The first full backend run passed452, found two failures and three fixture errors; the uninstall serialization/default-loader/SQL-fixture repairs are undergoing targeted verification. This is progress evidence, not a completed acceptance receipt. No real-provider spending, cloud operation or deployment is part of these checks.


## Approved file-level commit plan

The owner explicitly approved staging and multiple ticket-prefixed local commits after validation. The ignored env/private store and runtime logs are excluded. Every current changed/new file is allocated once below; no push or deployment is included. The generated private plan also records the baseline and exact staged path sets for verification.

### SBS-031: add encrypted conditional object persistence

- `apps/backend/choreograph/object_store.py`
- `apps/backend/choreograph/persistence.py`
- `apps/backend/tests/test_object_gcs.py`

### SBS-031: share booking source and CRM authority across stores

- `apps/backend/choreograph/acceptance.py`
- `apps/backend/choreograph/ai_admission.py`
- `apps/backend/choreograph/api.py`
- `apps/backend/choreograph/assistant.py`
- `apps/backend/choreograph/assistant_context.py`
- `apps/backend/choreograph/crm.py`
- `apps/backend/choreograph/crm_admission.py`
- `apps/backend/choreograph/hubspot.py`
- `apps/backend/choreograph/interactions.py`
- `apps/backend/choreograph/jobs.py`
- `apps/backend/choreograph/knowledge.py`
- `apps/backend/choreograph/knowledge_api.py`
- `apps/backend/choreograph/operator.py`
- `apps/backend/choreograph/service.py`
- `apps/backend/choreograph/sessions.py`

### SBS-031: select optional database mode and preserve local cutover

- `apps/backend/.env.example`
- `apps/backend/choreograph/db.py`
- `apps/backend/choreograph/readiness.py`
- `apps/backend/choreograph/runner.py`
- `apps/backend/choreograph/runtime_config.py`
- `apps/backend/choreograph/settings.py`
- `apps/backend/choreograph/storage_transfer.py`
- `scripts/local.mjs`
- `scripts/setup.py`

### SBS-031: recover sync and cleanup through authenticated requests

- `apps/backend/choreograph/dispatch.py`
- `apps/backend/choreograph/dispatcher.py`
- `apps/backend/choreograph/publication.py`
- `apps/backend/choreograph/release.py`
- `apps/backend/choreograph/task_delivery.py`

### SBS-031: validate both storage modes and provider failure paths

- `apps/backend/tests/conftest.py`
- `apps/backend/tests/test_acceptance.py`
- `apps/backend/tests/test_ai_admission.py`
- `apps/backend/tests/test_ai_config.py`
- `apps/backend/tests/test_assistant.py`
- `apps/backend/tests/test_assistant_quality.py`
- `apps/backend/tests/test_booking.py`
- `apps/backend/tests/test_crm.py`
- `apps/backend/tests/test_customer_booking.py`
- `apps/backend/tests/test_dispatch.py`
- `apps/backend/tests/test_fixture_guard.py`
- `apps/backend/tests/test_interactions.py`
- `apps/backend/tests/test_jobs.py`
- `apps/backend/tests/test_knowledge.py`
- `apps/backend/tests/test_live_assistant.py`
- `apps/backend/tests/test_live_crm.py`
- `apps/backend/tests/test_live_knowledge.py`
- `apps/backend/tests/test_local_setup.py`
- `apps/backend/tests/test_manual_ai.py`
- `apps/backend/tests/test_manual_crm.py`
- `apps/backend/tests/test_object_dispatch.py`
- `apps/backend/tests/test_object_storage.py`
- `apps/backend/tests/test_receipt_snapshot.py`
- `apps/backend/tests/test_release.py`
- `apps/backend/tests/test_requests.py`
- `apps/backend/tests/test_reservation_shortcut.py`
- `apps/backend/tests/test_security_crm.py`
- `apps/backend/tests/test_settings.py`
- `apps/backend/tests/test_storage_delivery.py`
- `apps/backend/tests/test_storage_races.py`
- `apps/backend/tests/test_storage_transfer.py`
- `apps/backend/tests/test_verification_session.py`

### SBS-031: verify Linux runtimes and prepare private object deployment

- `.github/workflows/ci.yml`
- `infra/cloud-run.example.yaml`
- `infra/cloud-run.object.example.yaml`
- `infra/object-storage.example.json`
- `infra/release-evidence.json`
- `infra/worker-pool.example.json`
- `scripts/object-linux-smoke.py`
- `scripts/release-smoke.mjs`

### SBS-031: document optional storage architecture and acceptance

- `AGENTS.md`
- `docs/CHOREOGRAPH.md`
- `docs/tickets/README.md`
- `docs/tickets/SBS-031-optional-database.md`
- `infra/README.md`

### SBS-029: record lower cost deployment research and supersession

- `docs/tickets/SBS-029-deployment-readiness.md`


## Final race-recovery refinement

The shared idempotent object mutation boundary now holds a per-workspace lease, matching the SQL caller's row lock while OAuth or CRM commands perform bounded network work. Reset/expiry use that same boundary. Token refresh and connection transitions share a connection lease/SQL row lock; tests pause exchange/rotation while Reset arrives and verify that installation tracking and the rotated cleanup token survive. Assistant interpretation/embedding remain outside authority locks, preserving edit/reset fencing during delayed AI work.

OAuth exchange has a separately committed one-use `unknown` marker before HTTP in both stores. A simulated process interruption cannot reuse the code or release uncertain installation capacity when the original OAuth timeout elapses. A narrow adoption operation merges this known committed marker into the object transaction baseline without overwriting independent accounting. The successful/denied/identified-account outcome still commits with the ordinary command receipt. Unknown attempts remain conservative and privately inspectable; no hidden automatic uninstall is introduced.

The read-only session context also releases leases on close, including contexts without an explicit transaction. File reads use the same short process lock as atomic replacement so a Windows read handle cannot deny a concurrent rename. Provider work never holds the file byte lock.

A complete509-test backend run passed before the final durable-OAuth refinement, followed by85 passing affected CRM/consent/uninstall/crash scenarios. The final consolidated run and final Linux receipt are being refreshed for that last refinement.160 Node tests, TypeScript, unchanged public contract generation and the separate-process storage smoke have passed. These checks remain fake/injected and do not claim a new paid AI/owner-account or hosted cloud acceptance run.

## Owner manual acceptance, after the local false-mode restart

- Start a fresh demo; try Continue without HubSpot, a grounded question/source page, Reserve an appointment, details/time selection, explicit booking, reschedule/cancel/complete and refresh.
- Reset with the existing designed dialog and confirm the HubSpot/no-HubSpot choice returns. Confirm the local process restart retains authoritative state while its original fixed expiry remains in force.
- Connect your own HubSpot account, verify a USD open-stage destination, allow sharing and book explicitly. Look for the app-created Demo Guest contact and `[Choreograph demo]` deal in that pipeline; this is a CRM summary, not a Google Calendar event or automatic meeting invitation. Only actually reserved/reviewed enquiries export; fictional seed appointments do not.
- Check verified native links and revised status/time, then exercise the designed uninstall confirmation in Business → Connections. Cleanup touches only app-created records; it requires still-valid access. Expiry/reset do not silently uninstall the account installation.
- No deployment is part of this continuation. GCS/Scheduler/Tasks/IAM, source-pack promotion, hosted grants, latency/contention and real hosted acceptance remain separate prerequisites.


## Completed local acceptance and cutover —26 October2026

- Final consolidated backend gate: **511 passed** in385.70s, including both stores, exact/concurrent booking, source authorization/replacement, injected real OpenAI/HubSpot adapters, finite accounting, OAuth crash/rotation/uninstall races, publication recovery and the read-only-source transfer. `.runtime/storage-final-511-backend.log` records the actual run; the test process exited0.
- **160 Node tests**, TypeScript, Ruff and public contract generation pass. Generated public contracts are unchanged. The Node/type processes exited0. One upstream Pydantic schema warning appeared in a concurrent app-factory test; it did not fail a scenario or become a visitor warning.
- Fresh non-root Linux images passed the schema roundtrip, corpus readiness, **44 HTTP requests /291 assertions**, private worker rejection and object-mode separate-process booking/RAG/sync/expiry cleanup. The checked-in release receipt matches source SHA256 **7a398342bd58094325f5e04208afae38a81ea4bfde923bedeb061df2ce56ca24**. Owned temporary containers/network were removed. This is local Linux evidence, not hosted IAM/provider acceptance.
- Actual owner-data preflight and final stopped-writer transfer passed with **zero provider calls and zero PostgreSQL writes**. It copied all populated model records, including23 AI attempts/three grants,61 CRM calls/one grant,15 document versions/three profiles/60 chunks, registry/connection/outbox state and six workspace tombstones. No active guest booking was silently reseeded or changed. Source PostgreSQL and its volume remain preserved as a stopped snapshot; the two stores are not mirrored.
- The new private object store reports `OBJECT_STORAGE_READY`, six ready live source slots and valid unchanged real/manual AI/CRM configuration. The owner's existing **`DATABASE_ENABLED=false`** is active; the other mode/secret values were preserved. It uses `.runtime/private-state`; the transfer receipt is `.runtime/storage-transfer.json`. A stale local PostgreSQL runtime is fenced from reopening without a reviewed reverse transfer.
- Verified old frontend/API/runner supervisor/descendant identities absent, released45860/45861, transferred state, then stopped only `choreograph-local-postgres-1` while preserving its volume. Replacement services are healthy and owned; no extra preview listener or sibling operation was used.
- With the actual PostgreSQL container stopped, **23 additional object-only tests passed** in58.88s. API health is live; frontend health and `/demo` return200; runner heartbeat stays fresh. These running-app probes were read-only/non-metered and made no AI/HubSpot test calls.

| Running service | Owned supervisor | Endpoint / readiness | Content-safe local log |
| --- | --- | --- | --- |
| Frontend |1828| `http://localhost:45860`; `/healthz` and `/demo`200 | `C:/Users/minat/Work/Choreograph/.runtime/frontend-08bcf8da-2497-4b16-9b88-b703adabc6cb.log` |
| API |26348| `http://127.0.0.1:45861/health`; live profile | `C:/Users/minat/Work/Choreograph/.runtime/api-3c00fe31-6eb2-467f-bd1f-c4e6430bfab4.log` |
| Local runner |27164| fresh `.runtime/runner-ready.json`; no listener | `C:/Users/minat/Work/Choreograph/.runtime/runner-19983270-0d88-4501-8170-f9a03044e054.log` |

No new live-provider acceptance spending, external-account test, cloud resource/IAM change, deployment or push occurred. Existing manual-mode background sync/cleanup remains governed by the owner's earlier consent; automated acceptance used fake/injected providers. The owner plans hands-on testing separately. The object-storage cloud examples and policy are prepared but unapplied, and single-shard throughput/latency plus actual hosted durability remain explicit deployment gates.

New-file line endings were normalized to LF before committing; Python syntax-tree equality was verified. The Linux receipt was rebuilt for the normalized byte hash above and passed again. This formatting change did not alter runtime behavior or configuration.


## Owner confirmation and current Git authorization —26 October2026

The owner explicitly requested documenting that no-database mode is working as intended, after testing the running local app and reviewing the onboarding/welcome refinements. This records the owner's confirmation of the local `DATABASE_ENABLED=false` path with PostgreSQL closed; it does not invent a list of individual manual actions or extend that confirmation to unperformed hosted/native lifecycle checks. Existing storage/regression evidence above remains the technical receipt.

The same instruction authorizes staging and committing all current work, including SBS-032. The exact two-commit file allocation is in `docs/tickets/COMMIT_PLAN.md` under the26 October2026 checkpoint. Ignored env files, private state, tokens, logs, screenshots and test fixtures remain excluded. No deployment, push, new provider spending or app restart is included.
