# SBS-037 — Final AFK quality, structure and efficiency audit

Status: Complete local quality; validated and ready for the authorized Git checkpoint —26 October2026. Baseline clean `266c89903c29bb51e1680fbd655cc47255bd6ce9`.

The owner explicitly requests a new complete quality pass first, scoped functionality-preserving repairs, meaningful validation and a file-level local commit plan/commits, followed only then by a separate security audit. They are AFK, prohibit questions and delegate routine decisions. Fake/injected providers, isolated no-database storage and paid-off checks are mandatory; PostgreSQL remains stopped. No deployment, cloud writes, secret payload access, paid calls, accounts, scanner inventory export, push or delegation is authorized. Current env flags were read by name only: databasefalse, faketrue, paidfalse. Preserve private logs and helpful public errors, exact domain behavior, source/session/consent boundaries and designed motion.

## Scope and ordered plan

1. Complete documentation-only SBS-036 Scheduler simplification plan. Distinguish future target from current Tasks-required runtime, with bounded retry/cleanup/cutover and honest cost tradeoffs. Do not implement that architecture during either audit.
2. Inspect current whole repository through its actual entry points: frontend state/projections/readers/dialogs/bridge; API/domain/session/timezone/availability/booking; object unit of work/GCS/retry ownership; ingestion/retrieval/provider admission; CRM/delivery/expiry; operator/release/configuration/CI tooling. Review legacy optional SQL code only where shared behavior could regress; run no SQL.
3. Record only concrete quality findings with evidence, consequence, minimal fix and exact file allocation **before** source changes. No line-count target, broad file splitting, cosmetic cleanup, new service/cache/framework or forced finding. Preserve safe diagnostics; technical/provider details must not reach visitors/browser console.
4. Execute scoped remedies and focused regressions. Review the settled full diff read-only against requirements, independently confirm any finding, repair and revalidate to no actionable scoped issue. No runtime rewrite merely because a Scheduler-only plan exists.
5. Run cohesive settled fake/no-SQL backend selection with SQL connections trapped, Node checks/types/Ruff/contracts/pip compatibility as affected. Use current fingerprint if image inputs are unchanged; otherwise refresh the actual objects-only Linux receipt without starting a database. Inspect affected real visual states only if UI behavior changes.
6. Update owning evidence/main progress, prepare exact current file-level allocation, scan final/staged private-value variants, stage explicit paths and commit. Verify clean before beginning security. AFK self-review is provisional, not owner paid/native/visual acceptance.

## Initial file allocation

SBS-036 plus AGENTS/README/blueprint/overview/lessons/runbook/queue own future deployment direction. This ticket owns quality scope/findings/results; main build progress owns AFK prompts/decisions; COMMIT_PLAN owns exact settled staging. Additional application/test files will be allocated here only after an actual finding is confirmed. No application source has changed at audit start.

## Q-037-01 — Repeated serialization of unchanged canonical vectors

Confirmed medium efficiency finding in `ObjectEngine.save`: each private-state commit reconstructs JSON and hashes the entire canonical source/vector pack even when its already-cached immutable content is unchanged. A focused regression fails before the fix with three unnecessary canonical serializations across three ordinary private writes, including a reopened reader. An isolated25-sample six-source/23-passage1536-dimensional injected-vector benchmark records p50=33.4376ms /p95=35.9968ms per encrypted file write. These are local measurements, not a hosted or browser latency claim.

Allocate `apps/backend/choreograph/object_store.py` to reuse the single cached content digest only after exact full canonical-content equality, and detach newly cached packs from caller-owned mutable dictionaries with one defensive deep copy. Changed source/vector/state/profile content must still serialize/hash/store a new immutable pack; state bytes and conditional generation behavior remain unchanged. Keep existing size/decryption/source hash checks, unknown-acknowledgement behavior, privacy and bounded one-pack-per-engine cache. No global cache, new dependency or behavior change.

Allocate `apps/backend/tests/test_object_pack_cache.py` to unchanged-pack serialization counts across writes/restart and in-place caller mutations that must create/read back new content. Keep all existing object CAS/corruption/delivery/expiry/source tests. Repeat the same local benchmark and focused tests before settled fake/no-SQL gates. Do not assert host timing in CI; output/invalidation and serialization counts are the meaningful regressions.

## Q-037-02 — Fake sample preparation bypasses shared persistence

The retained operator entry `scripts/prepare-knowledge.py` builds the selected engine through `load_local`, but directly imports SQLAlchemy Session. Under the current default false mode this hands an `ObjectEngine` to a SQL-only session and fails before preparing the six fake sources. The release composition already uses the shared persistence wrapper. This is a concrete stale entry point, not a reason to add a second pipeline or remove the command.

Allocate `scripts/prepare-knowledge.py` to importing the existing shared `choreograph.persistence.Session` only, preserving explicitly fake vectors, printed safe receipt, normal local loading and owned engine cleanup. Allocate `apps/backend/tests/test_prepare_knowledge_command.py` to executing the actual operator script with an injected isolated fake object engine and settings, SQL connections trapped, then reopening the encrypted store to verify all six sources. Reproduce failure before the one-line ownership fix. No live env or provider is loaded by the test.

## Results and scope coverage

| Area reviewed | Current conclusion |
| --- | --- |
| Frontend state/projections/calendar/source reader/dialogs/tour/scroll | Existing helpers, cancellation/focus and formatter ownership remain coherent. No demonstrated defect justified a UI rewrite or motion change.165 Node/types checks preserve behavior. |
| API/shared commands/prices/timezone/booking/idempotency/public errors | No rule/schema/contract change. Typed generic failures and scoped commands remain; no private diagnostic removed or exposed. Fake/no-SQL race/lifecycle checks pass. |
| Object persistence/GCS/leases/canonical ownership | Q-037-01 repaired through exact content comparison and detached cache ownership. Changed content, hash/size/decryption checks and conditional state writes remain authoritative. One bounded cached pack only. |
| Retrieval/admission/CRM/cleanup/publication | Shared authority, finite provider work, genuine skip, outbox retry/unknown outcomes and cleanup remain. Scheduler simplification is documentation-only; no new state machine/transport. |
| Local/operator/configuration/release/CI | Q-037-02 repaired through shared Session. The retained default no-database fake preparation command works without duplicate ingestion or deleted entry points; SQL wrapper delegation remains unchanged. |
| Dependencies/contracts/logs/structure | No dependency/API/UI/CSS change. Generated contracts unchanged, pip compatibility/Ruff pass. Runtime/private/generated exclusions stay. No speculative module split or new framework/service. |

Both findings have failing-before/passing-after regressions. The isolated25-sample unchanged-pack benchmark improved p50 **33.4376→12.1203ms**, p95 **35.9968→13.8601ms**. Canonical serialization count is **3→0** across three private writes. This is local synthetic-vector/file evidence, not hosted/browser latency. Changed source/vector data creates a new digest and fresh readback, including in-place caller mutation.

The actual fake preparation command failed before the wrapper fix with `AttributeError: ObjectEngine has no attribute connect`; afterward its regression reopens six fake guides from isolated encrypted state with SQL trapped.30 focused object/GCS/promotion checks and three direct quality regressions pass.

## Settled checks

- **374 backend tests passed,162 SQL-dependent cases deselected**,221.51seconds; SQL Engine.connect trapped for the entire run. Fake/injected providers and temporary encrypted stores only. Evidence: `.runtime/sbs037-backend.log`, `.runtime/sbs037-selected-tests.json`.
- **165 Node tests**, frontend TypeScript, full configured Ruff, `pip check` and actual generated-contract freshness pass; no generated diff. Evidence: `.runtime/sbs037-node.log` and command results.
- Fresh actual objects-only Linux release: two non-root amd64 images, six frontend page/asset/header checks and eleven object booking/RAG/replay/reschedule/restart/sync/expiry/credential scenarios; zero SQL/providers; owned resources removed. Current200-input source **e957cea3310dab33136e2128dff9e9336eb464fc83a09e096449c0d66c6be953**, recorded in `infra/release-object-evidence.json`, verifies fresh. Evidence: `.runtime/sbs037-linux.log`.
- Source UI files are unchanged; existing responsive/motion acceptance is preserved without manufacturing a new visual review. Owner paid-mode testing remains separate.

## Running-profile reconciliation

Owner env already says databasefalse/faketrue/paidfalse, but the old API health initially reported live. Tests were isolated and sent no chat/paid request. Only the verified owned API was stopped (tree/port released) and restarted through the normal loader; health now reports **fake**, PID5564 on45861. Frontend/runner, env keys and private state were preserved; PostgreSQL stayed stopped. No CRM action, grant/cloud change or database startup was used for readiness. Private startup log stays ignored at `.runtime/api-9c9d52ec-6d83-46e3-9c7f-05c081e7fc87.log`.

## Final read-only validation

**Meets ticket. No actionable quality findings remain.** Reviewed the complete quality/planning diff against clean266c899 without editing during the pass: exact-content pack reuse/ownership and invalidation, shared fake-command entry, preserved business/authorization/retry/byte/deadline rules, unchanged public errors/logs/motion, meaningful regressions and source-fresh Linux evidence. Q-037-01/02 are resolved. Security has not started; it follows only after the exact local quality commit and clean-tree check. SBS-036 remains future planning, not implemented.

AFK review is provisional, not personal owner paid/native/visual acceptance. COMMIT_PLAN owns exact staging; actual identities/clean-tree receipts remain ignored to avoid a post-commit tracked edit.
