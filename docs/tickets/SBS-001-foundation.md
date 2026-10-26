# SBS-001 — Create the Next/FastAPI contract foundation

> **Deployment supersession,26 October2026:** the selected deployment is **no database** (`DATABASE_ENABLED=false`), using private GCS objects, Cloud Tasks and authenticated minute Scheduler maintenance. SQL/pgvector/migration/WorkerPool requirements in this dated packet are historical or optional true-mode evidence. They do not authorize or require database provisioning. See [the current setup inventory](../../infra/README.md#verified-cloud-inventory-and-remaining-setup-26-october2026).

Status: **Complete local**  
Owning phase: **07-build**  
Depends on: **SBS-000, SBS-000A**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

Next owns presentation and a narrow same-origin bridge. Python owns strict Pydantic/OpenAPI contracts, sessions, domain commands and provider composition. Factories are inert; imports cannot load secrets, start listeners or dispatch providers. The approved Figma informs shared editable UI foundations.

## Implementation scope

1. Create strict public schemas and a FastAPI factory with safe fixed error codes, bounded JSON/body reading, content-free health/readiness and no raw diagnostic payloads.

2. Generate narrow TypeScript types from actual OpenAPI; do not maintain duplicate business schemas. The Next bridge accepts only fixed approved guest paths/methods, rejects arbitrary destinations/internal maintenance and forwards only approved headers.

3. Compose fake providers before tests import application code, independently of inherited flags/keys. Real mode without prerequisites fails closed, never silently switches to fake.

4. Build local font/token/control foundations and landing/demo shell from retained approved design source. Reuse glass, type and controls; no full-UI raster image. Keep primary actions reachable on phone and short laptop. This ticket does not implement booking rules or pretend the database/providers are ready.

## File allocation and cohesive commit plan

apps/backend/src/choreograph/{api,contracts,settings,bootstrap,errors}.py; frontend app/server/generated/UI/token owners; scripts/generate-contracts.mjs and focused boundary tests. Allocation: API/contracts, fixed bridge, then shared visual shell.

## Acceptance criteria

- [x] Minimal apps run on owned ports
- [x] bridge rejects unapproved forwarding and routes
- [x] generated types match OpenAPI
- [x] imports remain inert
- [x] fake test dispatch count is zero
- [x] landing/entry render from approved direction with no private config leak.

## Meaningful verification

Factory/config/bridge negative tests, generated-contract freshness, typecheck and production frontend build. Inspect initial landing at phone/short laptop/desktop; complete interaction verification belongs to SBS-008.

## Precision references

- [Blueprint: 104-one-frontend-and-one-backend-codebase](../CHOREOGRAPH.md#104-one-frontend-and-one-backend-codebase)
- [Blueprint: 163-figma-construction-evidence](../CHOREOGRAPH.md#163-figma-construction-evidence)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Implemented an inert FastAPI factory with strict public schemas, fixed safe errors and byte/total-time body admission; explicit composition; OpenAPI export/generated TypeScript; a same-origin allowlisted Next bridge with bounded streaming input; shared Figma token generation, local OFL Google Sans Flex font, reusable controls, landing and CRM entry shell. Live configuration fails closed. The workspace is a deliberate shell until later feature tickets.

Checks: six Python configuration/API tests passed, including origin/bridge rejection, body cap, total slow-trickle deadline and no raw echo; two bridge tests passed including arbitrary/internal destination rejection and oversized/stalled stream cancellation. Typecheck and settled production Next build passed. Initial restricted-sandbox build/asyncio tests failed due filesystem/socket permissions, then passed outside that sandbox; no code failure was hidden. OpenAPI export ran without secrets/database/providers.

Actual services started on frontend 45860 and API 45861. Recorded roots 22116/24948 were correlated with their listener children 15340/27988 at readiness. No runner/database was claimed ready. Playwright captured landing and entry at 1440x1000, 1280x720, 390x844 and 320x740: no horizontal overflow/page errors; desktop, short and phone renders visually inspected against approved Figma. Screens/evidence are private under .runtime. Browser headless shell worked after a full-browser spawn failure.

Read-only validation identified missing total body deadlines; confirmed and corrected in both bridge/API with regressions, then re-reviewed the settled ticket-owned scope. Final: Meets ticket; no actionable findings. Future booking/RAG/CRM and runtime owner acceptance are not implied. Nothing staged/committed. Next: SBS-002.

