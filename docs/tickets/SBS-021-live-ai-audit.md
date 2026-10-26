# SBS-021 — Real AI readiness audit and conversational command foundation

> **Deployment supersession,26 October2026:** the selected deployment is **no database** (`DATABASE_ENABLED=false`), using private GCS objects, Cloud Tasks and authenticated minute Scheduler maintenance. SQL/pgvector/migration/WorkerPool requirements in this dated packet are historical or optional true-mode evidence. They do not authorize or require database provisioning. See [the current setup inventory](../../infra/README.md#verified-cloud-inventory-and-remaining-setup-26-october2026).

Status: Complete locally — bounded real website evidence recorded in SBS-022;24 October2026

Audit and repair the actual OpenAI/RAG/chat/booking path. The original audit used fake/injected providers; the owner's later explicit real-test authorization, switches and finite allowance are owned by [SBS-022](SBS-022-turnstile-live-controls.md). That continuation supersedes the original fake-only stop for this one local test. Earlier unstaged SBS-019/020 and landing changes are preserved. No sibling, Figma or Git writes occurred.

## Inspected foundation and findings

The existing Responses adapter, local pinned tokenizers, real scoped PostgreSQL/pgvector retrieval, original document reader, durable finite admission, no-retry transport, source validation, short authority transactions, stale/reset/expiry fencing and explicit transactional booking are implemented. Their local tests do not establish real model quality. Read-only sibling inspection covers Retailor's typed proposals/fact grounding, Retrosum's bounded conversation/structured friendly explanations, and Roomedy's separated intent/advice/preparation and explicit Apply boundaries. No sibling settings, secrets, processes or files are changed.

Concrete gaps found: the live interpreter receives draft but no recent conversation or actual booking state; intent instructions do not define policy retrieval and booking/status routes clearly; social/help replies and missing-field questions are generic; date-only/time-only changes can retain or ignore an old draft preference; invalid provider field shapes and malformed output envelopes need stricter validation; an unprepared live knowledge pack should fail before spending rather than look like unsupported policy. The current model does not receive arbitrary SQL/HTTP or authority to reserve from prose, and this must remain true.

## Plan and acceptance

1. Supply bounded recent conversational context, pending date/time and scoped booking statuses to the live interpreter, without treating history as current document evidence. Bind context per command rather than mutating the shared runtime.
2. Document and enforce a narrow routing vocabulary for current-source guidance, exact quote edits, availability/preference, booking review, actual booking status and explicit Business management. Keep ordinary friendly copy/application facts separated from model interpretation, following the sibling patterns. No generic agent framework or autonomous booking loop is needed for this bounded product.
3. Strengthen strict provider field/envelope validation, contextual date normalization, stale preference handling, document-readiness preflight and evidence status/claim consistency. Retain exact source IDs/excerpts and same highlighted original-source reader.
4. Add meaningful injected Responses/embedding + actual isolated PostgreSQL tests for history/follow-ups, policy retrieval, multi-turn quote/availability/review/booking/status, failed/forged/refused/stale actions, timezone/preference corrections and finite/no-retry behavior. Recheck the existing relevant suites, contracts, types, lint, and actual affected fake UI states.
5. Record audited areas, fixed findings, actual checks, source links and the exact remaining live setup/acceptance prerequisites in this owning ticket and the current authority. Real provider quality remains unverified until a bounded authorized run.

Official OpenAI sources consulted: [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) and [function calling](https://developers.openai.com/api/docs/guides/function-calling). Strict schemas constrain shape, not semantic truth; source and domain validation remain application responsibilities. Existing structured intent routing is not advertised as native model function calling. Only explicit application commands reserve/change bookings.

## Implemented remedies

- `assistant_context.py` supplies the last eight bounded turns, source topics, pending preference and three actual booking statuses, with no source bytes/contact fields/secrets. Context is copied per command; it never changes the shared provider or substitutes for current retrieval.
- `providers.py` validates strict nullable structured fields, actual dates/times, bounded claims and completed assistant envelopes. Unexpected tools/roles, malformed data, refusal and inconsistent evidence fail honestly. The interpreter routes combined job/policy requests through both domain preparation and retrieval; short follow-ups use scoped history. Self-contained policy wording is preserved rather than expanded into unasked requirements. Source instructions addressed to customers are valid evidence; embedded attempts to change model authority remain untrusted.
- `assistant.py` keeps guidance/social/status routes from modifying the draft, anchors time-only edits to the saved local day, clears stale preferences for date-only requests and checks the actual whole-day availability. Morning/afternoon filters use the saved workspace timezone and actual appointment date on both API and calendar. Missing fields produce one useful question. Status replies use stored records. Management replies point to existing explicit Business controls. "Book it" prepares review; only the reviewed booking command reserves.
- `interactions.py` checks the actual six-slot live manifest before paid interpretation and skips evidence generation when retrieval returns no hits. Source identity/excerpt checks, short authority transactions, generation/revision fencing and durable finite admission remain in the real execution path.
- The non-streaming provider can wait for its first byte within the12-second response budget; the previous one-second read timeout could reject normal generation. The pre-SDK65,536-byte cap, identity encoding, no retries/fallback, fixed endpoint, sanitized diagnostics, monotonic checks and55-second turn fence remain. See the scoped SEC-005 follow-up in the [security review](../security/SECURITY_REVIEW.md).

## Actual verification

The settled full backend suite passed **294 tests** with actual isolated PostgreSQL/pgvector and fake/injected external providers. **69 Node tests**, configured Ruff, generated contracts, frontend types and the pinned Linux frontend build passed. The full backend run predates only the final interpreter/evidence prompt wording refinements; the corrected combined-request and changes-policy scenarios then passed through the real website. A final focused pass on the settled sources passed **37 tests** (three unrelated cases deselected). Its first sandboxed attempt passed34 non-database cases and could not connect to the isolated database for three fixtures; rerunning with the normal local database permission passed all37. This was an execution-environment limitation, not a product failure.

New regressions exercise the actual Responses SDK/composition with injected HTTP, strict schemas/envelopes, history, current sources, exact quote/availability/review/booking/status/management/thanks, absent knowledge, date/time/period corrections, unchanged bookings, finite admission and private context. Actual rendered fake/live states were inspected; [SBS-022](SBS-022-turnstile-live-controls.md#actual-bounded-real-results) owns the real sources, booking, responsive screenshots and allowance receipt. This is a bounded local quality check, not the full24-case real acceptance run or a latency benchmark.

## Final read-only validation — pass1

**Verdict: Meets ticket. No actionable findings.** Reviewed current unstaged changes and relevant untracked files against `c9cc03688f5cfbcdb77151251f4d9acdafe644c1`; the index is empty. Reviewed the real composition, schemas, context, source checks, intent/domain boundary, date/period logic, connected browser controls and relevant regressions. Earlier landing/hero/glass and SBS-019/020 implementation are excluded from this verdict except their touched integration points. Documentation was reconciled after the read-only pass.

| Requirement | Disposition |
| --- | --- |
| Bounded conversation and actual booking context | Covered |
| Friendly narrow routing, current-source evidence, explicit reservation authority | Covered |
| Strict provider shapes, source readiness and preference corrections | Covered |
| Meaningful isolated provider/database checks and affected rendered states | Covered |
| One authorized real website path | Covered within SBS-022's finite scope |
| Broad real semantic evaluation, human/hosted release acceptance | Unverified; separate external acceptance |
