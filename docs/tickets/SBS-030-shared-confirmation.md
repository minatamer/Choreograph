# SBS-030 — Reuse designed confirmations and return Reset to connection choices

Status: **Complete locally; owner visual acceptance remains unverified —25 October2026**

## Owner requirements

- Replace Reset demo's browser-native confirmation with the designed Choreograph dialog.
- Audit the complete app for browser `alert`/`confirm`/`prompt` and prevent recurrence.
- Provide a reusable confirmation component and use it for Reset and existing Business booking completion/cancel/decline confirmations.
- Only a confirmed successful reset returns to the HubSpot/without-HubSpot choice screen, using the existing setup transition; cancelling/failing stays in the workspace.
- Preserve existing backend/session/CRM cleanup, explicit consent, motion, pending/unknown-failure guards, keyboard/focus and both Customer/Business reset controls, including the mobile Business drawer.

## File allocation

- `apps/frontend/components/confirmation-dialog.tsx`: shared designed asynchronous confirmation on ExpandingDialog; explicit submit, duplicate/pending/exit locks, failure and focus behavior.
- `booking-action-dialog.tsx`, `workspace-controls.tsx`, `business-sidebar.tsx`, `workspace-client.tsx`: reuse the component; preserve reviewed booking revisions; return successful resets through Next client navigation; close mobile navigation before presenting confirmation.
- `apps/frontend/app/demo/page.tsx`: recognize the explicit connection-choice entry step, reusing EntryClient's existing setup animation/provider state.
- `apps/frontend/app/demo/booking-management.css`: shared confirmation sizing/error treatment within the current glass design.
- `use-dialog-focus.ts`: yield keyboard handling to a top-layer designed human-verification dialog during Reset, preserving its Tab/Escape handling.
- Existing `scripts/booking-action-dialog.test.mjs` plus focused shared/reset/native-prompt regressions: actual compiled components, exact command/navigation boundaries, failure/unmount/replay, entry mounting and keyboard behavior. CI already runs every scripts/*.test.mjs.
- AGENTS.md, blueprint, queue and this ticket: record the permanent native-prompt restriction, actual checks and evidence limitations. No duplicate deployment/provider documentation.

## Initial evidence and authorization boundary

Complete app/source search found only `window.confirm` in ResetDemo. Business booking confirmations already use an app dialog; calendar/source/management interfaces use their existing designed surfaces. Backend test documents deliberately contain hostile alert text; those are ingestion fixtures, not UI prompts, and must remain intact. Audit public scripts separately; do not patch browser APIs globally.

Current worktree already contains deployment docs/budget artifacts and HubSpot test/docs changes from prior owner requests. Preserve those. This task changes no backend command, env/key/mode, current workspace records, real CRM/AI grant or service lifecycle. Do not execute Reset against the owner's live workspace just to test the UI. Use injected callbacks and isolated evidence; existing frontend hot reload is the preview path. No Git/cloud/provider/push action is included.

## Validation and handoff

Run focused behavioral component/route checks, the settled Node suite and frontend types. Inspect the actual dialog without confirming a live reset where a permitted existing browser session allows it. Record unavailable visual evidence honestly. Recheck the complete production source for native prompt calls. Keep transition/focus/command behavior and unfinished hosted/HubSpot acceptance distinct from these UI changes.


## Implementation and actual checks

ResetDemo now renders the shared `ConfirmationDialog`, also used by BookingActionDialog for Business complete/cancel/decline. The component retains ExpandingDialog's spring/backdrop/glass, inert background, focus restoration and keyboard trap; it centralizes asynchronous confirmation, immediate duplicate lock, disabled pending/dismissal controls, unmount fencing and an inline unknown/failure state with no unsafe automatic replay. A named heading binds accessible dialog labelling. No browser API is patched or overridden.

Both Customer footer and Business sidebar await the existing guest reset command. A workspace-scoped reset-intent ref navigates only when the server supplies a different workspace ID, including verified recovery after an uncertain response. Ordinary polling/state revisions or unrelated workspace changes do not trigger that route. Next `replace('/demo?step=connect')` mounts EntryClient with resumeSetup, keeping the shared provider/fresh guest and existing animated setup branch; EntrySetup retains its scroll/focus and clean URL behavior. Cancel/failure does not navigate or re-create a session. The mobile Business drawer closes before the portal opens and supplies its visible menu opener for return focus.

Reset may invoke the existing fresh human-verification flow. The shared focus hook now yields Tab/Escape to a top-layer designed `dialog:modal`, so the underlying confirmation cannot steal the verification widget's keyboard controls. This does not solve/skip a challenge or change verification policy.

**Checks:**19 initial focused component/route/source checks passed; the additional modal-keyboard regression brings the focused set to20. The final complete Node suite passed **134 tests, zero failures/skips**, with output in `.runtime/sbs030-node-final.log`; frontend `npm run typecheck` passes. The first full run's Windows launcher test was blocked by sandbox process-identity access; the authorized outside-sandbox rerun passes and cleans its owned temporary probe. Anonymous no-JavaScript GETs of `/demo/workspace` and `/demo?step=connect` both return HTTP200, proving current hot-reload compilation without invoking guest/provider commands. Authored app/components/lib/public source and the offline overview/assets were scanned; the production native prompt call is gone. The new AST-based CI guard covers explicit/computed/bare/aliased common native-prompt references while allowing local handlers and ARIA alerts; hostile backend document fixtures are unchanged.

**Visual limitation:** browser inventory found only the existing in-app error tab. Selecting it was denied by Browser Use URL policy because the error page is represented as a data URL. No alternate browser/protocol/CDP/fixture-server workaround was attempted and no screenshot/physical-device claim is made. Phone/short-laptop/desktop layout continues through the existing responsive shared CSS; actual owner visual acceptance is still needed. No reset of the owner's workspace, live AI/Cloudflare/HubSpot action, mode/key/data edit, restart, new preview listener, cloud operation or Git stage/commit/push occurred. Cancel an already-open old native prompt and refresh once; frontend hot reload is sufficient.

## Validate pass1 — final relevant worktree against6019c8b

TL;DR: replace the last native Reset prompt, share the confirmation implementation and return confirmed resets to connection choices. The implementation and injected component/route checks cover these requirements; browser visual inspection is unverified.

**Verdict: Meets ticket with concerns. No actionable code findings.** The concern is the explicit visual-evidence limitation, not an identified functional defect.

Coverage: **Covered** — reusable ConfirmationDialog/BookingActionDialog/ResetDemo, explicit one-call confirmation, cancellation/pending/unknown/unmount guards, exact successful-reset route/recovery, existing setup motion, mobile menu closure/focus, top-layer verification keyboard and source-wide native-prompt guard. **Unverified** — actual owner browser/device appearance and live reset/CRM cleanup; the unchanged backend lifecycle is not reaccepted by these frontend tests.

Checks/scope: read-only review of the whole SBS-030 packet, empty staged diff, its current tracked/untracked source/tests/docs and neighboring entry/provider/focus paths against HEAD6019c8b3343d54c99a2ec97b3851b9d24e8ce65e. Prior deployment/budget docs/artifacts and HubSpot test/guide changes are preserved and excluded from this verdict. The134 Node/type/HTTP evidence above was obtained during implementation; validation created no test, ran no new suite, delegated/messaged nobody and performed no external/provider/Git mutation. A fresh Linux release receipt is still required for changed image inputs before deployment.

Current release-input fingerprint after this UI change: `f86622643c2ff894fcaf87759abc8967a7f216700ff2c0f63168630b960b2af0` across196 files. This fingerprint is not a new Linux build receipt. Final whitespace/link checks pass.
