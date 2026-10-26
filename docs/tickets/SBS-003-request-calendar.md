# SBS-003 — Implement exact quotes and persistent seeded availability

> **Deployment supersession,26 October2026:** the selected deployment is **no database** (`DATABASE_ENABLED=false`), using private GCS objects, Cloud Tasks and authenticated minute Scheduler maintenance. SQL/pgvector/migration/WorkerPool requirements in this dated packet are historical or optional true-mode evidence. They do not authorize or require database provisioning. See [the current setup inventory](../../infra/README.md#verified-cloud-inventory-and-remaining-setup-26-october2026).

Status: **Complete local**  
Owning phase: **07-build**  
Depends on: **SBS-002**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

Customer cards and assistant use one deterministic authority. Two-bedroom move-out plus oven is exactly 18500 cents and 270 minutes. Save the visitor's validated IANA zone; store UTC instants. The guided initial busy preference must be genuinely occupied in persistent fictional records.

## Implementation scope

1. Implement all documented service/size/oven combinations with pure integer cents/minutes and revision-bound quote snapshots. Validate unsupported combinations, time ordering, ambiguous/nonexistent local time, closed hours and 30-day horizon.

2. Use two eligible staff, Monday–Saturday 09:00–18:00 and 30-minute starts with half-open ranges. Full duration and staff eligibility determine availability.

3. Materialize a bounded mixed schedule once before availability is exposed. The initial busy scenario covers eligible staff and preserves an alternative; retries, role switches, refresh and later requests cannot move blockers or displace bookings.

4. Return a typed seven-day card with busy/free/closed labels and full-duration alternatives. Direct open-week queries need no initial date. Selecting service/time updates the same versioned draft without reserving/submitting.

5. Implement explicit quote/time review and customer submission to Awaiting review, bounded to ten requests/bookings per workspace. Duplicate idempotency keys return established results and stale revisions require fresh review.

## File allocation and cohesive commit plan

choreograph/{domain,service,contracts}.py, narrow model changes; frontend draft/week/quote owners and generated types; tests exact quote/time/seed/idempotency. Allocation: pure rules/tests, persisted commands, connected customer cards.

## Acceptance criteria

- [x] All 18 catalogue combinations match exact amounts/durations
- [x] busy/open-week paths use real same-record availability
- [x] fixture IDs persist across refresh/retry
- [x] UTC/local and DST/non-hour zones are correct
- [x] selection/submission does not confirm a reservation
- [x] replay/stale cases are safe.

## Meaningful verification

Pure catalogue cases plus real scoped PostgreSQL seed/time queries; two-resource eligibility, partial/adjacent intervals, DST/local-week boundaries and replay counters. Inspect short/mobile week and review action reachability.

## Precision references

- [Blueprint: 7-demo-catalogue-and-scheduling-policy](../CHOREOGRAPH.md#7-demo-catalogue-and-scheduling-policy)
- [Blueprint: 72-occupied-week-scenarios-and-consistent-availability](../CHOREOGRAPH.md#72-occupied-week-scenarios-and-consistent-availability)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Implemented pure integer catalogue/time/eligibility rules, a persistent once-only mixed 30-day staff calendar, typed seven-day availability with real occupied intervals, revision-bound drafts/quotes and explicit idempotent Awaiting review submission. Canonical two-bedroom move-out + oven is 18500 cents/270 minutes. The guided next working day is occupied for both staff; the next working alternative stays available. API and UI use the saved browser-local zone and UTC instants. Scenario column is migration 0003.

Connected customer controls now use generated API types and the real local database: service/home-size/oven changes, full-duration times, quote review, Send request, role switch, refresh and fresh-workspace recovery. Selections never create a reservation. Stale/changed idempotency keys reject safely; repeated submission returns its established request; the eleventh request is rejected. Server-backed fields wait for accepted state.

Checks: the settled 37-test Python suite passed on a fresh isolated PostgreSQL database. Includes all 18 price combinations, unsupported values, Berlin DST gaps/folds, Kathmandu offsets, Auckland week boundaries, hours/horizon, staff/half-open overlaps, persisted seed IDs, exact quote, occupied choice/alternative, replay/stale cases, ten-request cap and expired/invalid-cookie recovery. Four lifecycle/bridge checks passed. Generated contracts/typecheck and production frontend build passed.

Actual Playwright flow passed at 1440x1000, 1280x720, 390x844 and 320x740 with visitor-local zones: occupy→alternative→185-dollar review→explicit submission→refresh→Business view. Send reachable, no horizontal overflow or page errors; four renders inspected. A focused phone rerender after skip-link/time-range refinement also passed and was visually inspected. Chromium can spell Kathmandu as its equivalent Katmandu IANA alias; the saved zone matches actual browser detection. A development reload loop required an owned frontend restart; subsequent flows passed. Production build now runs with the dev frontend stopped. API/database/sibling services were preserved.

Read-only validation examined the settled domain/service/contract, commands, generated output and connected UI. Confirmed/fixed stale-calendar interaction, fresh-workspace recovery and schema-default optionality; temporary bootstrap diagnostics were removed. Final pass: Meets ticket; no actionable findings. Business approval, visual assistant/RAG and CRM are subsequent tickets, not claimed complete. Nothing staged/committed. Next SBS-004.

