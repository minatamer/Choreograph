# SBS-014 — Complete durable Cloud Tasks dispatch and unattended maintenance

Status: **Complete local**  
Owning phase: **07-build continuation**  
Depends on: SBS-013 provider identity; existing SBS-007 and release configuration.

## Outcome

Implement actual enqueue/reconciliation and an always-on deployment caller using the existing Python backend image. Cloud Tasks HTTP delivery remains the sole deployed CRM execution path. Cloud Run WorkerPool is the prepared native non-HTTP maintenance/dispatch target; no Cloud Scheduler or self-perpetuating finite-retry task chain is selected. No cloud resource is created during coding.

## Implementation

1. Validate a fixed project/region/queue, HTTPS worker origin/path, exact delivery service account/audience and explicit cloud mode. Add a bounded Google-authenticated Tasks REST transport or supported pinned client; trusted fixed routes only, finite bytes/deadline, no automatic unknown-write retry or credential logging. Inject transport/auth in tests.
2. Persist per-outbox publish state/lease/attempt/identity/reconciliation before network. Deterministic task names bind event and delivery epoch; confirm accepted/already-existing tasks against the exact target/payload. Ambiguous creates reconcile by name; database outbox remains authoritative after a lost response, crash-before-enqueue, task deletion/completion/dedup tombstone, expired lease and domain retry. Do not suppress pending work forever because one task was once accepted.
3. Bound scanning, publish concurrency/rates/backoff/horizon and maintenance work. Preserve genuine CRM skip, destination/generation/revision/expiry fences and five domain delivery attempts. Enqueue attempts and domain delivery attempts are different counters. Recheck authority before publish and on delivery.
4. Add a dedicated `dispatcher`/maintenance composition role that calls bounded SQL retirement/purge/recovery plus enqueue, never local `jobs.tick` direct CRM. Durable restart recovery and a PG maintenance lease handle two instances during rollout. Expose only content-free health/heartbeat for platform probes/operator diagnosis, no unauthenticated maintenance trigger or guest routes.
5. Prepare official WorkerPool configuration: manual count1, provisional1vCPU/512MiB, same immutable backend image, exact SA, supported Cloud SQL binding and numeric secret versions; finite shutdown and readiness/liveness supported by actual platform schema. Pools are continuously billed and count0 stops maintenance. Record this cost/availability prerequisite; no account/region/budget is assumed.
6. Grant dispatcher only required application DB credentials/Cloud SQL and queue-scoped create/get plus actAs on exact delivery identity. It receives no visitor token key/HubSpot/bridge secret or worker invoker if not used. Remove unused enqueue grants from API. Worker still verifies real signature/issuer/audience/exact verified email. Prepare monitoring for stale durable heartbeat/oldest due work plus concrete operator restart/reconcile commands; monitoring is not a fabricated deployed result.

## File allocation

Dispatch owner: new narrow task-enqueue/dispatcher modules, delivery handler changes where needed, dispatch/heartbeat models and migration `0009`, actualPG+injectedHTTP tests. Integration/release owner: explicit role composition, WorkerPool/IAM/queue examples and operations, smoke/CI adaptation. Coordinate shared models/settings/release edits. Root owns this slice and all shared files sequentially. Use the existing ORM/worker code; no new backend platform or generic scheduler.

## Acceptance

- [x] Actual composed enqueue path exists and default fake/local tests cannot contact Google.
- [x] Actual isolated PG + injected HTTP proves crash/lost-create-response/duplicate/stale/lease/rollout/retry/dedup-window cases without duplicate CRM effects or lost due work.
- [x] Unattended dispatcher restarts from durable state, expires/purges private data and enqueues cleanup while guest traffic is absent; bounded health/heartbeat failure is observable.
- [x] Worker identity and body/response limits remain; skipped CRM creates no publish work.
- [x] WorkerPool/least-privilege templates conform to current primary documentation, cost/region/provisioning remain unconfigured and explicit.
- [x] Focused/settled checks and independent read-only validation pass; actual IAM/Tasks/WorkerPool/Cloud SQL results stay pending.

## Evidence

Design recorded before implementation: one publication row per immutable outbox event, target fingerprint, hashed deterministic task name per epoch, short lease, separate bounded publish count and next-check time. One create/get request per publication action; unknown creates reconcile by exact name. FULL responses verify exact target/OIDC/UUID payload; IAM therefore needs queue-scoped tasks.fullView in addition to create/get. A missing task is never business success: re-read the authoritative outbox and, if eligible, advance epoch with bounded backoff. Retired destinations stop publishing; existing queued deliveries remain harmless through DB fences. Outbox delivery attempts stay separate and capped at5.

One PG advisory-lock leader performs bounded SQL maintenance then at most3 publish actions per cycle. Persist content-free cycle/success/error heartbeat for diagnosis; short publication leases fence acknowledgements across crash/rollout. Use a2-connection dispatcher pool, preserve capacity for two instances during rollout, and expose health-only probes without a maintenance route. Runtime uses a fixed Google metadata identity and Tasks endpoint only after explicit cloud configuration; tests inject both and make no Google calls. WorkerPool count1 is continuously billed;0 stops recovery. No Cloud Scheduler or self-task chain.

Primary references checked22October2026: Tasks [create](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues.tasks/create) and [get](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues.tasks/get), WorkerPool [health checks](https://docs.cloud.google.com/run/docs/configuring/workerpools/healthchecks) and [YAML reference](https://docs.cloud.google.com/run/docs/reference/yaml/v1). Real hosted acceptance still requires authorized resources/spending.


Implementation checkpoint: task_enqueue.py, dispatch.py and dispatcher.py are composed through release dispatcher/dispatch-once/dispatch-status roles. Migration0009 adds publication/heartbeat state. Actual cloud requests remain behind explicit configuration; tests use injected metadata/Tasks HTTP. A separate2-connection pool, exception-safe advisory lock, SQL-only maintenance, finite publication leases/epochs and health-only probes are implemented. The old maintenance Job now performs SQL only, and the WorkerPool v2 proposal has one numeric-version DB secret and no provider/bridge/token-key credential.

Focused evidence: initial13 dispatch/transport/delivery checks passed;19 caller/rollout/entrypoint checks and23 recovery/durable-job/transport checks passed. The settled integrated backend suite then passed **207 tests in54.57s**. Current final focused health/status/lease checks are recorded at completion. Local template parsing verified six Cloud Run documents/ten secret-version strings, plus WorkerPool scaling/SQL/probes/database-only secret and queue/actAs IAM scoping. No cloud operation ran.

Read-only implementation review caught two recovery gaps and confirmed them independently: a crashed fifth attempt previously depended on another direct worker claim to reach needs_attention, and late queue work could reach provider preparation after the existing three-hour retry window. SQL maintenance now recovers exhausted attempts and expires the finite window; direct late preparation refuses before token use. Durable work/publication code counts expose unresolved outcomes. Terminal publication receipts follow terminal business state, while a missing task is still never business success. These are scoped ticket repairs, not claims of deployed acceptance.


Final read-only revalidation found no remaining actionable local issue in SBS-014 scope. The integrated suite passed207 checks in54.57s; the final dispatch/metadata/health/status/rollout/tombstone/target-change/publish-limit set passed21 checks in14.46s, followed by12 final task-transport/worker checks in3.47s after explicit no-redirect/target-size bounds. Whole-repo configured Ruff passed, public generated contracts remained byte-identical, and unchanged frontend source retains SBS-013 type/build/14-Node/three-viewport evidence. Final integrated Linux/source/security evidence is owned by SBS-015 and the reopened build phases.

Prepared cloud files now separate native WorkerPool v2 health/scaling/SQL volume from service/job YAML. The optional maintenance Job is SQL-only; dispatcher settings filter provider/bridge/token-key values and use a2-connection pool. One DB secret version is pinned in the pool proposal, custom publisher IAM is queue-scoped create/get/fullView plus exact delivery-SA actAs, and API enqueue/actAs grants are absent. Local parsing/substitution checks passed; actual API acceptance, region support, IAM, pool billing/shutdown/monitoring/SQL/Tasks receipts remain external. No source change here authorizes provisioning, provider spending, deployment, Git writes or metadata export.
