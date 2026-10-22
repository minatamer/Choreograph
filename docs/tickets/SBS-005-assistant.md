# SBS-005 — Connect visual chat and guided demo inputs

Status: **Complete local**
Owning phase: **07-build**  
Depends on: **SBS-004, SBS-005A**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

The visual conversation is the primary workspace. Three starters and at least eighteen useful suggested questions let visitors explore without inventing text. Fake interpretation and answers exercise the same domain/retrieval path; OpenAI transport is prepared without real calls or a guessed model.

## Implementation scope

1. Use a small typed intent/tool vocabulary for clarification, authorized knowledge search and preparing supported request/lifecycle edits. No model SQL/HTTP/shell or direct booking confirmation.

2. Connect service/source/week/quote cards, direct edits and chat proposals to one versioned draft/command authority. Selection only fills composer or prepares an edit; explicit Send dispatches processing.

3. Cover busy-first-choice and open-week, service/supplies/method/pets and unsupported questions, ordinary greetings, contextual follow-ups and browsable bank. Preserve request context when switching guidance/availability and retire stale suggestions.

4. Retrieve only authorized ready passages and validate cited IDs/support. Missing/conflicting evidence and unsupported guarantees are honest; prices/time/status always come from deterministic authority.

5. Prepare bounded OpenAI transport with strict domain schemas, supported envelope tolerance, finite admission/deadlines and safe refusal/malformed/timeout/outage categories. Missing real configuration fails closed; live failure never selects fake.

6. Support Enter/Shift+Enter/IME, reachable Send, draft/focus preservation, cancellation/reset/generation fences and no late-result resurrection. Keep natural concise copy and smooth purposeful transitions.

## File allocation and cohesive commit plan

choreograph/{assistant,providers,contracts,service,knowledge}.py; frontend chat/controller/cards/question bank/API client; injected transport/intent fixtures. Allocation: typed authority integration, then interactive UI and recovery.

## Acceptance criteria

- [x] Suggested inputs can finish the actual no-CRM booking flow
- [x] Three editable starters and 24 grouped questions remain available; there is no fake-only UI branch
- [x] Actual calendar/source/quote authority and context switching agree
- [x] Failure/clarification/stale states are honest/recoverable
- [x] No paid fake-test dispatch
- [x] Enter/Shift+Enter/composition handling works.

## Meaningful verification

Grounded/retrieval evaluations and intent/command/injection fixtures; controlled late response/reset/revision cases; actual suggested-input and keyboard browser walkthrough. Do not infer real OpenAI quality from fakes.

## Precision references

- [Blueprint: 51-the-visual-assistant-is-the-primary-workspace](../CHOREOGRAPH.md#51-the-visual-assistant-is-the-primary-workspace)
- [Blueprint: 9-ai-behavior-and-boundaries](../CHOREOGRAPH.md#9-ai-behavior-and-boundaries)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Implemented typed interpretation, source retrieval and shared draft commands, strict bounded OpenAI Responses transport and injected/fake providers. No default live model or credential is selected, and the server's current profile is explicitly fake-only. A live failure cannot select a fake answer. Context, local dates and corrections persist; booking changes require ordinary explicit controls. Supplied citation IDs and exact excerpts are validated before any accepted chat state is committed. Malicious/conflicting document fixtures cause review, and a forged citation rolls back draft/message changes.

The visual chat has three editable starters, 24 grouped questions, contextual suggestions, service/clarification/quote/full-week cards, a glass composer and actual PDF/text evidence pane. Selection only fills the composer; Send dispatches. The shared manual planner remains available. The busy-first path uses persisted records; open-week does not force a conflict. Source opening preserves draft/composer; returning from Business view preserves the booking result without reopening an old source. After the first read-only/visual pass, corrected source reopening, duplicate coverage excerpts, phone source fit and page-render waits; targeted checks passed afterward. Sample section mapping is now verified against actual extracted PDF bodies, with `llama-token-section-v3` / `fake-hash-64-v2` provenance.

Verified: backend suite **50 passed**, final assistant/knowledge subset **8 passed**, generated contracts, TypeScript and actual Next production build passed. `node scripts/inspect-chat.mjs` passed the suggested-input → sourced answer → occupied day → alternative → quote review → submission → Business approval → confirmed no-CRM result at desktop, short laptop, phone and small-phone sizes, plus the Auckland open-week branch. Question discovery, context retention, Enter/Shift+Enter and simulated IME composition were exercised. Final source and phone result renders were inspected; no browser page errors or horizontal overflow. Distinct settled read-only validation found no remaining actionable local defect. Semantic-provider quality/live config, real HubSpot and human runtime visual acceptance are not claimed. Git remains unstaged/uncommitted. Next: SBS-006.

