# Release operations — prepared, unconfigured

This directory owns packaging and operational recovery. Product decisions and phase/evidence remain in [the blueprint](../docs/CHOREOGRAPH.md) and SBS-010/012–015. Examples and the offline renderer prepare reviewable configuration/commands; they contain no credentials and execute no provisioning/deployment/IAM writes. AI defaults remain fake; public CRM is disabled until real visitor HubSpot OAuth is configured. Fake CRM is reserved for isolated tests. Explicit live AI and independent visitor CRM code paths are implemented and tested with injected transports. Hosted examples remain restricted fake QA candidates until separately funded real/hosted acceptance. Hosting fakes and the continuously running WorkerPool still cost money.

## Implemented readiness and acceptance tools

Run Python module commands below from `apps/backend` with `../../.venv/Scripts/python.exe` on Windows (the corresponding `.venv/bin/python` on Linux). No command implicitly reads another repository's configuration. `apps/backend/.env.example` lists backend settings; the adjacent `.env.local` is ignored and server-only. `apps/frontend/.env.local` contains only frontend server bridge settings, based on its own example. Local API/runner/Compose/acceptance commands use the backend file; the former root env file is no longer used. Keep paid/CRM flags false until separately authorized. Do not paste secrets into chat or receipts.

```powershell
../../.venv/Scripts/python.exe -B -m choreograph.readiness
../../.venv/Scripts/python.exe -B -m choreograph.readiness --env-file .env.local --database --require-ready
../../.venv/Scripts/python.exe -B -m choreograph.acceptance ai evaluate
../../.venv/Scripts/python.exe -B -m choreograph.acceptance crm sync
../../.venv/Scripts/python.exe -B -m choreograph.cloud_plan
```

Readiness constructs no provider clients; only `--database` performs SQL reads. It checks configuration, checked-in corpus/tokenizer hashes, migration head0010, PostgreSQL17, vector0.8.5/btree_gist1.7, six ready sample slots and matching vector dimensions/profile. `python -m choreograph.release readiness` uses explicit container environment and exits2 if any check fails, without composing provider clients. Missing names/fixed error codes are safe; secret values and credential URLs are omitted.

Acceptance defaults to a no-network plan even if an env path is supplied. `--execute` is an explicit operation switch, **not owner authorization**. Execution requires the later approved lane, unique run UUID, exact account/grant and cleanup choices. Durable `acceptance_runs` records cannot be replayed or removed by downgrade. Failed/ambiguous work consumes its reserved allowance. Actual reported token counts, unknown-usage counts, phase latency, fixed failures and opaque source/page references remain separate from conservative reservations. The injected test mode is labelled and cannot be selected through the CLI.

The AI lane is local only, on the owned port45862, using a uniquely named `choreograph_acceptance_*` database. After authorization, `ai init-db --execute --run-id UUID` creates and migrates that disposable database using only the local DB setting; output contains its name. Then `ai prepare` and `ai evaluate` require **different** unique run UUIDs, `--execute --database-name NAME --max-cost-micros INTEGER`, a reviewed live `.env.local`, explicit model/tokenizer/dimensions/rates and one durable finite AI grant. Neither step creates a cloud resource or invokes HubSpot. `prepare` indexes the six canonical sources once; `evaluate` runs18 authored cases plus absent evidence, two replacements and policy→week→supplies continuity, at most two guests. It retires those guests/purges private sources before success. A real unsupported answer stops the run and stays failed. The CLI never silently retries or substitutes a fake result. Dropping a disposable DB is a later explicit, identity-verified cleanup action; development data is never dropped.

Maximums across the reviewed grant:78 provider requests (≤48 embedding and≤30 Responses),88 vectors (≤64 document/24 query),336,864 admitted input tokens (300,000 response/32,768 document/4,096 query),42,000 output tokens and30 minutes. The owner must still choose a hard currency ceiling from current official prices. A finite operation ceiling is not spending permission. Response transport caps/output bounds still apply. The two-step grant must cover both preparation/evaluation without resetting counters.

The CRM lane requires the selected visitor's already connected/ready account, chosen pipeline/stage, schema permission if needed, explicit export consent and one reviewed fictional booking. After separately authorizing the real test, `crm sync --execute --run-id UUID --workspace-id UUID --account-id ID` executes or inspects that exact bound outbox event. A stored verified receipt is labelled separately from a fresh readback. `crm cleanup` with those same explicit scope arguments requests owned-record cleanup; `--uninstall` additionally requests the actual account-wide uninstall and may cause HubSpot's super-admin notification. Protect other active uses; revocation can prevent cleanup. The grant is capped at60 total HTTP calls including OAuth/setup/readback/cleanup. Shared-account/slot-release/admin-notification observations remain human/provider acceptance, not synthetic proof. No static operator credential is a fallback.

## Offline cloud rendering and bootstrap

`python -m choreograph.cloud_plan` prints required non-secret substitution names and makes no calls. Supply their exact string-valued JSON dictionary with `--config FILE --output ../../.runtime/NEW-DIRECTORY`. The renderer refuses missing/extra inputs, mutable image references, `latest` secret versions, shared service identities, invalid names and existing/output paths outside `.runtime`. Values are resource names, project/region/number, QA group, digest hashes and numeric secret versions; **never secret bytes**. Outputs include separate service/job YAML, queue JSON, v2 WorkerPool JSON, scoped IAM additions and `plan.json` with concrete argument arrays and REST requests. `--execute-preflight` performs only seven bounded gcloud describe reads; it never echoes descriptions/credentials or changes resources. It proves readability/presence only.

After an owner approves project/billing/region/costs and provisioning: prepare managed Cloud SQL PostgreSQL17 with the selected backups/restore policy and restricted SQL roles, registry images, separate service identities and numeric secrets. Merge IAM additions against freshly read policies/etags; never replace unrelated bindings. Bootstrap the three **private** stable service names with generated health-only backend definitions. They require no app secrets/provider clients and return `application_ready=false`; they expose no guest/task handlers. Discover the actual service URLs with generated describe commands, verify/rerender the supplied origins, then apply/execute schema and fake sample jobs, queue/IAM, full service settings and WorkerPool last. WorkerPool v2 JSON is a REST body; do not feed it to gcloud's v1 YAML replacement command. Generated commands require separate authorization and were not run.

Before release, verify actual IAM rejects unauthenticated worker/API calls and wrong OIDC audience/email; a valid task reaches only its UUID-bound work. Stop the dispatcher under a bounded approved window, create due work, restore count1, verify persisted heartbeat/recovery and exactly one domain effect. Exercise accepted-task disappearance/new epoch, duplicate delivery, five-attempt exhaustion, three-hour deadline and expiry cleanup using only the chosen fictional workspace. `release dispatch-status` reads content-free SQL counts/codes/oldest-due state without queue clients; `dispatch-once` is a bounded actual publication/maintenance action, never a readiness probe. Inspect `needs_attention` rather than repeatedly retrying. The local injected suite covers these transitions, but hosted queue overrides/IAM/Cloud SQL/WorkerPool timing and backup restore need actual receipts. Keep images/secret versions and backup identity in a rollback record; do not infer populated-data downgrade safety from empty-schema smoke.

## Evidence boundaries

| Lane | What proves it | Current boundary |
| --- | --- | --- |
| Windows host | Owned hidden launcher/readiness, tests and frontend host build | Final source passed 105 backend tests, 11 Node tests, Ruff, contract freshness and production build/typecheck; see SBS-009C. |
| Actual Linux containers | Exact Docker build inputs/digests plus isolated container smoke | Final SBS-010 receipt matches source `01188ea208d46e60973f37b40579fdac90747528ae64e6765ff0e6eaf0d9523e`; 24 HTTP requests / 180 assertions passed with actual Linux images. These commands alone are not a receipt. |
| Hosted CI | A real run on the committed source | [No-key workflow](../.github/workflows/ci.yml) is prepared. Local syntax checks are not a hosted run; the Ruff gate remains owned by SBS-009A. |
| Prepared cloud | Reviewed IAM/configuration and replacement inventory | Examples only; region, instance, networking, costs, deployment and unattended recovery are unresolved. |
| Paid/live and owner acceptance | Specifically authorized bounded real-provider tests, deployed checks and direct owner review | Local fake success supplies none of this evidence. |

## Local release commands

Run from the repository root using Docker in Linux-container mode. These commands build local images; they do not log into or push to a registry. The Dockerfiles pin upstream runtime image digests and install the repository locks. `.dockerignore` excludes host environment files, caches, runtime receipts and generated host output; Dockerfiles copy explicit source inputs.

```text
docker build --platform linux/amd64 --file infra/Dockerfile.backend --tag choreograph-api:local .
docker build --platform linux/amd64 --file infra/Dockerfile.frontend --tag choreograph-frontend:local .
node scripts/release-smoke.mjs
node scripts/release-fingerprint.mjs --check
```

The backend image uses Python 3.11.17; frontend build/runtime use Node 24.19.0. A clean frontend build prepares the PDF.js worker/fonts/cmaps/wasm and sample PDF and includes the local Google Sans Flex font. No local `.env.local` is a build input. Keep provider credentials out of build arguments, image layers and output.

The owned smoke script builds from current inputs, uses an isolated disposable PostgreSQL container/network, publishes no host ports and does not operate the persistent development volume. A successful default run writes `infra/release-evidence.json` with source/input hashes, actual image IDs, checks and limitations; failures do not refresh that receipt. `release-fingerprint.mjs --check` rejects missing or stale recorded build inputs. Re-run smoke after affected source/lock/Dockerfile changes; a prior image build is not proof for new inputs. `--no-receipt` suppresses writing an evidence file, as used in CI; its actual output is the evidence for that run. The script must finish successfully before a Linux smoke claim is recorded.

The container entry point is `python -m choreograph.release ROLE`. Roles read explicitly supplied container environment, never the host checkout's ignored file. `api` and `worker` run one Uvicorn process on `0.0.0.0:$PORT` (default 8080), after a bounded `SELECT 1` connection check. Their `/health` and frontend `/healthz` contain no guest data; a successful probe is not a provider, schema-completeness or end-to-end acceptance check. `migrate` upgrades to head; `prepare-knowledge` prepares the canonical fictional sample pack with fake embeddings once before guests; `maintenance` performs one bounded SQL-only expiry/purge/recovery tick; `runner` repeats local direct delivery for a controlled local container. `dispatcher` is the unattended deployed publication role, `dispatch-once` performs one bounded publication/maintenance cycle, and `dispatch-status` reads private content-free heartbeat/work counts without constructing a Google client. Do not assume a request-driven Cloud Run service keeps an in-process runner alive.

## Cloud configuration review

[cloud-run.example.yaml](cloud-run.example.yaml) contains separate frontend, private API, private worker, schema Job, sample-preparation Job and one-shot maintenance Job documents. Replace every `REPLACE_*` field in a reviewed copy after authorization. Image references must use the actually built registry digest; secret references must use explicit numeric versions, never `latest`. Select the region, Cloud SQL instance/availability/backups, authorized SQL roles, connection path and current costs together before provisioning. CPU/memory/concurrency values are finite provisional QA inputs, not performance or cost evidence.

The proposed steady-state API limit is two instances and worker limit is one, each with one process. Current SQLAlchemy pools allow five retained plus two overflow connections per process: a nominal budget of 21 API/worker connections. Add up to seven for each concurrently running release or maintenance process, connector/admin reserve and rollout/transient headroom. Pools open lazily; Cloud Run maximum-instance settings can be exceeded temporarily, so 21 is not an absolute database connection guarantee. Check the selected instance's actual connection budget before deployment. Keep migration and maintenance executions serialized unless their additional budget is explicitly approved.

The frontend service identity obtains a Google ID token from the fixed metadata destination. Set `CHOREOGRAPH_API_AUTH=google`, `CHOREOGRAPH_API_URL` to the private API origin, and `CHOREOGRAPH_API_AUDIENCE` to that same stable Cloud Run origin without a path. The bridge and OAuth callback use this identity, plus the existing bridge secret and guest session protections. The frontend has no database or token-key access.

[iam.example.json](iam.example.json) lists resource-scoped policy additions; it is not a full policy to replace existing bindings. API invocation is granted only to the frontend identity; worker invocation only to the dedicated task-delivery identity. Invoker IAM checks stay enabled. The example frontend is restricted to a named QA group. Only the frontend may later receive public invocation after explicit publication approval. `ingress: all` keeps the candidate independent of an unselected VPC path while IAM still denies unauthorized invocation; stricter network ingress needs its own tested routing configuration.

API/worker/maintenance identities receive application SQL connectivity and only required named secrets. The separate migrator uses a schema credential secret and migration-only database privileges; enabling `vector`/`btree_gist` and ordinary DDL must be verified against Cloud SQL privileges. Its otherwise unused Settings key/bridge fields use valid throwaway values, avoiding access to guest cryptographic keys. A Cloud SQL socket URL secret has this shape (percent-encode credential components):

```text
postgresql+psycopg://REPLACE_SQL_USER:REPLACE_URL_ENCODED_PASSWORD@/REPLACE_DATABASE?host=/cloudsql/REPLACE_PROJECT_ID:REPLACE_REGION:REPLACE_SQL_INSTANCE
```

The frontend, API and worker URLs, IANA timezone persistence, secure guest cookies, Origin checks, certificate/token verification, selected SQL extensions and Secret Manager access require actual deployed acceptance. An environment placeholder is not evidence of any successful connection. No HubSpot/OpenAI credential reference is added by this fake template.

## Durable delivery, retention and recovery

[cloud-tasks.example.json](cloud-tasks.example.json) separates a queue resource from a `CreateTask` request. Use only persisted workspace/event UUIDs in the encoded body. The target is `/internal/tasks/crm`; the OIDC audience is the worker origin and the email is the exact dedicated delivery service account in the queue project. A queue-level `ALWAYS` override fixes HTTPS host/path/method and OIDC identity/audience even if a task description differs. Cloud Tasks generates the `Authorization` bearer header. The worker verifies the signed token, issuer, audience, verified email and exact email match; `X-CloudTasks-*` headers confer no authority. Keep `Authorization` intact through the platform and verify this on hosted acceptance. Queue HTTP retries and database attempts/leases are different bounds; the outbox owns revision, destination, expiry, reconciliation and `needs_attention` state.

Google's queue retry policy stops failed attempts once both the configured attempt count and retry duration are satisfied; they are not an either/or hard cap. The database's five-attempt domain limit remains separate. The composed dispatcher now performs actual fixed-target Tasks REST create/get with FULL response verification, durable publication leases, hashed epoch identities and finite backoff/count/window bounds. A lost create response is reconciled by name;409 can also be a dedup tombstone, and404 is never business success. Current outbox state determines whether a fresh epoch is needed. The worker remains the sole deployed CRM executor. Cloud Scheduler is not selected, and no automatic expiry uninstall policy is enabled. Actual queue/IAM/override/OIDC behavior remains unchecked until authorized hosted acceptance.

Current maintenance retires expired guest workspaces, removes private document bytes/chunks/embeddings and draft/messages, fences retired CRM work, and preserves cleanup/reconciliation references while needed. Completed private business state is purged after outstanding work is settled; eligible workspace tombstones are deleted after 24 hours past expiry. Unknown OAuth outcomes and `needs_attention` work can extend retention for honest recovery. Admission is transaction-serialized at a provisional **256 retained Workspace rows**, counting active, retired and unresolved rows. Capacity returns 429 `DEMO_CAPACITY`; rejected reset rolls back, and existing sessions continue. Do not delete unresolved rows or evict guests to work around capacity; inspect lifecycle/operator outcomes and reassess this local limit against an authorized public budget. Canonical fictional sample assets are shared release inputs, not guest replacements. Cloud database backup/PITR retention and deletion from backups remain an explicit unconfigured policy; database row deletion does not erase existing backups.

Inspect fixed diagnostic codes, counts and opaque references. Do not log environment values, URLs with credentials, contact content, document text, cookies, tokens, model payloads or raw task bodies. A revoked CRM authorization can prevent remote cleanup; retain/report that unresolved outcome and never substitute another account. HubSpot installation removal is separate from token deletion, and any actual admin notification/uninstall policy needs the existing disclosure and acceptance gates.

## Schema release and rollback

Apply migrations as an explicit release operation under the separate schema identity, after verifying a restorable backup and target database/extension versions. For a new database, run fake `prepare-knowledge` after migrations and verify all six ready source slots and their stored vectors before admitting guests. The optional sample-preparation Job is a finite execution vehicle for that required preparation; it shares the schema-release identity and needs no guest encryption keys. Unchanged sample versions are preserved by the preparation code; guest requests never prepare/re-embed the corpus. A funded real embedding profile needs its own compatible dimensions, preparation authorization and evaluation; do not switch this command to paid mode. Do not apply DDL or sample ingestion automatically in every API startup. The container command syntax is:

```text
python -m choreograph.release migrate
python -m choreograph.release migrate --target REPLACE_REVIEWED_FORWARD_REVISION
python -m choreograph.release prepare-knowledge
```

For application failure, first return traffic to the last verified compatible image/revision and retain the schema. Do not automatically downgrade a schema on failed application startup. After owner authorization, restore rehearsal, write-quiescence plan, compatibility/data-loss review and an explicit reviewed target, the separate rollback syntax is:

```text
python -m choreograph.release schema-downgrade --target REPLACE_REVIEWED_PRIOR_REVISION
```

The downgrade role requires `--target` and never chooses a target for the operator. Migration `0006` introduced private purge completion; current head0010 also preserves acceptance-run receipts against downgrade; downgrades can discard state and older migrations can remove whole tables. A container exit code does not prove backup restoration or safe deployed rollback. Record image digest, source/input fingerprints, migration head, target, backup reference and actual result without secret values. Keep the previous verified image and matching secret versions available through the authorized rollback window; key rotation must account for still-encrypted tokens.

## Official references checked 22 October 2026

These support the prepared formats and permission model, not a deployed result: [Cloud Run service/job YAML](https://docs.cloud.google.com/run/docs/reference/yaml/v1), [service-to-service identity and receiving tokens](https://docs.cloud.google.com/run/docs/authenticating/service-to-service), [Secret Manager version pinning](https://docs.cloud.google.com/run/docs/configuring/services/secrets), [Cloud SQL connections from Cloud Run](https://docs.cloud.google.com/sql/docs/postgres/connect-run), [Cloud Tasks authenticated HTTP targets and service agents](https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks), [queue rate resource](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues), [OIDC service-account permissions](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/OidcToken), [retry semantics](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/RetryConfig), and [maximum-instance caveats](https://docs.cloud.google.com/run/docs/configuring/max-instances).


## Native unattended dispatcher — prepared, not deployed

[worker-pool.example.json](worker-pool.example.json) is a Cloud Run v2 WorkerPool resource proposal: manual count1,1vCPU/512MiB, the same pinned backend image, a Cloud SQL volume, a numeric database-secret version and health-only startup/liveness probes. It deliberately contains no bridge, token-key, OpenAI or HubSpot secret. Its fixed metadata-server access-token flow uses the assigned user-managed SA; it never reads GOOGLE_APPLICATION_CREDENTIALS or an alternate metadata host. The pool has no application/maintenance HTTP route. Health probes return only empty200/503; their availability is not proof that CRM delivery succeeded.

The pool is continuously billed. Count0, missing billing/region support, stopped instances or inaccessible SQL stop unattended work. A session advisory lock admits one maintenance/publication leader while two revisions overlap; it is explicitly released before returning its connection to the pool. The role's2-connection pool reserves one connection for leadership and one for short work transactions. Budget at least4 dispatcher connections during a two-instance rollout in addition to the nominal21 API/worker connections and separately limited release/admin headroom. These are prepared limits, not measured Cloud SQL capacity.

Each cycle performs bounded expiry/private-source purge, recovery of a crashed fifth delivery, finite-window retirement and at most3 publication requests. It never calls local direct CRM delivery. Publish attempts cap at120 per event and stop at the existing three-hour workspace delivery window; errors/unknown creates retain durable state. Repeated delivery still has a separate five-attempt domain bound. Old private document bytes are removed independently of remote cleanup, and failed/expired cleanup remains needs_attention. Persisted heartbeat describes cycle execution, not booking/CRM success. Inspect work/publication codes and oldest due age as well as the heartbeat; a live process can still have unavailable queue permissions.

The queue-scoped custom role in [iam.example.json](iam.example.json) contains only tasks.create/get/fullView. The dispatcher also needs exact delivery-SA actAs, SQL connectivity and its database secret. API enqueue/actAs and dispatcher bridge/token-key grants were removed. The Google-managed Cloud Tasks service-agent grant must be verified separately; no broad application Owner/Editor/Run Invoker grant is introduced.

Operator commands against explicitly configured container environment:

```text
python -m choreograph.release dispatch-status
python -m choreograph.release dispatch-once
python -m choreograph.release dispatcher
python -m choreograph.release maintenance
```

Status reads SQL only. The publishing commands require CHOREOGRAPH_TASKS_ENABLED=true plus explicit project/region/queue/target/audience/delivery identity. Do not execute them against Google before the separate cloud authorization. Native worker-pool deployment/bootstrap plans are prepared under SBS-015. To recover after an approved stop or crash, restart the reviewed pool revision at manual count1, inspect a fresh heartbeat and oldest due work, and allow durable leases/epoch reconciliation to resume. Permission/target/receipt errors remain attention; do not reset budgets, delivery counts or delete rows to claim recovery. Human-reviewed intervention is required where the finite window or attempts have ended.

Primary format/identity references checked22October2026: [WorkerPool resource/scaling](https://docs.cloud.google.com/run/docs/reference/rest/v2/projects.locations.workerPools), [container probes and versioned secrets](https://docs.cloud.google.com/run/docs/reference/rest/v2/Container), [Cloud SQL volume](https://docs.cloud.google.com/run/docs/reference/rest/v2/Volume), [worker-pool health guidance](https://docs.cloud.google.com/run/docs/configuring/workerpools/healthchecks), [metadata access tokens](https://docs.cloud.google.com/run/docs/securing/service-identity), and Tasks [create](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues.tasks/create)/[get](https://docs.cloud.google.com/tasks/docs/reference/rest/v2/projects.locations.queues.tasks/get). Local configuration/schema checks do not establish real platform acceptance.

## Free HubSpot test account and real OAuth setup (23 October 2026)

Choreograph's visitor choices are **Continue with HubSpot** and **Continue without HubSpot**. Connecting uses HubSpot's real account-selection/authorization screen. Public simulated-account approval is removed. Local CRM currently stays disabled until the OAuth app is configured; AI can remain fake independently, so this setup needs no OpenAI credits.

### 1. Create your free account and isolated test portal

Start with [HubSpot Free CRM](https://www.hubspot.com/products/crm) and select Get free CRM. HubSpot advertises this plan without a card requirement. Use your real registration details and Egypt as your country.

Egypt appears supported: HubSpot's own [Egypt directory](https://ecosystem.hubspot.com/marketplace/solutions/egypt) lists local partners. This is evidence of service presence, not a completed test of your individual signup or verification.

Inside your account, open **Development → Testing → Test Accounts → Create developer test account**. Name it **Choreograph Testing**, then open it from that list or the account picker. This is a real, separate HubSpot portal for app testing, rather than a Choreograph imitation. Use fictional contacts and deals there.

HubSpot's [account-types documentation](https://developers.hubspot.com/docs/getting-started/account-types) describes up to ten free developer test accounts, with 90-day access to many Enterprise features. The separate Standard Sandbox requires Enterprise and is unnecessary here. Manage the test portal through Actions, including Renew trials; HubSpot also documents expiry after 90 days without qualifying API activity. A Free CRM account itself is distinct from these temporary test features.

### 2. Register Choreograph's OAuth app

The test portal supplies CRM data; an OAuth app supplies the credentials visitors authorize. Both are needed. A private/static access token cannot implement visitor-owned account selection.

Use HubSpot's current [CLI app-creation guide](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/create-an-app), rather than old tutorials that create a legacy public app in the UI. After installing the supported CLI using that guide:

```text
hs account auth
hs project create
```

Choose App, OAuth authentication and Marketplace distribution for the intended visitor-installable integration. Configure the generated app metadata with Choreograph's name/description and this exact local redirect:

```text
http://localhost:45860/auth/hubspot/callback
```

Choreograph's current transport requests these permissions:

```text
oauth
crm.objects.contacts.read
crm.objects.contacts.write
crm.objects.deals.read
crm.objects.deals.write
crm.schemas.contacts.read
crm.schemas.contacts.write
crm.schemas.deals.read
crm.schemas.deals.write
```

Match the app's OAuth permissions to that contract. No payments, marketing email, workflows or extra enterprise objects are needed. Once its configuration is reviewed, the official workflow uses `hs project upload`, then `hs project open`; open the app component and its Auth section to obtain App ID, Client ID and Client Secret. These commands create/update the HubSpot app; none was run by this guide's preparation.

The current [unlisted Marketplace distribution cap](https://developers.hubspot.com/changelog/new-marketplace-distribution-app-install-limits) is 25 account installs before listing approval. Private OAuth distribution normally permits ten selected customers. These are app-distribution limits, not a payment requirement for creating your test portal, and not unlimited public installs.

### 3. Configure the local app, then connect

HubSpot [permits HTTP localhost redirects but rejects IP-address redirects](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/oauth/working-with-oauth). When enabling OAuth, set `CHOREOGRAPH_ORIGIN=http://localhost:45860` consistently in both app-local files and browse that host throughout the connection. Keep the same frontend/API/database ports; do not mix localhost and 127.0.0.1 guest cookies.

Only `apps/backend/.env.local` receives the app credentials and CRM settings:

- `CHOREOGRAPH_CRM_PROVIDER=hubspot` and `CHOREOGRAPH_CRM_ENABLED=true`.
- `CHOREOGRAPH_HUBSPOT_APP_ID`, `CHOREOGRAPH_HUBSPOT_CLIENT_ID`, `CHOREOGRAPH_HUBSPOT_CLIENT_SECRET` and the exact `CHOREOGRAPH_HUBSPOT_REDIRECT_URI` above.
- `CHOREOGRAPH_HUBSPOT_DISTRIBUTION=marketplace_unlisted` and an explicit capacity no greater than 25.
- Explicit finite `CHOREOGRAPH_CRM_GRANT_ID`, `CHOREOGRAPH_CRM_EXPIRES_AT`, `CHOREOGRAPH_CRM_REQUESTS` and `CHOREOGRAPH_CRM_WORKSPACE_REQUESTS`, using the bounded acceptance process above. Do not enable an unlimited allowance.

Keep the client secret out of chat, browser code and Git. App ID and Client ID are sufficient to identify the app during setup; enter the secret locally. AI remains fake unless separately configured. Reload only the API/runner after configuration and keep the frontend on its normal hot reload.

Continue with HubSpot then opens HubSpot immediately. Select **Choreograph Testing**, review the requested access and authorize the app there. HubSpot may show its own unverified-app confirmation. On return, select/verify the booking destination and explicitly allow fictional-record exports. Those actual account/data approvals remain; the removed step is the pretend-account confirmation. Continue without HubSpot creates no HubSpot calls or exports.

Use the prepared bounded real-acceptance tools above to verify one reviewed contact/deal, native record links and cleanup. Developer test portals include trial features: successful testing there alone does not establish every Free-plan scope/property entitlement. No account creation, credentials, live OAuth exchange, export, cleanup or app registration has been performed by preparing this guide.

The official unmodified HubSpot wordmark comes from the [HubSpot newsroom logo pack](https://www.hubspot.com/newsroom), used to identify this integration under the [Developer Terms branding rules](https://legal.hubspot.com/hs-developer-terms). No partnership/certification claim is made.
