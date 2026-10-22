# SBS-006 — Prepare safe optional HubSpot integration

Status: **Complete local**
Owning phase: **07-build**  
Depends on: **SBS-004, SBS-005**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

Implement genuine no-call CRM skip plus injected OAuth/CRM development and a safe real adapter configuration. Public visitors never receive an operator login or silently export to it. No real registration/credentials/redirects/records are authorized in this build.

## Implementation scope

1. Bind one-use short-lived OAuth state to guest session/generation and authenticated account, preserve draft, encrypt usable server-side tokens and serialize refresh. Browser portal IDs/tokens never authorize.

2. Show selected destination and exact reviewed synthetic fields; only consented current approval queues export. Booking and CRM states are separate. Real native links require actual verified read-back; fake mode is labelled and never offers a fabricated HubSpot URL.

3. Track distinct app/account installations separately from visits/tokens, with conservative pending/unknown/capacity states and operator-only aggregates. Denial/cancellation/unavailable scopes/capacity preserve the no-CRM route.

4. Prepare narrow contacts/deals/association/update/read-back/cleanup operations with supported unique identity/mappings. Ambiguous create requires reconciliation; do not mutate pre-existing contacts based only on shared sample email.

5. Separate finish/detach/record cleanup/account-wide uninstall through fakes. Protect other active same-account uses and disclose provider admin notification. Expiry uninstall stays off without a disclosed policy; token deletion is not uninstall.

6. Verify current primary contracts during adapter work. Actual free-account scopes/native records/install-slot release remain externally gated.

## File allocation and cohesive commit plan

choreograph/{crm,models,contracts,service}.py; frontend connection/consent/status/settings; protected config/example and fake account/CRM fixtures. Allocation: connection/registry, narrow provider mappings, then UI.

## Acceptance criteria

- [x] Skip/denied/capacity produce no CRM calls/tasks/operator fallback
- [x] Simulated connection and durable provider-record upsert/read-back are honest; background dispatch is SBS-007
- [x] State/account/secret handling is guest/generation-bound
- [x] Duplicate identity, ambiguous transport, 429, cleanup and uninstall have distinct handling; durable outcomes are SBS-007
- [x] Actual account evidence remains unchecked.

## Meaningful verification

Injected counters/callback mismatch/install dedup/capacity races, encrypted/public-state checks, skipped outbox and ambiguous-create cleanup fixtures. No real HubSpot or scanner metadata operation.

## Precision references

- [Blueprint: 12-hubspot-what-connects-and-who-signs-in](../CHOREOGRAPH.md#12-hubspot-what-connects-and-who-signs-in)
- [Blueprint: 122-install-visibility-disconnect-and-capacity-handling](../CHOREOGRAPH.md#122-install-visibility-disconnect-and-capacity-handling)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Implemented one-use expiring OAuth state, server-authenticated account binding, encrypted tokens, scoped consent, no-call skip/detach, conservative account installation capacity and shared-account uninstall protection. Ambiguous OAuth outcomes retain conservative capacity; detaching/deleting tokens never frees an install. A local operator CLI returns fixed aggregate counts without a public account list. The simulated provider persists separately from guest transactions, so later worker crashes can be recovered without inventing external success.

Prepared a narrow HubSpot transport using OAuth `2026-09`, exact contacts/deals identity, uniqueness preflight, owned-record reads/updates/archives, association and separate uninstall. No email-based mutation of an existing contact. Actual native links require a verified current account/revision mapping; simulated records never expose fabricated HubSpot URLs. Added the fixed Next callback bridge with bound guest state, stable replay key and clean redirect; excluded callback query strings from local request logging. Real app registration, scopes/free-account unique-property support, lifecycle behavior and install-slot release remain unverified and gated.

Verification: settled backend suite **55 passed**; CRM/database subset **12 passed**, final CRM subset **5 passed**; TypeScript, generated contracts and final Next production build (including callback route) passed. Desktop/phone browsers passed simulated denial/connect/consent/disconnect and admin-notification disclosure without overflow/page errors. The actual callback bridge also passed using a local simulated OAuth code, preserving the guest and cleaning the URL. Phone entry render was inspected. Read-only review found and corrected connection selection under equal injected timestamps, unknown installation outcomes and a transient DB error category. A lower-level concurrent exclusion test legitimately produced a PostgreSQL deadlock victim; it now accepts either constraint rejection or deadlock rejection while still requiring exactly one committed reservation. Application commands serialize the workspace and return safe retry/conflict categories.

No real HubSpot calls, account operations or credentials were used. Pending/cleanup work is honestly pending until SBS-007 dispatch exists. All changes remain unstaged/uncommitted. Next: SBS-007.

