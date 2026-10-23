# SBS-010 — Prepare local Linux release and cloud files

## Current continuation receipt — SBS-012–015 / final phase12

Final source `c803fbcd8d491d794dc3504bd08d0da056f5521363fcdd8e1fdaa73f7c7251b4` has107 image inputs. Actual non-root Linux/amd64 builds and owned isolated smoke pass: empty migration0010 round-trip, explicit fake sample preparation, schema/profile/six-source readiness, health-only bootstrap without secrets,24 HTTP requests/180 assertions, genuine skip/no outbox, private worker rejection, SQL maintenance and owned-resource removal. `release-fingerprint --check` matches. Frontend image `sha256:1bdd91e937cd7098271a1c2e93eefbf9925dda3cbd3b2bcfd118b9ffda103ddd`; backend `sha256:9f51268707052e7e91e63ed3ab693a24379a43e87490c1c576db60cf48e48fb5`. Exact timestamp/input hashes are in `infra/release-evidence.json`; older receipts below are historical.

Settled227 backend/15 Node checks, configured Ruff, pip compatibility, contracts/types, Windows production build and affected actual responsive checks pass. Source includes implemented live AI/CRM/Tasks/dispatcher/readiness/acceptance/cloud rendering; defaults remain fake and real operation is unperformed. Local services are restored hidden with retained data preserved; siblings were untouched. SBS-011's owner-input table and infra/README own the next authorized lane. No deployment, spending, real account/keys, scanner export or Git write occurred.

Status: **Complete local**
Owning phase: **07-build; refresh at 12-handoff**  
Depends on: **SBS-008**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

Prepare reproducible concrete local release files for Next/FastAPI/PostgreSQL. This authorizes local packaging checks, not Cloud SQL provisioning, Cloud Run deployment, registry push, real secrets, OAuth registration or publication.

## Implementation scope

1. Create supported pinned Linux frontend/backend Docker builds, narrow contexts/ignore rules and content-free health/readiness. Prove actual Linux builds separately from host builds where available.

2. Prepare no-key CI for contracts/unit/isolated pgvector DB/build gates; no push or claim of actual hosted CI.

3. Prepare private API/service identity, authenticated queue OIDC, bounded Cloud SQL pools and Secret Manager references using explicit examples/unconfigured identifiers. No unauthenticated maintenance or X-CloudTasks-header trust.

4. Document verified local/release commands, migrations/rollback/retention and non-secret source/build fingerprints. Refresh proof after later quality/security source changes.

5. Leave region/instance/exact costs, funded providers and unattended hosted maintenance as explicit external decisions; do not add Cloud Scheduler silently.

## File allocation and cohesive commit plan

infra/Dockerfile.frontend, Dockerfile.backend, contexts/release examples; CI; scripts/release verification; actual README/AGENTS operations and narrow distinct operational docs if needed. Allocation: packaging/CI then current release evidence.

## Acceptance criteria

- [x] Concrete local builds/inputs are reviewable and secret-free
- [x] host/Linux/CI/deployed claims are separate
- [x] finite least-privilege config is prepared without provisioning
- [x] final handoff identifies source/commands and pending external/rollback work.

## Meaningful verification

Actual Docker Linux builds and bounded local smoke, CI/config/build-context checks and fingerprint freshness. No registry/cloud/publication action.

## Precision references

- [Blueprint: 101-realfake-providers-and-localdeployed-execution](../CHOREOGRAPH.md#101-realfake-providers-and-localdeployed-execution)
- [Blueprint: 15-cost-plan-and-spending-boundaries](../CHOREOGRAPH.md#15-cost-plan-and-spending-boundaries)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Completed 22 October 2026. Pinned official Node 24.19.0 and Python 3.11.17 Linux images build from explicit inputs with the repository locks. The Linux build exposed the previously implicit setuptools dependency; requirements now pin 84.2.1 and Linux pip check passes. Runtime images use non-root users. Next standalone tracing preserves the monorepo layout, local font, PDF.js assets and sample PDF. The release composition reads explicitly supplied environment only, exposes content-free probes and separates guest API, authenticated worker, explicit migrations/sample preparation and one-shot maintenance. Settings reject libpq query overrides that could bypass test-host isolation. Frontend Google identity is opt-in, bounded/cached and never falls back after failure; plain HTTP destinations are limited to loopback or the isolated Docker alias.

`node scripts/release-smoke.mjs` built and tested the exact source inputs on a unique internal Docker network, with no published ports and a disposable PostgreSQL/pgvector database. Actual checks: empty-schema upgrade→explicit downgrade→upgrade, once-only fake knowledge preparation, API/frontend readiness, 24 HTTP requests / 180 assertions across real source bytes/passage/page, exact $185/270-minute busy-date quote, selection without reservation, explicit submission/approval, shared booking refresh, genuine CRM skip with zero outbox rows, private TXT replacement/re-ask and guest/manifest isolation. Static self-hosted assets, bridge rejection, private worker unauthenticated denial/absent guest routes and one-shot maintenance passed. All uniquely labelled containers/network were removed; development services/volume were preserved. Immutable image IDs and 83-file input hashes are in [release evidence](../../infra/release-evidence.json); `node scripts/release-fingerprint.mjs --check` passes. Refresh after subsequent source fixes.

Settled host verification: **70 backend tests passed**, with one existing PDF fixture deprecation warning owned by SBS-009A; **8 lifecycle/bridge/identity tests passed**, including the Windows no-visible-window regression. Linux frontend production build/type checks passed. The owned frontend was separately stopped, its generated PDF worker moved aside, and startup regenerated identical bytes before readiness; the backup was removed and API/runner remained owned/running. No extra listener was introduced.

Read-only validation caught and independently confirmed/fixed database query routing, missing fresh-database sample preparation, remote plaintext API configuration, shared mutable image-tag evidence and create-response-loss cleanup. Revalidation found no remaining actionable issue within this ticket. Cloud YAML/JSON/CI structures, placeholder secret references and role/URL/OIDC agreement were inspected; numeric placeholder types were checked after substitution. [Operations runbook](../../infra/README.md) owns commands, IAM/pool limits, retention and rollback. The no-key workflow is prepared, not hosted-run evidence. Repository-wide lint/quality/security remain subsequent phases.

External limits: no registry push, hosted CI run, Cloud Run/SQL/Tasks/IAM/Secret Manager provisioning or acceptance, paid embeddings/answering, real HubSpot flow or owner runnable acceptance. Real Cloud Tasks enqueue transport and reliable unattended recovery/expiry invocation remain explicitly unimplemented deployment prerequisites. Cloud examples are restricted fake QA candidates with unresolved identifiers/costs, not deploy-ready public service. The empty disposable downgrade check is not proof of safe populated-data rollback. No Git writes occurred.

Subsequent phase 08 source/reader optimizations intentionally invalidate this milestone's image-input fingerprint. Preserve this historical result; refresh the Linux smoke/receipt after final quality/security fixes at phase 12 rather than treating the earlier image as proof for changed source.

## First phase 12 refresh — before the final local admission refinement

After performance, quality and all selected security changes settled, `node scripts/release-smoke.mjs` passed again at source **`2e1c01c2af3e0754995750caaaa6d31fc5e4884d46e5cbfb5b58cef32f118d41`** (83 release-input files), recorded at **16:35:28 UTC**. `node scripts/release-fingerprint.mjs --check` verified the exact file hashes. Actual Linux/amd64 images: frontend **`sha256:4cdd05628d9d15babb2d3456876602a58e324558a9db675b404cced3dec67aea`**, backend **`sha256:0f19675bd5227f1dee089b3a8dab934e9e343497394fc1a6bb25d30d540f4114`**. The non-root image IDs, no-secret inputs and full checks are in the refreshed receipt.

All original bounded checks passed on the final source: empty-schema upgrade/downgrade/remigrate, explicit once-only fake sample preparation, actual PDF/passage/page and private TXT replacement/isolation, exact quote/busy-date→selection→submission→approval/shared-calendar refresh, genuine CRM skip with zero outbox, self-hosted assets, private bridge/worker rejection and one-shot maintenance. **24 HTTP requests / 180 assertions** passed. All uniquely owned temporary containers/network were removed; no host ports, persistent development volume, sibling service or cloud/provider was used by the smoke. Host settled gates are now **105 backend / 11 Node tests**, configured Ruff, contract freshness and Windows production build/typecheck; the historical 70/8 count above belongs to the earlier milestone.

No hosted CI/image vulnerability scan/cloud acceptance is inferred from these local builds. Human and real/hosted results remain pending under SBS-011's prepared finite plan. All external limits above still apply; no Git staging/commit/push occurred.


## Final current receipt — after AFK-0018

The original128 local-cap proposal did not fit189 retained pre-remedy development rows. AFK-0018 refined only the shared admission constant and test target to256, preserving data/retention/provider limits; the full105-test backend suite and Ruff passed again. The fresh-browser fake/CRM-skipped source check passed after ownedAPI/runner reload. Unchanged frontend/bridge/contract inputs retain the Windows build/typecheck,11Node checks and contract-freshness proof.

`node scripts/release-smoke.mjs` then passed at final source **`01188ea208d46e60973f37b40579fdac90747528ae64e6765ff0e6eaf0d9523e`** (83inputs), recorded **2026-10-22T16:43:20.464Z**. All24HTTPrequests/180assertions, migration/sample/worker/maintenance/nonroot/ownedcleanup checks passed; no host ports or provider/cloud calls occurred. Current immutable Linux/amd64 image IDs: frontend **`sha256:6ffff2867a23979ee838fad67fed153de309686a6652680a5604a88ef1da620e`**, backend **`sha256:25e1eeb287149d306cc71747ec08a18a71e5fca38e97e24295e18edbb6e5c086`**. `node scripts/release-fingerprint.mjs --check` passed against the refreshed receipt. Earlier2e1c01…/128proposal evidence above is historical, not the current release proof.

## Owner-requested pre-commit CI verification,23 October2026

The owner required running the GitHub Actions checks locally, repairing failures, then documenting/staging a granular ticket-prefixed commit series. This later authorization covers local staging/commits of the current checkpoint; no push/deployment is authorized. Earlier receipts above remain historical.

- The complete backend suite passed **236 tests in107.32s** against an isolated local PostgreSQL/pgvector database. Dependency integrity, the settled Ruff policy, frontend TypeScript and the exact workflow's numeric Cloud Run/WorkerPool template assertions passed. Generated OpenAPI/TypeScript output was already fresh on regeneration. All **47 Node tests** passed, including the Windows hidden-process check; its first sandboxed run lacked CIM permissions, and the approved unsandboxed repeat passed without a source workaround.
- Fixed one actual Ruff error by making the equal-length guide-preview iteration `zip(...,strict=True)`. The frontend Docker builder now copies approved `public` assets before the build; `.dockerignore` continues excluding local environment/runtime/vendor/sample inputs. Without that change, the new icons, collage, logo and guide pages would be missing from the release. CI now selects every `scripts/*.test.mjs`, including the newer status, availability, bubble and UTC regressions. Updated the release smoke's obsolete all-blocked calendar expectation to the persisted mixed history; added actual foreign-guest clear denial, persisted removal without changed bookings, and all17 new public image-asset checks.
- Both pinned Linux/amd64 images built successfully, including a fresh locked npm install and optimized Next16.4.2 production build/type compilation. Production compilation ran in Docker so the existing hot-reload `.next` directory/listener was not disturbed. Docker backend locked dependencies and `pip check` passed. No new host listener was published.
- Refreshed `infra/release-evidence.json` at **2026-10-23T16:37:54.017Z**: source **`840299fdfc344b8e459357d42c1f1a765e4b8ade3d11553e347539ee0caa3673`**, **166 build inputs**, **45 HTTP requests/297 assertions**. The full migration roundtrip, fake sample preparation, corpus/profile readiness, secret-free bootstrap, grounded actual-page answer, quote/request/approval/calendar, private replacement/isolation, skipped-CRM zero-outbox, private worker, one-shot maintenance and nonroot-image checks passed. Owned ephemeral containers/network were removed. New image IDs are frontend **`sha256:ad6da9c5c6b6e56c3a2f54ed6f251da95362e8af203b2020d3d646f75ae89966`** and backend **`sha256:958eb3e7fa254b500c49a384d846364139b64e55759cd6f2e6dd539f8fe27663`**.
- This is local Windows test evidence plus actual isolated Linux production-image/smoke evidence. No hosted GitHub Actions run, remote push, registry publication, live provider/account operation, cloud provisioning/deployment or human acceptance is inferred. The file-level22-commit plan lives in SBS-016; final clean-tree/contract/fingerprint checks follow the commits.


## Owner-authorized workspace checkpoint acceptance —23 October2026

Before the latest owner-authorized20 local commits, refreshed the complete no-key local gates against the final SBS-017/018 source:236 fake/injected backend tests on isolated actual PostgreSQL/pgvector databases,56 Node tests (including hidden-process ownership), full configured Ruff, pip dependency integrity, generated OpenAPI/browser contract freshness, frontend types and the workflow's numeric Cloud Run/WorkerPool template assertions all pass. Existing harmless Node module-type warnings remain. No fresh install or development frontend shutdown was required; the Linux frontend image performs the locked npm install and production compilation independently.

Actual isolated Linux release receipt verified at 2026-10-23T20:56:06.710Z: source `4f33f0a3c6fa507d21e113ef521a90c278a765625fdbaab130f2a8070f4779c1`, 178 build inputs,45 HTTP requests/297 assertions. Both pinned production images built and ran as nonroot: frontend `sha256:6bc1baa47b69de830d737f7f7f5632b2d33c5e400424d8b82ff5f17a3e06707a`; backend `sha256:a18722e8c13734793230e65d001285406e96bd9ee271f8749ecf9c520d6c7d0d`. Empty-schema roundtrip, explicit fake knowledge preparation, profile/corpus readiness, secret-free bootstrap, genuine CRM skip/no outbox, actual sources/private replacement/isolation, quote/request/approval/shared calendar, private bridge/worker, self-hosted assets and one-shot maintenance pass. Owned ephemeral containers/network were removed; no host port, development volume, account/provider/cloud resource or sibling service was changed. The final source fingerprint was rechecked before staging and will be checked again after commits.

The exact53-file/20-commit allocation and actual hashes are owned by [COMMIT_PLAN](COMMIT_PLAN.md#owner-authorized-workspace-checkpoint23-october2026). This refresh supersedes the older166-input receipt for source freshness; historical evidence stays readable. It proves local Windows gates plus actual Linux images and isolated smoke, not a hosted GitHub Actions run, remote push, live/hosted operation or owner visual approval.
