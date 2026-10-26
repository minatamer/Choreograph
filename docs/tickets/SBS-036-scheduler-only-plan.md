# SBS-036 — Plan one Scheduler-driven worker for no-database deployment

Status: Planned only —26 October2026. **Do not implement this refactor in the current audit.**

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
