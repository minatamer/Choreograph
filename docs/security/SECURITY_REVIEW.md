# Choreograph security review

## Current continuation review — SBS-012–015

Read-only manual review,22 October2026, source `c803fbcd8d491d794dc3504bd08d0da056f5521363fcdd8e1fdaa73f7c7251b4` (107 image inputs). The primary agent inspected the changed AI/CRM/Tasks/operator boundaries and relevant existing authority code after quality completion. This review includes untracked source; Git remains unstaged. No application change was made during this audit. Existing227 backend/15 Node tests and the focused adversarial/race/cleanup tests are local injected/actual-PG evidence. The previous six findings/dispositions below remain historical and their regression tests still pass.

**Disposition: no new substantial actionable local finding confirmed.** No new security fix is proposed. This does not establish that the application or dependencies are vulnerability-free, or that deployed IAM/capacity/provider behavior is accepted. Human security review remains outstanding under provisional AFK review.

| STRIDE boundary | Actual controls inspected and evidence | Limit / release consequence |
|---|---|---|
| Spoofing: guest/BFF/API/OAuth/task identity | Fixed browser route vocabulary; server-only bridge plus Origin/CSRF/cookie authorization; server-owned generation/revision; OAuth one-use hashed state bound to guest/app/provider; callback origin/duplicates and secret-free redirect; task issuer/audience/exact email/email_verified before parsing; headers alone confer no authority. Session/callback/private-API/task tests reject mismatches. | Actual TLS, Google service IAM and valid/invalid OIDC delivery still require the chosen cloud project. |
| Tampering: booking/document/provider results | Domain exact prices/durations and explicit Send/review/approval; PG exclusion/version/idempotency constraints preserve failed-reschedule reservations. Retrieval joins ready profile/owner/manifest before ranking; actual passage/excerpt validation and real source preview; stale/reset/expiry results fenced. Hostile PDF/text remains data and cannot execute tools or SQL. | Real semantic support must pass the bounded evaluation. Unsupported evidence remains a failure/handoff. |
| Repudiation: durable action/usage/receipt | Separate committed AI/CRM grants survive business rollback; attempt/run keys, unknown usage and no refunds; global/per-guest request/token/vector/cost bounds; acceptance run cannot replay or downgrade receipts. New atomic usage/success finalizer prevents misleading receipt success. Durable outbox/publication leases, epoch identity and fixed codes preserve ambiguity. | Operator receipts avoid raw model/contact/source/token data; actual provider usage/native-readback and hosting logs still need authorized inspection. |
| Information disclosure: credentials/source/account | Tokens encrypted server-side; secret repr excluded; client secret/API key never in browser contracts. Fixed official provider/metadata URLs, redirects disabled even for borrowed clients, ambient SDK headers/overrides removed, identity encoding/response caps. Actual source authorization rechecked through server manifest; BFF retains sandbox/no-store/referrer protections. Tests include cross-guest/retired source, app/account/config mismatch and synthetic secret markers. | No production key/secret was entered; actual Secret Manager versions and least-privilege SQL/IAM remain owner/project setup. |
| Denial of service / paid misuse |256 retained guests, no eviction; finite chat/request/upload bytes/work; parser child5s/256MiB; offline verified BPE assets; AI shared leases and55s operation fence, durable global4 network slots/2 ingestion interactions; CRM finite request grants and45/90s operation windows; network reads/total response caps/monotonic checks. Dispatcher two-connection pool, one SQL leader, bounded3 publications/cycle,120 publication attempts, five domain attempts and three-hour horizon. Failure stays failure. | Socket read timeouts plus monotonic checks are bounded, not an exact preemptive wall-clock guarantee. Public fairness/perimeter and funded capacity require project/budget review; local timings are not an SLO. |
| Elevation of privilege: integrations/cloud/operator | Visitor chooses discovered open pipeline/stage and separately permits schema/export; no operator fallback, and skip has no HTTP/outbox. App/provider/account/generation/destination fences protect tokens/late work. Uninstall serializes with registry and protects other active uses. Dispatcher has no provider/bridge/token key; WorkerPool template separates identities/queue FULL permissions/actAs. Health-only bootstrap exposes no guest/task handler. | Cloud templates are proposals, not applied permissions. Actual uninstall/admin notification/install-slot release and cloud recovery/backup restore remain external checks. |
| Operator input / supply chain | CLI default dry run reads no key file/provider; explicit run/account/unique local DB restrictions; cloud renderer validates complete small input dictionary and writes only a new ignored runtime folder; gcloud preflight is seven bounded describe reads, no secret bytes/stdout export or writes; YAML uses safe_load. Locked wheels/images/actions and pip compatibility were inspected. | No remote scanner or dependency graph upload. This is targeted primary-advisory review, not complete transitive/OS-image attestation. |

### Current targeted dependency check

No version change was required by this review. Locked Next16.4.2 and sharp0.35.5 meet the maintainer's patched16.4.1/sharp0.35.5 boundary for [image SVG RCE](https://github.com/vercel/next.js/security/advisories/GHSA-2464-fhr4-w9xw); Next also exceeds the patched16.4.1 boundary for [typed-array cache RCE](https://github.com/vercel/next.js/security/advisories/GHSA-673q-mjm6-r5xr). React/ReactDOM19.3.1 match the current patched branch in the [RSC advisory](https://github.com/react/react/security/advisories/GHSA-xqc2-xf4c-x3h3); the framework's compiled runtime is covered by the Next patch, rather than assuming the React package alone fixes it. This app adds no Server Actions, arbitrary remote image configuration or dynamic code tools.

Pypdf6.21.2 matches the patched version in the October21 [repeated missing-object advisory](https://github.com/py-pdf/pypdf/security/advisories/GHSA-6c7f-9265-g8fw), alongside the earlier xref fixes below. Cryptography50.0.2 remains beyond the [50.0.0 PKCS7 patch](https://github.com/pyca/cryptography/security/advisories/GHSA-g6cj-pr64-35w5), and urllib3 2.8.0 meets the [chunk-line patch](https://github.com/urllib3/urllib3/security/advisories/GHSA-vxq7-64xx-v4gw). LlamaIndex0.14.25 is used for bounded local parsing/retrieval, without arbitrary loaders/evaluation tools; an empty maintainer advisory index is not proof of safety. PyYAML6.0.3 is now an explicit already-locked tooling dependency, using safe constructors. OpenAI3.36.1, google-auth2.62.0 and existing HTTP/SQL dependencies remain pinned; no broad vulnerability-free claim is made.

### Outstanding external evidence and future-edit rules

Only real operation/hosting/human evidence remains: current supported models/rates and a finite funded key; selected visitor app/account/scopes/schema/destination/consent and cleanup/uninstall observations; authorized project/billing/region/SQL/backups/secrets/IAM/queue/WorkerPool setup, restricted deployment and real recovery; hosted CI and owner runnable/security review. SBS-011 and infra/README own concrete limits/commands. No missing application path is deferred as an account blocker.

Future changes must preserve fake-forced isolated tests; exact money/minutes/timezone/overlap and explicit approval; server-owned source/profile/manifest authorization; failed/stale cleanup and unknown-outcome counters; no token/raw-body logs; app/account/destination fences and genuine skip; task signature/exact-target validation, attempt horizons and leader recovery. Repeat targeted tests and rebuild the image receipt for changed inputs. New substantial findings require a fresh documented disposition; do not weaken a bound to make a provider test pass.

---

## Historical initial audit and remediation record

Audit date: **22 October 2026**. Audit snapshot: `44de3efce446e0bc261d9b1be2cbaf23fee084dde885b0ab377a9de781089db1` (83 release-input files). Owning tickets: [SBS-009B](../tickets/SBS-009B-security-review.md) and, after explicit selection, [SBS-009C](../tickets/SBS-009C-security-fixes.md). [PM overview](SECURITY_OVERVIEW.html).

## Scope and disposition

This manual review examined the local fake-provider application, prepared provider adapters, durable jobs, locked dependencies and release examples. Three independent reviewers inspected backend authority/documents/providers, browser/bridge/release boundaries, and CRM/jobs. The primary agent confirmed the code paths and reproduced the secret-representation case with synthetic values. No application fixes occurred during the audit. Probes used injected responses or isolated disposable PostgreSQL; no live accounts, paid calls, remote scanners, dependency-graph export or Git writes occurred.

The settled pre-audit checks were 85 backend tests, eight Node lifecycle/bridge/identity tests, configured Python lint, generated-contract freshness and a Windows production frontend build. Those checks are useful context, not proof of security. This is a proportionate review, not a penetration test, exhaustive vulnerability scan or compliance certification. Human security review remains outstanding under AFK delegation.

| ID | Severity | Finding | Initial disposition |
|---|---|---|---|
| SEC-001 | Medium / P2 | New and reset guests have no aggregate retained-workspace admission bound | Open; eligible local remedy |
| SEC-002 | Medium / P2 | Old uninstall completion can overwrite a newer installation | Open; eligible local remedy |
| SEC-006 | Medium / P2 | Definitive fake OAuth denials permanently consume installation capacity | Open; eligible local remedy |
| SEC-003 | Medium / P2 | Public source bridge drops the backend sandbox policy | Open; defense in depth |
| SEC-005 | Medium / P2 | Prepared OpenAI adapter buffers upstream responses before its size check | Open; fix before live activation |
| SEC-004 | Low / P3 | Settings representations include protected configuration values | Open; diagnostic hardening |

No critical/high finding was confirmed in this scope. Initial severity reflects reachability and consequence; it does not imply a successful external exploit. The original findings below remain the audit record. Actual selection, changed source and regression results belong to the remediation ticket and final disposition section.

## Trust boundaries and STRIDE review

| Boundary | Examined controls and evidence | Finding / remaining limit |
|---|---|---|
| Guest browser → Next bridge → private API | Fixed route vocabulary/upstream, server-only bridge credential, Origin/CSRF checks, HTTP-only session, hashed token lookup, generation/expiry checks. Existing session/bridge/identity tests exercise rejection. | SEC-001, SEC-003; deployed TLS/IAM/cookie settings still require hosted evidence. |
| API/domain → PostgreSQL | Workspace-scoped relationships, exact money/minutes, explicit review/approval, versions/idempotency, exclusion constraints and transaction rollback. Actual isolated-PG concurrent booking tests passed. | No additional confirmed reservation-authority defect; cloud roles/backups/migration operations unverified. |
| Guest file → parser → manifest/retrieval/source reader | 2 MiB input, ten pages, 32,000 extracted characters, bounded traversal/chunks, 256 MiB child and five-second limit, active PDF rejection; atomic ready-version manifest and explicit server authorization. Original/replacement/cross-guest tests and actual PDF/page browser checks exist. | SEC-003; a parser check is not a substitute for response sandboxing. |
| Assistant → provider proposals → commands | Strict envelopes, bounded context/claims, actual supplied passage identities/excerpts, no arbitrary SQL/HTTP/shell authority; model cannot approve bookings. Ordinary configuration is fake-only. | SEC-005 in the prepared live transport; real semantic quality/model/pricing remain unselected. |
| OAuth → account registry → encrypted connection | Hashed expiring one-use workspace/generation-bound state; explicit export consent; encrypted server tokens; fixed provider routes and verified account/readback fences. | SEC-002, SEC-006; actual scopes, install limits and slot release need authorized provider acceptance. |
| Reservation/outbox → leased worker → external receipts | Destination/revision/generation fences, bounded attempts/leases, reconciliation for ambiguous writes, deterministic app-owned keys, verified native-link criteria, cleanup limited to owned records. Worker verifies signature/issuer/audience/exact email before parsing. | SEC-002; deployed enqueue transport and reliable unattended maintenance caller are unfinished deployment gates. |
| Operator/build → runtime/diagnostics | Explicit fake profile, no startup environment reads on import, isolated test DB guards, pinned non-root images, allowlisted build context, private QA templates and no-key CI. | SEC-004; hosted CI, cloud IAM/log redaction and image/distro scanning were not executed. |

The review considered spoofing, tampering, repudiation/diagnostics, information disclosure, denial of service and privilege escalation across these boundaries. No further validated cross-workspace authorization, prompt-to-tool authority or booking integrity defect was found in the inspected paths. This statement is bounded by the scope above.

## SEC-001 — Aggregate workspace admission

**Evidence:** `apps/backend/choreograph/sessions.py:create_workspace` validates a timezone and inserts without an aggregate limit. All session/restart/reset creation paths in `api.py` share it. Per-guest action, enquiry, message and upload limits, and concurrent parser/assistant limits do not bound repeated new guests. Each guest persists seeded calendar data. An actual isolated-PG probe admitted eight guests plus four reset replacements: 12 retained rows, eight active; immediate maintenance still retained 12. The disposable database was removed.

**Impact:** Anonymous guest/reset churn can grow retained database/calendar/source state and use shared resources. Immediate cleanup cannot assume acknowledged CRM cleanup or delete unresolved references. This is denial of service/retained-storage exposure, not a bypass of another guest's authorization.

**Bounded remedy:** Serialize shared admission with a PostgreSQL transaction advisory lock; count **all retained Workspace rows**, including retired/unresolved rows and the current transaction's additions. Adopt a provisional local cap of **128 retained workspaces** and a fixed 429 `DEMO_CAPACITY` response. Reject a reset atomically so an existing workspace remains usable; never evict an active guest. This is a local bound, not a fairness control, public-launch capacity promise or funded budget. Reassess perimeter/admission and retention against an authorized hosting budget.

**Final local refinement:** The first 128-row proposal was below the actual 189 pre-remedy development rows. Final browser admission exposed that mismatch. AFK-0018 selected **256 retained rows** with the same serialized all-row semantics and no eviction/retention change; existing data is preserved. The initial proposal above remains historical. Backend tests, current browser admission and Linux proof are rechecked after this one-constant refinement.

**Regression:** Concurrent admissions for the final slot yield exactly one success; retired rows count; rejection rolls back reset retirement; existing sessions continue at capacity. Keep test data isolated and restore any cap fixture state.

## SEC-002 — Uninstall completion race

**Evidence:** `jobs.py:perform` holds the account registry advisory lock through provider uninstall, releases it, then `deliver` calls `finish_job`. The latter independently sets Installation to `uninstalled`. A newer `crm.callback` can record the same account as installed in the gap. A hermetic execution of the actual functions reproduced old completion overwriting the new state.

**Impact:** Installation counts can underreport an active newer install, corrupting account/capacity bookkeeping. Other-use guards during uninstall do not fence its later completion.

**Bounded remedy:** Commit the verified registry removal while still holding account serialization in `perform`; remove the later unfenced registry overwrite. Preserve conservative registry state on an uncertain/failed uninstall. Keep the other-active-use check and owned-record cleanup boundaries.

**Regression:** Controlled PostgreSQL interleaving of uninstall and another workspace's successful same-account callback must preserve the newer installed state when old job completion runs. Failed/ambiguous uninstall must not free a slot.

## SEC-006 — Definitive fake denial reserves capacity indefinitely

**Evidence:** `FakeHubSpot.exchange` rejects an invalid fake code as `CRM_DENIED` before an installation exists. `crm.callback` currently records every `CRMFailure` as `unknown`; `available` and maintenance preserve uncertain installations indefinitely. Actual `begin`, validated callback schema and callback code with in-memory Session stubs admitted 25 invalid-code attempts from one guest: zero installations, 25 unknown outcomes, capacity unavailable the following day and the next begin blocked.

**Impact:** One local demo guest can permanently disable the shared optional CRM connection path. Genuine ambiguous real exchanges must remain conservative; expiring unknown states indiscriminately would hide actual installations.

**Bounded remedy:** Distinguish the fake provider's definitive no-install denial from uncertain exchange/introspection/preflight failures. Do not release real unknowns on a timer. Where an account has already been identified and retained in Installation, count that same attempt once rather than as an additional unidentified installation.

**Regression:** Repeated invalid fake callbacks retain available capacity and create no installation/connection/outbox. Unidentified uncertain exchanges still reserve a slot; known-account uncertain preflight counts one conservative installation, including a previously uninstalled row.

## SEC-003 — Source sandbox headers lost at bridge

**Evidence:** `knowledge_api.py:original` supplies `Content-Security-Policy: sandbox; default-src 'none'` and `X-Content-Type-Options: nosniff`. `apps/frontend/app/api/demo/[...path]/route.ts` rebuilds the response and forwards only disposition/source-page metadata, dropping CSP. A hermetic execution of the actual transpiled route returned 200 and the disposition but no CSP. Global Next headers retain nosniff; they do not restore the sandbox.

**Impact:** Direct public source navigation lacks an intended isolation layer. No arbitrary-script exploit was demonstrated: ingestion rejects active PDFs, text is escaped and PDF.js renders to canvas with annotations disabled. Medium severity reflects the untrusted-file boundary and a lost existing control.

**Bounded remedy:** Preserve the fixed CSP and nosniff headers in an explicit response-header allowlist. Keep no-store and disposition; do not forward arbitrary upstream credentials/headers or change route authority.

**Regression:** Execute the actual route with injected PDF/TXT upstream responses; assert sandbox, nosniff, no-store and disposition survive while unrelated sensitive headers do not. Retain existing bridge and private-identity tests.

## SEC-005 — Prepared OpenAI response materialization

**Evidence:** `providers.py:OpenAITransport` configures token/time/pool limits, but normal SDK `responses.create` materializes the HTTP response/model before `parse_envelope` checks 16,000 text characters. Installed SDK/httpx source confirmed full buffering. A zero-network SDK MockTransport probe consumed the entire 262,411-byte success and 262,209-byte error bodies without Content-Length despite `max_output_tokens=1400`.

**Impact:** A malformed or oversized upstream response can use memory before application validation; per-chunk read timeouts alone do not impose a total response deadline. Current ordinary app configuration is fake-only and never constructs this transport. This is locally fixable preparation for later authorized activation, not evidence that live use occurred.

**Bounded remedy:** Enforce a small response-byte cap before SDK/error parsing. Request identity encoding and reject compression before decoding, preventing expanded-body allocation. Add a monotonic response budget checked before/after reads, with a short individual read timeout; this does not preempt a socket operation at an exact wall-clock deadline. Close on failure and retain no retries, bounded timeout/pool and fixed sanitized diagnostics. Do not add live model defaults or fake fallback.

**Regression:** Zero-network SDK tests for oversized chunked success/error responses without Content-Length, compressed decoded-size expansion, deadline and normal strict-envelope success. Assert early close and no retry; no real API key/call is needed.

## SEC-004 — Secret-bearing Settings representation

**Evidence:** The default dataclass representation in `settings.py` includes database_url, bridge_secret and token_key. Two independent synthetic-marker probes confirmed all three; no real configuration value was printed or persisted in this report. SQL engine parameter hiding and short pytest tracebacks do not suppress all object representations.

**Impact:** Accidental logging/debugging/assertion representations could expose protected server configuration. No public response route was found that returns Settings; this is low-severity diagnostic hardening.

**Bounded remedy:** Mark exactly those three fields `repr=False`; preserve explicit constructor/access and useful nonsecret profile/origin/testing diagnostics. No storage/key rotation is implied by this change.

**Regression:** Synthetic markers must be absent from repr while explicit properties remain usable and ordinary configuration checks still pass.

## Targeted dependency and support review

Exact frontend lock versions include Next 16.4.2, React/React DOM 19.3.1 and PDF.js 6.4.299; backend locked versions below were compared with the listed current primary advisories. This was targeted patch/reachability research, not a complete transitive/OS-image scan and not a vulnerability-free claim. No dependency graph was uploaded. Version changes were not justified solely to create audit activity.

| Locked dependency | Primary advisory context / application relevance |
|---|---|
| pypdf 6.21.2 | Patched for reviewed October 21 malformed-xref issues: [GHSA-gmh7-3g9r-mjh5](https://github.com/py-pdf/pypdf/security/advisories/GHSA-gmh7-3g9r-mjh5), [GHSA-jr96-gvgh-j3r4](https://github.com/py-pdf/pypdf/security/advisories/GHSA-jr96-gvgh-j3r4). Relevant to bounded untrusted PDF parsing. |
| urllib3 2.8.0 | Patched for reviewed [deflate loop](https://github.com/urllib3/urllib3/security/advisories/GHSA-gh4c-6fx4-qh6g) and [chunk-line bound](https://github.com/urllib3/urllib3/security/advisories/GHSA-vxq7-64xx-v4gw). Reachable via Requests/Google certificate verification. |
| Requests 2.34.2 | Beyond the reviewed 2.33.0 [temporary-file reuse fix](https://github.com/psf/requests/security/advisories/GHSA-gc5v-m9x4-r6x2). |
| cryptography 50.0.2 | Beyond reviewed 50.0.0 [PKCS7 fix](https://github.com/pyca/cryptography/security/advisories/GHSA-g6cj-pr64-35w5); this app uses Fernet, not untrusted PKCS7. |
| Starlette 1.9.0 | Beyond reviewed fixes for [hostname poisoning](https://github.com/Kludex/starlette/security/advisories/GHSA-jp82-jpqv-5vv3), [form DoS](https://github.com/Kludex/starlette/security/advisories/GHSA-82w8-qh3p-5jfq) and [Windows StaticFiles UNC](https://github.com/Kludex/starlette/security/advisories/GHSA-wqp7-x3pw-xc5r). |

HubSpot's [May 2026 requirements](https://developers.hubspot.com/changelog/app-listing-and-app-certification-requirement-updates-for-may-2026?hs_amp=true) still require API uninstall and disclose super-admin notification. The legacy-labelled uninstall endpoint is therefore not classified as unsupported merely from its label. Revalidate current date-versioned OAuth/CRM transition support, scopes, permissions and uninstall/slot-release behavior during authorized real acceptance; no provider account was contacted in this review.

## External acceptance gates

These are unfinished evidence/operations, not invented passing findings or local defects reclassified to skip work:

- Human security review and hands-on owner acceptance of the runnable app; AFK selection remains provisional.
- Hosted CI execution and image/distro vulnerability review appropriate to an actual release.
- Authorized TLS/cookie/IAM/service identity, Cloud SQL least privilege/backups, actual migrations and populated rollback planning. Keep OAuth query/credentials/contact/source bodies out of operator logs.
- Actual Cloud Tasks enqueue transport, verified OIDC delivery/retry and a reliable funded unattended due-work/expiry/cleanup caller. A prepared handler or local runner does not complete these.
- Authorized real model/embedding selection and finite spend admission, supported answer/retrieval evaluation, HubSpot scopes/owned records/native links/uninstall and install-slot release. Real failures must remain failures.
- Reassess the provisional retained-workspace limit against public exposure, lifecycle and a funded resource budget before publication.

## Remediation disposition

**All six selected remedies verified locally**, 22 October 2026. AFK-0017 selected the actual IDs before changes; [SBS-009C](../tickets/SBS-009C-security-fixes.md) owns detailed implementation and test evidence. Final remediated release-input fingerprint: `01188ea208d46e60973f37b40579fdac90747528ae64e6765ff0e6eaf0d9523e` (83 files). The audit snapshot and initial findings above are preserved.

| ID | Local disposition / actual proof |
|---|---|
| SEC-001 | Serialized all-retained final 256-row admission; three actual-PG tests prove final-slot waiting/winner, retained/unflushed counting, exact429 and atomic reset/session/source preservation. |
| SEC-002 | Registry removal commits under account serialization, no unfenced late overwrite; controlled actual-PG callback/uninstall/old-completion interleaving passes. Ambiguous and auth failures do not free a slot. |
| SEC-006 | Only definitive fake denial is exempt; real unidentified uncertainty persists and identified uncertainty counts once. Twenty-five invalid fake callbacks, absent/prior-uninstalled known-account preflight and late-capacity regressions pass. Eight new CRM security cases, 24 focused CRM/jobs/security tests passed. |
| SEC-003 | Source CSP/nosniff remain in explicit allowlist; three actual-route injected PDF/TXT/authority tests pass. No unrelated private header is forwarded. |
| SEC-005 | 65,536-byte identity-response cap before SDK parse; compression rejected before consumption; one-second read timeout and 12-second monotonic budget checks. Eight real-SDK injected-stream tests pass, including a delayed-EOF defect found and repaired during independent validation. This is not an exact preemptive socket wall deadline. |
| SEC-004 | Three sensitive fields excluded from repr; synthetic marker/access/nonsecret-diagnostic regression passes. |

Settled **105 backend tests**, **11 Node tests**, configured Python lint, unchanged regenerated API contracts and the Windows production frontend build/typecheck passed. Three independent read-only reviewers checked the selected changes and their regressions; no actionable local finding remained in that scope. Required local process/filesystem access was used after sandbox-only ownership/output-write failures. API/runner reloaded and frontend restored with verified ownership. After AFK-0018 refined the local cap to256, the full backend recheck passed **105 tests in63.26seconds** and Ruff passed; owned API/runner were reloaded. Final current-source Linux images and isolated smoke passed **24 HTTP requests /180 assertions**, migration/sample preparation, private worker rejection, one-shot maintenance and owned-resource removal at the final remediated fingerprint above. Receipt freshness and the fresh-browser source check passed. Earlier2e1c01…/128-proposal evidence remains historical; no hosted result is inferred.

These dispositions close the local remedies, not human acceptance or external gates. The final 256-row cap is provisional, live compatibility/activation is unverified, and cloud IAM/delivery/maintenance, real provider behavior, hosted CI/image review and owner acceptance remain pending. No protected external action, vulnerability-free claim or human approval is implied.

Final current-browser verification after AFK-0018: one new fake guest was admitted successfully with genuine CRM skip. Actual public PDF and canonical FAQ text retained sandbox/nosniff/no-store/disposition; desktop1440×900 and phone390×844 rendered Service Guide page2 with real canvas ink and the cited excerpt, reachable Close/focus return and no overflow/page errors. No booking/private upload/provider call was made. `.runtime/security-final-browser-review.json` records the bounded check. The prior capacity rejection and256 refinement are recorded above; existing development data was preserved.
