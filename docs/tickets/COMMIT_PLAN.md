# Ticket-prefixed local commit plan

The owner directly requested: “file level commit plan, stage andcommit everything with ticket prefixes”. This authorizes local staging/commits of the complete Choreograph build. No push, deployment, paid/provider/account action is included. Product/visual/security AFK reviews remain provisional; Git permission does not approve those results.

Before this operation Git contained only initial commit5601be0 and the short README; the completed app/design/docs were untracked. These commits group the final verified snapshot by owning responsibility. They do not reconstruct historical intermediate implementations. The SBS-015 application group consolidates the interdependent final SBS-001–009/012–015 code, migrations, assets and regressions so its shared contracts/providers are recorded together. Earlier ticket evidence remains in each packet.

Commit on the existing main branch. Stage explicit literal paths only; verify exact allocation, staged blobs and secret/runtime exclusions before each commit. Preserve raw build-input bytes with `.gitattributes` because this host has core.autocrlf=true and the release receipt hashes exact bytes. Do not change tested application code, dependencies, running services or data.

Validation already settled before Git work:227 isolated-PG/injected backend tests,15 Node checks, lint/pip/contracts/types/Windows build, responsive/performance/security reviews and source-fresh Linux107-input smoke with180 HTTP assertions. Recheck release freshness, staged contents and clean final tree; no broad test rerun is needed for grouping unchanged code.

Excluded by design: ignored .env.local, runtime receipts/logs/screenshots, local DB data, virtualenv/dependency trees, build caches and generated PDF.js/sample copies. Canonical fictional PDFs, licensed fonts/BPE tokenizer assets, safe release/Figma receipts, blank-secret .env.example and source tests remain included. This is a local source snapshot; actual provider/hosted acceptance remains open in SBS-011.

## Exact file allocation

### 1. SBS-000: Pin toolchain and add owned local service lifecycle

17 files:

- `.env.example`
- `.gitattributes`
- `.gitignore`
- `.node-version`
- `apps/backend/pyproject.toml`
- `apps/backend/requirements.in`
- `apps/backend/requirements.lock.txt`
- `apps/frontend/package.json`
- `compose.yaml`
- `config/baseline.json`
- `config/local-services.json`
- `package-lock.json`
- `package.json`
- `scripts/local.mjs`
- `scripts/local.test.mjs`
- `scripts/service.mjs`
- `scripts/setup.py`

### 2. SBS-000A: Preserve approved Figma design and authoring receipts

30 files:

- `design/figma/.doc-baseline.json`
- `design/figma/.pruned-delta.json`
- `design/figma/.refinement-delta.json`
- `design/figma/compact-keyframes.js`
- `design/figma/controls.js`
- `design/figma/copy-refinement.json`
- `design/figma/final-component-refinements.js`
- `design/figma/foundations.js`
- `design/figma/helpers.js`
- `design/figma/library-showcase.js`
- `design/figma/native-prototype.js`
- `design/figma/product-components.js`
- `design/figma/prototype-contract.js`
- `design/figma/public-screens.js`
- `design/figma/refine-composer.js`
- `design/figma/refine-copy.js`
- `design/figma/refine-public.js`
- `design/figma/refine-system.js`
- `design/figma/screen-wrappers.js`
- `design/figma/state.json`
- `design/figma/support-components.js`
- `design/figma/token-renames.json`
- `design/figma/tokens.json`
- `design/figma/validation.json`
- `design/figma/verify-current.js`
- `design/figma/verify-propagation.js`
- `design/figma/verify-screens.js`
- `design/figma/workspace-screens.js`
- `docs/tickets/SBS-000A-figma.md`
- `scripts/design-tokens.mjs`

### 3. SBS-015: Add complete booking, grounded AI and visitor CRM application

163 files:

- `apps/backend/alembic.ini`
- `apps/backend/choreograph/__init__.py`
- `apps/backend/choreograph/acceptance.py`
- `apps/backend/choreograph/ai_admission.py`
- `apps/backend/choreograph/ai_config.py`
- `apps/backend/choreograph/api.py`
- `apps/backend/choreograph/assistant.py`
- `apps/backend/choreograph/cloud_plan.py`
- `apps/backend/choreograph/composition.py`
- `apps/backend/choreograph/contracts.py`
- `apps/backend/choreograph/crm.py`
- `apps/backend/choreograph/crm_admission.py`
- `apps/backend/choreograph/crm_api.py`
- `apps/backend/choreograph/crm_composition.py`
- `apps/backend/choreograph/crm_config.py`
- `apps/backend/choreograph/db.py`
- `apps/backend/choreograph/dispatch.py`
- `apps/backend/choreograph/dispatcher.py`
- `apps/backend/choreograph/domain.py`
- `apps/backend/choreograph/errors.py`
- `apps/backend/choreograph/hubspot.py`
- `apps/backend/choreograph/interactions.py`
- `apps/backend/choreograph/jobs.py`
- `apps/backend/choreograph/knowledge.py`
- `apps/backend/choreograph/knowledge_api.py`
- `apps/backend/choreograph/migrate.py`
- `apps/backend/choreograph/models.py`
- `apps/backend/choreograph/operator.py`
- `apps/backend/choreograph/parse_document.py`
- `apps/backend/choreograph/providers.py`
- `apps/backend/choreograph/readiness.py`
- `apps/backend/choreograph/release.py`
- `apps/backend/choreograph/runner.py`
- `apps/backend/choreograph/server.py`
- `apps/backend/choreograph/service.py`
- `apps/backend/choreograph/sessions.py`
- `apps/backend/choreograph/settings.py`
- `apps/backend/choreograph/task_delivery.py`
- `apps/backend/choreograph/task_enqueue.py`
- `apps/backend/choreograph/tokenizers.py`
- `apps/backend/migrations/env.py`
- `apps/backend/migrations/versions/0001_schema.py`
- `apps/backend/migrations/versions/0001_schema.sql`
- `apps/backend/migrations/versions/0002_manifest_scope.py`
- `apps/backend/migrations/versions/0003_scenario.py`
- `apps/backend/migrations/versions/0004_knowledge.py`
- `apps/backend/migrations/versions/0005_simulated_crm.py`
- `apps/backend/migrations/versions/0006_retirement.py`
- `apps/backend/migrations/versions/0007_ai_profiles.py`
- `apps/backend/migrations/versions/0008_crm_identity.py`
- `apps/backend/migrations/versions/0009_task_publication.py`
- `apps/backend/migrations/versions/0010_acceptance_run.py`
- `apps/backend/tests/conftest.py`
- `apps/backend/tests/fixtures/conflicting-guide.txt`
- `apps/backend/tests/fixtures/malicious-guide.txt`
- `apps/backend/tests/test_acceptance.py`
- `apps/backend/tests/test_ai_admission.py`
- `apps/backend/tests/test_ai_config.py`
- `apps/backend/tests/test_ai_entrypoints.py`
- `apps/backend/tests/test_api_boundary.py`
- `apps/backend/tests/test_assistant.py`
- `apps/backend/tests/test_assistant_apply.py`
- `apps/backend/tests/test_booking.py`
- `apps/backend/tests/test_cloud_plan.py`
- `apps/backend/tests/test_composition.py`
- `apps/backend/tests/test_crm.py`
- `apps/backend/tests/test_database.py`
- `apps/backend/tests/test_dispatch.py`
- `apps/backend/tests/test_domain.py`
- `apps/backend/tests/test_fixture_guard.py`
- `apps/backend/tests/test_interactions.py`
- `apps/backend/tests/test_jobs.py`
- `apps/backend/tests/test_knowledge.py`
- `apps/backend/tests/test_live_crm.py`
- `apps/backend/tests/test_live_embeddings.py`
- `apps/backend/tests/test_live_knowledge.py`
- `apps/backend/tests/test_provider_limits.py`
- `apps/backend/tests/test_receipt_snapshot.py`
- `apps/backend/tests/test_release.py`
- `apps/backend/tests/test_requests.py`
- `apps/backend/tests/test_security_crm.py`
- `apps/backend/tests/test_session_admission.py`
- `apps/backend/tests/test_settings.py`
- `apps/backend/tests/test_settings_repr.py`
- `apps/backend/tests/test_task_delivery.py`
- `apps/backend/tests/test_task_enqueue.py`
- `apps/backend/tests/test_tokenizers.py`
- `apps/frontend/AGENTS.md`
- `apps/frontend/app/api/demo/[...path]/route.ts`
- `apps/frontend/app/auth/hubspot/callback/route.ts`
- `apps/frontend/app/demo/page.tsx`
- `apps/frontend/app/demo/workspace/page.tsx`
- `apps/frontend/app/fonts/GoogleSansFlex.ttf`
- `apps/frontend/app/fonts/OFL.txt`
- `apps/frontend/app/globals.css`
- `apps/frontend/app/healthz/route.ts`
- `apps/frontend/app/layout.tsx`
- `apps/frontend/app/page.tsx`
- `apps/frontend/app/tokens.css`
- `apps/frontend/components/booking-outcome.tsx`
- `apps/frontend/components/business-review.tsx`
- `apps/frontend/components/chat-workspace.tsx`
- `apps/frontend/components/crm-controls.tsx`
- `apps/frontend/components/documents.tsx`
- `apps/frontend/components/entry-client.tsx`
- `apps/frontend/components/request-planner.tsx`
- `apps/frontend/components/source-reader.tsx`
- `apps/frontend/components/staff-calendar.tsx`
- `apps/frontend/components/ui.tsx`
- `apps/frontend/components/use-guest.ts`
- `apps/frontend/components/week-calendar.tsx`
- `apps/frontend/components/workspace-client.tsx`
- `apps/frontend/lib/api.ts`
- `apps/frontend/lib/bridge.ts`
- `apps/frontend/lib/generated/api.d.ts`
- `apps/frontend/lib/generated/openapi.json`
- `apps/frontend/lib/private-api.ts`
- `apps/frontend/next-env.d.ts`
- `apps/frontend/next.config.ts`
- `apps/frontend/tsconfig.json`
- `assets/knowledge/access-and-arrival.pdf`
- `assets/knowledge/changes-and-cancellations.pdf`
- `assets/knowledge/evaluation-adversarial.txt`
- `assets/knowledge/evaluation.json`
- `assets/knowledge/manifest.json`
- `assets/knowledge/preparation-guide-v2.pdf`
- `assets/knowledge/preparation-guide.pdf`
- `assets/knowledge/safety-and-exclusions.pdf`
- `assets/knowledge/service-guide.pdf`
- `assets/knowledge/service-questions.md`
- `assets/knowledge/sources/guides.json`
- `assets/tokenizers/LICENSE.tiktoken`
- `assets/tokenizers/cl100k_base.tiktoken`
- `assets/tokenizers/manifest.json`
- `assets/tokenizers/o200k_base.tiktoken`
- `scripts/author-knowledge.py`
- `scripts/bridge-source.test.mjs`
- `scripts/bridge.test.mjs`
- `scripts/browser-fixtures.mjs`
- `scripts/callback-route.test.mjs`
- `scripts/expire-browser-fixture.py`
- `scripts/export_openapi.py`
- `scripts/generate-contracts.mjs`
- `scripts/inspect-accessibility.mjs`
- `scripts/inspect-booking.mjs`
- `scripts/inspect-chat.mjs`
- `scripts/inspect-crm-recovery.mjs`
- `scripts/inspect-crm.mjs`
- `scripts/inspect-documents.mjs`
- `scripts/inspect-flow.mjs`
- `scripts/inspect-integrations.mjs`
- `scripts/inspect-performance.mjs`
- `scripts/inspect-poll-recovery.mjs`
- `scripts/inspect-recovery.mjs`
- `scripts/inspect-request.mjs`
- `scripts/inspect-shell.mjs`
- `scripts/inspect-sync.mjs`
- `scripts/inspect-visual.mjs`
- `scripts/measure-performance.py`
- `scripts/pdf-assets.mjs`
- `scripts/prepare-knowledge.py`
- `scripts/prepare-tokenizers.py`
- `scripts/private-api.test.mjs`

### 4. SBS-010: Package Linux release and no-key CI verification

13 files:

- `.dockerignore`
- `.github/workflows/ci.yml`
- `infra/Dockerfile.backend`
- `infra/Dockerfile.frontend`
- `infra/README.md`
- `infra/cloud-run.example.yaml`
- `infra/cloud-tasks.example.json`
- `infra/iam.example.json`
- `infra/release-evidence.json`
- `infra/worker-pool.example.json`
- `scripts/release-fingerprint.mjs`
- `scripts/release-http-smoke.mjs`
- `scripts/release-smoke.mjs`

### 5. SBS-011: Record build, security and external acceptance handoff

28 files:

- `AGENTS.md`
- `README.md`
- `docs/CHOREOGRAPH.md`
- `docs/CHOREOGRAPH_OVERVIEW.html`
- `docs/LESSONS_LEARNED.md`
- `docs/security/SECURITY_OVERVIEW.html`
- `docs/security/SECURITY_REVIEW.md`
- `docs/tickets/COMMIT_PLAN.md`
- `docs/tickets/README.md`
- `docs/tickets/SBS-000-baseline.md`
- `docs/tickets/SBS-001-foundation.md`
- `docs/tickets/SBS-002-database.md`
- `docs/tickets/SBS-003-request-calendar.md`
- `docs/tickets/SBS-004-booking.md`
- `docs/tickets/SBS-005-assistant.md`
- `docs/tickets/SBS-005A-knowledge.md`
- `docs/tickets/SBS-006-crm.md`
- `docs/tickets/SBS-007-durable-work.md`
- `docs/tickets/SBS-008-responsive-flow.md`
- `docs/tickets/SBS-009A-quality.md`
- `docs/tickets/SBS-009B-security-review.md`
- `docs/tickets/SBS-009C-security-fixes.md`
- `docs/tickets/SBS-010-release.md`
- `docs/tickets/SBS-011-external-acceptance.md`
- `docs/tickets/SBS-012-live-ai.md`
- `docs/tickets/SBS-013-live-crm.md`
- `docs/tickets/SBS-014-cloud-dispatch.md`
- `docs/tickets/SBS-015-integration-readiness.md`

## Commit receipts

Preceding commit hashes are recorded here before the final documentation commit. The final documentation commit’s own hash is available from `git log`; a file cannot contain its own commit hash. The complete sequence is verified after committing.

| Order | Actual local commit | Subject |
|---|---|---|
|1|`e0273defa4594b8bf6fdfc928163ec07978eb136`|SBS-000: Pin toolchain and add owned local service lifecycle|
|2|`a71db0360752065a37e127ed62cc7c8439eda3f8`|SBS-000A: Preserve approved Figma design and authoring receipts|
|3|`75e2fc8c7934deb0959a860fe25628af1d686e10`|SBS-015: Add complete booking, grounded AI and visitor CRM application|
|4|`0b999bbe475a11049260ccdecccbb56a7fd6173c`|SBS-010: Package Linux release and no-key CI verification|
|5|Final documentation commit: its own hash is in `git log -1`|SBS-011: Record build, security and external acceptance handoff|

Staged review: every staged blob matches the reviewed worktree bytes; no credential candidates were found in included text. Ignored secret/runtime/dependency/build paths were verified absent. Git whitespace diagnostics were reviewed: Markdown hard breaks, generated SQL/license spacing, PDF cross-reference spaces and one existing CI EOF blank line were retained without changing verified code/assets. Current release source remains `c803fbcd8d491d794dc3504bd08d0da056f5521363fcdd8e1fdaa73f7c7251b4`; no test or hosted result is invented by committing. Final clean-tree, committed-blob, source-freshness and five-subject checks run after the last commit. No remote push is included.
