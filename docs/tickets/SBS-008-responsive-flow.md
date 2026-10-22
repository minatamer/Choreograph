# SBS-008 — Verify the complete responsive demo

## Continuation visual review — SBS-012–015

Fresh local fake core review produced18 captures across desktop1440, short laptop1280x720 and phone390, including landing, guided customer conversation, actual coordinator approval/calendar, Documents and page2 source reader. Three actual-component injected-account setup captures passed separate schema/export consent, destination selection, reset during pending work, no horizontal overflow and zero page errors. The latter is a PostgreSQL/MockTransport snapshot, not a real HubSpot connection.

The document browser check initially assumed a business-library open would default to the pet paragraph. Independent source-reader inspection confirmed it has no citation selection and correctly uses its first ordered page passage. The scoped harness now verifies that exact real passage, the presence of the revised pet instruction in metadata, replacement PDF SHA bytes, actual page canvas and refresh. All four sizes1440/1280/390/320 pass with no overflow/page errors. No app behavior or visual design was changed to satisfy an excerpt-order assumption. Screenshots of phone setup, reachable customer composer/Send, narrow PDF/excerpt and short-laptop Business view were manually inspected by the agent. Existing colors, type, cards, motion and explicit approval remain. This is a provisional AFK self-review; owner runnable acceptance and Figma editing/privacy remain outstanding.

Status: **Complete local**
Owning phase: **07-build**  
Depends on: **SBS-005, SBS-006, SBS-007**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

Settle the complete actual local fake-provider visitor story against approved key designs. Figma is deliberately compact; every implemented flow still needs phone/tablet/short-laptop/desktop usability, keyboard and recovery.

## Implementation scope

1. Walk landing/entry through both starters, source guidance, weekly alternatives, quote, submission, business approval and simulated connected/skipped outcomes; verify same records and no replay on refresh/role switch.

2. Exercise actual source selection, Documents replacement/ready/re-ask, real page and honest excerpt fallback. Keep quote/calendar/document authority distinct.

3. Cover reschedule/cancel/complete, stale cards, true competing-approval conflict, retry/attention, reset/expiry and denied/capacity/unavailable CRM. Label injected scenarios clearly.

4. Inspect keyboard/IME/focus and reachable composer/approval at phone, tablet, short laptop and desktop. Samples remain visible in configured modes; headers continuous and motion purposeful/interruptible. Remove confirmed filler/technical public logs/duplicate logic.

5. Compare rendered key surfaces with retained native design source/tokens/renders. Do not claim a fresh quota-blocked Figma extraction, real AI/HubSpot or hosted acceptance. Only repair demonstrated scoped defects.

## File allocation and cohesive commit plan

Actual frontend feature/style/state owners and narrow confirmed backend fixes; browser checks/screenshot receipts; actual command docs. Allocate each confirmed fix to its owner; no broad cosmetic refactor.

## Acceptance criteria

- [x] Complete suggested journeys and lifecycle/recovery work against real API/PostgreSQL
- [x] readable reachable responsive states are inspected
- [x] restore/retirement and guest isolation are correct
- [x] settled code/DB/build gates pass with honest external limits.

## Meaningful verification

Actual browser journeys and keyboard/short viewport checks; relevant settled lint/type/unit/DB/build gates once cohesive. Avoid CSS/wording mirror tests or repeated unrelated funded operations.

## Precision references

- [Blueprint: 17-verification-that-matters](../CHOREOGRAPH.md#17-verification-that-matters)
- [Blueprint: 6-customer-and-business-surfaces](../CHOREOGRAPH.md#6-customer-and-business-surfaces)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Completed the connected busy-first-choice journey from landing through actual source page 2, $185 quote, review, approval and simulated read-back, then replaced the preparation PDF and re-asked the pet question. The new answer cites the replacement and the reservation stays unchanged. The skipped open-week journey also reaches approval/booking. Refresh preserves records and reset creates an empty isolated workspace. `node scripts/inspect-flow.mjs` passed at desktop 1440×900 and tablet 768×1024, including saved detected timezone (Chromium resolves the Kathmandu alias as Asia/Katmandu).

Confirmed and fixed recovery defects: status polling now survives transient failures with finite attempts and a visible retry path; expired initialization/mutations/polls remove retired content; missing timezone detection plus lost cookies requires a new choice. Accepted chat retry clears only the unchanged accepted text, and a newer question selected while an earlier Send is pending stays unsent. Source readers capture return focus once, preserve current Escape handling, skip disabled controls in focus wrapping and return to the initiating citation/guide button or composer. Explicit CRM skip fences its pending OAuth callback; revoked authentication shows attention without stale receipts/links. Added API regressions for unverified exchange/scope failures and conservative installation tracking, and a refreshed competing-approval loser now proves TIME_OCCUPIED after revision fencing.

Actual checks on 22 October 2026:

- Backend settled suite: **68 passed**, actual uniquely named PostgreSQL/pgvector database and forced fake providers. One PDF-fixture deprecation warning remains. The bounded expiry test was corrected to drain due batches instead of assuming its fixture belonged to the first batch; production maintenance limits were preserved. After safe lint/import cleanup, affected booking/jobs subset: **13 passed**.
- Frontend typecheck and actual host production `next build` passed. Only the owned frontend was stopped/restored; API, runner, development volume and sibling apps were preserved. This is a Windows host build, not Linux/cloud evidence.
- Scoped Ruff check for crm.py and test_booking.py/test_crm.py/test_jobs.py passed. The first broad lint inventory found 91 import/idiom/boundary findings before these scoped cleanups; repository-wide cleanup remains owned by SBS-009A and is not claimed passed here.
- `inspect-accessibility.mjs`: desktop, short laptop, tablet, 390px and 320px phones; 24 keyboard-reachable questions, three starters, IME composition events, Enter/Shift+Enter, PDF/FAQ focus return/wrap, actual PDF rendering and honest excerpt fallback. At a reduced 420px phone height Send remains reachable. Focused `--retry-only`, `--pending-only`, and `--timezone-only` checks passed accepted-text clearing, preservation of newer edits and required timezone recovery.
- `inspect-poll-recovery.mjs`: transient injected response recovers automatically; actual expiry of a fresh fake fixture retires content during polling and on the first mutation with **zero polls** in the skipped path. `inspect-crm-recovery.mjs`: explicitly injected capacity-unavailable status and unavailable callback return keep the actual skip route usable. Backend capacity/failure tests cover authoritative states independently.
- Refreshed landing/entry screenshots at 1440×1000, 1280×720, 390×844 and 320×740 passed no overflow/page errors. Inspected current phone and short-laptop landing, narrow reader and prior booking/cleanup renders against retained Figma tokens/native authoring sources. Neutral/blue, Google Sans Flex, glass, bubbles and continuous headers remain. No new Figma extraction or frame collection was made.

Read-only validation found mutation-expiry, pending-question and no-zone/cookie-loss gaps; each was independently confirmed, fixed and covered. Final revalidation: Meets ticket in reviewed local scope, no actionable findings. Native device keyboard/IME remains unverified; tests use Chromium composition events and reduced viewport simulation. Real AI/HubSpot, actual Linux builds, hosted IAM/recovery and owner runnable-app acceptance remain separate. All changes are unstaged/uncommitted. Next eligible build ticket: SBS-010 release packaging; later quality/security gates remain outstanding.

## Phase 09 provisional runnable visual review

After phase 08's source/reader changes, `scripts/inspect-visual.mjs` captured 18 current viewport PNGs indexed in ignored `.runtime/visual-review.json`. It reused one fake/CRM-skipped workspace per run across desktop 1440×900, short laptop 1280×720 and phone 390×844; initial request/conversation preparation was synthetic API setup, while approval was an actual UI action. Landing, grounded conversation, occupied seven-day calendar, confirmed Business card, six-document area, desktop approval and actual Service Guide page 2 on desktop/phone passed. Send/approval/booking actions were reachable, rendered canvas identity and ink/excerpt resolved, close returned focus, and no horizontal overflow/page errors occurred. A screenshot-anchor correction caused one extra isolated fake workspace; no CRM installation/private upload was created.

Primary visual inspection covered current desktop conversation, short-laptop landing, phone calendar/confirmed Business card and phone source page, alongside retained approved Figma native construction/token evidence and previous unaffected CRM/error renders. The neutral/blue Google Sans Flex, rounded bubbles, glass controls and header/hero direction remains intact. Page text is readable via zoom and the honest supported-excerpt reader; no decorative PDF evidence or pixel-perfect claim. No additional visual change was justified. This is an **AFK provisional self-review**, not owner runnable acceptance; human app review, native keyboard/IME, Figma hands-on editing/privacy and funded/hosted acceptance remain pending. No new Figma extraction or mobile frame set was created. Next: SBS-009A quality, then security review/fixes and final release refresh.

