# SBS-000 — Verify the supported baseline and owned lifecycle

Status: **Complete local**  
Owning phase: **07-build**  
Depends on: **None**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

One frontend and one Python backend need a verified reproducible foundation before feature work. Node 24.19.0, Python 3.11.9 and Docker Engine 29.8.1 were read back on this host. Fresh ports 45860/45861/45862 were absent from searched sibling source records and current listeners/exclusions; a future conflict must fail safely.

## Implementation scope

1. Verify exact compatible supported versions from primary sources before installing Next/React/TypeScript, FastAPI/Pydantic, SQLAlchemy/Alembic, the PostgreSQL driver and pgvector. Pin resolved packages and lockfiles; do not copy sibling fixed models or secrets. Keep one ORM ecosystem and leave the real OpenAI model unset pending configuration/verification.

2. Create repo-local ignored server-side configuration and a blank-secret example. Fake/paid-off is default; explicit startup alone loads configuration. Install into an owned environment, never a sibling environment.

3. Create local service/port configuration and ownership-aware launch/stop helpers. Bind loopback, recheck immediately before launch and fail if occupied; never kill by executable/port alone. Track the repo's children and preserve development volumes. Frontend iteration uses hot reload.

4. Establish actual installation/check/lifecycle commands and document them only after verification. Adopt useful inert factory/boundary patterns from actual sibling code while preserving the selected Python architecture.

## File allocation and cohesive commit plan

Root manifests/locks/ignore rules; apps/backend/pyproject.toml and locked requirements; config/local-services.json; .env.example; scripts/local.mjs and owned lifecycle helpers; actual command/version/port sections of README and AGENTS. Allocation: toolchain/config, then lifecycle. Suggested subject SBS-000; no staging/commit authorization.

## Acceptance criteria

- [x] Exact compatible versions and isolated install succeed
- [x] owned ports are checked and unrelated listener conflicts fail safely
- [x] configuration/test isolation rejects inherited live settings
- [x] stop preserves siblings and data
- [x] only actual verified commands/readiness are claimed.

## Meaningful verification

Configuration/ownership/inert-import checks, frozen install and relevant baseline builds. Inspect manifests and generated outputs for accidental secrets/sibling dependencies.

## Precision references

- [Blueprint: 10-tech-stack-and-responsibility-boundaries](../CHOREOGRAPH.md#10-tech-stack-and-responsibility-boundaries)
- [Blueprint: 18-local-services-and-sibling-safety](../CHOREOGRAPH.md#18-local-services-and-sibling-safety)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Implemented pinned npm workspaces, a repo-local Python venv/frozen requirements, explicit fake-only config, secret-free examples, a verified PostgreSQL 17/pgvector 0.8.5 image, fresh loopback ports and ownership-aware launch/stop helpers. Configuration/secrets are ignored. Node 24.19.0 was used explicitly for the frozen npm ci because the global npm wrapper launches Node 22.23.2.

Checks: Node lifecycle tests 2 passed; Python settings tests 3 passed; pip check clean; frozen no-deps Python lock install succeeded; Node 24 npm ci succeeded (67 packages, audit reported 0 vulnerabilities). An owned temporary Node fixture bound both app ports, was stopped through the real helper after PID/creation-time/command ownership verification, and both ports were released. Docker image manifest/pull succeeded; digest is pinned in Compose. No database/container was created in this ticket.

Read-only validation: inspected the complete ticket-owned manifests/config/lifecycle/settings/test files and unstaged scope. An initial running-container ownership gap was independently confirmed, fixed with Compose label verification, and re-reviewed. Final pass: Meets ticket, no actionable findings. Runtime app readiness and actual DB schema are later tickets; no paid/live/hosted acceptance is claimed. No files were staged or committed. Next: SBS-001.

Follow-up during SBS-007, 22 October 2026: the owner reported visible console windows. Replaced Windows detached launches with an explicitly hidden `Start-Process` supervisor; per-instance direct logs and existing process-tree ownership remain. Verified all three real services survive launcher exit without visible supervisor windows, and runner-only restart preserves API/frontend. Lifecycle checks now **3 passed**, including a short hidden probe and paths with spaces. See SBS-007 for the recovery/browser evidence.

Owner-requested follow-up,23 October2026: matched the inspected Roomedy/Retailor app-local env structure without reading their secret files. Moved the blank-secret backend example to `apps/backend/.env.example`, added the frontend equivalent, and migrated this checkout's existing values into ignored `apps/backend/.env.local` / `apps/frontend/.env.local`; the root file was removed only after value-preservation checks. Backend/API/runner/Compose own database/provider configuration; frontend receives only its server-side API/origin/bridge settings. Both providers remain fake. Setup is repeatable, preserves existing credentials and rejects conflicting files. Updated explicit Python loading, service-specific launcher environments, DB fixture/performance parsing (including quoted URLs), acceptance/readiness defaults, CI and owning docs.

Verification:19 configuration/setup/fixture-guard Python tests plus17 isolated PostgreSQL/API/acceptance tests pass; all16 Node lifecycle/bridge tests and affected Ruff pass. Full restart verified old supervisors/descendants absent and all45860/45861/45862 listeners released before replacements; the owned development volume was retained. Replacements passed frontend/entry HTTP200, API fake-mode health, runner fresh fake-mode heartbeat and frontend→API `GET session` returning expected401 `SESSION_REQUIRED` rather than a bridge error. An API-only stop/restart kept frontend HTTP200 and frontend/runner supervisor identities unchanged. All requested services are left running under hidden supervisors; current PIDs/logs are in ignored `.runtime/services.json`. No sibling was changed; no provider/account/cloud or Git write ran. The existing Linux/source receipt predates this follow-up and must be refreshed before release; full historical suite/Linux/hosted checks were not rerun for this local-config change.

