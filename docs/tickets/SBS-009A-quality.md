# SBS-009A — Review quality and bounded performance

> **Deployment supersession,26 October2026:** the selected deployment is **no database** (`DATABASE_ENABLED=false`), using private GCS objects, Cloud Tasks and authenticated minute Scheduler maintenance. SQL/pgvector/migration/WorkerPool requirements in this dated packet are historical or optional true-mode evidence. They do not authorize or require database provisioning. See [the current setup inventory](../../infra/README.md#verified-cloud-inventory-and-remaining-setup-26-october2026).

## Continuation phase08 — SBS-012–015

### Continuation10a quality plan — recorded before edits

**Execution/disposition:** completed the four items below. The confirmed receipt-ordering issue is fixed by `complete_ai_run`: reported usage, finished time and success commit atomically after private cleanup; a reporting failure rolls back success and records `ACCEPTANCE_RECEIPT_FAILED`. The focused failure injection and full24-case sequence pass. Runtime ownership, pure domain/generated schema boundaries and separate dispatcher/publisher/worker responsibilities are intentional and retained; no dead public behavior or warranted broad refactor was established. Content-free errors and existing private diagnostics remain. Settled validation:227 backend tests,15 Node checks,14 focused ownership/receipt/release checks, configured Ruff and pip compatibility pass. Public contract hashes stay `c36c20b5…ccdc0` / `d71b783c…86be1`; UI source is unchanged, so the fresh types/Windows build and actual responsive review remain applicable. Read-only settled re-review found no remaining actionable quality defect. Final Linux receipt must be refreshed for the private operator-code change at phase12. No Git/provider/cloud operation occurred.

1. Review composition/ownership and boundaries: one AI runtime, borrowed versus owned clients, immutable scoped admission, explicit local/container settings and mixed AI/CRM modes. Retain pure domain commands, generated contracts and narrowly separate dispatcher/publisher/worker responsibilities; remove code only if unused behavior is independently established. No speculative refactor.
2. Review acceptance receipt/cleanup lifecycle. Confirmed issue: `execute_ai` marks success before the final reported-usage transaction. A DB error in that final step can leave a succeeded receipt while the command fails. Extract a narrow finalizer that locks the running run, aggregates only its grant/workspaces/operator key, stores reported usage and success/finished time atomically after private cleanup. On failure, keep a fixed failed receipt; never refund allowance, repeat work or turn the failure into fake success. Test transaction failure and once-only replay, plus the full injected24-case sequence.
3. Inspect readiness/cloud CLI for no implicit provider construction, content-free errors, explicit input ownership, finite requests and safe output paths. Keep duplicate fixed diagnostic boundaries where their operation/ownership differs; no general framework is warranted. Preserve secret repr protection, source bytes and private logs.
4. Validate focused affected tests, configured Ruff and unchanged contracts/types; run settled backend/Node gates and source-fresh Linux smoke at final handoff. Preserve all UI behavior and motion; the prior actual responsive review remains valid for a private operator-receipt fix. No new paid/account/cloud/Git action. Read-only re-review after fixes must find no actionable local defect before the security audit begins.

Source `07b2ced2a3dfba7359640874d2cb4c9e0cb8db1d0db5eb45357fb4e434551f03`, Python3.11.9/Windows, actual isolated PostgreSQL17/vector0.8.5, eight samples per concurrency1/4/8. The initial measurement overlapped image builds; the settled repeat ran afterward. Safe raw results are `.runtime/performance-sbs015-settled.json`. No paid/network/hosted capacity result is implied.

| Operation | p50/p95 ms at1 ·4 ·8 | SQL per attempt |
|---|---|---|
| Scoped retrieval plus explicit source reads |14.9/16.0 ·24.5/44.5 ·44.5/57.6|6|
| Independent booking approval |36.8/40.8 ·112.0/144.3 ·140.9/158.4|19|
| Targeted worker claim/delivery |131.2/232.3 ·179.7/214.4 ·125.4/217.7|64 at1/4;33 averaged including four admission deferrals at8|

Session reads remain flat at9 SELECTs for1 versus10 enquiries, with p95≈24–25ms. All24 approval attempts confirmed with zero overlaps;25 events including the duplicate probe verified once, duplicate claim admission was exactly one, and skipped CRM outbox count was zero. Retrieval's three blob selects per attempt belong to intentional explicit source authorization; the candidate ranking still defers source bytes. No speculative cache/batch fix is justified. Live AI network work remains outside authority transactions; grants/interaction leases are durable, bounded and fenced. CRM uninstall deliberately retains registry serialization around its bounded remote action. Dispatcher uses a two-connection pool, one leader, at most three publication actions per cycle, separate publication/domain attempt caps and a three-hour domain horizon. Existing isolated-PG race/deadline/stale-result tests pass; actual provider latency, cloud contention and unattended hosting require later acceptance.

Status: **Complete local**
Owning phase: **10a-quality**  
Depends on: **SBS-008**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

Document a functionality-preserving quality plan from actual code before editing. Fix demonstrated unnecessary work/duplication/boundary or lifecycle defects; do not build a platform or refactor to an arbitrary line count.

## Implementation scope

1. Trace current module/command/state ownership, reachability, duplicate calculations, dead code, query/pool/queue bounds and cleanup. Preserve private content-free diagnostics, guest/revision fences, exact domain authority and designed motion.

2. Measure bounded local concurrent booking/retrieval/worker paths with deterministic fake providers and actual PostgreSQL. Prioritize a scoped earlier-ticket follow-up if it owns a confirmed bug; do not claim paid/production capacity.

3. Execute only justified plan items with meaningful regressions, then perform read-only validation and independently disposition findings until no actionable local issue remains. No animation-off/render-off setting, extra service or broad cosmetic churn.

## File allocation and cohesive commit plan

Confirmed source/test owners plus a concise quality/performance plan and actual evidence in the main blueprint/ticket. File allocation is refined from actual findings before edits.

## Acceptance criteria

- [x] Concrete plan precedes fixes
- [x] measurements support changes
- [x] accepted functionality remains
- [x] settled relevant gates/read-only review pass
- [x] live/hosted scale is unclaimed.

## Meaningful verification

Targeted local measurements, relevant regressions/boundary checks and settled build gates. Repeat only when changed scope or failures justify it.

## Precision references

- [Blueprint: 17-verification-that-matters](../CHOREOGRAPH.md#17-verification-that-matters)
- [Blueprint: 20-deliberately-deferred](../CHOREOGRAPH.md#20-deliberately-deferred)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Completed locally, 22 October 2026. The plan below preceded edits. Isolated fixture guards reject unsafe drivers/authority/query routing before constructing an admin engine; 11 non-connecting regressions pass, and default short tracebacks reduce test diagnostic exposure. The configured repository Python lint gate passes, including inspected import hygiene, named small idioms, explicit closure bindings and local explanations for intentional sanitized boundaries. Existing compact layout remains. The deprecated PDF action fixture now uses supported APIs and a readable benign control before adding the rejected action.

Receipt snapshots now share one current connection/event snapshot and one scoped mapping query, preserving all destination/generation/revision/account checks. Actual SELECT counts are flat from one to ten enquiries: skipped **9→9**, connected **11→11**; an actual fake-delivered receipt and nine unreserved proposals retain correct states. New plus existing CRM/jobs tests **19 passed**, and independent read-only review found no actionable issue. Settled full gates: **85 backend tests passed** on isolated PostgreSQL/pgvector, **8 lifecycle/bridge/identity tests passed** (including hidden Windows supervision), configured Ruff across backend/scripts passed, generated API contract hashes stayed current, and the Windows frontend production build/type checks passed. Frontend was restored; API/runner/development volume/siblings were preserved. No deprecation warning remains. No paid/live/hosted or capacity claim, no Git writes. Linux receipt refresh follows security disposition at handoff. Next: SBS-009B read-only security audit.

Historical preliminary inventory from SBS-008: the first broad Ruff run reported 91 findings, dominated by 35 import-order and 18 unused-import reports. The scoped SBS-008 owners were subsequently cleaned. Nine Depends-default reports were normal FastAPI injection; broad catches were deliberate parser/provider/worker/runner boundaries. No dangerous runtime defect was established by that lint inventory.

Historical plan (completed as recorded above; pending language below describes its original checkpoint):

Proposed bounded plan before edits: configure only the known fastapi.Depends immutable-call exception; explain deliberate sanitizing/recovery catches; remove unused imports/bindings; rename the knowledge loop variable shadowing sqlalchemy.text; explicitly state subprocess check=False because exit status is inspected; bind the retry test's injected clock; apply safe import/idiom fixes without a formatting rewrite. Update the deprecated PDF malicious-fixture construction if supported by the installed version. Measure isolated PostgreSQL booking/retrieval/worker query counts and latency before proposing query/batch changes. Preserve domain authority, finite work and designed motion. Final quality-phase prompt, refined measurements, execution and validation remain pending.

## Phase 08 performance investigation

This investigation precedes phase 10a execution. Use eight bounded samples at concurrency 1/4/8 against a unique local PostgreSQL test database, fake providers and the same domain commands. Separate fixture preparation from warm retrieval, independent guest approvals and targeted worker delivery; report worker admission honestly against its four-job global cap. Record SQL statement counts and monotonic latency without a capacity threshold. No provider latency, hosted capacity or device timing is inferred.

Confirmed initial source cost: six shared documents contain 15,863 source bytes; the existing 23-row retrieval candidate join selects 62,631 source-column bytes even though ranking uses metadata/text only. Metadata documents also select full source blobs. Plan a narrow SBS-005A follow-up: query-local source deferral for metadata/retrieval, identity-only sample attachment, and regressions proving actual authorized source bytes and replacement/manifest isolation still work. Leave the explicit source endpoint and ingestion authorization unchanged; add no cross-guest cache.

Frontend baseline: initial→125%→150%→page2→page1→narrow→phone caused source/worker request counts 1→2→3→4→5→6→7. Short laptop width did not change the reader width and caused no extra load. Detail had one completed request and one development StrictMode cancellation, with no later refetch. Actual two-page canvas pixels/page identity, excerpts, close/focus and explicit CRM skip passed without page errors. Three browser-injected pending-status clones plus restored real skipped state caused availability requests 2→3→4→5→6, with identical revisions; the first two include the development StrictMode setup. No real CRM pending outcome was claimed. Plan a narrow SBS-005A reader follow-up: load one authorized document per mounted identity; cancel renders on page/width/zoom changes; destroy it on close/version change; clear retired-version selections after replacement and remount Business Documents on workspace change. Preserve focus, actual page identity, excerpt fallback and lazy PDF.js loading. Use stable duration plus existing workspace/revision/request/week fences for availability. Preserve polling bounds and motion. Settled post-fix counts remain pending.

Actual pre-fix host/ASGI measurements (Python 3.11.9, real local PostgreSQL/pgvector, eight samples per group; migration/corpus/fixture preparation excluded):

| Operation | Concurrency | p50 / p95 ms | SQL per attempt |
| --- | --- | --- | --- |
| Scoped retrieval plus explicit source authorization | 1 / 4 / 8 | 13.8/15.1 · 22.8/44.2 · 48.1/56.9 | 5 |
| Independent guest approval | 1 / 4 / 8 | 39.0/42.6 · 74.8/84.4 · 136.9/161.4 | 21 |
| Session with 1 / 10 enquiries | 1 | 26.7/31.3 · 33.4/35.4 | 11 / 20 |
| Targeted fake worker delivery | 1 / 4 | 113.4/133.6 · 300.8/386.6 | 57 |

Eight-way workers admitted four and deferred four under the intentional global cap; untimed draining completed them, so mixed admitted/deferred timings are not throughput evidence. All 24 retrievals were supported, 24 approvals produced no overlaps, skipped CRM produced zero outbox rows, and 25 worker events were verified once. Eight simultaneous claims for one event admitted exactly one. The test database was removed. Each session snapshot performed one unnecessary source-blob SELECT; retrieval counts also include legitimate explicit source reads and must not all be labelled waste. Session SQL 11→20 for one→ten enquiries demonstrates bounded historical-CRM per-request lookups; consider a scoped batching plan in phase 10a after preserving revision/destination fences. The source fingerprint stayed `71f238c74a0203ea87614b526dc50ae19cd09ae8142faf14395dd2ac2eee7beb`; harness hash was `8f1fe3c4c49d33749dd187d7a974d4e73d58b1f4220348c9e6ac8d417ed71b03`. These small host fixtures establish neither a latency SLO nor production capacity.

Read-only quality inventory also confirmed that the test fixture's pre-admin-connection guard permits libpq query routing overrides despite checking URL authority. Settings now rejects them, but phase 10a must reject nonempty source queries and wrong drivers before constructing the fixture admin engine. Add non-connecting rejection regressions. No fixture/application edit has been made for this follow-up yet.

Refined phase 10a plan from 51 Python files: the explicit `E4,E7,E9,F,I,UP,B,BLE,SIM` inventory, excluding compact-line style E701/E702, reports 91 findings before the current projection follow-up (45 import order, 13 unused imports, nine normal Depends defaults, seven measurement closures, five deliberate broad boundaries, four context-manager simplifications, two path-bootstrap imports and six individual idioms/shadowed/unused bindings). Keep the existing compact source style; do not rewrite 445 line-layout reports. Configure this explicit gate in backend pyproject, with only `fastapi.Depends` as the immutable-call exception. Review safe import changes; explain intentional parser/provider/worker/runner/measurement catches and standalone bootstrap imports locally; bind measured-operation closures explicitly without claiming a demonstrated race. Fix the small named idioms and malicious-PDF fixture deprecation, then add the same config-driven gate to CI.

Confirmed batching plan before phase 10a edits: `api.full_view` resolves its current connection once and passes that plus the already loaded workspace event list explicitly into CRM view helpers. `public_view` selects its current-connection cleanup outcome from that same list; `apply_receipts` indexes exact connection/workspace generations and enquiry/revision, retains all historical export IDs for disconnected status, and loads mappings once for displayed requests/current destination. Preserve verified/account/revision and native-link checks, `needs_attention`, fake receipts, consent and skip. Remove the dead initial sync/status calculation only because every request is overwritten before return. No cache, new service or schema change. Test warmed skipped and genuinely fake-delivered connected session snapshots with one versus ten enquiries: query counts remain constant and real receipts/statuses remain correct. Keep existing revision/auth-loss/cleanup tests; add only missing stale generation/account cases. Owning files: api.py, crm.py and a dedicated receipt-snapshot test; no unrelated refactor.

A focused test was accidentally attempted inside the network-restricted sandbox and failed before database creation; pytest's long driver-frame traceback included local connection arguments. Do not reproduce those values in evidence. Use short tracebacks for subsequent database checks and configure a safe default before later quality gates: SQLAlchemy parameter hiding alone does not redact pytest driver-frame locals. No provider credential, source contents or connection string belongs in the report. Test-output hardening is part of the phase 10a fixture boundary work.

Post-fix evidence: knowledge suite **4 passed**, strengthened identity-map regression **1 passed**. The same bounded backend harness passed all invariants at source `0115e9499c89c2534e4f9966d38bf65b30a556c257c2a5f927ea156083f91294`; sanitized output is ignored `.runtime/performance-backend-after.json`. Per eight attempts, retrieval source-column SELECTs fell **32→24** (the remaining 24 are deliberate explicit source authorization reads), approval metadata **8→0**, and both session metadata groups **8→0**. SQL counts remain 5/21/11-or-20/57 as previously measured. Host timings rose throughout setup and operations, so the demonstrated improvement is resource removal, not latency: serial p50/p95 ms retrieval 42.8/56.1, approval 60.5/66.8, session one request 56.9/68.7, ten requests 65.9/72.1, worker 294.5/385.3. No thresholds or retries were used.

Post-fix browser output `.runtime/performance-browser-after.json` passed: source/worker loads stay **1** across zoom/pages/resizes/rapid cancellation, metadata has zero additional loads, availability stays at its two initial development requests through all unchanged polls/restoration. Actual canvas, excerpts, close focus, private PDF→TXT replacement/removal and reset→canonical-source restoration passed; retired private sources returned 404 and no CRM installation was created. A final read-only reviewer found an additional Documents async retirement race: sample fetch/file arrayBuffer could finish after reset and invoke the retired mutation, cancelling new work before server rejection. Root confirmed and fixed it with per-operation epoch/workspace guards and sample-fetch abortion on retirement. Targeted `.runtime/performance-browser-retired-upload.json` passed: a real sample response withheld across reset generated zero retired replacement POSTs, a new workspace's delayed chat still completed, and its ordinary replacement succeeded. Typecheck passed; final read-only revalidation found no actionable issue. One setup attempt was interrupted by root's API reload, then the targeted check passed after readiness. These later frontend-only guards do not alter the measured backend paths. Phase 08 is complete; phase 10a quality execution remains pending. Linux release receipt refresh is required after settled quality/security changes.

