# SBS-009C — Apply selected security remedies

## Continuation11 disposition

The fresh SBS-012–015 review confirmed no new substantial local finding. Under the recorded provisional AFK no-fixes disposition, phase11 requires no additional code change. Earlier SEC-001–006 remedies remain and227 backend/15 Node regressions pass. Actual owner/security/provider/hosted acceptance remains open; no Git write or external scanner/account action was performed.

Status: **Complete local; human security review remains pending**  
Owning phase: **11-security-fixes**  
Depends on: **SBS-009B recorded selection**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

Implement only actual findings selected through the recorded human/AFK security review. Preserve original audit guidance and do not treat unknown or newly discovered findings as selected by default.

## Implementation scope

1. Read exact selected findings and independently confirm/reproduce each. Record concrete source/test file allocation before edits and apply the narrow justified remedy.

2. Add meaningful regression checks, validate settled changes read-only and independently disposition findings; repeat only for actionable defects. Preserve accepted flow, diagnostics, limits, design and state authority.

3. Retain unselected/deferred external issues with reasons. Update review status from actual proof; no paid/cloud/Git permission arises from AFK selection.

## File allocation and cohesive commit plan

AFK-0017 explicitly selected SEC-001 through SEC-006 after the audit artifacts existed. Only these source/test owners plus security evidence are allocated:

- SEC-001: `apps/backend/choreograph/sessions.py` and a new isolated-PG admission regression module; shared creation path only, no migration or eviction.
- SEC-002/006: `apps/backend/choreograph/jobs.py`, `crm.py`, new CRM security regressions and the existing known-account uncertain-failure expectation in `tests/test_crm.py`. Retain conservative uncertain real outcomes.
- SEC-003: the existing Next demo bridge route and `scripts/bridge-source.test.mjs`; root adds the new test to the existing CI gate. No broad frontend refactor.
- SEC-004/005: `apps/backend/choreograph/settings.py`, `providers.py` and focused synthetic/hermetic regression modules. No live profile/model selection.
- Root owns this packet, original audit disposition, main canonical state and final settled gates. No shared-file concurrent formatter writes. Suggested finding-ID commits are plans only; Git writes remain unauthorized.

## Acceptance criteria

- [x] Only selected findings change
- [x] each has confirmed disposition/regression proof
- [x] no actionable local finding remains and affected settled gates pass
- [x] deferred/unknown checks stay honest.

## Meaningful verification

Focused security regression and relevant DB/frontend/boundary checks. No unrelated live/scanner/export action.

## Precision references

- [Blueprint: 17-verification-that-matters](../CHOREOGRAPH.md#17-verification-that-matters)
- [Blueprint: 14-guest-isolation-retention-and-cleanup](../CHOREOGRAPH.md#14-guest-isolation-retention-and-cleanup)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Implemented all six actual findings selected by AFK-0017; no additional finding was silently selected. Original audit evidence remains in [SECURITY_REVIEW.md](../security/SECURITY_REVIEW.md). Three independent read-only reviewers checked another owner's source/regressions; no actionable finding remained after the response EOF fix below.

- SEC-001: shared PostgreSQL advisory transaction lock, explicit flush and count of all retained rows before admitting a workspace. The final 256-row provisional local cap returns fixed 429 without eviction. Three new actual-PG tests cover a truly waiting concurrent final-slot contender, retired/unknown/unflushed rows, same-transaction repeat creation and failed real-API reset preserving cookie, zone, generation, revision, draft, calendar and private source/manifest. Test-owned fill rows are removed and the original fixture count restored.
- SEC-002/006: verified uninstall registry removal commits under account serialization; late job completion never writes that registry. Only definitive fake `CRM_DENIED` stops reserving capacity; unidentified real uncertainty remains unknown, while identified uncertainty occupies one conservative registry entry, including previous uninstalled rows. Eight new actual-PG cases cover the controlled two-workspace callback/uninstall/late-completion interleaving, ambiguous/auth failure, 25 invalid fake callbacks, uncertain nonfake denial, known-account/preflight and late-capacity cases. Focused CRM/jobs/security run: **24 passed**.
- SEC-003: explicit bridge response allowlist retains source CSP/nosniff. Three hermetic tests execute the actual transpiled route for PDF/TXT, assert body/no-store/disposition/sandbox and rejection of unrelated sensitive headers, internal routes and cross-origin writes. Added this test to the existing no-key CI gate; hosted CI was not run.
- SEC-004: only database URL, bridge secret and token key use `repr=False`; synthetic regression preserves explicit field access and nonsecret diagnostics.
- SEC-005: the prepared transport requests identity encoding, rejects compression before any body decode, rejects malformed/oversized declared length and caps actual identity bytes at 65,536 before SDK/error materialization. It closes upstream on every path, retains no retries/fallback, uses a one-second read timeout and checks a 12-second monotonic budget before/after reads. This is not an independently preemptive socket deadline. Eight new real-SDK MockTransport tests cover oversized success/error bodies without length, compressed expansion rejection before consumption, declared length, delayed chunks, valid strict output and delayed EOF. Independent review caught the EOF branch skipping its final budget check; root reproduced and repaired it, and the new regression/recheck pass. Ordinary configuration remains fake-only.

Settled verification after all selected changes: **105 backend tests passed in 62.36 seconds**, **11 Node lifecycle/bridge/private-identity/source tests passed**, full configured Ruff passed, generated OpenAPI/TypeScript files were regenerated and hash-unchanged, and the Windows production frontend build/typecheck passed. Sandbox-only lifecycle ownership access and standalone-output writes failed initially; the same checks passed with the required local process/filesystem access. Those environment failures were not represented as application success. No live provider, scanner export or cloud call occurred. The owned API/runner were reloaded and frontend restored; all three report verified ownership/readiness. Development PostgreSQL/volume and siblings were preserved.

SEC-001's final 256 retained rows remain an AFK local default, not a funded public capacity decision. Provider compatibility/live activation, genuine uninstall/slot timing, hosted IAM/delivery/maintenance, image review and human security/runnable acceptance remain external. Final phase12 SBS-010 Linux images/receipt were refreshed and passed on this changed source (24 HTTP requests / 180 assertions); SBS-011 has a concrete finite external plan but no real execution.


## Final admission refinement

The last current-browser check exposed 189 retained pre-remedy development rows (97 active, 92 retired), already above the original 128-row proposal. Its session admission failed; no browser source action was treated as passed. Aggregate counts were read without content or credentials. AFK-0018 refined the selected SEC-001 local cap to **256**, leaving finite headroom while preserving every existing guest and unresolved cleanup reference. Only the constant and the regression target changed; all-retained counting, transaction serialization, 429, failed-reset rollback, provider installation cap25 and retention remain unchanged. Phases11/12 were reopened for the actual backend recheck, API/runner reload, current browser check and new source-fresh Linux receipt. The original128 proposal and earlier receipt remain historical evidence. This is a local default, not funded public capacity approval.

Refinement recheck: the full isolated PostgreSQL suite passed **105 tests in63.26seconds**, and configured Ruff passed. Independent read-only review found unchanged admission/rollback authority. Owned API/runner were reloaded; frontend remained running. The single bounded fresh-browser retry returned200 with fake profile/trueCRMskip. Public PDF and FAQ TXT retained sandbox/nosniff/no-store/disposition; actual Service Guide page2 canvas/ink/excerpt, Close focus and overflow/error checks passed at1440×900 and390×844. Root also inspected the phone source screenshot. Runtime browser evidence is ignored `.runtime/security-final-browser-review.json`; no booking, private upload or provider call was added by this final check.
