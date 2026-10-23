# SBS-013 — Complete visitor HubSpot composition and account setup

## Owner correction: public real-or-skip HubSpot flow,23 October2026

The owner rejected the public simulated-account approval step. The two visitor paths are now **Continue with HubSpot** and **Continue without HubSpot**. CRMControls no longer renders a challenge, simulated consent, fake callback action or fake-connected presentation. It accepts an authorization URL only from a non-simulated OAuth response and immediately navigates there. Only a configured HubSpot provider can enable the connection action or display connected/setup controls. Existing destination selection, explicit fictional-record export consent, cleanup/uninstall controls and provider/app/session fences remain. Those are real account/data approvals, not the removed simulated-account step.

The official primary HubSpot SVG is copied byte-for-byte from the [corporate newsroom's logo pack](https://www.hubspot.com/newsroom), including its original wordmark typography and current orange artwork. Source ZIP: `https://www.hubspot.com/hubfs/WBZ%202025%20Rebrand/HubSpot%20Logo/HubSpot%20Logo%20Zip/HubSpot%20Logos_2025.zip`, entry `HubSpot Logos_2025/HubSpot_Logo_Primary.svg`. The local asset is `apps/frontend/public/brand/hubspot-logo.svg`. No font imitation, recolouring or partnership claim was added. [Developer Terms](https://legal.hubspot.com/hs-developer-terms) and [trademark guidance](https://legal.hubspot.com/tm-usage-guidelines) were reviewed for referential integration branding.

Runtime defaults and fresh setup now select disabled CRM; isolated tests still select fake CRM or explicitly inject transports. The actual ignored backend env's CRM selector was changed to disabled without printing or altering credentials, AI mode or other settings. The fake adapter/API contract remains for isolated deterministic tests; visitors cannot enter that flow from the UI. Local AI remains fake. The existing real transport is retained; actual OAuth cannot be enabled until an app/client secret, matching localhost origin/callback and finite allowance are configured. Disabled/capacity-unavailable paths remain honest and permit the full no-HubSpot demo.

[The free test-portal and OAuth guide](../../infra/README.md#free-hubspot-test-account-and-real-oauth-setup-23-october-2026) owns the account-creation steps, current CLI workflow, required scope/callback/configuration and source links. Official docs describe free developer test portals; paid Enterprise sandboxes are a separate product. HubSpot's Egypt partner directory supports expected availability but does not prove this owner's personal registration or verification. No account, app, credentials, real OAuth exchange or provider records were created during this work.

Actual checks:

- Eight configuration/setup tests and39 CRM/live-transport/security regression tests pass. The latter use actual isolated PostgreSQL with fake/injected transports, not HubSpot. Frontend TypeScript, affected Ruff and whitespace checks pass.
- Real running UI inspection at1440×900,1280×720,768×1024,390×844 and320×740 finds the official logo loaded, no horizontal overflow, no simulated consent, the real connection unavailable until configuration, and an enabled Continue without HubSpot action. That action reaches `/demo/workspace` with Sample mode, Africa/Cairo, HubSpot not connected and no alert. Browser warning/error logs are empty. Ignored receipts: `.runtime/hubspot-real-choice-responsive.json`, `hubspot-real-choice-final.png` and `hubspot-real-choice-phone.png`.
- Owned runner16764 and API19332 plus their recorded descendants were stopped and verified absent before replacement. New API supervisor34288 is ready on45861, with log `C:/Users/minat/Work/Choreograph/.runtime/api-7df37ad1-f1cd-4995-b8b7-73a4fcd3e8d5.log`; new runner9708 has current readiness, with log `C:/Users/minat/Work/Choreograph/.runtime/runner-3167758c-703f-4087-bc89-ec6265809d32.log`. Frontend supervisor16548 stayed on45860, log `C:/Users/minat/Work/Choreograph/.runtime/frontend-d6e24e1a-2a73-4453-a424-62320c5bea63.log`; the database/volume and siblings were preserved. The run/restart/kill skills' scoped lifecycle checks were used.

No Git write, deployment, Figma update, new listener/preview route, paid provider or account action occurred. The actual HubSpot account/consent/native-record/Free-plan entitlement and hosted acceptance gates remain unverified. The historical fake-connected browser evidence below is superseded as a visitor design, while its isolated backend testing remains useful.

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
