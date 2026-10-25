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


## Owner-authorized workspace checkpoint —23 October2026

The owner directly requested a file-level plan, many meaningful ticket-prefixed commits, and staging/committing. This authorizes the following complete local checkpoint on the existing main branch from 3d81c44eddc93125c71138d0f0c031efa52b532a. It supersedes earlier no-new-Git-action statements for these SBS-017/018 changes only. No push, remote publication, deployment, paid provider/account operation or sibling change is included.

There are20 commits covering53 unique files. Each file is assigned once. Dependency helpers, optional-compatible controls and new components land before their integration. The nine integration files in commit13 stay together because they change required props and relocate the calendar/review/overview; splitting them would break intermediate TypeScript builds. This records the final implemented snapshot, including later owner corrections, rather than reconstructing abandoned designs.

Before staging: refresh full fake/isolated backend and Node checks, Python quality/dependency integrity, contracts/types, production Linux images and owned-container release smoke. Preserve existing hot reload and all development data. Stage only each explicit allocation, verify staged paths/blob bytes and whitespace, reject secret/runtime/dependency/build artifacts, and commit normally without bypassing hooks. Record actual results and hashes before the final documentation commit; verify clean tree and release fingerprint afterward. Historical receipts remain readable and do not become hosted GitHub Actions evidence.

| # | Exact commit subject | Exact files |
|---|---|---|
|1|SBS-017: Delay hero discovery until five idle seconds|`apps/frontend/components/hero-scroll-cue.tsx`|
|2|SBS-017: Share the landing collage and conversation motion|`apps/frontend/components/hero-collage.tsx`<br>`apps/frontend/app/hero-collage.css`<br>`apps/frontend/app/landing-hero.css`<br>`apps/frontend/components/hero-schedule.tsx`<br>`apps/frontend/app/globals.css`|
|3|SBS-017: Make every source discoverable in the intro carousel|`apps/frontend/components/guide-papers.tsx`<br>`apps/frontend/app/demo/welcome.css`<br>`apps/frontend/app/demo/guides.css`|
|4|SBS-017: Validate and preserve workspace destinations|`apps/frontend/lib/workspace-navigation.ts`<br>`scripts/workspace-navigation.test.mjs`|
|5|SBS-017: Support compact perspective controls on primary blue|`apps/frontend/components/view-switch.tsx`<br>`apps/frontend/app/materials.css`|
|6|SBS-017: Add shared reset and powered-by workspace controls|`apps/frontend/components/workspace-controls.tsx`|
|7|SBS-017: Add the full-height blue business sidebar and drawer|`apps/frontend/components/business-sidebar.tsx`<br>`apps/frontend/app/demo/workspace-shell.css`|
|8|SBS-017: Add the glass appointment-filter dropdown|`apps/frontend/components/calendar-filters.tsx`|
|9|SBS-018: Preserve calendar detail origins across overview cards|`apps/frontend/components/calendar-event-dialog.tsx`|
|10|SBS-018: Derive truthful overview and day metrics from shared records|`apps/frontend/lib/calendar-metrics.ts`<br>`apps/frontend/lib/business-overview-data.ts`<br>`scripts/business-overview.test.mjs`|
|11|SBS-018: Make calendar hours explorable with day details|`apps/frontend/components/calendar-activity-chart.tsx`<br>`apps/frontend/components/activity-day-dialog.tsx`<br>`apps/frontend/app/demo/activity-chart.css`|
|12|SBS-018: Add agenda, attention, service mix and workload panels|`apps/frontend/components/business-overview-panels.tsx`<br>`apps/frontend/app/demo/overview.css`|
|13|SBS-017: Assemble dedicated customer and business workspace pages|`apps/frontend/components/workspace-client.tsx`<br>`apps/frontend/components/workspace-tour.tsx`<br>`apps/frontend/components/business-overview.tsx`<br>`apps/frontend/components/business-review.tsx`<br>`apps/frontend/components/staff-calendar.tsx`<br>`apps/frontend/app/demo/layout.tsx`<br>`apps/frontend/app/demo/workspace.css`<br>`apps/frontend/app/demo/customer-chat.css`<br>`apps/frontend/app/demo/calendar-details.css`|
|14|SBS-017: Call the customer source collection documents|`apps/frontend/components/chat-workspace.tsx`<br>`apps/frontend/components/conversation-library.tsx`|
|15|SBS-017: Use document terminology in source readers|`apps/frontend/components/guide-reader-dialog.tsx`<br>`apps/frontend/components/source-reader.tsx`|
|16|SBS-017: Align entry and business document copy|`apps/frontend/components/entry-client.tsx`<br>`apps/frontend/components/documents.tsx`|
|17|SBS-017: Align assistant and admission messages with documents|`apps/backend/choreograph/assistant.py`<br>`apps/backend/choreograph/ai_admission.py`|
|18|SBS-017: Align document replacement and indexing notices|`apps/backend/choreograph/interactions.py`<br>`apps/backend/choreograph/knowledge.py`|
|19|SBS-010: Refresh isolated Linux acceptance for the workspace checkpoint|`infra/release-evidence.json`<br>`docs/tickets/SBS-010-release.md`|
|20|SBS-017: Record workspace guidance, validation and checkpoint commits|`AGENTS.md`<br>`docs/CHOREOGRAPH.md`<br>`docs/tickets/README.md`<br>`docs/tickets/SBS-017-workspace-navigation.md`<br>`docs/tickets/SBS-018-business-overview.md`<br>`docs/tickets/COMMIT_PLAN.md`|

The browser/runtime screenshots, ignored environment files, dependency trees, build caches and local databases are excluded. Canonical document titles/bytes remain accurate; UI terminology is Documents. The generated release receipt is safe fake-only source/image evidence.

### Current checkpoint execution record

All local pre-commit gates passed on the exact final application snapshot:236 backend/56 Node tests, full Ruff, pip dependency integrity, generated contract freshness, frontend types and CI template assertions. Both actual pinned Linux production images and the isolated fake release walkthrough passed45 HTTP requests/297 assertions. All temporary owned resources were removed. No hosted Actions, push, deployment, paid/live-provider operation or personal visual acceptance is claimed.

The refreshed178-input source receipt is `4f33f0a3c6fa507d21e113ef521a90c278a765625fdbaab130f2a8070f4779c1`, verified 2026-10-23T20:56:06.710Z. The source fingerprint was independently rechecked before staging. Existing Node module-type warnings and historical Markdown hard breaks were retained; no credential candidates or forbidden runtime/secret/dependency/build files were found in the allocation.

Commits1–19 are complete, with47 exact allocated files. Each staged/committed blob was compared byte-for-byte with its reviewed worktree file; each commit path set matched its group, and the index was empty after each commit. Commit20 records these six documentation owners. Its own hash is available from Git; final clean-tree,20-subject/file-allocation/committed-blob and release-fingerprint verification run after it.

| # | Actual commit | Subject |
|---|---|---|
|1|`305e6c35d6bbd286329f6bb5ab54891c062ec2db`|SBS-017: Delay hero discovery until five idle seconds|
|2|`c6948f5b4ece3b038608583ff4e69fa4062a9d50`|SBS-017: Share the landing collage and conversation motion|
|3|`216d57151294f8329f3eb287278ffe0b157c01e6`|SBS-017: Make every source discoverable in the intro carousel|
|4|`f354316236a2b28ddd6388bffcb0b4d3a572f856`|SBS-017: Validate and preserve workspace destinations|
|5|`e2047b1e1a956e646b1fd5569ac3671e96672725`|SBS-017: Support compact perspective controls on primary blue|
|6|`ca620ae35f74831028cf8364434c9555520f7370`|SBS-017: Add shared reset and powered-by workspace controls|
|7|`790a7945daa81bc51284bc5f97fa09ecfcc83b98`|SBS-017: Add the full-height blue business sidebar and drawer|
|8|`528c0554f783f34a48905d4fa362480c5238bc3d`|SBS-017: Add the glass appointment-filter dropdown|
|9|`570a600afbb8fa6dd82841be2fe2164bd487fb95`|SBS-018: Preserve calendar detail origins across overview cards|
|10|`1cc7adcec3f9fdab99698e8366ff8e936a01e24f`|SBS-018: Derive truthful overview and day metrics from shared records|
|11|`65c301bf5ab4d038c995eddf658c1a05fd0373b8`|SBS-018: Make calendar hours explorable with day details|
|12|`74ef90687c4d5b3160131c2cfb618a5a76eeb6b8`|SBS-018: Add agenda, attention, service mix and workload panels|
|13|`e64b2e5cb2d1063df102776b9fd9a7881a1e730d`|SBS-017: Assemble dedicated customer and business workspace pages|
|14|`4d1f1e544be25189964b49b798911e098810fe46`|SBS-017: Call the customer source collection documents|
|15|`af1ca6b8f609743aef367b803a9e2b48ee33d872`|SBS-017: Use document terminology in source readers|
|16|`072f27dc3e35cfc7943478a97464ee2588d6734a`|SBS-017: Align entry and business document copy|
|17|`d6d08e02170a832ac6ba2c76e1e80f585de827c8`|SBS-017: Align assistant and admission messages with documents|
|18|`fc627be56d2619cf9002cdaf03463b1556595da7`|SBS-017: Align document replacement and indexing notices|
|19|`2e5d7095afdbb5fce97cd0130bb8c27282af5bab`|SBS-010: Refresh isolated Linux acceptance for the workspace checkpoint|
|20|Final documentation commit; read its hash from `git log -1`|SBS-017: Record workspace guidance, validation and checkpoint commits|

No code fixes or plan deviations were needed during this checkpoint. No hooks were bypassed, history rewritten, branch switched or remote contacted. Earlier source snapshots/permissions above remain historical.


## Owner-authorized pre-audit checkpoint —24 October2026

The owner directly said: “you are allowed to make a staging commit, file-level commit plan, and you are allowed to stage and commit … If you already have any kind of unstaged work right now, make another file-level commit plan for it first, and then stage and commit it … when the unstaged is completely empty and everything is committed, you can then start the security audit and the code quality audit.” This is fresh local Git authorization for the entire existing continuation plus later AFK audit remedies; no push or external action is included. Active AFK-SESSION-001 is reconciled in the main progress record.

Baseline HEAD: `c9cc03688f5cfbcdb77151251f4d9acdafe644c1`. The following exact allocation records the final interdependent SBS-019–025/landing snapshot; it does not invent historical intermediate states. Shared contract/service/provider files are allocated once by final responsibility. Commit the complete sequence before starting either new audit.

Existing settled evidence:326 isolated-PG/injected backend tests,73 Node tests, types/Ruff, actual responsive/new real conversation receipts in SBS-023, and the latest isolated Linux44-HTTP/291-assertion receipt at source `c53466859b700085a78214f5d2795e5d3e47ecdc2e34765b292c990a13a12673` (192 inputs). No source/dependency/runtime change is needed merely for grouping. Explicit paths only; compare staged bytes with reviewed source, inspect actual secret exclusions locally without revealing values, check the staged diff and leave `.env.local`, `.runtime`, dependencies/caches and development data ignored. Preserve the running app and sibling services.

### Checkpoint commit 1: SBS-019: Refine landing motion and scheduling illustration

- `apps/frontend/app/landing-hero.css`
- `apps/frontend/components/hero-schedule.tsx`
- `apps/frontend/components/landing-motion.tsx`
- `apps/frontend/components/workflow-steps.tsx`

### Checkpoint commit 2: SBS-020: Show grounded source previews and original passage highlights

- `apps/backend/choreograph/contracts.py`
- `apps/backend/choreograph/knowledge.py`
- `apps/frontend/app/demo/source-citations.css`
- `apps/frontend/components/documents.tsx`
- `apps/frontend/components/guide-papers.tsx`
- `apps/frontend/components/guide-reader-dialog.tsx`
- `apps/frontend/components/source-reader.tsx`
- `apps/frontend/components/chat-sources.tsx`
- `apps/frontend/components/source-thumbnail.tsx`
- `apps/frontend/lib/chat-sources.ts`
- `apps/frontend/lib/source-highlights.ts`
- `apps/frontend/lib/generated/api.d.ts`
- `apps/frontend/lib/generated/openapi.json`
- `apps/frontend/lib/sample-guides.json`
- `apps/frontend/public/guide-previews/access-1.webp`
- `apps/frontend/public/guide-previews/service-1.webp`
- `apps/frontend/public/guide-previews/service-2.webp`
- `assets/knowledge/access-and-arrival.pdf`
- `assets/knowledge/manifest.json`
- `assets/knowledge/service-guide.pdf`
- `assets/knowledge/service-questions.md`
- `assets/knowledge/sources/guides.json`
- `scripts/author-knowledge.py`
- `scripts/source-highlights.test.mjs`

### Checkpoint commit 3: SBS-019: Reserve reviewed customer bookings through shared lifecycle commands

- `apps/backend/choreograph/service.py`
- `apps/backend/tests/test_customer_booking.py`
- `apps/frontend/app/demo/availability.css`
- `apps/frontend/components/booking-outcome.tsx`
- `apps/frontend/components/business-review.tsx`
- `apps/frontend/components/chat-review.tsx`
- `apps/frontend/components/week-calendar.tsx`
- `apps/frontend/lib/api.ts`
- `apps/frontend/lib/availability-period.ts`
- `scripts/availability-period.test.mjs`

### Checkpoint commit 4: SBS-021: Ground live assistant turns and preserve scoped command context

- `apps/backend/choreograph/assistant.py`
- `apps/backend/choreograph/assistant_context.py`
- `apps/backend/choreograph/composition.py`
- `apps/backend/choreograph/interactions.py`
- `apps/backend/choreograph/providers.py`
- `apps/backend/choreograph/tokenizers.py`
- `apps/backend/tests/test_assistant.py`
- `apps/backend/tests/test_assistant_apply.py`
- `apps/backend/tests/test_assistant_quality.py`
- `apps/backend/tests/test_composition.py`
- `apps/backend/tests/test_live_assistant.py`
- `apps/backend/tests/test_provider_limits.py`

### Checkpoint commit 5: SBS-022: Verify protected demo actions with background Turnstile

- `apps/backend/choreograph/api.py`
- `apps/backend/choreograph/verification.py`
- `apps/backend/tests/test_verification.py`
- `apps/frontend/app/api/demo/[...path]/route.ts`
- `apps/frontend/app/demo/layout.tsx`
- `apps/frontend/app/demo/verification.css`
- `apps/frontend/components/demo-guest.tsx`
- `apps/frontend/components/use-guest.ts`
- `apps/frontend/components/verification-provider.tsx`
- `apps/frontend/lib/bridge.ts`
- `apps/frontend/lib/turnstile.ts`
- `scripts/bridge.test.mjs`
- `scripts/turnstile.test.mjs`

### Checkpoint commit 6: SBS-024: Prepare currency-safe visitor HubSpot booking exports

- `apps/backend/choreograph/crm.py`
- `apps/backend/choreograph/crm_api.py`
- `apps/backend/choreograph/hubspot.py`
- `apps/backend/choreograph/jobs.py`
- `apps/backend/tests/test_crm.py`
- `apps/backend/tests/test_live_crm.py`
- `apps/backend/tests/test_hubspot_readiness.py`
- `apps/frontend/components/crm-controls.tsx`
- `infra/hubspot/app-hsmeta.json`

### Checkpoint commit 7: SBS-025: Keep private environment small and own fixed policy in backend code

- `apps/backend/.env.example`
- `apps/backend/choreograph/acceptance.py`
- `apps/backend/choreograph/ai_config.py`
- `apps/backend/choreograph/crm_config.py`
- `apps/backend/choreograph/dispatcher.py`
- `apps/backend/choreograph/readiness.py`
- `apps/backend/choreograph/runtime_config.py`
- `apps/backend/choreograph/settings.py`
- `apps/backend/tests/conftest.py`
- `apps/backend/tests/test_acceptance.py`
- `apps/backend/tests/test_ai_config.py`
- `apps/backend/tests/test_ai_entrypoints.py`
- `apps/backend/tests/test_dispatch.py`
- `apps/backend/tests/test_local_setup.py`
- `apps/backend/tests/test_release.py`
- `apps/backend/tests/test_runtime_configuration.py`
- `apps/backend/tests/test_settings.py`
- `apps/frontend/.env.example`
- `infra/cloud-run.example.yaml`
- `scripts/local.mjs`
- `scripts/local.test.mjs`
- `scripts/setup.py`

### Checkpoint commit 8: SBS-023: Offer useful chat replies and reviewed appointment management

- `apps/frontend/app/demo/booking-management.css`
- `apps/frontend/app/demo/customer-chat.css`
- `apps/frontend/components/chat-booking-management.tsx`
- `apps/frontend/components/chat-workspace.tsx`
- `apps/frontend/components/conversation-library.tsx`
- `apps/frontend/components/workspace-client.tsx`
- `apps/frontend/components/workspace-tour.tsx`
- `apps/frontend/lib/chat-messages.ts`
- `apps/frontend/lib/chat-questions.ts`
- `scripts/chat-messages.test.mjs`
- `scripts/chat-questions.test.mjs`

### Checkpoint commit 9: SBS-010: Refresh isolated Linux acceptance for the complete assistant snapshot

- `infra/release-evidence.json`
- `scripts/release-smoke.mjs`

### Checkpoint commit 10: SBS-025: Record continuation evidence and the authorized pre-audit checkpoint

- `AGENTS.md`
- `README.md`
- `docs/CHOREOGRAPH.md`
- `docs/security/SECURITY_REVIEW.md`
- `docs/tickets/COMMIT_PLAN.md`
- `docs/tickets/README.md`
- `docs/tickets/SBS-008-responsive-flow.md`
- `docs/tickets/SBS-017-workspace-navigation.md`
- `docs/tickets/SBS-019-customer-booking.md`
- `docs/tickets/SBS-020-rag-citations.md`
- `docs/tickets/SBS-021-live-ai-audit.md`
- `docs/tickets/SBS-022-turnstile-live-controls.md`
- `docs/tickets/SBS-023-assistant-quality.md`
- `docs/tickets/SBS-024-hubspot-free-readiness.md`
- `docs/tickets/SBS-025-local-configuration.md`
- `infra/README.md`

The final documentation commit records preceding hashes after they exist; its own identity is read from `git log`. Clean `git status --porcelain` is the required boundary before quality/security work starts. No new audit finding or fix is part of this baseline checkpoint.

### Pre-audit checkpoint execution record

All first nine groups passed explicit staged allocation/raw-byte comparison, known-private-value exclusion and whitespace checks before their local commits. Current image-input freshness remains verified. The final documentation commit has the subject below and its hash is read from Git; quality/security work starts only after the resulting working tree is actually empty.

| Group | Actual commit | Subject |
| --- | --- | --- |
| 1 | `1015b4eae20477bd90712d982bf76bfd9bbe3343` | SBS-019: Refine landing motion and scheduling illustration |
| 2 | `99278425fe85a5791e88229437e4e2c7373ade39` | SBS-020: Show grounded source previews and original passage highlights |
| 3 | `9e82017e22883efd9e62e7565e0bf6ff2e3f4039` | SBS-019: Reserve reviewed customer bookings through shared lifecycle commands |
| 4 | `a330bb81d493ecf340936afec4bcf22fd26913ad` | SBS-021: Ground live assistant turns and preserve scoped command context |
| 5 | `f0974975d9f7ec757e98a0cd4665ffdd9c250be7` | SBS-022: Verify protected demo actions with background Turnstile |
| 6 | `f76082ace498c0c639077ab94f3cf21a60e8141f` | SBS-024: Prepare currency-safe visitor HubSpot booking exports |
| 7 | `778380df43be1e9e9580d02653cd5f92cbd25257` | SBS-025: Keep private environment small and own fixed policy in backend code |
| 8 | `d62811def454c4ec75e27c39aef55a9d12451fd5` | SBS-023: Offer useful chat replies and reviewed appointment management |
| 9 | `d7999e5da4e6aa234cec2adf28f66abb26f42a4b` | SBS-010: Refresh isolated Linux acceptance for the complete assistant snapshot |
|10|Read from `git log` after commit|SBS-025: Record continuation evidence and the authorized pre-audit checkpoint|


## SBS-026 quality commit allocation —24 October2026

The owner's current AFK audit/local Git authorization applies after the clean prior checkpoint13f608b. Plan and execute/validate evidence: SBS-026. This is the quality phase only; commit it before starting the separate security audit.75 Node tests/types and final source-fresh Linux44-request/291-assertion stack checks pass. The unchanged backend retains its326-test baseline. Preserve current private env, running services and motion; no external operation/push is authorized.

### Quality commit 1: SBS-026: Reuse scoped date formatters and unify source dialog ownership

- `apps/frontend/components/guide-reader-dialog.tsx`
- `apps/frontend/components/source-reader.tsx`
- `apps/frontend/components/staff-calendar.tsx`
- `apps/frontend/components/week-calendar.tsx`
- `apps/frontend/lib/api.ts`
- `apps/frontend/lib/business-overview-data.ts`
- `apps/frontend/lib/calendar-metrics.ts`
- `apps/frontend/lib/timezone.ts`
- `scripts/date-readers.test.mjs`

### Quality commit 2: SBS-010: Refresh isolated Linux evidence after quality remedies

- `infra/release-evidence.json`

### Quality commit 3: SBS-026: Record quality audit evidence and AFK workflow decisions

- `AGENTS.md`
- `README.md`
- `docs/CHOREOGRAPH.md`
- `docs/tickets/COMMIT_PLAN.md`
- `docs/tickets/README.md`
- `docs/tickets/SBS-026-pre-sharing-quality.md`

Inspect explicit stage allocation, raw-byte/source equality, known-private-value exclusions and staged diff before each local commit. Final docs record preceding hashes after they exist; its own identity is read from Git.

Quality preceding commits: `e59c247c1d565ad6a903cf289da14f10ff04b412` (SBS-026: Reuse scoped date formatters and unify source dialog ownership), `742bb0b8f2ecf07d43705f699489b679034310b8` (SBS-010: Refresh isolated Linux evidence after quality remedies). Final documentation identity is read from Git.


## SBS-026 supplemental CI commit allocation -24 October2026

The current direct owner authorization includes local staging and commits. Reopened Q-026-03 was planned before source edits, reproduced by the actual workflow-generator/loader test and repaired with26 focused tests/Ruff passing. No image inputs changed; existing Linux receipt remains source-fresh. This local commit resumes quality before security completion.

| File | Owning purpose |
|---|---|
| `.github/workflows/ci.yml` | Replace the two legacy-profile locations with fake=true/paid=false. |
| `apps/backend/tests/test_runtime_configuration.py` | Execute actual CI generator in temporary checkout and verify real loaders remain offline/fake. |
| `docs/tickets/SBS-026-pre-sharing-quality.md` | Supplemental plan, failure proof, repair and read-only validation. |
| `docs/tickets/COMMIT_PLAN.md` | Exact file allocation/current local Git authority. |
| `docs/CHOREOGRAPH.md` | Canonical AFK decision, quality reopening/completion and preserved security prompt. |

Subject: `SBS-026: Keep no-key CI compatible with the two-switch configuration`

Stage only these paths, verify staged source bytes/private-value exclusion and whitespace, commit, then verify the entire index/worktree empty before restarting the security audit. No provider/account/cloud/remote Git action.


## SBS-027 audit/handoff documentation allocation -24 October2026

Current direct owner request authorizes local stage/commit after file-level planning and AFK security selection. Security audit stayed source-read-only. Its concrete reports received explicit provisional AFK no-fixes; phase11 is skipped because no new substantial actionable local security defect was confirmed, not because a local failure was relabelled external. Source baseline96cf2b5 was completely clean before the audit resumed. Prior ten checkpoint and four quality commits remain separate.

One cohesive documentation commit, subject `SBS-027: Record renewed security audit and bounded AFK handoff`:

| Exact file | Responsibility |
|---|---|
| `docs/security/SECURITY_REVIEW.md` | Full current STRIDE/general review, official advisory comparisons, actual evidence/limits, investigated non-findings and future-edit guards; dated history preserved. |
| `docs/security/SECURITY_OVERVIEW.html` | Concise ranked PM findings/controls/evidence and external acceptance, with prior review collapsed as history. |
| `docs/tickets/SBS-027-security-review.md` | Audit-only plan, exact scope/authority, results, read-only validation and honest HTML-preview limit. |
| `docs/tickets/README.md` | Current audit packet/queue result. |
| `docs/CHOREOGRAPH.md` | Current checkpoint and canonical complete prompts, provisional AFK no-fixes/skip, material deferrals and complete_local handoff. |
| `docs/tickets/COMMIT_PLAN.md` | This exact allocation and current Git authority. |

Validation:326 full backend tests plus26 focused config/setup checks including the new actual CI-generator regression;75 Node/no skips; Ruff; pip check;192-input release freshness retaining actual Linux44 HTTP/291 assertions;373-file bounded current-tree private-value scan;112 npm HTTPS/integrity entries and93 Python exact pins; static HTML nesting/relative targets; owned frontend/API/runner still running without restart. No image input changed during this report-only security phase. HTML local-file browser preview was policy-blocked and not bypassed; no browser-rendered report check is claimed. No paid/account/provider/cloud/remote scanner metadata export/push operation.

Stage explicit paths only after final settled read-only review. Verify staged/worktree byte equality, known private-value absence and CRLF-aware whitespace; commit and verify the entire worktree/index empty. Final verified commit/clean receipt is retained in ignored runtime evidence and reported at handoff to avoid an endless post-commit documentation change. Human/native/hosted/scanning acceptance remains outstanding.


## Owner current-work checkpoint —25 October2026

The owner directly requested a file-level plan and local staging/commits for **all current work**. Baseline: `632d335f1eac657f9e2fec0d13b9295a33ad206a` on `main`. This allocation covers75 existing Git-visible paths plus this plan update: **76 unique files in eight ordered commits**. Each path is assigned once. Shared multi-feature files are kept whole; later groups depend on the earlier contract/configuration/parent-callback groups. No push, provider/account action, app restart or private env/runtime inclusion is authorized by this Git checkpoint.

Before each commit, stage only its exact paths; verify staged allocation, byte equality with the reviewed working file, snapshot hashes, private-value exclusion and CRLF-aware whitespace. Preserve the owner's running real-profile services/data. Tests use fake/injected providers and isolated storage. Final settled checks and actual commit identities are recorded below before the last documentation commit; its own identity and the final clean index/worktree are read from Git to avoid a post-commit edit loop.

### Commit 1: SBS-025: Preserve unquoted local environment values

Keep the owner's bare env syntax and reject ambiguous values before writing configuration.

| Exact file | Responsibility |
| --- | --- |
| `scripts/setup.py` | Render bare values and reject unsafe loader interpretations. |
| `apps/backend/tests/test_local_setup.py` | Verify preservation and refusal cases across setup. |
| `docs/tickets/SBS-025-local-configuration.md` | Own the no-wrapping-quotes correction and actual checks. |

### Commit 2: SBS-028: Isolate owner-local manual AI and HubSpot policies

Support separately authorized local manual use while retaining finite automated/hosted acceptance, durable accounting and visitor consent.

| Exact file | Responsibility |
| --- | --- |
| `apps/backend/choreograph/acceptance.py` | Reject unbounded manual policies in automated acceptance. |
| `apps/backend/choreograph/ai_admission.py` | Represent manual AI accounting and retain request fences. |
| `apps/backend/choreograph/ai_config.py` | Parse explicit manual and finite AI policies separately. |
| `apps/backend/choreograph/composition.py` | Handle an intentionally absent manual expiry. |
| `apps/backend/choreograph/crm_admission.py` | Account for separately authorized manual CRM use. |
| `apps/backend/choreograph/crm_composition.py` | Keep finite expiry checks separate from manual CRM. |
| `apps/backend/choreograph/crm_config.py` | Compose registered OAuth transport and scoped allowances. |
| `apps/backend/choreograph/models.py` | Allow an explicit nullable manual AI grant expiry. |
| `apps/backend/choreograph/readiness.py` | Diagnose local manual policies without provider calls. |
| `apps/backend/choreograph/runtime_config.py` | Own public OAuth identifiers and explicit local policy constants. |
| `apps/backend/choreograph/settings.py` | Restrict manual loaders to the owned loopback stack. |
| `apps/backend/migrations/versions/0011_manual_ai.py` | Migrate nullable expiry with a guarded downgrade. |
| `apps/backend/tests/test_manual_ai.py` | Check accounting, loader isolation and finite acceptance. |
| `apps/backend/tests/test_manual_crm.py` | Check manual CRM accounting and independent finite acceptance. |
| `apps/backend/tests/test_runtime_configuration.py` | Make missing-registration cases independent of the registered app. |
| `docs/tickets/SBS-028-owner-manual-ai.md` | Record direct owner authorization and local-only evidence. |
| `docs/tickets/SBS-024-hubspot-free-readiness.md` | Own actual OAuth registration/manual readiness and limitations. |
| `infra/README.md` | Explain operator registration, local consent and native verification. |

### Commit 3: SBS-023: Add upcoming scheduling and scoped guest verification

Keep the shared API/service/interaction changes together with their generated contracts and narrow browser bridge. These whole files contain both scheduling and verification changes.

| Exact file | Responsibility |
| --- | --- |
| `apps/backend/choreograph/api.py` | Bind recent verification receipts and rolling guest/request endpoints. |
| `apps/backend/choreograph/assistant.py` | Route the explicit reserve shortcut to authoritative availability. |
| `apps/backend/choreograph/contracts.py` | Add the reserve card and preview availability schema. |
| `apps/backend/choreograph/domain.py` | Evaluate bounded rolling windows and backward navigation. |
| `apps/backend/choreograph/interactions.py` | Preserve interaction guards around deterministic scheduling and verification. |
| `apps/backend/choreograph/service.py` | Share exact/preview availability and safe rescheduling queries. |
| `apps/backend/choreograph/verification.py` | Sign finite session-bound human receipts without caching proof tokens. |
| `apps/backend/tests/test_verification.py` | Retain the explicit missing-proof boundary regression. |
| `apps/backend/tests/test_reservation_shortcut.py` | Verify fake/live-injected discovery and unchanged booking authority. |
| `apps/backend/tests/test_availability_windows.py` | Check local dates, duration and scoped rescheduling. |
| `apps/backend/tests/test_verification_session.py` | Check expiry, tampering, scope and fresh-proof requirements. |
| `apps/frontend/app/api/demo/[...path]/route.ts` | Forward only approved rolling queries and guest/receipt cookies. |
| `apps/frontend/lib/generated/api.d.ts` | Synchronize generated browser types with the API schema. |
| `apps/frontend/lib/generated/openapi.json` | Record the authoritative generated schema. |
| `apps/frontend/components/use-guest.ts` | Let the server validate the receipt before asking for another proof. |
| `apps/frontend/components/verification-provider.tsx` | Warm public configuration/script without minting authorization. |
| `scripts/verification-session.test.mjs` | Exercise command retry, cancellation and the actual cookie bridge. |

### Commit 4: SBS-023: Reveal upcoming appointments and review feedback in chat

Deliver the reservation pin, shared upcoming picker and immediate saving/review reveal. The parent also prepares the async Business callback used by the next commit.

| Exact file | Responsibility |
| --- | --- |
| `apps/frontend/app/demo/availability.css` | Keep rolling dates horizontally reachable in the existing card. |
| `apps/frontend/app/demo/customer-chat.css` | Style the pinned shortcut, loading/error review and focus. |
| `apps/frontend/components/chat-review.tsx` | Show saving/error state before enabling explicit booking review. |
| `apps/frontend/components/chat-workspace.tsx` | Pin reservation discovery and reveal the selected-time review. |
| `apps/frontend/components/use-chat-scroll.ts` | Target the review smoothly with cancellation and resize tracking. |
| `apps/frontend/components/week-calendar.tsx` | Share upcoming windows and select an actual fitting day. |
| `apps/frontend/components/workspace-client.tsx` | Return real mutation promises to Customer and Business handlers. |
| `apps/frontend/lib/chat-questions.ts` | Keep a stable generic reservation shortcut. |
| `apps/frontend/lib/chat-sources.ts` | Anchor review beside the current reserve/calendar message. |
| `apps/frontend/lib/availability-window.ts` | Normalize requested dates and reject stale selections. |
| `scripts/availability-window.test.mjs` | Exercise restored Sunday, timezone and navigation behavior. |
| `scripts/chat-review-flow.test.mjs` | Exercise delayed/failing saves and unchanged explicit booking. |
| `scripts/chat-review-scroll.test.mjs` | Exercise intermediate scrolling, focus, cancellation and cleanup. |
| `scripts/reservation-shortcut.test.mjs` | Exercise pin reachability, shared picker and draft-only edits. |

### Commit 5: SBS-023: Confirm Business booking actions in branded dialogs

Replace booking lifecycle browser prompts with the shared animated glass dialog and preserve exact reviewed commands.

| Exact file | Responsibility |
| --- | --- |
| `apps/frontend/app/demo/booking-management.css` | Size the compact confirmation and style error/focus feedback. |
| `apps/frontend/components/business-review.tsx` | Open app dialogs bound to the reviewed record/revision. |
| `apps/frontend/components/booking-action-dialog.tsx` | Show explicit completion/cancel/decline with pending/failure guards. |
| `apps/frontend/components/expanding-dialog.tsx` | Support contextual focus fallback and a focusable modal panel. |
| `apps/frontend/components/use-dialog-focus.ts` | Keep keyboard focus trapped while every saving action is disabled. |
| `scripts/booking-action-dialog.test.mjs` | Verify explicit dispatch, stale records, duplicate guards and focus. |

### Commit 6: SBS-016: Align entry layouts and canonical local demo navigation

Match the shared entry spacing/provider cards, place feedback in context and repair the old-host CRM skip failure.

| Exact file | Responsibility |
| --- | --- |
| `apps/frontend/app/demo/welcome.css` | Share entry padding, transition and card feedback styles. |
| `apps/frontend/app/materials.css` | Use a reusable inline provider wordmark treatment. |
| `apps/frontend/components/crm-controls.tsx` | Place provider notes/feedback before a bottom-aligned CTA. |
| `apps/frontend/components/entry-client.tsx` | Keep entry scroll/layout/copy and route feedback consistent. |
| `apps/frontend/next.config.ts` | Redirect only old local demo hosts to the configured canonical host. |
| `scripts/entry-origin.test.mjs` | Check host matching and strict-origin skip behavior. |

### Commit 7: SBS-008: Start hero motion after font and frame preparation

Remove the visible entrance hold while preserving the approved headline animation and other landing motion.

| Exact file | Responsibility |
| --- | --- |
| `apps/frontend/app/landing-hero.css` | Define the prepared native hero entrance. |
| `apps/frontend/components/landing-motion.tsx` | Wait for font readiness and preparation frames before revealing text. |
| `scripts/hero-entrance.test.mjs` | Check readiness, cancellation and fallback behavior. |
| `docs/tickets/SBS-008-responsive-flow.md` | Own the actual entrance investigation and scoped results. |

### Commit 8: SBS-028: Record the owner-authorized current-work checkpoint

Record current instructions, consolidated evidence, exact file allocation and preceding commit identities without claiming unperformed native/hosted acceptance.

| Exact file | Responsibility |
| --- | --- |
| `AGENTS.md` | Preserve accepted owner configuration and interaction corrections. |
| `README.md` | Summarize local manual policy and actual HubSpot setup. |
| `docs/CHOREOGRAPH.md` | Own the current architecture/product checkpoint and evidence boundaries. |
| `docs/tickets/README.md` | Register the manual-use continuation in the ticket queue. |
| `docs/tickets/SBS-016-guided-workspace.md` | Record shared entry and local navigation corrections. |
| `docs/tickets/SBS-022-turnstile-live-controls.md` | Record finite verification reuse and current limitations. |
| `docs/tickets/SBS-023-assistant-quality.md` | Own reservation, calendar, review and confirmation evidence. |
| `docs/tickets/COMMIT_PLAN.md` | Own this exact allocation, validation and commit execution record. |

### Settled validation and execution

All settled gates pass before staging:

- **366 backend tests** on actual isolated PostgreSQL with fake/injected providers (`.runtime/checkpoint-20261025-backend.log`). No running app database or provider credential was used as a test fixture.
- **122 Node tests**, no failures/skips, including the scoped lifecycle fixtures (`.runtime/checkpoint-20261025-node.log`). Frontend types, configured Ruff, pip dependency compatibility and regenerated Pydantic/OpenAPI browser contracts pass.
- **Actual isolated Linux production builds and full-stack smoke:**44 HTTP requests/291 assertions, migrations/downgrade/remigration, six prepared fake sources, actual PDF/private replacement, booking/refresh/CRM skip/worker authorization and owned-resource cleanup pass. No host ports or real provider/account operations. Receipt log: `.runtime/checkpoint-20261025-linux.log`.
- The smoke source exactly matches the current **195 image inputs**, SHA256 `f9fc9254884c5e7e7adddae9dd640740d4fa9642c45ba4b65249df45a89fa940`. Frontend image `sha256:3f2a6df85c66a133af093318252912f3008c4c96debb6fa3375b0f4ace020c36` runs as `node`; backend `sha256:7a0074bb85ee7804a99ddc52fe922b8be8c64f04d655e93cf63bb6a6f1f1a369` runs as `10001:10001`. This was `--no-receipt`: the older `infra/release-evidence.json` remains historical/stale for these sources and was not relabelled current.
- The exact76-file allocation has no omissions or duplicate paths. A private-value scan against18 raw/encoded variants of the owning app's current credentials finds **zero matches**. Private env/runtime paths remain ignored. Before each commit, the helper separately checks the actual staged blobs against the reviewed raw working bytes/snapshot and CRLF-aware whitespace. No private values are printed or placed in Git.

No new independent security audit, live-provider/Cloudflare/native HubSpot acceptance, physical-device visual acceptance or hosted deployment is claimed. The earlier standalone visual-preview browser URL rejection is not bypassed by this Git checkpoint. Current local service mode/keys/data and siblings are preserved; no restart or push occurs.

Observed commit identities are appended after the first seven groups actually commit. The final documentation commit's own identity and the final entirely clean worktree/index are read from Git and retained in ignored runtime evidence, avoiding an endless post-commit documentation edit.

### Current-work checkpoint execution record

The first seven commits below were created after their individual exact staged-allocation, raw-byte/snapshot,18-variant private-value and CRLF-aware whitespace checks passed. No private values were found. The index was empty after each commit.

| Group | Actual local commit | Subject | Files |
| --- | --- | --- | --- |
| 1 | `5c84ace3c4d1565ab38d5a7906a5d83fb886b992` | SBS-025: Preserve unquoted local environment values | 3 |
| 2 | `08f07600762f1e40474442ba6ef9f09c46a081b4` | SBS-028: Isolate owner-local manual AI and HubSpot policies | 18 |
| 3 | `acbceabcac36fa7b15cbb91c1a5c0e9cb1ba7c48` | SBS-023: Add upcoming scheduling and scoped guest verification | 17 |
| 4 | `10a74f5d798d52d2848bfc1d1d13705033a56cd6` | SBS-023: Reveal upcoming appointments and review feedback in chat | 14 |
| 5 | `907db7c3eefe6aca5c5dc8712c44bfe462e2f8e9` | SBS-023: Confirm Business booking actions in branded dialogs | 6 |
| 6 | `67edcfd67839ad70443eeaa31d9d641fcd93e3e2` | SBS-016: Align entry layouts and canonical local demo navigation | 6 |
| 7 | `cbadaeb90c992aa7595f516b7129ecb59a0d18d2` | SBS-008: Start hero motion after font and frame preparation | 4 |
| 8 | Read from `git log` after this documentation commit | SBS-028: Record the owner-authorized current-work checkpoint | 8 |

All76 allocated files are covered exactly once. The final commit is checked against the remaining eight documentation paths; its own SHA, all eight commit parents/subjects/file allocations, private-path exclusions and final empty worktree/index are verified from Git and retained in ignored `.runtime/checkpoint-20261025-final.json`. No post-commit tracked-file receipt edit is needed.


## Native HubSpot / shared UI / deployment checkpoint —25 October2026

The latest direct owner request explicitly authorizes a file-level plan, multiple ticket-prefixed local commits and staging/committing all current work. No push is requested. Baseline is `6019c8b3343d54c99a2ec97b3851b9d24e8ce65e`, with an empty index. Existing real-mode services, configuration, data and sibling apps remain untouched by this Git operation.

The eleven groups below preserve useful feature/repair boundaries. Four shared files appear in more than one group; explicitly described staged snapshots split their changes without editing the working files. Every other path is allocated once. There are **38 distinct files /43 commit-file allocations**, including this plan. Partial staged Python snapshots parse successfully.

### Commit 1: SBS-030: Share branded confirmation and keyboard safeguards

Centralize guarded asynchronous confirmations and migrate Business booking actions to the shared animated dialog.

| Exact file | Allocation |
| --- | --- |
| `apps/frontend/components/confirmation-dialog.tsx` | Reusable animated async confirmation with duplicate, failure, exit and focus guards. |
| `apps/frontend/components/booking-action-dialog.tsx` | Migrate reviewed booking completion/cancel/decline to the shared dialog. |
| `apps/frontend/components/use-dialog-focus.ts` | Yield keyboard handling to the top-layer human-check dialog. |
| `apps/frontend/app/demo/booking-management.css` | Shared confirmation sizing and inline failure styling. |
| `scripts/booking-action-dialog.test.mjs` | Exercise migrated action binding, confirmation and focus behavior. |

### Commit 2: SBS-024: Verify USD through account details and account identity

Repair unavailable currency lookup, distinguish unreadable currency from mismatch and bind the response to the selected account.

| Exact file | Allocation |
| --- | --- |
| `apps/backend/choreograph/hubspot.py` | Read USD company currency from account details and verify portal identity. |
| `apps/backend/choreograph/crm.py` | Only setup currency notices; contact construction remains for commit4. |
| `apps/backend/tests/test_crm.py` | Align the injected adapter fixture with the supported account-details schema. |
| `apps/backend/tests/test_hubspot_readiness.py` | Cover USD mismatch/unavailable/account change and read-only route restrictions. |
| `apps/backend/tests/test_live_crm.py` | Only the account-details currency fixture; later tests stay for commits3/4. |

### Commit 3: SBS-024: Preserve cleanup progress when uninstall becomes blocked

Keep completed cleanup receipts honest when a competing active workspace prevents uninstall; cover explicit native removal separately.

| Exact file | Allocation |
| --- | --- |
| `apps/backend/choreograph/jobs.py` | Only cleanup-progress/shared-use failure handling; contact payload stays for commit4. |
| `apps/backend/tests/test_jobs.py` | Reproduce a concurrent shared installation appearing after owned-record cleanup. |
| `apps/backend/tests/test_live_crm.py` | Currency fixture plus injected native uninstall/helper changes; export/readback additions stay for commit4. |

### Commit 4: SBS-024: Export demo contacts without rejected synthetic email

Use the existing unique app-owned identity without email; reproduce INVALID_EMAIL and verify same-deal lifecycle/readback failures.

| Exact file | Allocation |
| --- | --- |
| `apps/backend/choreograph/crm.py` | Omit rejected synthetic email and keep the consent preview truthful. |
| `apps/backend/choreograph/jobs.py` | Build no-email contact payloads while retaining unique identity and readback. |
| `apps/backend/tests/test_live_crm.py` | Add email validation and same-deal lifecycle/mismatch/association regressions. |

### Commit 5: SBS-024: Simplify connection actions and complete sharing onboarding

Expose one confirmed Uninstall action, inline setup feedback and automatic post-consent entry with tracked finite navigation recovery.

| Exact file | Allocation |
| --- | --- |
| `apps/frontend/components/crm-controls.tsx` | Single confirmed uninstall, optional cleanup, concise consent, setup/progress/recovery feedback. |
| `apps/frontend/app/demo/workspace.css` | Style inline setup errors and tracked entry progress. |
| `apps/frontend/components/workspace-client.tsx` | Only dashboard manageConnection wiring; Reset/navigation changes stay for commit6. |
| `apps/frontend/components/entry-client.tsx` | Enter only after server-confirmed sharing; finite document-navigation recovery. |
| `scripts/hubspot-uninstall.test.mjs` | Exercise uninstall, verify/sharing locks, errors, data review and bounded navigation. |

### Commit 6: SBS-030: Confirm Reset and return to connection choices

Replace the last browser prompt, preserve asynchronous reset acknowledgement and reuse the existing connection-entry transition.

| Exact file | Allocation |
| --- | --- |
| `apps/frontend/components/workspace-controls.tsx` | Replace native Reset confirmation with the shared guarded dialog. |
| `apps/frontend/components/business-sidebar.tsx` | Support async Reset and close the mobile drawer before confirmation. |
| `apps/frontend/components/workspace-client.tsx` | Acknowledge successful Reset before routing to the existing connection-choice entry. |
| `apps/frontend/app/demo/page.tsx` | Recognize the explicit connection-choice entry step. |
| `scripts/confirmation-reset.test.mjs` | Cover reset confirmation, cancellation, uncertain failures and correct route acknowledgement. |
| `scripts/native-prompts.test.mjs` | Prevent native alert/confirm/prompt calls throughout authored app source. |
| `docs/tickets/SBS-030-shared-confirmation.md` | Own Reset/shared-dialog requirements, implementation and actual evidence limitations. |

### Commit 7: SBS-023: Guide availability replies with in-card choices

Explain missing cleaning/home details, send selected-date shortcuts through ordinary chat and retain the calendar during clarification.

| Exact file | Allocation |
| --- | --- |
| `apps/frontend/app/demo/availability.css` | Fit reply guidance and compact in-card controls on narrow preview calendars. |
| `apps/frontend/components/chat-workspace.tsx` | Send in-card choices through ordinary chat and keep requested-date clarification visible. |
| `apps/frontend/components/week-calendar.tsx` | Expose missing-detail reply choices scoped to the selected available date. |
| `apps/frontend/lib/availability-copy.ts` | Derive service/bedroom prompts/examples without inventing defaults. |
| `scripts/availability-window.test.mjs` | Use the shared reply helper in rolling-calendar fixtures. |
| `scripts/reservation-shortcut.test.mjs` | Cover typed drafts, selected dates, pending/read-only guards and no automatic booking. |
| `docs/tickets/SBS-023-assistant-quality.md` | Record current interactive availability changes and offline checks. |

### Commit 8: SBS-029: Prepare a reviewed Cloud Run spending cap example

Provide the separate opt-in USD5 Cloud Run cap configuration without applying it or misrepresenting notification-only alerts as caps.

| Exact file | Allocation |
| --- | --- |
| `infra/budget-cloud-run-cap.example.json` | Reviewed opt-in cap example only; no activation or actual alert modification. |

### Commit 9: SBS-029: Document deployment budgets secrets and private database steps

Record the existing project, actual notification-only budgets and empty exact-name secrets; document costs/private topology and remaining release gates.

| Exact file | Allocation |
| --- | --- |
| `docs/tickets/SBS-029-deployment-readiness.md` | Own real budget/empty-secret receipts, private deployment plan and open gates. |
| `infra/README.md` | Exact-name secret guidance, costs/private topology/CLI steps and current HubSpot test operations. |

### Commit 10: SBS-024: Record native booking verification and expiry cleanup

Consolidate owner-account diagnostics, successful scoped export and immediate automatic expiry deletion without claiming an active native record.

| Exact file | Allocation |
| --- | --- |
| `docs/tickets/SBS-024-hubspot-free-readiness.md` | Record registration/onboarding/uninstall repairs, native booking readback and subsequent expiry. |

### Commit 11: SBS-028: Record the approved integration and UX checkpoint

Preserve owner instructions, current evidence boundaries, execution queue and this exact file/hunk commit allocation.

| Exact file | Allocation |
| --- | --- |
| `AGENTS.md` | Preserve the owner's permanent shared-dialog/native-prompt restriction. |
| `docs/CHOREOGRAPH.md` | Reconcile current product/evidence state with retained historical decisions. |
| `docs/tickets/README.md` | Update the owning ticket statuses and register the new continuation packets. |
| `docs/tickets/COMMIT_PLAN.md` | This exact approved file/hunk allocation, checks and execution safeguards. |

### Settled checks and execution safeguards

- **376 backend tests passed in191.51seconds**, with fake/injected external providers and actual isolated PostgreSQL (`.runtime/checkpoint-hubspot-backend.log`). No real app data/provider was used as a test fixture.
- **160 Node tests passed**, zero failures/skips (`.runtime/checkpoint-hubspot-node.log`), including the owned process fixture. Frontend types and configured Ruff for the full backend pass. Dependencies/contracts did not change; no new dependency installation or provider test was performed.
- All38 modified/new paths exactly match the plan; index is empty before staging. The five partial snapshots were checked against their stated boundaries and Python snapshots parse. Keeping the entry consumer and CRM prop change in the same commit preserves their interface; Reset producer/caller changes share commit6.
- Prior implementation receipts distinguish65 focused CRM checks, actual native create/readback and automatic expiry cleanup from this no-provider checkpoint. Frontend/API/runner remain owned/running; no service restart or app operation is needed for Git.
- Read-only checkpoint review covers the current tracked/untracked source/tests/docs against baseline6019c8b, including four shared-file staging sequences. No actionable allocation/implementation finding remains; original browser/native lifecycle/uninstall/hosted acceptance gaps remain documented. The known-value scan and exact staged-byte verification are enforced before every commit. Checks above preceded the read-only review; no new implementation/test/provider action occurred during it.

The image input fingerprint is `6ba812ef25ae75ef3de6d3b16acffa06653df644f9e53e3a2db30f9d711c50b7` across196 files. Older Linux smoke/image receipts are historical and no fresh hosted/build acceptance is asserted by this checkpoint. Native proof is a successful contact/deal/association readback followed by the existing two-hour expiry cleanup; that deal is no longer active. Other native lifecycle/uninstall and physical-device visual acceptance remain open.

Before staging, freeze exact working bytes and each intermediate staged snapshot; verify the38-file plan exactly covers tracked/untracked changes and the index is empty. Scan both final source and actual staged blobs against raw/URL-encoded/base64 variants of only this app's known private values, without printing them. Reject private runtime/env/cache paths, unexpected HEAD changes, unplanned staged paths, byte changes after review and whitespace errors. Stage explicit paths only.

Each commit is verified against its exact planned paths, message and expected staged bytes, with an empty index afterward. An ignored `.runtime/checkpoint-hubspot-commits.json` records actual identities as they are created. The final clean-tree/parent-chain/file coverage verification is retained in `.runtime/checkpoint-hubspot-final.json`, avoiding a post-commit tracked receipt edit. No provider/cloud call, deployment, app restart or push is performed as part of staging/committing.
