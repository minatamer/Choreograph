# SBS-002 — Add PostgreSQL, migrations and guest isolation

Status: **Complete local**  
Owning phase: **07-build**  
Depends on: **SBS-001**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

Use actual owned local PostgreSQL/pgvector with SQLAlchemy/Alembic, not SQLite or an in-memory substitute. Guest workspaces are scoped and expire after two hours. Synthetic customer/business switching grants no production employee identity. Every browser-provided ID must be authorized server-side.

## Implementation scope

1. Pin and verify a Cloud SQL-compatible PostgreSQL/pgvector image and vector/btree_gist extensions. Own one Compose project/volume on loopback 45862. Tests require isolated database/schema and refuse development/production storage.

2. Create migrations and scoped models for workspaces/session hashes/generations, staff/catalogue, revisioned enquiries/quotes/bookings, idempotency/activity, document manifests/versions/chunks, CRM connections/install registry and outbox/mappings. No plaintext provider tokens in ordinary rows.

3. Enforce workspace-scoped relationships and database active-interval overlap protection. Keep pure domain code independent of FastAPI/vendor startup and use bounded pools/queries.

4. Issue opaque high-entropy HttpOnly/SameSite sessions with appropriate Secure policy, mutation origin/CSRF checks, fixed expiry and immediate retirement/reset fencing. Cleanup/backup erasure is separate. Reject cross-workspace IDs and stale generations with safe errors.

## File allocation and cohesive commit plan

infra/compose.yaml; backend alembic.ini/migrations; choreograph/{db,models,guards,sessions}.py; actual isolated PostgreSQL migration/session/concurrency fixtures. Allocation: owned storage/schema, then guest security boundary.

## Acceptance criteria

- [x] Real migrations/extensions and scoped foreign keys pass
- [x] cross-guest/expired/stale/cookie/origin/CSRF access fails safely
- [x] PostgreSQL overlap protection is demonstrated
- [x] tests cannot inherit live flags or normal DB
- [x] sibling data/processes are intact.

## Meaningful verification

Actual isolated PostgreSQL migration/schema probes, two-session isolation, fixed-time expiry/reset and concurrent range inserts. Record exact engine/extension/image identities and test cleanup.

## Precision references

- [Blueprint: 11-postgresql-model-and-concurrency](../CHOREOGRAPH.md#11-postgresql-model-and-concurrency)
- [Blueprint: 14-guest-isolation-retention-and-cleanup](../CHOREOGRAPH.md#14-guest-isolation-retention-and-cleanup)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Implemented 15 scoped PostgreSQL tables, frozen initial Alembic DDL and a separate immutable/private document-manifest guard migration. PostgreSQL 17 with vector 0.8.5/btree_gist 1.7 is running only in choreograph-local on 127.0.0.1:45862, pinned image digest d2ef61f42ef767baa5a1475393303cc235bcd92febd9d7014eddb48b41f3bad0. Development volume is preserved.

Guest routes issue high-entropy HttpOnly/SameSite cookies, store only SHA-256 references, derive CSRF tokens server-side, validate IANA zones, preserve the initial zone/fixed two-hour expiry and fence reset generations. Unit-of-work dependencies commit before sending successful responses. Live profile remains disabled.

Actual checks: 13 Python tests passed across isolated DB/session/config/API boundaries. Created and removed only a unique choreograph_test_* database. Verified upgrade→downgrade→upgrade to 0002, exact extensions/vector(64), simultaneous partially overlapping inserts (one commit/one PostgreSQL 23P01 conflict), adjacent intervals, cross-guest staff/manifest rejection, immutable document ownership, cookie restoration, invalid-zone rejection, expiry/reset/stale generation and no browser workspace-ID authority. Generated contracts/typecheck passed. A synthetic actual frontend→API→PostgreSQL cookie/restoration smoke passed with no provider calls. Local migrations applied to development DB.

Lifecycle helper now records descendants, catches known orphans/PID reuse, cleans failed launches and supports selected-service start/stop. Actual API-only stop verified its root/children gone and port free before a new healthy API started; frontend/database were preserved. Four lifecycle/bridge tests passed.

Read-only validation confirmed the final scoped schema/session/migration/bridge/lifecycle implementation and ticket coverage. The document-manifest ownership gap and invalid token-key admission were independently confirmed and fixed with DB guards/strict key checks; reset replay was fenced. Final pass: Meets ticket; no actionable findings. Physical retired-data cleanup is owned by SBS-007; no hosted/provider/owner acceptance claimed. Nothing staged/committed. Next: SBS-003.

