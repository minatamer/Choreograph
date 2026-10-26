# Lessons learned for Choreograph

**Selected deployment,26 October2026: NO DATABASE (`DATABASE_ENABLED=false`).** Use encrypted private GCS objects, three scale-to-zero Cloud Run services, Cloud Tasks and authenticated minute Scheduler maintenance. No Cloud SQL, hosted PostgreSQL/pgvector, SQL migrations, database secret or always-running WorkerPool is required. PostgreSQL remains an optional `true` implementation; dated SQL-first designs and test receipts are historical. Database-specific lessons below apply only to optional SQL compatibility, not a hosting prerequisite.

Merged guidance · prepared 21 October 2026; project alignment updated 22 October 2026 · Prepared from the Retailor-derived lessons used in Roomedy and fresh evidence from Roomedy itself.

## How this document was assembled

The existing reference is Roomedy's **LESSONS_FROM_VISUAL_FEEDBACK.md**. It was originally prepared from four owner-referenced Retailor feedback chats and later updated with direct Roomedy corrections. It is the requested inherited lessons document, rather than a newly invented replacement for those earlier lessons.

The new Roomedy contribution below is derived from its current product/ticket authority, review checklist, local implementation and recorded real-provider test/fix results. Both sources are merged into one adapted guide here; separate inherited and newly written source copies are intentionally not left in this packet.

This is a reusable build reference, not an instruction to copy another product. The service-booking blueprint controls the new app. Historical integration/Figma assumptions yield to its current decisions; completing a documentation task does not authorize design execution, ticket creation or live provider work. Roomedy's 3D geometry, palette, camera, export formats, runtime model, funded limits, old approval gates and local service ports do not become requirements for a booking product.

The source lessons attribute earlier chat evidence; this preparation did not reopen all four chats or visually re-inspect their historical screenshots. Current Roomedy validation receipts are reported evidence from that repo, not newly rerun tests or proof that the future booking app works.

## 1. Inherited Retailor lessons, adapted once

### I-01 — Build the complete visitor story before expanding features

Choose a recognizable input, useful transformation and explorable result. In this product the story is request → clarification → quote → review → reservation → CRM outcome. A polished list of dashboards and integrations without that path is not a successful demo.

Keep the portfolio demo, a client's commercial MVP and a full SaaS distinct. One working CRM connection and a correct scheduling invariant are more useful than five decorative integration logos. Extra accounts, queues and storage should have a job; here durable server authority and delivery are justified; encrypted object storage implements that authority without a hosted database.

### I-02 — Give each piece of copy or chrome a visitor task

A badge, setting, note, chip, CTA or panel should help the visitor decide or act. Omit repeated status slogans, implementation terminology, proof badges and filler inserted to occupy space. Keep essential uncertainty, transfer disclosure, clear field errors and deliberate confirmation without turning every screen into a warning sheet.

Apply this to the request page: useful questions, selected services, exact quote and next action. The public UI need not explain database locks or advertise a queue.

### I-03 — Fix the owning component and preserve the scope of feedback

Read exactly what the owner wants changed and which surface it affects. Correct the shared owner across appropriate variants; do not layer a local CSS override onto every screen or redesign unrelated components. Preserve explicitly liked colours, typography, backgrounds and interaction behaviour.

A request to simplify a quote card is not permission to remove price provenance. A change to application chrome must not rewrite the configured cleaning company's catalogue or accepted job data.

### I-04 — Spend space on the task

Test wide, narrow, tall-tablet and short-laptop layouts. Avoid both dead columns and giant full-height cards containing one sentence. Give conversation, proposal and calendar useful dimensions and rearrange them as the viewport changes. Preserve deliberate breathing room; removing dead space does not mean filling every gap.

Keep the composer and primary confirmation action reachable. If a panel expands, preserve enough context to understand the job being reviewed. Prefer natural mobile document flow to several competing scroll wells.

### I-05 — Use representative, connected previews

The product preview should resemble what the app can actually do. Real controls must affect the same underlying data used by the quote, calendar and detail views. A hover state or selected chip that does not change anything is a defect, not a completed interaction.

An offline HTML concept can be scripted, but say so once clearly. It cannot report actual OpenAI, HubSpot, database or cloud acceptance. In the future app, a Synced status requires a real confirmed integration outcome in live mode.

### I-06 — Keep identity and text stable

Use coherent tokens for type, colour, spacing, motion and controls. Refresh, font loading, route entry and restored state should not change wordmark dimensions, jump primary actions or shrink chat into unreadable text. Verify actual rendered output; shared variable declarations alone do not establish consistency.

Use the new product's selected brand. Copy useful engineering from siblings without importing their visual identity or unrelated features.

### I-07 — Motion should explain a change and remain smooth

Coordinate related layout changes, make transitions interruptible, and keep loading responsive. Wait for actual readiness when a resource is required; do not introduce arbitrary delays to hide work. Avoid repeating a welcome or typing animation after unrelated state updates.

For booking, animate the reviewed request becoming a calendar appointment and the integration status settling. Do not add a heavy 3D hero because Roomedy has one. Profile the actual bottleneck instead of substituting animation suppression for a repair.

### I-08 — Make chat functional and friendly first

Provide reachable Send, Enter/Shift+Enter, IME-safe handling, useful clarification and contextual replies. Preserve draft text and focus after recoverable failures. Reply choices belong near the composer; old suggestions must retire when their context no longer applies.

The assistant can explain and guide without creating an edit every turn. Confirmed receipts should match the exact applied action. Friendly language does not justify invented appointments or CRM success.

### I-09 — Separate input, processing, review and application

Selecting a sample or preparing an input is different from sending it to a model. Interpretation produces a proposal; a human accepts a quote/request; backend approval creates a reservation. Keep those boundaries visible in both code and UI.

An imperfect but usable extraction should remain editable. A missing property size can become one clarification, not a technical failure that discards the entire enquiry. A refusal, malformed response and timeout still need distinct honest outcomes.

### I-10 — One canonical model and mutation authority

Charts, totals, calendars, forms and assistant actions must agree because they use the same domain rules. Server code owns price/duration and reservation changes. Presentation code formats accepted values rather than recalculating a second version of the quote.

Use narrow adapters and application commands. Avoid a separate mutation pathway for chat or a dashboard-only edit that bypasses approval. Keep pure domain rules testable outside framework startup.

### I-11 — Fence reset, restore and asynchronous results

Every result belongs to a workspace, generation, record revision and input. A late model response or CRM task cannot restore a retired session, overwrite a manual correction or recreate a cancelled booking. Restore semantic data, not old provider availability, credentials or permission flags.

Test reset during processing, reset followed by a sample, refresh during cleanup and expiry after a sleeping tab. For the new database-backed product, retire access immediately while retaining the minimal durable references needed to finish external cleanup.

### I-12 — Keep diagnostics useful and private

Record fixed failure-stage/rule codes, timings, attempt counts and opaque references. Distinguish interpretation, normalization, business-rule rejection and external API failure. Do not print raw requests, chat, contact details, model payloads, cookies or secrets.

The visitor gets a helpful error and next step; the operator gets enough safe context to diagnose it. A polished interface should not require removing diagnostics from the server.

### I-13 — Verify behaviour at the right boundary

Use deterministic fakes for domain/API tests, appropriate real dependencies for their distinctive guarantees, and actual rendered inspection for visual changes. Run focused checks during iteration and the established relevant gates after a cohesive settled change. Avoid tests that merely mirror labels, selectors or CSS declarations.

Historical image hashes are not a deterministic unit-test oracle. A release verifier must reject stale proof; ordinary unit tests should use controlled stale/current fixtures rather than assuming a checked-in release is always fresh.

### I-14 — Preserve the selected runtime and isolate siblings

Use hot reload for presentation work. Restart only the owning service when required; verify actual process/listener ownership and never kill by executable name or port alone. A test suite must independently force safe provider settings and isolated storage instead of inheriting a manually enabled live environment.

Do not read another repo's ignored keys, reuse its volume or edit its ports. A style revision does not justify repeating a paid provider walkthrough or rebuilding every sibling app.

### I-15 — Keep quality and security proportionate

Fix demonstrated defects, stale ownership, leaks, unsafe boundaries and unnecessary work. Avoid speculative services, cosmetic mass rewrites and splitting a controller solely to meet a line-count preference. Inspect framework entry points, workers, dynamic assets and public exports before deleting apparently unused code.

Record dependency findings with actual installed-version/reachability/patch context. Passing tests or a scanner count is not a blanket security guarantee. Preserve accepted functionality while repairing confirmed problems.

### I-16 — Evidence and permission do not transfer

Fake tests, real-provider quality, actual Linux runtime, cloud IAM, public domain delivery and owner visual acceptance are separate claims. Name what actually ran, on which source/mode/input, and which checks remain unperformed.

Earlier approvals to use paid AI, commit or deploy a sibling do not authorize those actions here. Preparing this documentation packet authorizes no account setup, external write or spending. Routine reversible choices inside the requested document work can proceed without repeatedly asking.

## 2. New lessons from Roomedy's implementation

### R-01 — Solve readiness causes instead of adding timers

Roomedy's landing work exposed a gap between a loaded page and a prepared 3D frame. Its implementation moved preparation to actual resources and initial work rather than using a cosmetic timeout. Later performance revisions addressed expensive photographic filters and redundant layers while preserving the desired motion.

**Apply here:** a request is ready when its schema, quote and eligible actions are ready. Do not display “confirmed” after a set delay, animate fake processing percentages or claim CRM success because an animation finished. A delayed worker can be pending without freezing the rest of the app.

Evidence: RM-015M/O/P and their recorded follow-ups. GPU-specific mechanics are not requirements for the booking product.

### R-02 — Treat semantic facts separately from presentation defaults

Unknown-size photo furniture initially appeared as tiny markers. Roomedy introduced illustrative dimensions for presentation while preserving unknown measurements in semantic records, checks and exports. A useful preview did not become fabricated certainty.

**Apply here:** showing a suggested duration or date is not customer confirmation. Keep inferred, catalogue-calculated, customer-reviewed and coordinator-approved values distinct. A placeholder staff card must not become an actual assignment. Only an accepted booking transaction creates a confirmed appointment.

Evidence: RM-015BL successful live photo adoption and preview repair; RM-015BK editable photo estimates.

### R-03 — Keep inferred output easy to correct

Roomedy's photo estimates needed the same finish controls and useful size editing as manual pieces. New defaults became editable while deliberate visitor locks/corrections survived subsequent processing. Removing editability to make uncertain AI output seem final would have reduced usability.

**Apply here:** let the visitor correct the service, property size, add-ons and dates before acceptance. Preserve their explicit correction during a new interpretation. If recalculation changes a quote, show it for review rather than silently treating an old acceptance as valid.

Evidence: RM-015BK, RM-015AN and the BL finish/Undo observations.

### R-04 — Share authority between direct controls and AI

Roomedy's manual and Medy actions ultimately share semantic commands, final constraints and review/Apply paths. Model prose never grants a capability or widens the target scope. The same final checks apply regardless of how a request was expressed.

**Apply here:** chat and the calendar both call the same reschedule command. A cancellation proposed by AI still requires the same scoped confirmation and version check as the button. Neither can bypass the database overlap constraint or modify another guest workspace.

Evidence: RM-015AT capability audit, spatial command boundary and RM-015BL constrained-layout tests.

### R-05 — Broad capabilities do not require broad tools

In Roomedy's actual live review, a deterministic arrangement tool already prepared a valid proposal, but an additional model-authored preparation step could fail. The offered tool surface was simplified to finish after the computed proposal. The local strict preparation/compiler remained authoritative.

**Apply here:** calculate quote/find slots should return a valid revision-bound result that the UI can review. Do not make the assistant reconstruct it through a second tool solely for architectural neatness. Avoid arbitrary SQL, arbitrary API URLs or generic “execute action” tools.

Evidence: RM-015BL tool simplification, fewer live rounds and final successful constrained-layout preview.

### R-06 — Provider compatibility and application strictness are different

Roomedy's real tests found that the adapter rejected a valid image-part count and documented response variants, including reasoning content/tool metadata. Those failures occurred before useful domain interpretation; no amount of fake UI polish could establish compatibility.

**Apply here:** normalize documented provider envelopes into a narrow internal representation. Reject unsupported actions and malformed domain arguments without rejecting harmless valid optional transport fields indiscriminately. Capture representative compatibility fixtures with safe synthetic content, and verify current official API behaviour before spending on a large live test.

Evidence: RM-015BL first-batch decoder/image-parts repairs. These are historical Roomedy findings; do not claim the new provider adapter has been tested.

### R-07 — Diagnose the stage before changing the prompt

The Roomedy receipt separated pre-dispatch rejection, actual provider parsing, hypothesis validation and command failure. Fixed diagnostic categories allowed targeted repairs and avoided logging private photos or whole model output.

**Apply here:** distinguish missing information, extraction failure, quote policy rejection, reservation conflict, task delivery failure, CRM authentication failure and ambiguous remote outcome. A booking conflict should not trigger another paid AI call. A revoked CRM credential should not be retried as a transient network failure.

Evidence: RM-015BL typed diagnostics and privacy canary regression.

### R-08 — Test repairs economically, with fixed expectations

Roomedy used offline red-to-green checks between bounded real retests. The recorded four-photo request had explicit expected objects; subsequent UI repairs reused accepted data without repeating the photo call. Successful and failed operations remained in the evidence.

**Apply here:** define a small request corpus and expected exact quote/slot outcomes. Reproduce a defect with fake/synthetic fixtures, fix it, then repeat only the affected real provider operation when authorized. Do not change expected results to accommodate every model mistake or spend again merely to obtain a prettier screenshot.

Evidence: RM-015BL baseline, photo retests, constrained-layout retest and later no-new-paid-call UI follow-ups.

### R-09 — Contextual suggestions belong to current state

Roomedy moved quick replies above the composer and retired obsolete choices. A cancelled preview initially left a stale review suggestion; a truthful receipt and current-message identity corrected it. Friendly greetings also needed routing that did not incorrectly demand a furniture target.

**Apply here:** show a few relevant replies near the input. “Choose a time” disappears after a time is selected; “Review cancellation” disappears after Cancel. A greeting does not need a booking ID. Never let an old suggestion act on an expired quote or reservation revision.

Evidence: RM-015BI/BJ and RM-015BL conversational/cancellation checks.

### R-10 — Public samples must exercise the real intake

Roomedy's latest correction makes sample photos visible immediately in both live and fake modes. Selecting them prepares ordinary inputs; a deliberate Continue still performs normal real processing. Sample visibility is not an environment switch or a licence to return fake live output.

**Apply here:** sample enquiries are first-class public inputs and stay available in live mode. Selection fills the ordinary composer. Send uses the configured provider and normal admission. Keep clearly labelled simulated failure scenarios separate from live provider acceptance.

Evidence: RM-015BL public-sample follow-up and actual prepared-sample observations.

### R-11 — Review the whole geometry of the interaction

Roomedy needed repeated corrections to card height, useful width, short-screen scrolling, composer size, touch targets and control ownership. A surface can pass a desktop screenshot and still hide its next action on a phone or a short laptop.

**Apply here:** inspect the full quote, slot list, approval card, calendar detail and keyboard-raised composer. Prefer an appointment list to a squeezed seven-column mobile calendar. Confirm controls remain reachable after validation errors, long service names and an open side panel.

Evidence: RM-015K/R/Y, AU/AV/AY/AZ refinements, and BL phone/short observations.

### R-12 — A small visual correction should remain small

Roomedy's header divider was fixed at its actual CSS owner. The correction preserved navigation, photograph, button borders and focus. It did not require a new layout, new tests mirroring one CSS declaration or another paid model run.

**Apply here:** maintain visually continuous navigation headers and fix actual style ownership. Preserve purposeful card separators. Use targeted rendered checks for reversible presentation changes and regression tests for real state/security defects.

Evidence: RM-015BL no-header-divider follow-up and inherited I-03/I-13.

### R-13 — Model parameters and edits need separate provenance

Roomedy distinguishes observed, estimated, unknown and visitor-corrected values, and keeps deliberate locks through later processing. A blanket “confirmed room” flag would have erased those differences.

**Apply here:** retain who supplied a service/date, which catalogue version calculated the quote, and which revision the customer/coordinator approved. No single “AI verified” flag can establish correctness. A model's repeated suggestion must not override an explicit user edit.

Evidence: Roomedy blueprint provenance/locks and current photo-processing follow-ups.

### R-14 — Freeze a snapshot for an operation; fence late results

Roomedy exports and AI proposals are bound to a snapshot/revision. Edits, reset, import, expiry and cancellation invalidate a late result without mutating the current scene. Some native work cannot be interrupted immediately, so lifecycle retirement and resource accounting remain distinct.

**Apply here:** a quote approval, CRM task and reschedule refer to exact versions. A cancellation that supersedes a pending confirmation must not be overwritten by a late sync. Preserve the old reservation if replacing it fails. Reconcile an already-dispatched external mutation rather than pretending cancellation reversed it.

Evidence: RM-015X export/lifecycle design and BL proposal/cancel receipts.

### R-15 — Latest narrow evidence supersedes only its own scope

Roomedy's older README/fake-mode checkpoint lagged behind actual local live testing. Later receipts recorded successful real photo adoption and assistant operations, while public deployment and owner visual acceptance remained separate. Some visual follow-ups had scoped checks but no fresh whole-root test run.

**Apply here:** update the product's current-status summary when a real gate changes. Keep exact source/mode/corpus and stale receipts identifiable. Do not promote one successful CRM request into proof of retry safety, guest isolation or hosted acceptance.

Evidence: Roomedy current ticket index and RM-015BL compared with its historical README/BH records.

## 3. Additional decisions specific to this new product

These are adaptations for the selected stack, not claims that Roomedy already implements a database/CRM booking engine.

1. **Let PostgreSQL enforce overlap protection.** Real competing transactions are necessary evidence. A successful UI availability check does not protect against another approval before commit.
2. **Write booking and authorized CRM outbox together.** On a connected, consented path, a process crash after reservation commit must not erase the CRM obligation. A deliberately skipped CRM path has no CRM work; document/cleanup jobs remain separate.
3. **Treat external delivery as at least once.** Use stable IDs, supported upsert/reconciliation and version checks. Do not promise exactly-once remote creates after an ambiguous timeout.
4. **Separate booking success from CRM success.** Keep the accepted appointment while showing a pending or attention-needed integration state.
5. **Make cleanup a real workflow.** Expiry retires access immediately, but database/CRM cleanup, archives and backups have their own acknowledged retention. Preserve mappings until cleanup can finish.
6. **Keep guest roles honest.** Playing customer/coordinator in one seeded workspace is useful. It is not Google SSO, a permanent account or evidence of production staff administration.
7. **Use free CRM primitives, own the automation.** Do not quietly introduce paid HubSpot workflows or real outreach. Visitor-owned OAuth is now explicitly selected in the blueprint; its install limits, uninstall behavior and native provider notifications still need honest handling.
8. **Respect the selected Google Cloud database.** The owner accepted paid Cloud SQL. No different provider, free-tier assumption or SQLite production substitute without a new product reason.
9. **Test database-specific behaviour on PostgreSQL.** Use isolated test storage, migrations, timezone/concurrency cases and current driver semantics; fakes complement that evidence rather than replace it.
10. **Expose proof through useful UX.** A confirmed job, correct conflict alternative and clear retry timeline demonstrate engineering better than a wall of infrastructure badges.
11. **Make a demo self-starting and evidence inspectable.** Give visitors ready-made requests/questions and useful follow-ups. Show the actual source/page beside a grounded answer, while keeping retrieval/provenance checks distinct from a persuasive screenshot. Keep an optional Figma pass small and truthful; limited design-artifact scope does not remove responsive implementation checks.
12. **Make guided conflicts persistent scenario data.** A selected busy-first-choice path can guarantee a useful demonstration using fictional existing appointments. Show an interactive week and real alternatives from those same records. Materialize once before availability is exposed; repeated messages cannot move blockers or invalidate a free slot merely to force the story. Keep a concurrent approval race distinct from the seeded busy-date example.
13. **Carry visitor-local time through the whole guest story.** Save the browser's validated IANA zone for the isolated workspace, interpret local hours/relative dates there and retain UTC instants. Refresh, OAuth return, chat, Business view and CRM must agree; a device-zone change cannot silently reschedule a booking. Test non-US zones, offset and DST boundaries. These are Choreograph requirements, not inherited sibling behavior.

## 4. Working review checklist

Before calling a feature complete, answer the relevant questions:

- Does it help the selected customer/coordinator story and preserve accepted functionality?
- Do direct controls and the assistant agree on the same data, quote and booking state?
- Can the user correct uncertainty, see the next action and recover from failure?
- Do pending/confirmed/synced labels reflect actual distinct states?
- Are phone, short-laptop, keyboard, long-content, empty and restored states usable?
- Can stale AI, quote or task results affect a later revision or retired workspace?
- Is external work bounded, observable and recoverable without duplicate effects?
- Were actual appropriate tests run, and are fake/local/live/hosted/owner claims separated?
- Are credentials, unrelated repos, existing services and owner spending protected?
- Is the documentation updated at its narrow owner instead of duplicated across several competing specifications?

This checklist does not create an enterprise compliance programme or require irrelevant testing for every style edit. It protects the actual story and its important boundaries.

## 5. Evidence and source index

### Inherited reference actually located

- [Roomedy's Retailor-derived visual feedback lessons](C:/Users/minat/Work/Roomedy/docs/references/LESSONS_FROM_VISUAL_FEEDBACK.md): L-01 through L-24, E01–E27 and later direct Roomedy amendments. This file identifies the four original Retailor chats and the limits of its historical screenshot/chat inspection.
- [Roomedy review checklist](C:/Users/minat/Work/Roomedy/docs/design/REVIEW_CHECKLIST.md): relevant interaction, lifecycle, evidence and proportionality checks.

### Newly reviewed Roomedy evidence

- [Current ticket authority](C:/Users/minat/Work/Roomedy/docs/tickets/README.md) and [product blueprint](C:/Users/minat/Work/Roomedy/docs/ROOMEDY.md).
- [RM-015BL real photo/Medy test, fixes, retests and UI follow-ups](C:/Users/minat/Work/Roomedy/docs/validation/RM-015BL.md).
- [RM-015AT assistant capability work](C:/Users/minat/Work/Roomedy/docs/validation/RM-015AT.md), [RM-015BJ contextual replies](C:/Users/minat/Work/Roomedy/docs/validation/RM-015BJ.md) and [RM-015BK editable photo furniture](C:/Users/minat/Work/Roomedy/docs/validation/RM-015BK.md).
- Earlier M/O/P, K/R/Y and X records are linked by the inherited lessons/current blueprint and supply attributed examples; this preparation did not rerun their browser/GPU/export checks.

### Earlier reusable roots located in Retailor

- [Lessons from ClipBuilder](C:/Users/minat/Work/Retailor/docs/references/LESSONS_LEARNED_FROM_CLIPBUILDER.md).
- [Lessons from Retrosum](C:/Users/minat/Work/Retailor/docs/references/LESSONS_LEARNED_FROM_RETROSUM.md).
- [Portfolio demo build playbook derived from ScreenPilot](C:/Users/minat/Work/Retailor/docs/references/PORTFOLIO_DEMO_BUILD_PLAYBOOK.md).

Their scope/method sections were inspected as reusable context. They remain in their source repositories, with historical product overrides clearly distinguished. No credentials, private logs or raw user inputs were copied. The final new packet carries this one merged lessons file, not a duplicate library of old references.
