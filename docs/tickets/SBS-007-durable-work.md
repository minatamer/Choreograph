# SBS-007 — Add durable outbox recovery and cleanup

Status: **Complete local**
Owning phase: **07-build**  
Depends on: **SBS-006, SBS-005A**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

Authorized CRM/document work must survive process failure. Local runner processes due work without Google services; Cloud Tasks later delivers but is not the only record. Reset/expiry immediately fences late effects and reports physical/external cleanup separately.

## Implementation scope

1. Commit authorized destination-bound outbox with booking; skip has no CRM work. Acquire bounded leases across concurrent workers, recheck workspace generation/record revision/account/connection before dispatch.

2. Persist attempts/outcomes/next-time/mappings and recover crash-before-dispatch/enqueue or expired leases. Bound five transient attempts, horizon/concurrency/deadlines and Retry-After. Auth/scope failures require attention; ambiguous creates require reconciliation rather than blind retry.

3. Implement explicit local runner startup/polling and startup recovery using shared application functions; tests inject time/ticks. FastAPI BackgroundTasks is not durability; internal maintenance is not a public unauthenticated route.

4. Retire access immediately, clean private originals/chunks/embeddings and consented app-created CRM data resumably, preserve minimal cleanup references and fence late publication/exports.

5. Prepare service-identity Cloud Tasks boundary without contacting Google. Hosted unattended recovery remains an explicit external choice; do not silently add Cloud Scheduler or equate scale-to-zero timers with recovery.

## File allocation and cohesive commit plan

choreograph/{jobs,crm,knowledge,service,models}.py; runner entry point and bounded delivery adapter; pending/retry/attention UI; real DB lease/recovery tests. Allocation: transactional leases, retirement/cleanup, then visible outcomes.

## Acceptance criteria

- [x] Pending work survives restart
- [x] repeated/concurrent delivery is harmless
- [x] leases/late revisions/reset/destination changes are fenced
- [x] finite honest retry/attention/reconcile outcomes
- [x] private source data cleans while samples remain
- [x] no local Google requirement.

## Meaningful verification

Actual PostgreSQL lease/rollback/restart races with injected provider outcomes/time and bounded-call counters. Verify owned runner lifecycle preserves siblings and volume.

## Precision references

- [Blueprint: 13-durable-work-retries-and-recovery](../CHOREOGRAPH.md#13-durable-work-retries-and-recovery)
- [Blueprint: 14-guest-isolation-retention-and-cleanup](../CHOREOGRAPH.md#14-guest-isolation-retention-and-cleanup)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Implemented PostgreSQL leases with bounded delivery attempts, persisted reconciliation/verified mappings, revision/destination/lifecycle fences, a separately owned local runner, reset/expiry retirement, private source purge and separate cleanup/uninstall receipts. The prepared private `task_delivery.py` factory verifies a Google-signed identity for a configured audience and exact service account, bounds body/certificate work and invokes the same durable handler. It is not mounted by the local guest API. Its tests inject identity verification; no Google call, task enqueue, IAM or hosted recovery check ran. `google-auth` 2.62.0 and its installed dependencies are included in the frozen lock.

Checks on 22 October 2026: isolated PostgreSQL `tests/test_jobs.py` **7 passed**; injected private-boundary `tests/test_task_delivery.py` **2 passed**; frontend typecheck and `pip check` passed. `node scripts/inspect-sync.mjs` passed at 1440×1000, 1280×720, 390×844 and 320×740: simulated read-back, no fake native links, record removal, uninstall and no page errors/overflow. Inspected actual desktop, short-laptop and phone renders. Visual review caught a pending notice surviving successful cleanup; it is now bound to the connection state/revision and the affected four-view walkthrough passed again.

`node scripts/inspect-recovery.mjs` stopped only the owned runner, confirmed a booking export remained pending across browser refresh, started a new runner and observed the same booking/receipt sync. Frontend/API supervisor identities were preserved. The Windows launcher was repaired after the owner's screenshot: `Start-Process -WindowStyle Hidden` starts a small Node supervisor with direct per-instance log files. Runtime ownership/readiness and no visible supervisor windows were checked; lifecycle regressions **3 passed**, including surviving launcher exit and paths containing spaces. Development volume and sibling services were preserved.

Read-only validation covered the current jobs/retirement/token/receipt paths, private task boundary and launcher change against this packet. No remaining actionable ticket finding. Changes remain unstaged/uncommitted. Live HubSpot cleanup/uninstall/slot timing, real Google identity/IAM and unattended deployed recovery remain external acceptance. Next: SBS-008 complete-flow/responsive checks.

