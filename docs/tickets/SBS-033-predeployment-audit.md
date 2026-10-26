# SBS-033 — No-database pre-deployment audit

Status: Complete local audit —26 October2026. Local findings repaired; actual hosted/provider acceptance is required before public release.

## Owner request and boundaries

Audit the repository broadly now that the owner confirms the local no-database path works, execute safe local pre-deployment checks, repair confirmed local gaps and explain what remains before deployment. Preserve local real/manual settings, active services, credentials and records. PostgreSQL stays stopped. No deployment, cloud provisioning/IAM write, push, new Git commit, real provider/account test, spending or external dependency-inventory upload is authorized.

## Audit plan

1. Review the selected object deployment against runtime composition, task/maintenance identity, private storage, RAG preparation, provider grants, cookies/bridge/OAuth, cleanup and recovery.
2. Run isolated object-mode and storage-independent backend checks, Node regressions, types, Python lint/dependency compatibility, contract freshness, canonical asset/lock/context integrity and release fingerprint checks. Explicitly exclude PostgreSQL fixtures and trap any SQL connection during this audit's tests.
3. Inspect current dependency advisories using public primary sources without uploading repository metadata. Verify version applicability and reachable configuration; do not call a targeted comparison a complete vulnerability scan.
4. Repair confirmed repository defects with focused regressions, then perform a read-only validation of the settled changes. Keep cloud-only acceptance distinguishable from local evidence.
5. Produce an evidence-based launch checklist and staged rollout sequence in the existing release runbook, with clear owner/account/cloud prerequisites and no invented readiness.

## Initial observations to verify

- The offline cloud renderer still exclusively selects the older SQL/WorkerPool templates; the selected object examples are not wired into that release path or its CI structure checks.
- The checked-in Linux receipt predates SBS-032. Docker Desktop's Linux engine was initially unavailable; the owner then opened it and explicitly authorized Docker use while prohibiting database use. Only the objects-only Linux path is used; PostgreSQL remains stopped. The existing full release smoke always starts disposable PostgreSQL before its object check.
- Hosted AI policy still contains the expired historical grant, and hosted CRM grant fields are empty. The local manual policy must not be exported as public spending authority.
- Prepared live source data must be explicitly prepared/promoted into a fresh private hosted store, without copying local guest tokens, outbox or account registry.
- GCS response-size checks currently happen after materializing response bodies; inspect bounded transport and failure behavior before public exposure.

## Acceptance

- [x] Broad local checks and current source/configuration review recorded with exact scope and results.
- [x] Confirmed local findings repaired or explicitly dispositioned with owning code, severity, consequence and regression evidence.
- [x] Object deployment planning cannot silently propose SQL/WorkerPool resources by default; safe offline examples and tests reflect the chosen topology.
- [x] Security/storage/asset/grant/callback/worker/cleanup checks and their limitations are explicit.
- [x] Final review distinguishes local readiness from outstanding Linux, hosted load/IAM/queue, finite provider, real-account and owner runnable checks.
- [x] Running local app and PostgreSQL-off state preserved; no unauthorized external or Git operation performed.


## Findings and dispositions

| ID | Severity | Finding / consequence | Disposition |
| --- | --- | --- | --- |
| DEP-001 | Medium | `cloud_plan.py` only rendered the older SQL/WorkerPool path, risking an incorrect deployment plan for the selected no-database release. | Repaired: objects is now the default for CLI and rendering; explicit `--storage postgres` retains the optional path. New object IAM/Scheduler artifacts, private bootstrap, fake corpus preparation job and seven bounded object-mode presence reads have offline regressions. No cloud command was executed. |
| DEP-002 | Medium | `GCSObjects` materialized `.content` before checking its cap, allowing an oversized or trickling upstream body to consume resources before rejection. | Repaired: raw streamed reads bounded before parsing/decryption, identity encoding, bounded metadata/error bodies, finite socket/elapsed guards, fixed errors and response closure. Regressions cover oversized/encoded/chunked/late responses, actual requests/urllib3 loopback transport and lost upload acknowledgements without write replay. The elapsed check is not an independently preemptive socket deadline. |
| DEP-003 | Medium | CI's actual Ruff command reported six E402 failures in the object smoke script's deliberate path bootstrap. | Repaired with a documented file-scoped E402 exception at that standalone bootstrap; all other configured lint rules remain active. The actual CI lint command now passes. |
| DEP-004 | Medium | The release receipt was stale and the only smoke entry point started PostgreSQL before reaching the object checks. | Repaired: `--objects-only` builds both non-root images, serves production frontend pages/assets, runs separate-process object booking/RAG/CRM/cleanup checks, creates no PostgreSQL container and writes a separate object receipt. CI exercises both explicit paths; the selected path has actual fresh local Linux evidence. |

## Settled checks

- **358 backend checks passed**,162 SQL-dependent/bound cases deselected, with every SQL connection trapped. This is not a new full dual-mode511-test claim. The first conservative selector encountered13 SQL-only fixture/migration cases; the guard prevented connections. Alias/direct-fixture detection was corrected before the final run. A known upstream Pydantic field-alias warning appeared in a concurrent factory test; there was no failed scenario. Evidence: `.runtime/sbs033-backend-final.log` and `.runtime/sbs033-selected-tests.json`.
- **165 Node checks passed**; frontend types, full configured Ruff, `pip check` and actual generated-contract freshness pass. New focused cloud/storage checks are included in the backend total. No new dependency or provider model/rate change was made.
- Actual current Linux/amd64 images run as `node` and `10001:10001`. Six production frontend HTTP checks cover `/`, `/demo`, `/demo/workspace`, health, PDF worker and font license plus nosniff/frame headers. Eleven object scenarios cover original sources, retrieval, booking discovery, exact quote/booking/replay/reschedule, process-restarted sync/refresh, browser-closed expiry cleanup and encrypted credentials. Zero SQL connections/real provider calls. All owned temporary containers/network removed; the owner's PostgreSQL stayed stopped.
- `infra/release-object-evidence.json` records actual source hash **fd2c4d159d77f8c6d2c8f36cfbbc59dcab39a0339726f7ae108c6b68c431d802** across200 build inputs. `node scripts/release-fingerprint.mjs --check --objects-only` passes. The older SQL/full-HTTP receipt remains historical; the new receipt does not claim real GCS, Google IAM or queue delivery.
- Local integrity checks found zero known-current-private-value matches in416 current files and857 historical text objects. Seven canonical assets (six originals plus the replacement) match their hashes;111 registry npm packages have HTTPS/integrity and93 Python requirements are exact pins. App-local env assignments remain unquoted. This is a bounded known-value/private-key-pattern check, not a comprehensive secret-history scanner. Evidence: `.runtime/sbs033-integrity.json`; no inventory uploaded.
- Primary advisory comparisons: Next16.4.2 exceeds the [critical cache RCE patch16.4.1](https://github.com/vercel/next.js/security/advisories/GHSA-673q-mjm6-r5xr) and the [root-param cache fix16.3.8](https://github.com/vercel/next.js/security/advisories/GHSA-h694-7cp9-m8p3). Pypdf6.21.2 includes the [xref-header fix6.21.2](https://github.com/py-pdf/pypdf/security/advisories/GHSA-gmh7-3g9r-mjh5) and [array/dictionary memory fix6.21.0](https://github.com/py-pdf/pypdf/security/advisories/GHSA-f54x-cmq8-qg57). Cryptography50.0.2 matches its [maintainer release notes](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst). No upgrade is justified by these selected comparisons; full transitive/distro/image vulnerability scanning is still unverified.

## Full release acceptance scope — audit record

The owner subsequently requested a setup-only handoff that excludes tests performed after provisioning. The current finalized list is [the verified runbook inventory](../../infra/README.md#verified-cloud-inventory-and-remaining-setup-26-october2026); this wider acceptance matrix is retained as the original audit scope, not that handoff list.

1. Approve actual project/region/resource/cost scope and immutable image publication. Provision only the reviewed object topology: frontend, private API/worker, private bucket, queue and authenticated minute maintenance. No Cloud SQL/VM/WorkerPool is required for this mode.
2. Verify actual IAM and policy: only frontend invokes API; only delivery/maintenance identities invoke worker; exact-bucket runtime access, no public bytes, pinned secret versions and no retained guest object history. Exercise missing/wrong identity/audience and denied bucket/queue permissions. [Google's service-to-service requirements](https://docs.cloud.google.com/run/docs/authenticating/service-to-service) and [Scheduler OIDC](https://docs.cloud.google.com/scheduler/docs/http-target-auth) were rechecked.
3. Prepare/promote a verified, profile-matching canonical live pack into the fresh hosted store. Repo source PDFs alone do not make live retrieval ready. Do not transfer local guest tokens, outbox, accounts or manual grant state. Verify all six original source/citation/highlight paths and unsupported-policy behavior through the hosted site.
4. Establish new finite hosted AI and CRM authority. The code's historical AI grant is expired and hosted CRM grant fields are blank; local manual authority cannot authorize hosting or automated tests. Approve explicit ceilings/window and lifecycle/cleanup coverage, enter provider secrets privately, configure the public Turnstile hostname and exact HubSpot callback/distribution/scopes. No key or grant was copied/renewed here.
5. Run private hosted contention/cold-start/memory tests before public traffic. This design commits to one conditional mutable shard; [GCS limits writes to one object name to one per second](https://docs.cloud.google.com/storage/quotas). Local file concurrency is not evidence of hosted latency/capacity. Test concurrent booking/replay/edits,429/412/lost acknowledgements, backlog, queue deletion/retries, rollout/process death and cleanup after closing every browser. Keep state/key versions compatible across API and worker; define key-retention/rotation and recovery before activation.
6. Complete bounded real site acceptance: skip makes no CRM work; connect/consent/native create/readback/change/status/cleanup/uninstall and shared-install capacity behave honestly; human verification/error recovery and expiry/source retirement work. Prior native booking/expiry evidence is retained, not generalized to all untested lifecycle cases.
7. Review operational release controls: recent image/transitive/distro vulnerability scan under an approved no-export/local or explicitly approved scanner; application logs contain only fixed diagnostics; review Cloud Run/request-log routing so OAuth callback code/state and sensitive query strings are not retained in platform logs; useful alerts for storage failures/cleanup backlog/provider admission/capacity; budgets are notification-only unless a separate hard control exists; previous revision/pack/key rollback and a private-QA-to-public decision are documented.

## Verdict and next lane

No remaining actionable finding was identified in the final scoped local review. The repository now has a tested no-database release-check path and coherent offline QA artifacts. This is **ready for a separately authorized private hosted QA stage**, not a claim of public production readiness. The concrete next step is to review the rendered object plan, resource/cost scope, secret-version names and fresh finite acceptance grants, then provision restricted fake QA and execute the hosted negative/load/recovery matrix before enabling real traffic.

The owner's running local app, mode flags, data and services remain intact. Docker use was explicitly authorized during this audit; no database was started or used. No real provider/account operation, cloud write, image push, staging or commit occurred. The new/modified audit files are left for review.


Platform logging is a hosted privacy gate: [Cloud Run automatically generates request logs](https://docs.cloud.google.com/run/docs/logging), independently of the app's suppressed callback logging. Review [log routing/exclusion rules](https://docs.cloud.google.com/logging/docs/routing/overview) for `/auth/hubspot/callback` and verify actual retained logs contain no OAuth code/state. Do not assume a Next.js application logging filter controls Google request logs. During the original local audit no cloud logging policy was read or changed; the later authorized metadata inventory below read project sink configuration only.

## Owner reconciliation and authenticated cloud inventory —26 October2026

The owner explicitly fixes **deployment to no database**, asks that current instructions consistently say so, confirms AI limits are already implemented, authorizes gcloud metadata inspection, and authorizes only missing empty Secret Manager name creation while retaining value entry themselves. No service provisioning, API enablement, IAM binding, secret-value access/copy, paid call or grant renewal is implied.

Readback explicitly targeted project `choreograph-512713` without changing the active sibling CLI configuration. The project is active and billing enabled. All six object/live secret resources already exist, use automatic replication and have zero versions. Both unused SQL secret names also remain empty. No resource needed creation, and no cloud mutation occurred. User-managed service-account list and bucket list are empty. Secret Manager is enabled; Cloud Run, Tasks, Scheduler and Artifact Registry are absent from the enabled API inventory. Both project USD10 and Cloud Run USD5 monthly alerts exist with50/80/100% thresholds and no observed spend cap. Project log sinks are `_Required`/`_Default` with no exclusions; Monitoring alert-policy count and log-based metric count are both zero. No application logs, secret payloads, OAuth tokens, account data or billing transactions were read.

Read-only local object inspection confirms **six live canonical sources,23 chunks,1536-dimensional `text-embedding-3-small` vectors**, matching all six repo source hashes. The originals already ship through explicit backend Dockerfile copies. Preparing a new index is not unfinished work: one canonical-only promotion into a fresh hosted store is the remaining release-data step. The whole local store includes private guest/accounts/outbox/ledger data and must not be promoted. The current transfer CLI migrates whole local PostgreSQL state; it is not a hosted canonical-only promotion command. No paid ingestion or storage write occurred.

AI request/token/vector/cost limits and durable global/workspace accounting are **implemented**. Hosting still needs an active release policy because the checked-in AI test grant expired24 October and CRM hosted grant fields are unset; the local manual exemption does not apply to containers. No control or allowance was changed here.

The [finalized setup-only list](../../infra/README.md#remaining-pre-deployment-setup) contains only values/version pins, no-database hosting configuration, promotion of existing canonical data, hosted policy/public URLs, and operational security/logging/rollback setup. Post-provision testing is excluded from that list at the owner’s request. Current authority docs and HTML overviews are reconciled; old SQL tickets/configurations are marked historical/optional while preserving their actual evidence. Docs-only validation checks links, configuration parsing, release source freshness and whitespace; local services, mode and PostgreSQL-off state remain intact.

Reconciliation validation:11 focused offline cloud-plan tests passed,48 new relative links/anchors across44 changed documents resolve, both edited HTML inline scripts parse, cloud JSON/YAML parses and all three selected services omit SQL configuration. The current-tree known-private-value scan found zero matches. The200-input object release fingerprint remains unchanged/current (`fd2c4d159d77f8c6d2c8f36cfbbc59dcab39a0339726f7ae108c6b68c431d802`). `git diff --check` passes. Owned API/runner/frontend remain running; the PostgreSQL container remains stopped. No staging/commit/push or cloud mutation occurred.

## Explicit database-secret removal —26 October2026

The owner then explicitly requested deleting unused cloud database secrets. Before mutation, fresh `gcloud secrets describe` and `versions list` metadata confirmed `CHOREOGRAPH_DATABASE_URL` and `CHOREOGRAPH_DB_PASSWORD` in project `choreograph-512713` both had zero versions. Exactly those two resources were deleted with the project supplied explicitly. A final list verifies both are absent and all six required non-database resources remain. No secret contents were accessed; no other cloud resource, IAM policy, API, grant or service revision changed. Local optional-SQL configuration/data and the owner’s running no-database app were preserved.

Ignored receipts: `.runtime/sbs033-database-secret-predelete.json` and `.runtime/sbs033-secrets-after-database-removal.json`. The runbook and AGENTS now prohibit recreating database secret resources for this selected deployment. The private bucket’s role is clarified: canonical source/search packs plus encrypted application state, not documents alone. `git diff --check` passes; no application code or build input changed in this cleanup.

## Subsequent private-storage setup — SBS-034

The owner then populated all six secrets (enabled version1 metadata confirmed) and explicitly selected deployed-app bucket access. [SBS-034](SBS-034-private-storage-foundation.md) owns the now-created europe-west1 private bucket, API/worker identities and exact-bucket role. That subsequent scoped authorization supersedes this audit’s earlier no-cloud-write boundary only for those foundation operations. No application deployment, paid calls or canonical promotion occurred. Use the current runbook inventory rather than the earlier empty-project snapshot.
