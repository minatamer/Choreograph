# SBS-013 — Complete visitor HubSpot composition and account setup

Status: **Complete local**  
Owning phase: **07-build continuation**  
Depends on: SBS-012 configuration/composition boundary; existing SBS-006/007.

## Outcome and scope

Make real visitor-owned HubSpot selectable independently of AI mode, with no operator fallback and a genuinely skipped path. Wire one owned provider/client per process through API, local runner and private worker, with shutdown cleanup. Do not make real OAuth/CRM calls during implementation.

Persist provider/app identity on connections and OAuth attempts, migrate existing fake identities and reject transport/app mismatch before exchange binding, refresh, export, cleanup or uninstall. Scope pending/unknown admission and private operator counts by app. Replace hardcoded live capacity with explicit distribution-aware bounded configuration: current official unlisted marketplace limit25, private distribution normally10; no cap evasion or unverified higher allowance.

Validate exact callback against configured origin and supported host rules. Real local OAuth uses `http://localhost:45860` consistently for entry/cookie/origin/callback; production uses HTTPS. IP redirects, credentials, query/fragment and cross-origin callback configuration fail closed. Preserve actual server-side callback state/CSRF/session/replay fences and add no-store/no-referrer callback responses.

Complete visitor-account setup: verify scopes/account identity, app-owned unique properties and actual pipeline/stage eligibility. Never silently use an operator account or assume global pipeline IDs work across visitor accounts. Discover bounded eligible account pipelines/stages and require explicit reviewed visitor selection when necessary; store that destination on the connection and fence queued exports against its revision. Schema creation must be explicitly enabled/disclosed, not a hidden side effect.

Bound actual HubSpot requests across API/runner, including refresh, failure, readback and cleanup. Retain conservative uncertain outcomes and honest attention on exhausted/revoked cleanup. Harden prepared transport with identity/raw-byte bounds, final deadline/EOF checks, strict result validation and no blind write retries. Verify current official date-versioned OAuth contracts before wiring them.

Expose independent truthful CRM capability/provider labels and eligible destination choices; fake AI plus real CRM and real AI plus skipped CRM must be accurate. Keep Connect your HubSpot/Continue without CRM, disclosure, explicit export consent, native-link verification, same-account protection and existing visual direction.

## File allocation

CRM owner: `hubspot.py`, `crm.py`, CRM-related `jobs.py` fences, `operator.py`, models and migration `0008`, focused transport/identity/account/capacity tests. Integration owner: provider settings/composition/API/runner/release, contracts/generated types, CRMControls, callback route and actual-route callback tests. Allocate shared files explicitly before edits. Root owns this slice, including new crm_config.py/crm_composition.py/crm_admission.py, connection setup command and callback route tests. No schema/record provisioning or Git action is authorized.

## Acceptance and verification

- [x] Independent configured providers, invalid config fails before network, shutdown closes clients.
- [x] Real-path injected HTTP covers current exchange/refresh/introspection, account setup, owned upsert/readback/association/cleanup/uninstall without real network.
- [x] Old fake/different-app tokens cannot reach a new transport; app-scoped concurrent capacity/unknown handling is conservative and tested on actual isolated PG.
- [x] Visitor pipeline/stage is selected/verified against that account, persists and fences destination changes; true skip produces zero calls/outbox.
- [x] Bounded request admission survives rollback/restart; response limits, failures and retained cleanup references are meaningful tested cases.
- [x] Actual callback route tests and mixed-mode UI/browser checks pass; labels/native links never claim simulated operations are real.
- [x] Focused plus required settled checks and read-only validation pass. Actual HubSpot installation/scopes/notification/slot timing remain unchecked until authorized acceptance.

## References

Blueprint12/12.2/13–14, SBS-011; [official OAuth](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/oauth/working-with-oauth), [distribution limits](https://developers.hubspot.com/changelog/new-marketplace-distribution-app-install-limits), [uninstall requirements](https://developers.hubspot.com/changelog/app-listing-and-app-certification-requirement-updates-for-may-2026). No live credentials, provider/account/cloud/spending/deployment/messages/scanner export or Git permission is supplied.

## Evidence

Implementation is wired through API, local runner and private worker. The provider is independent of AI, disabled/fake modes remain available, provider/app identity is persisted before token use, and finite HTTP grants/calls commit outside the business transaction. A connected visitor must select a bounded account-specific open pipeline/stage and explicitly permit optional demo-ID field creation before separate export consent. No operator pipeline is substituted.

Official current OAuth schema was read from HubSpot's own public OpenAPI repository, September2026 rollout279897: source SHA256 de31e83715649a3831082fbd25752f48cafde7a4c7f7a2ece769eec157323040. It confirms /oauth/2026-09/token and /token/introspect, the introspection form field `token`, and the app_id/client_id/hub_id/token_use/token_type/is_private_distribution response fields. Website migration guidance still describes2026-03; the newer official schema supports the selected September contract. No real OAuth request was made.

Focused evidence:32 CRM/account/identity/transport checks passed on actual isolated PostgreSQL and injected HTTP. Three hermetic tests execute the actual Next callback route and verify server session/CSRF, stable replay key, cross-origin/duplicate rejection, no-store/no-referrer redirects and no leaked code/error. TypeScript/contracts/Ruff passed during integration. Final migration/refresh/late-EOF checks and settled full suite are running.

Read-only validation V1 found two boundary gaps to close: the standalone CRM parser relied on Settings to reject empty/invalid origins, and a direct destination update did not require advancing the connection generation. Add direct parser validation and a database generation fence, then independently revalidate. Actual HubSpot account scopes, permissions, native results, admin notifications and installation slot-release timing remain external acceptance, never inferred from this fixture.


Final revalidation: **189 backend tests passed in78.05s** on fresh isolated PostgreSQL; **14 Node checks** passed, including the actual callback body; generated contracts, TypeScript, backend Ruff and Windows production build passed. Both V1 findings are independently resolved with direct invalid-origin cases and a database destination-generation regression. The old receipt test's fake→real retag is now correctly rejected by the identity constraint; native-link and malformed-ID coverage moved to the complete injected OAuth/setup/upsert/readback flow. No actionable local finding remains in this ticket scope.

Actual components were inspected at1440×900,1280×720 and390×844 using a snapshot produced by the isolated-PG/injected-HTTP flow: setup selection, separate unchecked sharing consent, reachable action, truthful fake-AI/real-CRM capability labels, no horizontal overflow or page errors, and Reset during a waiting assistant all passed. Screens were visually inspected. This UI data is explicitly injected, with zero live calls; receipt `.runtime/integration-browser-review.json` is local QA evidence.

Verified the owned `choreograph-local/postgres` resource and applied preserving migrations0007–0008 to local fake development. Counts matched before/after:190workspaces,6document versions,23chunks,14connections,26reservations. API and runner were stopped by verified ownership only, then restored hidden and ready; frontend was restored after its successful build. The development volume and siblings were preserved. No real keys, account operations, spending, deployment or Git writes occurred.
