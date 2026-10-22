# Choreograph execution queue

The owner approved the revised Figma and authorized the full build with AFK mode on on 22 October 2026. [The main blueprint](../CHOREOGRAPH.md) contains the canonical build phase/AFK ledger. These standalone packets replace the earlier dependency outline. Product/ticket/security/runnable-visual reviews while AFK are provisional agent decisions; Figma approval is a separate direct human decision.

Read the full selected ticket and precision references. Execute one eligible ticket, validate read-only, independently confirm/fix findings and revalidate before continuing. The first local ticket is SBS-000; SBS-000A adopts completed design evidence. During phase 07 do SBS-005A before SBS-005. Quality/security packets run in their named later phases. SBS-010 release files are refreshed after subsequent fixes; SBS-011 prepares a bounded plan but real actions remain externally gated.

File allocations live inside each packet and do not authorize staging/commits. Commands in plans are requirements until actually created and verified. Record actual evidence in the ticket and queue. Missing funded/live/hosted prerequisites do not stop independent local work; local defects cannot be relabelled external.

Fresh local ports: frontend **45860**, API **45861**, PostgreSQL **45862**. Selection checks found no conflicts or prior source references. Recheck before binding, use loopback and verified repo ownership, preserve development volumes and never stop/change a sibling.

| Ticket | Outcome | Owning phase | Dependencies | Status |
| --- | --- | --- | --- | --- |
| [SBS-000](SBS-000-baseline.md) | Verify the supported baseline and owned lifecycle | 07-build | None | Complete local |
| [SBS-000A](SBS-000A-figma.md) | Adopt the approved compact Figma | Design milestone | None | Adopted visual design; owner approved |
| [SBS-001](SBS-001-foundation.md) | Create the Next/FastAPI contract foundation | 07-build | SBS-000, SBS-000A | Complete local |
| [SBS-002](SBS-002-database.md) | Add PostgreSQL, migrations and guest isolation | 07-build | SBS-001 | Complete local |
| [SBS-003](SBS-003-request-calendar.md) | Implement exact quotes and persistent seeded availability | 07-build | SBS-002 | Complete local |
| [SBS-004](SBS-004-booking.md) | Implement business approval and booking lifecycle | 07-build | SBS-003 | Complete local |
| [SBS-005A](SBS-005A-knowledge.md) | Author the knowledge pack and bounded retrieval | 07-build | SBS-003 | Complete local |
| [SBS-005](SBS-005-assistant.md) | Connect visual chat and guided demo inputs | 07-build | SBS-004, SBS-005A | Complete local |
| [SBS-006](SBS-006-crm.md) | Prepare safe optional HubSpot integration | 07-build | SBS-004, SBS-005 | Complete local |
| [SBS-007](SBS-007-durable-work.md) | Add durable outbox recovery and cleanup | 07-build | SBS-006, SBS-005A | Complete local |
| [SBS-008](SBS-008-responsive-flow.md) | Verify the complete responsive demo | 07-build | SBS-005, SBS-006, SBS-007 | Complete local |
| [SBS-009A](SBS-009A-quality.md) | Review quality and bounded performance | 10a-quality | SBS-008 | Complete local |
| [SBS-009B](SBS-009B-security-review.md) | Audit security and present findings | 10b-security-review | SBS-009A | Complete local; provisional AFK selection |
| [SBS-009C](SBS-009C-security-fixes.md) | Apply selected security remedies | 11-security-fixes | SBS-009B recorded selection | Complete local |
| [SBS-010](SBS-010-release.md) | Prepare local Linux release and cloud files | 07-build; refresh at 12-handoff | SBS-008 | Complete local |
| [SBS-011](SBS-011-external-acceptance.md) | Prepare bounded live and hosted acceptance | External; 12-handoff | SBS-010 and security disposition | Bounded plan prepared; external execution pending |
| [SBS-012](SBS-012-live-ai.md) | Complete live-capable AI, versioned retrieval and durable admission | 07-build continuation | SBS-005/005A baseline | Complete local |
| [SBS-013](SBS-013-live-crm.md) | Complete visitor HubSpot composition and account setup | 07-build continuation | SBS-012 | Complete local |
| [SBS-014](SBS-014-cloud-dispatch.md) | Complete actual Tasks publication and unattended dispatcher | 07-build continuation | SBS-013 | Complete local |
| [SBS-015](SBS-015-integration-readiness.md) | Finish executable readiness, acceptance tools and release files | 07-build continuation;12 refresh | SBS-012/013/014 | Complete local |

Scope is one Python backend, one Next frontend, SQLAlchemy/Alembic, actual PostgreSQL/pgvector, narrow LlamaIndex/OpenAI/HubSpot adapters and local durable runner. No payments/outreach/Google Calendar, extra vector platform or agent framework. Figma remains six desktop key frames and one mobile landing; the implemented app is responsive throughout.

**Continuation authorized 22 October 2026:** the owner requested all possible remaining coding. SBS-012–015 make unfinished implementation explicit; these are not credential-only blockers. Earlier “Complete local” rows preserve fake-provider milestone evidence rather than claim live/hosted completion. SBS-011 acceptance depends on the new implementation and subsequent quality/security/release checks. AFK remains active; real operations/spending, deployment and Git writes still require their own concrete scope/authorization.


**Final continuation handoff:** all coding rows are complete locally, including SBS-012–015 and refreshed performance/visual/quality/security/release gates. Final source `c803fbcd8d491d794dc3504bd08d0da056f5521363fcdd8e1fdaa73f7c7251b4`,227 backend/15 Node checks and fresh Linux107-input smoke pass. SBS-011 is the remaining real-operation acceptance packet; its exact owner-input table distinguishes accounts/keys/funding/deployment/human/Git prerequisites from code. No active coding ticket remains.

**Local Git follow-up:** the latest direct owner request authorizes the [five-group file-level plan](COMMIT_PLAN.md) and local commits with SBS ticket prefixes. The canonical Git permission is updated independently of provisional product/visual/security reviews. Git log/clean-tree verification owns actual completion; no push/deployment/paid action is included.
