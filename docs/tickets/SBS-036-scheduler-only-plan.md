# SBS-036 — Plan one Scheduler-driven worker for no-database deployment

Status: Complete local implementation/validation —26 October2026; actual deployment remains blocked under SBS-039. The preceding quality/security audits kept this plan documentation-only. [SBS-039](SBS-039-paid-deployment.md) now owns the direct deployment authorization; this prerequisite implements the already selected cheaper topology before any deployment. Earlier “do not implement now” text below records the previous audit boundary and is superseded for this implementation.

The owner prefers fewer deployment components and explicitly requests thinking through/documenting a single Scheduler-driven worker that removes Cloud Tasks. The selected persistence stays `DATABASE_ENABLED=false`, private encrypted GCS. This ticket is the future implementation owner. Current runtime still requires Tasks (`release.application` rejects GCS without its publisher), and current maintenance publishes jobs rather than executing them. Changing docs must not pretend the refactor exists or disable current protections.

## Proposed topology and behavior

Keep three request-billed, scale-to-zero Cloud Run services: frontend, private API and private worker. Keep the existing private bucket and three runtime/secret identities. Use **one authenticated Cloud Scheduler HTTP job** to invoke the private worker, initially once per minute. No Cloud Tasks queue/API/publisher role/task-delivery identity, always-on WorkerPool, database, VM or new service is selected for the future object path. Leave optional SQL compatibility separate.

The API commits the booking/change plus destination-bound durable CRM intent atomically to GCS and returns its honest saved/pending state. It performs no queue publication or unreliable after-response background thread. Booking success remains independent of external CRM success; skip creates no CRM work. The scheduled worker runs the existing shared maintenance and domain claim/deliver/finalize primitives against the same authoritative records. Local `runner` behavior remains unchanged.

Separate responsibilities remain: Scheduler supplies the wake-up, the durable outbox owns eligibility/retry/ambiguity, and the worker performs the bounded provider operation. A scheduled execution is not business completion. Keep current five domain attempts, next-due backoff, three-hour delivery window, destination/account/revision/connection fences, exact export consent, API budget/idempotency and unknown-create reconciliation. Never reset counters or replay an old store's outbox to adopt the new transport. Cleanup/uninstall still needs its existing disclosed policy and approval; expiry never invents uninstall consent.

## Bounded execution and duplicate safety

Start with **one claimed CRM job per sweep**, after bounded maintenance, rather than draining the backlog. Existing normal/cleanup provider deadlines (45/90seconds) stay intact. Proposed outer sweep budget150seconds, worker request timeout180seconds, Scheduler attempt deadline240seconds and a non-renewing240second object lease provide room for bounded maintenance and state I/O; implementation must reconcile these against measured worst-case paths before adopting them. Do not increase per-provider allowances to fit a timer. One job/minute is a small-demo throughput choice; sync can wait for the next tick plus backlog/backoff, which must remain honestly pending in the UI.

Use a generation-conditional global sweep lease in the existing object store to admit one sweep across duplicate/overlapping requests/revisions. Scheduler is at-least-once, so the lease is an optimization/fence, not proof of exactly-once effects. Retain per-job claims/tokens and recheck lifecycle/revision/destination before effects and finalization. A late sweep that loses its lease cannot finalize another owner's job. Lease expiry and process death must recover without clearing unknown outcomes. A lease loser returns a bounded successful no-op; legitimate provider failure remains durable retry/attention according to current domain policy. Do not trust Scheduler headers as authentication.

Authenticate worker invocation with its existing distinct maintenance service account: Run Invoker only on the worker, OIDC audience equal to the stable worker origin, and server verification of issuer/audience/email before reading a fixed small command body. Keep frontend-to-API identity, CSRF/session/guest checks, private source authorization and exact-bucket roles. No browser credentials, signed public state URL or downloadable service-account key.

## Recovery, cleanup and capacity

Periodic invocation discovers outbox work even if the API dies immediately after committing, and handles expired claims/workspaces without any browser open. Reuse `jobs.maintenance` and `jobs.claim`/`deliver`/`finish_job`; do not create a second booking/CRM state machine or hidden retry queue. Preserve private-source retirement, credential retention through required cleanup/unknown outcomes, global ledgers and current safe diagnostic codes/counts. A GCS lifecycle rule cannot replace semantic cleanup of records inside the encrypted shared shard or visitor HubSpot records.

Missed ticks resume at the next invocation without catch-up storms. Observe oldest-due work, cleanup backlog, failed sweeps and needs-attention counts privately. The one-write-per-second same-object GCS limit and150second proposed sweep bound require later bounded injected contention tests and measured hosted capacity; no throughput/SLO is claimed by this plan. Increase batch size/frequency only from evidence, with a finite work/deadline budget.

## Future file-level implementation ownership

| Owner | Planned responsibility |
| --- | --- |
| `choreograph/release.py`, `task_delivery.py` | Compose the object scheduler-only worker without requiring a Tasks publisher; preserve authenticated bounded ingress. |
| `choreograph/jobs.py`, `object_store.py`, `persistence.py` | Reuse current domain primitives and existing conditional leases; add only the narrow sweep orchestration/fencing needed. |
| API/service enqueue hooks, `dispatch.py`, `task_enqueue.py` | Remove publication from the selected object path after atomic intent commit; retain explicitly optional compatibility paths until their callers are proven unnecessary. |
| `cloud_plan.py`, object Cloud Run/IAM/Scheduler examples | Render no queue or delivery-SA/actAs/publisher grants for the future object path; update timeouts, identity and source-ready prerequisites together. |
| Backend object/delivery/race/expiry tests and object Linux smoke | Exercise scheduler delivery, overlap/crash/lost-ack/replay and browser-closed cleanup with fake providers and isolated state. |
| Runbook, blueprint, AGENTS and queue | Record actual implemented cutover, measured limits and exact remaining hosted setup; retire superseded Tasks requirements only then. |

Do not modify these runtime files now. Keep existing foundation/canonical/secret receipts and resources intact. Later cutover must stop writers, ensure no old delivery invocations remain, inspect any existing publications/outbox/unknown work, and resume from durable domain intent without changing attempt counts, consent, grants or account bindings. The currently hosted store has canonical data only, but reverify before acting; do not assume it stays unused.

## Future acceptance checklist

- Unchanged exact quote/booking/reschedule/cancel/complete and source/manifest/timezone behavior; CRM skip produces zero provider work.
- Claim a saved connected event on a scheduled tick; native success only after verified provider response. Keep four contextual replies, reservation shortcut, tour/welcome and UI motion intact.
- Repeated/concurrent sweep, duplicate delivery, expired lease, crash before/after provider effect, lost acknowledgement, stale revision/destination, reset/expiry and exhausted budgets produce one permitted effect or honest ambiguity, never false success.
- Failures persist next-due/retry/attention across process restarts; no unbounded loop or work beyond remaining deadline. Provider bookkeeping remains independent of rolled-back business transactions.
- No-browser expiry removes private data while retaining only necessary authorized cleanup/unknown credentials; eventual cleanup/uninstall follows current consent/shared-account protections.
- Renderer/worker start and local Linux object smoke need no Tasks API; optional SQL behavior is unchanged. Finish fake/injected checks first; paid/hosted/native acceptance remains separately authorized.

## Cost and decision record

The main expected gain is **simpler setup and fewer queue/IAM/reconciliation components**, not a guaranteed large bill reduction. [Cloud Scheduler](https://cloud.google.com/scheduler/pricing) listsUSD0.10/job/31days with three free jobs per billing account; [Cloud Tasks](https://cloud.google.com/tasks/pricing) has a first-million-operation allowance, so low-volume queue cost can already be zero. Worker Cloud Run compute and GCS requests still cost money and a more frequent polling design can offset queue savings. Compare actual region/traffic/backlog before publishing a dollar claim. These primary price inputs were checked26 October2026; no cloud resource was created or changed.

The owner approves planning this direction, not its implementation now. The recommended next deployment path is to implement/validate this ticket before provisioning the remaining transport resources; do not provision a new Tasks queue solely because older examples contain one. Current code, cloud state and provider settings remain unchanged by the plan.


## Implementation allocation — subsequent owner deployment request

Validation follow-up allocation: `scripts/local.test.mjs` owns a demonstrated Windows-only fixture race. Two full runs passed164 checks but its8second self-stopping probe exited before the13second identity/window/cleanup sequence finished (taskkill128/255). Keep exact PID ownership and assertions; extend only that finite test probe lifetime to60seconds, preserving immediate verified cleanup and no production launcher change. Rerun the full Node suite after this bounded fixture repair.

The direct deployment request makes this previously deferred dependency current. Reuse `create_delivery_app` with an internal object Scheduler-only composition: maintenance-only route, exact OIDC identity before bounded body; no Tasks route/client/publisher for object containers. Optional SQL transport remains intact. `jobs.scheduled_tick` owns a240second encrypted conditional global lease,150second outer budget and at most one existing domain job. Preserve independent job180second token leases/five attempts/three-hour horizon, maintenance and90second maximum provider window. Stop admitting a new job unless at least90seconds remain; pass the smaller outer deadline to delivery, preserving conservative ambiguity/retry on timeout. Global lease expiry does not authorize another job's receipt; per-job token/expiry remains authoritative.

Files before source edits: `jobs.py` (narrow bounded orchestration and optional smaller delivery deadline), `task_delivery.py` (reuse ingress, omit Tasks route for object-only composition), `release.py` (derive object topology without a new env switch), `cloud_plan.py` (no queue inputs/REST/preflight in objects mode), existing object Run/IAM/Scheduler examples (remove queue/delivery grants,180/240second timeouts), focused Scheduler tests/object composition tests/renderer tests and `scripts/object-linux-smoke.py` (actual authenticated separate-process scheduled delivery/cleanup). No booking/source/UI/schema or paid policy changes. `object_store.py` may add a narrow lease-ownership check only if needed to return a duplicate no-op without waiting. Preserve GCS policy, canonical pack and current diagnostics.

Validate injected identity/body failures, no Tasks route/client, duplicate/concurrent tick, bounded one-job batch, retry/backoff/restart, expired job claim and stale completion, deadline admission, process-loss recovery and browser-closed cleanup. Run the no-SQL suite and Linux objects release at the settled boundary; record that old Python security runtime still blocks deployment. Update current docs/queue and exact file-level commit plan, commit the local prerequisite separately from eventual deployed acceptance. No new paid calls are needed for this ticket.

## Actual implementation, validation and read-only verdict

Complete locally —26 October2026. Object API commits only durable intent; the private Scheduler endpoint performs shared maintenance and at most one eligible domain job. No object-container Tasks client/route/publisher, queue render/input/REST/preflight, task-delivery identity or publisher/actAs grant. Local direct runner and optional SQL Tasks compatibility remain. Exact booking/source/consent/revision/idempotency/provider admission rules and UI are unchanged. Configuration is validated before provider construction; no new public mode switch.

| Evidence | Actual result |
| --- | --- |
| Focused final Scheduler/renderer checks | **25 passed**, including exact OIDC/body-first denial, absent Tasks/guest route/client, unknown create/backoff/restart without duplicates, concurrent cross-engine no-op, expired job recovery/stale finisher, bounded one-job batch, browser-closed cleanup/skip, slow-maintenance admission, late ack ambiguity and global-lease expiry/old-release fencing. All use isolated objects/injected providers. |
| Portable backend gate | **386 passed,162 SQL-dependent cases deselected**,416.52s with `Engine.connect` forbidden. One existing Pydantic alias warning in the concurrent booking case; no test failure. The later two additional lease/late-ack cases and small final config-before-client ordering are covered by the final25 focused cases. |
| Frontend/tooling | **165 Node checks passed**, zero skipped; types, whole configured Ruff and `pip check` pass. The finite60second Windows fixture lifetime fixes the reproduced8second auto-exit/13second cleanup race; production launchers are unchanged. |
| Actual Linux objects gate | **Six frontend HTTP/asset/header checks and13 encrypted-object scenarios pass**, including actual exact-OIDC-injected Scheduler ingress in a distinct Python process for sync/expiry; no Tasks route, no browser, no SQL or real provider call. Non-root images; owned containers removed. |
| Fresh release source | `51cc624cfad5f3694064dfec2a347e1b4e916f3c81ff9a3a241a114be7caacbd`,200 inputs, current in `infra/release-object-evidence.json`. Frontend image `sha256:22379005551d6b71d36f1dafb63d2e64efe2e647c6091fc45bd7eead93433872`; backend `sha256:0ef7c82a6a7459ca5b605adfd87eaa7a54cdcf676624cdedbb243f97d480ae0e`. Backend still uses the blocked Python3.11.17 base; local smoke is not security-release approval. |

Validation dispositions: an initial Linux run correctly rejected changing a source comment during acceptance. A subsequent isolated Docker command failed under concurrent checks; the same owned image/scenario passed direct network-disabled reproduction, and the final complete source-frozen gate passes. Failed runs are excluded from success receipts. Deadline tests now replace only the jobs module clock reference, preserving asyncio timers. Two full Node runs exposed the bounded Windows fixture lifetime race and passed164/165 before the allocated fixture repair; the complete final rerun passes165/165.

Read-only validation: **Meets local ticket; no new actionable finding in the settled Scheduler diff.** Covered functional/identity/retry/expiry/ambiguity/duplicate/private-IAM-template safeguards and docs. Actual GCS contention, real Scheduler OIDC/recovery, native provider semantics and public paid acceptance remain **unverified** under SBS-039. Existing SEC-038-02 is retained, not closed. Direct owner deployment authority is recorded, but the absent official Python security image and missing fresh finite hosted policy still block public activation. No old outbox, grants or private data were transferred.

Ignored logs: `.runtime/sbs036-backend.log`, `sbs036-focused-settled.log`, `sbs036-node-final.log`, `sbs036-linux-settled.log`, `sbs036-selected-tests.json`. Current docs/HTML/relative links and known-private current-tree checks pass. Exact local staging/hash/private-byte/parent/clean-tree verification belongs to COMMIT_PLAN and the ignored checkpoint receipt.
