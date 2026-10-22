# SBS-005A — Author the knowledge pack and bounded retrieval

Status: **Complete local**
Owning phase: **07-build**  
Depends on: **SBS-003**  
Planning date: **22 October 2026**  
Queue: [ticket index](README.md)

## Outcome and standalone context

Create five original text-based Juniper PDF guides and one FAQ, with real stored pages/provenance and actual PostgreSQL vector retrieval. Fictional policies do not make the PDF bytes/citations fictional. Use LlamaIndex Python as the bounded ingestion/retrieval adapter; ordinary embeddings are deterministic fakes, not semantic-provider evidence.

## Implementation scope

1. Author editable sources and readable labelled/versioned PDFs: Service Guide, Preparation Guide, Access and Arrival, Changes and Cancellations, Safety and Exclusions; add Service Questions.md. Include service/method/supplies/equipment/access/fragrance guidance without unsupported guarantees or catalogue changes. Coverage must be on actual Service Guide page 2, pets on Preparation page 1.

2. Render/extract PDFs through the PDF skill. Preserve real version/hash/page/section/passage mapping and author Preparation v2 plus isolated malicious/conflicting test fixtures.

3. Chunk/retrieve with LlamaIndex and actual pgvector under a server-owned ready-version manifest. Authorize SQL search and preview before retrieval; metadata filters alone are insufficient. Prepare shared sample vectors once, not per guest.

4. Bound 3 guest replacements, 2 MiB/10 pages each, total extracted text/chunks/embedding/queue work and deadlines. Support text PDF/TXT/Markdown; reject scanned/password/unreadable/oversized/active content safely.

5. Publish replacement atomically only after complete processing; failure preserves ready version. Reset/expiry fences late work and removes private bytes/chunks/vectors. Original sample assets remain immutable.

6. Build compact Documents and actual authorized PDF/text reader. Show matching page and highlight or clearly labelled supported-excerpt fallback, never decorative PDF art.

## File allocation and cohesive commit plan

assets/knowledge sources/PDFs/manifest; scripts/prepare-knowledge.py; choreograph/{knowledge,models,contracts}.py; frontend Documents/source reader; lifecycle/retrieval/evaluation tests. Allocation: authored pack, scoped ingestion/retrieval, then reader/replacement.

## Acceptance criteria

- [x] Five readable/extractable PDFs and FAQ have correct provenance, plus Preparation v2
- [x] Real isolated pgvector retrieval/scope checks pass with fake embeddings and no paid calls
- [x] Eighteen retrieval cases cover paraphrases/methods/unsupported guarantees; separate malicious/conflicting fixtures are ready for the dependent SBS-005 answer-boundary checks
- [x] Atomic replacement/reset access and private purge are verified; periodic expiry cleanup is owned by SBS-007
- [x] Actual source reader resolves authorized document/version/page/passage identities.

## Meaningful verification

PDF render/text review, real pgvector scope/lifecycle queries, malformed/oversized input bounds and replacement/reset races. Evaluate source support separately from pending funded semantic-provider acceptance.

## Precision references

- [Blueprint: 92-sample-knowledge-pack-and-visible-proof](../CHOREOGRAPH.md#92-sample-knowledge-pack-and-visible-proof)
- [Blueprint: 95-document-lifecycle-and-guest-isolation](../CHOREOGRAPH.md#95-document-lifecycle-and-guest-isolation)

## Execution and evidence rules

Read the latest owner instruction, root AGENTS.md, this full packet and its precision references. The canonical phase/decision ledger is the main blueprint. AFK-SESSION-001 delegates recommended reversible decisions without questions; record material choices before relying on them. Figma visual approval is direct human evidence; owner editing/privacy are unverified.

Execute one eligible ticket, then validate read-only. Independently confirm/fix findings and revalidate until no actionable local issue remains. Missing funded/live/cloud prerequisites remain external; local defects cannot be relabelled external. Preserve unrelated changes and sibling apps.

Tests force fake providers, isolated storage and injected time where useful; inherited keys/live flags cannot enable real dispatch. Actual PostgreSQL/pgvector is required for DB-specific claims. No paid/provider/account/cloud/deployment, messages, metadata export or Git staging/commit/push permission is added. Suggested commits/file allocations are plans only.

## Handoff record

Authored the original editable source pack, six labelled PDFs (five base guides plus Preparation v2), FAQ, content hashes and eighteen expected-source retrieval cases. Rendered and inspected all seven actual PDF pages. Coverage is Service Guide page 2; pets are Preparation page 1. The deliberate preparation command stores shared sample vectors once; guest visits attach manifests without re-embedding. LlamaIndex chunks within actual page/section boundaries and runs a server-manifest-authorized pgvector retriever using explicitly fake 64-dimensional embeddings and lexical ranking.

Guest replacements are bounded to three lifetime admitted attempts, 2 MiB/10 PDF pages, 32,000 extracted characters and 64 chunks. The fixed parser child has a 256 MiB memory limit and 5-second deadline; two PostgreSQL advisory admission slots bound concurrent parses. Active/encrypted/scanned/malformed content is rejected; failure preserves the ready guide. Publication, version and revision changes are atomic under the workspace lock. Reset retires access and purges private originals/chunks/vectors. Historical sources are unavailable rather than silently retargeted. Periodic expiry cleanup remains SBS-007.

Built compact Business Documents and an actual self-hosted PDF.js 6.4.299 canvas reader with page/zoom controls, section text and labelled excerpt fallback. No decorative PDF or live-model evidence claim. Visual inspection found and fixed an initial phone fit/stale-page-render issue; the browser harness now waits for the actual rendered page identity and checks nonblank canvas pixels. Desktop, short laptop, phone and small-phone checks passed replacement, refresh, page 2 provenance and no page errors/overflow. Phone and desktop final renders were inspected.

Verification: backend suite **45 passed** using actual isolated PostgreSQL; knowledge/database subset **10 passed**; generated contracts, TypeScript, bridge tests **2 passed** and actual Next production build passed. Read-only validation reviewed authorization joins, parser bounds, manifest publication, source lookup and settled UI. No remaining actionable issue in this slice. Grounded answer/conflict/injection acceptance remains SBS-005, paid semantic quality remains externally gated, Linux verification is SBS-010, and human visual acceptance is outstanding. All changes remain unstaged/uncommitted. Next: SBS-005.

Phase 08 follow-up, 22 October: measured and removed unused source-blob selection from metadata/retrieval and changed first sample attachment to identity-only queries. Explicit source bytes and manifest/guest authorization remain intact; focused knowledge suite **4 passed**, strengthened same-session identity-map regression **1 passed**. The reader retains one authorized PDF per mounted/version lifetime, cancels superseded canvas renders and destroys it on close/retirement. Browser source loads fell 7→1 across zoom/page/resizes; unchanged-poll calendar refetches fell four→zero using stable duration/fences. Replacement/reset remove retired readers and Business Documents remounts per workspace. Epoch/workspace guards prevent delayed file/sample preparation from invoking retired mutations. Actual canvas, excerpts, focus, private PDF→TXT replacement, reset/404 and delayed-sample/new-action regressions passed with no page errors. [Phase 08 evidence and limits](SBS-009A-quality.md#phase-08-performance-investigation) owns measurements; no latency/capacity or human acceptance claim. Subsequent quality/security source changes require fresh settled release evidence.

