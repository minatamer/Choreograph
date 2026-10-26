# SBS-038 — Final AFK material security audit and scoped remedies

**Subsequent SBS-040 resolution:** Python is no longer a blocker. The patched3.11.18 image is built from the authenticated official recipe/source, passed actual packaged/no-database checks and was uploaded privately. [Runtime evidence and exact scope](SBS-040-python-security-runtime.md). Earlier wait-only instructions/results below are retained as dated history; finite hosted provider authority/origin/consent remain separate.


Status: Local security/runtime preparation complete; Python subsequently resolved under SBS-040. Public paid activation still has separate SBS-039 conditions —26 October2026.

The owner explicitly requests quality first (completed/committed), then a new full material security audit, justified local fixes/validation and exact local staging/commits without questions while AFK. No deployment/cloud/account/secret-payload/paid-provider action, database startup, dependency-inventory export, push or delegation. Current API health is fake; all tests use injected providers and isolated no-database state. The future Scheduler-only change is **plan only** and is not a security implementation task.

## Scope and ordered work

1. Review the actual frontend/API/domain/RAG/provider/CRM/object-store/operator/release trust boundaries with STRIDE and common threats: authorization/CSRF/session/account/nonce/generation/revision, exact concurrent business rules, document scope/hostile input, paid admission/idempotency, ambiguity/retries/cleanup, secrets/error/log privacy, finite resource/network/parser work, fixed endpoints/IAM/supply chain.
2. Compare all locked npm/PyPI and actual current image distro packages to public bulk advisory datasets locally if available, with exact primary dataset revisions/timestamps and honest unsupported/unavailable scope. Send no private inventory/code to external scanners. Target current maintainer advisories when version/reachability needs clarification.
3. Confirm only material actionable findings with reproducible evidence and a minimal exact file/validation plan. Preserve earlier reports as dated history; no finding quota or speculative cosmetic recommendations. Missing real hosting/provider/manual evidence is a limitation, not a fabricated vulnerability.
4. Finish detailed `docs/security/SECURITY_REVIEW.md` and concise severity-ranked `SECURITY_OVERVIEW.html`. Record AFK provisional selection of actual findings (or no-fixes), then execute only justified local remedies under direct owner authorization. Independently confirm/validate until no actionable scoped issue remains.
5. Run appropriate focused/settled fake/no-SQL gates for actual changes. Preserve logs, UI/motion, source/domain/admission/privacy and quality gains. Prepare exact file-level commit allocation, staged private checks and clean local security commit. No owner paid/native/visual acceptance is inferred.

## File allocation before source fixes

This ticket owns scope/findings/results. The existing security Markdown/HTML own detailed/PM coverage; main blueprint owns AFK prompts/decisions; AGENTS/README/queue/runbook/COMMIT_PLAN receive current status, guardrails and exact Git allocation. Application/dependency/test changes require a confirmed finding and explicit allocation here first. No security application source changes have been made at audit start.

## Confirmed findings and pre-fix allocation

The source-led audit and local advisory comparison completed before source edits. Two material runtime supply-chain findings are confirmed; no new application-authorization/booking/source/admission/CRM exploit was reproduced. Severity is application-context **medium/P2** for each: upstream Node includes high-severity issues, but no public Choreograph RCE/TLS exploit was demonstrated. Do not translate an upstream CVSS score into a claimed app exploit.

| ID | Concrete evidence / impact | Recommended AFK disposition |
| --- | --- | --- |
| SEC-038-01 | Actual frontend image runs Node24.19.0. The official21 October release fixes TLS/certificate trust, HTTP/decompression and other runtime issues in24.22.1. The BFF makes authenticated outbound requests; Next/sharp patching does not patch Node's runtime. | Select official same-LTS/same-Debian image24.22.1, immutable index `sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205`; align Docker assertion, CI and root engine metadata. Rebuild production frontend and run no-database acceptance. |
| SEC-038-02 | Actual backend image runs Python3.11.17. Python3.11.18, released25 October, adds emergency rejection of compromised eMudhra intermediate keys, plus other security fixes. Backend TLS carries protected provider/storage credentials. | Required **before deployment**. Official `python:3.11.18-slim-bookworm`, `3.11.18-slim-trixie` and `3.11.18-bookworm` all return not-found; maintained3.11-slim-bookworm still resolves exactly to the old3.11.17 digest. Record upstream artifact blocker; do not invent a digest, add custom crypto validation or introduce an unreviewed compiler/base-distribution migration. Once published, verify/pin official3.11.18+ same-series image and rebuild/test before deployment. |

Primary evidence: [Node security release](https://nodejs.org/en/blog/vulnerability/october-2026-security-releases), [Python3.11.18](https://www.python.org/downloads/release/python-31118/). Public Docker manifest inspection was read-only. No cloud/provider operation or attack on a real endpoint was used.

Exact source remedy allocation: `infra/Dockerfile.frontend` (official Node pin/assertion), `.github/workflows/ci.yml` (Node version only), `package.json` and `package-lock.json` (root supported engine only). `infra/release-object-evidence.json` will contain actual rebuilt image evidence. No app/domain/UI/provider/transport behavior edit is selected. Backend Dockerfile stays on its truthful existing pin until a real official artifact exists. README/infra runbook/AGENTS/blueprint/lessons/queue and the two existing security reports own current status, remaining Python blocker and local-vs-hosted scope. COMMIT_PLAN owns literal staging allocation. No additional service, scanner or scheduled task.

Baseline checks at `e60092f`:374 no-SQL backend tests,165 Node checks, types/Ruff/contracts/pip compatibility and fresh Linux objects-only acceptance. A new focused security run completed with `Engine.connect` trapped; its initial sandboxed collection stalled and was stopped by verified exact PID, without a test result, then restarted outside the sandbox with trace diagnostics. Only the completed rerun may count as evidence.

## Settled validation and independent read-only review

**Complete local audit and available Node remedy —26 October2026. SEC-038-02 remains externally blocked, not fixed.** The owner-requested order is preserved: Scheduler plan only, quality commit `e60092f`, then this separate security checkpoint. No application Python/React/bridge/domain/transport source changed in the security remedy; package dependency versions/integrities are unchanged. Exact runtime/CI/root engine edits match the pre-fix allocation. No new finding appeared in the read-only diff/acceptance review.

| Check | Actual outcome |
| --- | --- |
| Focused backend security | **199 passed,66 SQL-dependent cases deselected,118.69s**; `Engine.connect` raises throughout. Includes GCS bounds/corruption/CAS/lost acknowledgements, object authorization/concurrency, OAuth reset/refresh/uninstall races, AI/CRM admission, provider byte/time bounds, human receipts, private task ingress/delivery, canonical filtering and manual-policy isolation. Fake/injected only. |
| Node, normal Windows access | **165 passed,0 skipped**. Initial sandbox run denied process identity inspection (164/165); the full unsandboxed rerun passes. No source workaround for a tooling permission failure. |
| Node under patched production image | **164 passed,1 Windows-only test skipped**, Node**24.22.1**, network disabled/read-only source mount; no app or real account request. |
| Types/lint/lock compatibility | Frontend TypeScript, configured whole Python Ruff and `pip check` pass. Root package/lock engine metadata agree; all dependency versions remain unchanged. Contract/app source unchanged, so no schema regeneration required by this remedy. |
| Actual fresh Linux release | Six production frontend pages/assets/header checks and11 encrypted-object lifecycle scenarios pass: source/retrieval/rolling discovery/quote/booking/idempotency/reschedule/separate process/refresh/browser-closed cleanup/encrypted credentials. Non-root identities preserved, zero SQL connections/real provider calls; owned containers removed. |
| Release freshness | **200 inputs**, source `89fb2bc0ad669a78caab3f5c46b7a9e4a56a2c77028e624b87a2d3bfdf1a87c5`; `infra/release-object-evidence.json` matches. Frontend `sha256:a35afcc84049e5a1275ce318a709c401826f9b1bd77cb58028473a89a422a43d`; backend `sha256:57997a0142ae95d460e4ff5df07df1accf3bae917e334fc1961c59c987fed898`. Actual backend still**3.11.17**, not falsely patched by a rebuild. |
| Final image advisory inventory | New source-package inventories remain63/73; the updated official Node base removes21 frontend older-than-fixed pairs; the final Debian comparison has6 backend OpenSSL older-than-fixed and218 open/undetermined image/advisory pairs, with the report's reachability/mapping limits. No additional material app finding selected. This is not a clean-image attestation. |
| Documentation/privacy | New relative links/HTML IDs/syntax and object examples parse; known local private-value variants have zero current-tree matches. Final staged/committed private-byte/path/hash/whitespace checks belong to COMMIT_PLAN and the ignored Git receipt. |

Read-only validation verdict: **Meets ticket with concerns**. Covered: whole-repo material audit, actual ranked findings/AFK selection, available minimal Node fix, functionality preservation, fake/no-SQL validation, current reports and precise Git plan. **Partial/external:** Python security remedy awaits an actually published official artifact and must be completed before deployment. Unverified: actual hosted/private-IAM/load behavior and owner paid/native/visual/security acceptance. Do not mark all security findings closed, deployment-ready or owner-approved. A synthetic local Node hostname probe rejected the tested names even in the old image; no exploit reproduction is claimed from it. Runtime version plus primary security release, not a fabricated public attack, is the finding evidence.

Ignored evidence: `.runtime/sbs038-backend.log`, `sbs038-selected-tests.json`, `sbs038-node.log`, `sbs038-patched-node.log`, `sbs038-linux.log`, `sbs038-final-runtime.json`, `sbs038-advisories/{receipts,package-results,distro-results}.json`, before/final image inventories. Public downloads never received code/inventory. The initial incomplete archive/aborted collection are explicitly excluded from pass counts.

## Required next actions before deployment

1. When the official Python3.11.18+ same-series container exists, verify its registry digest/provenance, pin it, rebuild and rerun the fake/no-database gates. No automatic wake-up or cloud change was configured.
2. Implement the separately planned SBS-036 Scheduler-only transport and prove retry/ambiguity/expiry/duplicate/crash/cutover behavior before removing Tasks requirements.
3. Configure the remaining hosting release inputs and fresh finite hosted provider authority; retain the completed private bucket/canonical pack/secret IAM. Owner paid/native/visual/security review is separate.

No PostgreSQL started, paid/real account action, cloud mutation, deployment or push. Existing local fake services, keys and private data remain available; the global/local running Node/Python installation was not silently upgraded. The container/CI Node fix does not claim to patch the already-running owner's host toolchain.
