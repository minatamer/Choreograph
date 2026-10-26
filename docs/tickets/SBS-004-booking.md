# SBS-004 — Implement business approval and booking lifecycle

> **Deployment supersession,26 October2026:** the selected deployment is **no database** (`DATABASE_ENABLED=false`), using private GCS objects, Cloud Tasks and authenticated minute Scheduler maintenance. SQL/pgvector/migration/WorkerPool requirements in this dated packet are historical or optional true-mode evidence. They do not authorize or require database provisioning. See [the current setup inventory](../../infra/README.md#verified-cloud-inventory-and-remaining-setup-26-october2026).

Status: **Complete local**
Owning phase: **07-build**  
Depends on: **SBS-003**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

Complete request → coordinator review → atomic booking. Customer and Business views read the same scoped records. Confirmation is an accepted transaction, never model prose or a client-side availability check. CRM trouble must not undo a valid reservation.

## Implementation scope

1. Build business request review, meaningful record-based counts, shared staff calendar, assignment and explicit confirmation.

2. Validate current revisions and full availability in a transaction; commit reservation, request transition, idempotency and authorized destination-bound outbox together. CRM skip creates no CRM work.

3. Prove real PostgreSQL concurrent/partially overlapping approvals allow only the permitted booking. A conflict remains reviewable with current alternatives.

4. Reschedule atomically and preserve the old reservation if the replacement fails. Cancel releases the interval; complete changes status without claiming real delivery/payment. Replays and stale revisions are safe.

5. Return compact accepted-action receipts with independent CRM state. Perspective changes and refresh preserve accepted data without replaying processing.

## File allocation and cohesive commit plan

choreograph/{service,domain,models,contracts}.py; frontend business/calendar/outcome/lifecycle owners; real competing-transaction and rollback tests. Allocation: transactional commands, then connected business/outcome UI.

## Acceptance criteria

- [x] Customer-controls no-CRM booking works end-to-end; guided composer inputs remain owned by SBS-005 and the full-flow gate SBS-008 (AFK-0009).
- [x] PostgreSQL races/partial overlaps/adjacent reservations behave correctly
- [x] Failed reschedule retains old booking
- [x] Cancellation/completion/replay are correct
- [x] All controls share command authority.

## Meaningful verification

Independent real DB connections/barriers, request-version races, duplicate keys, replacement rollback and post-cancel availability. Inspect business actions on phone/short laptop/desktop and refresh restoration.

## Precision references

- [Blueprint: 8-state-and-action-model](../CHOREOGRAPH.md#8-state-and-action-model)
- [Blueprint: 11-postgresql-model-and-concurrency](../CHOREOGRAPH.md#11-postgresql-model-and-concurrency)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Implemented transactional approval, reschedule, cancel and completion, request-scoped availability, generated response contracts, Business review, actual staff calendar, record-based counts and booking outcomes. Explicit review gates precede approval; UI actions call the same Python commands. A skipped CRM creates no outbox work; a consented injected connection queues destination-bound work atomically with the reservation. Dispatch belongs to SBS-006/007.

Verified on 22 October 2026: isolated actual PostgreSQL booking tests (5 passed); combined booking/database tests after final summary assertions (12 passed); generated contracts, TypeScript and Next production build passed; bridge tests (2 passed). `node scripts/inspect-booking.mjs` passed at 1440×1000, 1280×720, 390×844 and 320×740, exercising approval, refresh restoration, reschedule and cancellation, plus desktop completion. No page errors or horizontal overflow; actual Business, phone outcome and short-laptop renders were inspected. `.runtime` retains private local screenshots/receipts. The frontend was stopped before the production build and restored afterward, preserving API/PostgreSQL and siblings.

Distinct read-only validation covered the settled command/contract/UI changes, explicit action gates, ownership, idempotency target binding, rollback and current summary rules. No remaining actionable issue in this slice. The first criterion was allocated to manual customer controls because the suggested composer depends on SBS-005; the full guided end-to-end acceptance remains mandatory in SBS-008. Live providers, CRM dispatch, Linux/hosted acceptance and human runtime visual review are not claimed. Changes remain unstaged/uncommitted. Next: SBS-005A.

