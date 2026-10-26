# SBS-032 — Default tour and assistant welcome

Status: Complete local —26 October2026. Owner real-account/runnable acceptance remains separate.

## Owner request

The tour must start by default after both Continue without HubSpot and the successful HubSpot setup/return, even if a previous demo's tour was completed. Finish, Skip, Close and Escape return to Customer chat. Reveal a friendly assistant introduction only after the tour has exited, with the existing Moving out with pets, Find a regular clean and Help me choose starters inside its visual card. Recommend document-grounded questions as well as booking, with direct-send shortcuts using ordinary scoped chat.

## Plan and boundaries

- Replace the global localStorage completion veto with a current-workspace/generation UI completion marker in sessionStorage. An explicit entry from either setup path starts a new tour; ordinary refresh/perspective changes within a completed visit do not repeatedly interrupt the conversation. Storage denial cannot block the tour.
- Do not consume the initial tour check while a transient pending action or typed draft prevents it. Merely focusing the composer must not suppress it.
- End the animated tour in Customer chat, then reveal the plain welcome message. Keep it in conversation history, avoid typing replay on ordinary refresh/perspective changes, animate it after deliberate tour exits, and preserve the three starters, four contextual suggestions, reservation shortcut and24-question library.
- Greeting copy introduces Juniper and invites service, preparation and policy questions with original-page links. This is authored orientation, not a retrieved answer or an automatic provider request. Shortcut clicks use the existing chat command and preserve an unrelated composer draft.
- Preserve callback/session/CSRF/OAuth/consent boundaries, existing accounts, no-database mode and running services. No paid provider/account tests, PostgreSQL startup, deployment, staging or commits are part of this UI request.

## Acceptance

- [x] Both setup paths default to a tour despite an old completion preference; direct workspace entry also offers it, while same-visit refresh preserves completion.
- [x] Finish/Skip/Close/Escape leave Customer chat with useful focus, no lingering inert state and no welcome behind the tour.
- [x] Friendly welcome and all three existing starters appear after exit, with guide-question shortcuts and no automatic chat/provider request.
- [x] Welcome stays in history; refresh/role changes do not repeat typing, while every explicit tour exit animates the same welcome. Ordinary shortcuts, draft preservation, pending protection and explicit booking remain.
- [x] Meaningful onboarding/entry/callback/reset regressions, frontend types and responsive rendered checks on phone, short laptop and desktop pass using injected browser/API responses and the existing frontend.
- [x] Read-only final validation reports no remaining actionable finding. Real owner HubSpot/OAuth/AI and hosted acceptance remain separate.

## Findings and implementation

The old `choreograph:workspace-tour:v1=seen` localStorage value disabled onboarding across all later demos. The initial check was also consumed before testing whether focus or an open reader prevented opening, so a focused composer could suppress the tour permanently for that mount. The tour restored its original perspective, allowing a Business replay to end away from chat, and the empty state had starter buttons but no assistant introduction.

Both successful entry paths and navigation recovery now request `?tour=start`, which is consumed after the workspace is ready. Completion uses only an opaque workspace/generation UI marker in sessionStorage; old global preferences are ignored. Pending/draft/reader deferral does not consume the check, and composer focus is not a veto. The tour's existing fade completes before returning to Customer chat and revealing the welcome.

The welcome is a conversation article with the original three starters, three service/preparation/changes questions, existing finite reply text animation and clear-glass styling. It remains above subsequent messages. A newly revealed welcome is brought into view even when older messages were restored; subsequent sends and normal perspective changes keep their ordinary history behavior. Authored introductory copy is not represented as a retrieved answer and performs no background chat call.

## Local evidence and limits

- **165 Node tests passed**, including five new default/forced-entry, deferral, completion/replay and animated exit regressions; callback/session/consent/reset, sharing progress, fallback navigation and native-prompt guards remain passing. `.runtime/sbs032-node.log` records the settled run.
- Frontend TypeScript passed. Final diff/whitespace and ticket-scope review found no remaining actionable issue. No backend schema, API contract, provider configuration or persistence change was required.
- Actual browser checks used the existing frontend on45860 with isolated browser contexts and fully injected app API responses; external requests were blocked. The fixture was produced by the real fake-provider backend against a temporary encrypted object store, without reading the owner's live workspace. Original canonical PDF/FAQ bytes were injected for document thumbnails.
- Rendered **1440×900,1280×720,390×844 and320×740**: no horizontal overflow, composer reachable, welcome starts at scrollTop0, all original starters reachable in the conversation pane. Both skip entry and a sharing-approved callback return were exercised despite prior completion. Full desktop/laptop/mobile tours, Skip/Escape/Close, mobile perspective switching and replay passed; welcome is absent throughout the tour and appears after exit with no remaining inert state.
- One guide shortcut per scenario produced exactly one ordinary chat request and preserved an unrelated draft. Refresh preserved the welcome without repeated tour/typing. Six scenarios, including restored conversation history, produced zero browser errors and zero external requests. Receipts/screenshots are ignored `.runtime/sbs032-browser-result.json`, `.runtime/sbs032-browser-extra-result.json` and `.runtime/sbs032-*.png`.
- The initial sandboxed Node run was limited by Windows process-identity access; isolated fixtures and the settled Node/browser checks ran outside the sandbox. Browser harness source/typing locators were corrected without weakening app assertions. No live OAuth, HubSpot account mutation, paid AI call, PostgreSQL startup or deployment was used for validation.
- The owner's existing frontend/API/runner and real/manual provider settings remain active. Earlier Linux release receipts predate this UI edit; a new release build and actual hosted/owner account acceptance remain separate. Nothing staged, committed or pushed for SBS-032.


## Owner visual/Skip correction —26 October2026

The owner rejected the welcome's extra top-left logo and enclosing card frame. The welcome now uses a plain message-body with the existing text/buttons, without the extra orb, border, shadow or duplicated identity label. The main conversation header and starter-button surfaces remain.

Every explicit tour exit, including Skip at any step and replay exits, returns to Customer chat and reveals the same welcome with the shared normal assistant `new-message` arrival and finite `ReplyText` reveal. It does not append duplicate welcome articles or send an automatic provider request. Ordinary refresh and perspective changes still show it as history. This narrowly supersedes the earlier no-typing-on-replay rule; the prior six-scenario evidence above describes the earlier design.

Focused exit regressions now cover Close/Skip/Escape at the intro and all eight steps, plus renewed welcome animation after an explicit replay exit. Frontend TypeScript passes. The settled165-test Node suite and TypeScript pass. Actual browser validation passed19 Skip scenarios: the intro and all eight steps on1280×720 laptop and390×844 phone, plus a Business-step exit at1440×900. Three additional replay skips reanimated exactly one welcome; refresh retained it without retyping. The shared `workspace-arrive` animation and an intermediate typing frame were observed, with no extra welcome logo/border/shadow, horizontal overflow, browser error, external request or API mutation. Evidence: `.runtime/sbs032-skip-matrix-result.json`, `.runtime/sbs032-plain-welcome-*.png` and `.runtime/sbs032-plain-welcome-node.log`. Final read-only review found no actionable issue. Existing services/provider settings were preserved, PostgreSQL was not started, and nothing was staged or committed.


Owner refresh-outline correction: the blue frame was the welcome article focus-visible outline after the existing reveal restored focus. Removed only that non-interactive article outline; focus/reveal and interactive focus indicators remain. Rendered refresh checks at1280×720 and390×844 confirm no welcome outline/border and a visible3px keyboard outline after Tab reaches the first guide button. Injected API only, no account/provider operations. Screenshots: `.runtime/sbs032-focus-removed-*.png`. No new unit test or broad suite was added for this scoped style correction.


## Owner checkpoint —26 October2026

Following the refresh-outline correction, the owner positively reviewed the welcome appearance, confirmed that no-database mode is working as intended locally, and explicitly requested documenting that confirmation and staging/committing current work. This supersedes the earlier no-staging/no-commit statements for this checkpoint. The exact file allocation lives in `docs/tickets/COMMIT_PLAN.md`; actual Git history owns the resulting commit identities. No additional provider test, deployment or push is authorized or claimed.
