# Release operations — deployment preparation

## Deployment checkpoint —25 October2026

**25 October later UI follow-up:** SBS-030 changes production confirmation/reset code after the Linux smoke cited below. Its current checks are scoped Node/components/types and HTTP compilation; a new Linux release receipt is still needed before deployment. The earlier source fingerprint is a historical tested image pair, not the latest worktree.

**Ready for cloud preparation, not ready for public release.** [SBS-029](../docs/tickets/SBS-029-deployment-readiness.md) owns this deployment continuation. Current application code has366 passing isolated backend tests,122 Node tests and actual Linux production-image smoke evidence (44 HTTP requests/291 assertions). The older tracked `release-evidence.json` is historical; the latest actual run deliberately used `--no-receipt`. Local evidence does not prove hosted networking, IAM, billing controls, native HubSpot or backup restoration.

### What is actually set up

| Item | Observed state |
| --- | --- |
| Dedicated project | Existing `choreograph-512713`, project number729503363583, billing enabled; reused rather than creating another project. |
| CLI | Authenticated gcloud588.0.0; global project remains ScreenPilot. Always pass `--project=choreograph-512713`; do not change sibling configuration. |
| Secrets | Eight resources created with the existing env names below; all eight have **zero versions**. No credentials were copied or runtime accessor grants added. Automatic replication was selected; revisit residency before values if required. |
| Budget alerts | **Two verified monthly alerts:** Choreograph Cloud Run USD5 and project USD10. Both include credits, use50/80/100% actual-spend thresholds and default billing IAM email recipients. These are notification-only; no spend cap. Readback confirms configuration, not delivery. |
| Cloud APIs | Secret Manager was enabled; Budget API enabled for this task. Cloud SQL Admin, Cloud Run, Compute, Service Networking, Cloud Tasks, Cloud DNS and Artifact Registry were absent from the initial enabled inventory. No SQL/Run/network/registry resources were created or inspected through disabled APIs. |
| Region | `europe-west1` is the proposed common region, following the existing CLI setting; owner confirmation remains pending. |
| Public launch | No image push, service deployment, public IAM grant, DNS change, paid AI call, HubSpot test, local restart or Git commit in this continuation. |

The owner is deferring HubSpot testing. Its local Connect readiness is not native account/record acceptance. The private backend/database work described below is still required even if local HubSpot subsequently passes.

### Costs and the sibling budget pattern

Read-only billing metadata confirms Retailor, Roomedy, Retrosum and ClipBuilder use a **USD5/month Cloud Run gross spend cap** plus **USD10/month project alerts**; ScreenPilot's USD5 Cloud Run budget is alerts-only. Choreograph is linked to a different existing billing account; no billing account was moved. The project alert mirrors that alert pattern; the owner follow-up also created the missing USD5 Cloud Run notification-only budget, matching ScreenPilot. Both use50/80/100% actual-spend thresholds ($2.50/$4/$5 service; $5/$8/$10 project). They are early warnings, **not** a chosen infrastructure allowance or stop mechanism.

Google now supports service-scoped [Cloud Run spend caps](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps). They cover Cloud Run services/jobs/worker pools in one project, not Cloud SQL, registry, DNS, all networking or OpenAI. Enforcement has delay/overage and can stop the website and dispatcher; the database bill continues. Ordinary [budget alerts](https://docs.cloud.google.com/billing/docs/how-to/budget-api) notify billing recipients and do not stop resources. Avoid a billing-disable automation: it can interrupt persistence/recovery across the project. See [Cloud Run cap behavior](https://docs.cloud.google.com/run/docs/configuring/billing-settings).

The existing always-on dispatcher materially changes the cost compared with request-only sibling apps. Current public Catalog API rates read25 October for Belgium give the following **730-hour, USD, before-credit estimates**:

| Resource | Inputs and estimate |
| --- | --- |
| Dispatcher at current template size |1vCPU × $0.000011244/second +0.5GiB × $0.000001235/GiB-second = **$31.17/month**. CPU SKU F7DC-B124-640A; RAM F30E-913C-E55A. |
| Cloud SQL PostgreSQL17 Enterprise, zonal micro | db-f1-micro,0.6GiB/shared CPU; $0.0105/hour = **$7.67/month compute** (SKU4C57-F0D3-6029). Memory/connection suitability is unproven. |
| Cloud SQL PostgreSQL17 Enterprise, zonal small | db-g1-small,1.7GiB/shared CPU; $0.035/hour = **$25.55/month compute** (SKU79B6-5148-74CC). Proposed safer pilot starting size, still needs capacity checks. |
| SQL storage and backups | Additional provisioned SSD/storage growth; current listed starting SSD rate $0.17/GB-month is a planning input requiring the selected-region quote. Backup SKU FB45-227E-BC1B is $0.08/GiB-month in EMEA; actual retained bytes vary. |
| Other | Frontend/API/task worker requests, release jobs, Tasks, registry images, build execution if selected, private DNS, logs/retention, data transfer and taxes; OpenAI is a separate bill. |

Thus dispatcher + SQL compute alone is about **$38.84 micro / $56.72 small** before storage/traffic/credits, rather than a full $5–10 app. Free allowances are shared at billing-account level and must not be counted as guaranteed savings. The live [Catalog API](https://docs.cloud.google.com/billing/v1/how-tos/catalog-api) metadata, saved privately under `.runtime`, supports these calculations. The lower worked worker example on the [pricing page](https://cloud.google.com/run/pricing) disagrees with the current returned rates; use the actual current region/SKU quote before purchase. See [SQL prices](https://cloud.google.com/sql/pricing?hl=en) and [storage overview](https://cloud.google.com/sql). Shared-core SQL has no SLA. No commitment/HA/replica is selected.

**Decision still needed:** monthly infrastructure allowance, SQL tier and region, then an appropriate Cloud Run cap. A $5 cap would interrupt the present design. If the owner needs a $10 total deployment, revisit the unattended dispatcher architecture explicitly; do not silently remove expiry/recovery, add Cloud Scheduler or present request-only services as equivalent.

The installed stable `gcloud billing budgets create` supports ordinary alerts; its help has no spend-cap flag. The [Budgets v1 REST API supports caps](https://docs.cloud.google.com/billing/docs/how-to/budget-api-spend-cap), including from PowerShell/CLI. [budget-cloud-run-cap.example.json](budget-cloud-run-cap.example.json) is an **unapplied** body matching the sibling $5 gross cap. Replace the project number and review the name/amount first. It uses exactly50/80/100% CURRENT_SPEND, excludes credits, enables project/default IAM recipients and sets `spendCap.inputState=CONFIGURED`. REST POST is to `https://billingbudgets.googleapis.com/v1/billingAccounts/BILLING_ACCOUNT_ID/budgets`, with an in-memory gcloud access token, `x-goog-user-project: choreograph-512713` and JSON body. Never print/save the token, repeat POST after an unknown outcome without listing, or replace another project's budget. Keep the returned budget ID privately for etag-preserving updates. No cap was applied here.

### Empty secrets: what the owner should enter

Open [Choreograph Secret Manager](https://console.cloud.google.com/security/secret-manager?project=choreograph-512713), select each existing resource and choose **New version**. Enter **only the value**, without `NAME=`, surrounding quotes or a trailing newline. Do not paste values into chat. Values are runtime configuration, not Docker build arguments. Pin each resulting numeric version in the reviewed release configuration; never deploy `latest`. [Secret versions](https://docs.cloud.google.com/secret-manager/docs/add-secret-version) contain the bytes; a resource without versions is intentionally not usable yet.

**Exact-name check:** all eight resources were compared with the key names in the actual backend/frontend `.env.local` files, without displaying their values. They already exist, so no duplicate or differently named secret was created. The four non-secret keys (`FAKE_MODE`, `PAID_DEMO_ENABLED`, `CHOREOGRAPH_ORIGIN`, `CHOREOGRAPH_API_URL`) remain ordinary deployment settings.

**What can be filled now:** copy the existing matching value from your own backend `.env.local` for `OPENAI_API_KEY`, `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY` and `CHOREOGRAPH_HUBSPOT_CLIENT_SECRET`, if you intend to reuse those provider credentials. Cloudflare still needs the final deployed hostname authorized. Use fresh deployment values for bridge/encryption/database credentials. Leave `CHOREOGRAPH_DATABASE_URL` empty until the cloud database and secure transport are configured; the local URL will not work in Cloud Run.

| Exact existing resource name | Value / consumer |
| --- | --- |
| `CHOREOGRAPH_DATABASE_URL` | **Cloud** database URL using the restricted application login and chosen secure private transport. API, task worker and dispatcher only. Wait for SQL provisioning; never use localhost/the development DB here. |
| `CHOREOGRAPH_DB_PASSWORD` | Choose a fresh strong cloud database bootstrap/admin password (the generator below is suitable), then set it on the actual SQL administrator when provisioning. This name currently serves local Compose, **not** the hosted application; keep the cloud resource administrator-only. Storing its value alone does not create a database login. The restricted application login/URL is separate. |
| `CHOREOGRAPH_BRIDGE_SECRET` | Generate a fresh deployment-only random value, at least32 characters, with the first command below. Same value/version in frontend, API and current worker settings. |
| `CHOREOGRAPH_TOKEN_KEY` | Generate fresh deployment-only URL-safe base64 encoding of exactly32 random bytes (44 characters including padding) with the second command below. API/worker only; protects stored visitor OAuth tokens. Preserve old key/version through rollback; rotation needs a token migration/reconnection policy. |
| `OPENAI_API_KEY` | Backend key for the intended funded provider project, API and explicitly approved real preparation job only. Do not bind it to fake QA, frontend or dispatcher. Adding it does not renew expired hosted allowances. |
| `TURNSTILE_SITE_KEY` | Public site identifier, stored under the same requested env name for consistency. API exposes the needed public configuration; this is not a confidential password. |
| `TURNSTILE_SECRET_KEY` | Server-side Siteverify key, API only. Configure the actual deployed hostname with Cloudflare; local success does not prove hosted verification. |
| `CHOREOGRAPH_HUBSPOT_CLIENT_SECRET` | Confidential Choreograph OAuth app secret, API/task worker only when hosted CRM is enabled under reviewed finite policy. Visitors never enter this credential. |

Run these **yourself in a private terminal at the repository root**; their output is the value to paste into Secret Manager. Generate a separate first-command value for the bridge and database password. The second command is specifically for `CHOREOGRAPH_TOKEN_KEY`; retain its final `=` padding. These commands have not been run to generate or collect your deployment values.

```powershell
# CHOREOGRAPH_BRIDGE_SECRET, or a separate fresh CHOREOGRAPH_DB_PASSWORD:
./.venv/Scripts/python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
# CHOREOGRAPH_TOKEN_KEY:
./.venv/Scripts/python.exe -c "import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

Shell/JSON syntax quotes are different from the secret's bytes: paste only the generated value, without wrapping quotes. Keep an existing encryption key/version if this is a rotation of a deployed database with stored tokens; the fresh-key instruction applies to this new empty deployment.

No secret is needed for `FAKE_MODE`, `PAID_DEMO_ENABLED`, origins/URLs, public OAuth client ID, model names/rates or Tasks transport settings. Those remain explicit non-secret deployment values/code-owned policy. Cloud SQL's migration login requires a **different** protected database-URL resource (proposed `CHOREOGRAPH_DATABASE_URL_MIGRATION`, not created here), injected into that job under the existing **`CHOREOGRAPH_DATABASE_URL` env name**. Separate resources prevent ordinary app identities from reading administrative credentials. The runtime env key does not change.

The frontend gets only its API URL, Google-auth mode/audience, canonical origin and bridge secret. It gets no SQL password, OpenAI key, token encryption key or OAuth client secret. Use resource-scoped `roles/secretmanager.secretAccessor` for the actual consumers, not a project-wide grant to every runtime. No downloaded service-account JSON keys are needed: [Cloud Run uses its assigned identity](https://docs.cloud.google.com/run/docs/securing/service-identity) to read the pinned [secret references](https://docs.cloud.google.com/run/docs/configuring/services/secrets).

### Proposed private connection path

```text
Browser --HTTPS--> public Next.js frontend
                   server bridge + Google ID token + bridge secret
                         |
                         | Direct VPC + private Google Access / private run.app DNS
                         v
                 internal-ingress FastAPI API (IAM required)
                         |
                         | Direct VPC + authenticated/encrypted SQL transport
                         v
                 Cloud SQL PostgreSQL17 + pgvector (private IP only)

API transaction --> durable SQL outbox <-- dispatcher WorkerPool
                                              |
                                        Cloud Tasks OIDC
                                              v
                                    internal-ingress task worker
                                              |
                                    same private Cloud SQL
```

Use one dedicated custom-mode VPC and a same-region subnet with Private Google Access. **Direct VPC egress** avoids a continuously billed Serverless VPC Access connector; use `private-ranges-only` so OpenAI, Cloudflare and HubSpot can still use ordinary outbound HTTPS without adding Cloud NAT. Source services must actually route requests to the internal API through this VPC. For that, use the documented **private `run.app` DNS → private.googleapis.com address range** in this dedicated VPC, plus Private Google Access. Keep the default stable API URL as the Google token audience. The API and task worker use **ingress internal AND IAM checks enabled**, with no `allUsers`/`allAuthenticatedUsers`. Same-project Cloud Tasks at the default worker `run.app` URL qualifies as internal; another Cloud Run service does not qualify merely by sharing a project. [Internal routing options](https://docs.cloud.google.com/run/docs/securing/private-networking), [ingress rules](https://docs.cloud.google.com/run/docs/securing/ingress), [Direct VPC service/job/worker-pool configuration](https://docs.cloud.google.com/run/docs/configuring/vpc-direct-vpc).

Use a private-IP-only SQL instance (`--no-assign-ip`), no internet-authorized networks, and dedicated restricted SQL users. For this single VPC, **private services access (PSA)** is the proposed straightforward peering path. Google now defaults new console setups to **Private Service Connect (PSC)** and recommends it for flexible isolation/multiple VPCs; selecting PSA explicitly remains supported. Do not mix PSC endpoint/DNS instructions with PSA peering. [Connection choices](https://docs.cloud.google.com/sql/docs/postgres/private-ip), [PSA setup](https://docs.cloud.google.com/sql/docs/postgres/configure-private-services-access). PSA uses a reserved non-overlapping range separate from the application subnet. No public port5432/SSH firewall rule is required. Review VPC egress rules/tags so the frontend cannot access the SQL destination unnecessarily.

**Implementation gate:** existing examples attach Cloud SQL managed Unix-socket volumes and contain no VPC configuration. Attaching that volume alone does **not** prove private-IP selection. For the private-only release choose and test one explicit transport:

1. Prefer a pinned **Cloud SQL Auth Proxy v2 with `--private-ip`**, running in the same Direct-VPC-enabled workload and using its service identity. It gives authenticated, encrypted database transport and can retain the accepted `/cloudsql/PROJECT:REGION:INSTANCE` socket URL. Add/test its socket volume, startup ordering, memory, shutdown and health for API/worker/dispatcher **and finite Jobs**; a background proxy must not keep a completed migration job running. Recalculate costs if the sidecar increases allocated resources.
2. Alternatively implement direct private-IP PostgreSQL TLS with trusted CA/server verification. Current Settings rejects connection-query options except the validated socket form, so a TLS URL is **not supported as-is**. Add narrowly validated TLS configuration and connect arguments with negative tests before using it. Never relax the existing host-override guard or use unauthenticated plaintext TCP just because the address is private.

Neither transport adaptation has been implemented/tested here. [Cloud Run→SQL private-IP instructions](https://docs.cloud.google.com/sql/docs/postgres/connect-run), [explicit proxy private-IP selection](https://docs.cloud.google.com/sql/docs/postgres/connect-auth-proxy), [TLS enforcement](https://docs.cloud.google.com/sql/docs/postgres/configure-ssl-instance). Windows/Cloud Shell do not acquire VPC access by running the proxy; keep public IP disabled and perform schema/admin work inside the VPC via a separately authorized one-shot job or an approved private admin path.

### CLI provisioning sequence — prepared, not executed

Use explicit Choreograph arguments throughout; inspect existing named resources before creation, stop on unexpected conflicts/errors and keep receipts without credentials. These PowerShell examples are a reviewed **proposal** requiring the pending budget/region/tier decision; they do not create resources by appearing here. Commands intentionally omit passwords. Each gcloud exit must succeed before continuing.

```powershell
$cloudProject = 'choreograph-512713'
$cloudRegion = 'europe-west1'
$cloudNetwork = 'choreograph-vpc'
$cloudSubnet = 'choreograph-run'
$cloudSql = 'choreograph-postgres'

gcloud services enable run.googleapis.com sqladmin.googleapis.com compute.googleapis.com servicenetworking.googleapis.com cloudtasks.googleapis.com artifactregistry.googleapis.com dns.googleapis.com --project=$cloudProject

gcloud compute networks create $cloudNetwork --subnet-mode=custom --project=$cloudProject
# Proposed range: inspect overlap/reservations before applying.
gcloud compute networks subnets create $cloudSubnet --network=$cloudNetwork --region=$cloudRegion --range=10.84.0.0/24 --enable-private-ip-google-access --project=$cloudProject
gcloud compute addresses create choreograph-sql-range --global --purpose=VPC_PEERING --prefix-length=16 --network=$cloudNetwork --project=$cloudProject
gcloud services vpc-peerings connect --service=servicenetworking.googleapis.com --ranges=choreograph-sql-range --network=$cloudNetwork --project=$cloudProject

# Paid resource: proposed SMALL pilot, not approved/executed.
gcloud sql instances create $cloudSql --project=$cloudProject --region=$cloudRegion --database-version=POSTGRES_17 --edition=ENTERPRISE --tier=db-g1-small --availability-type=ZONAL --network=$cloudNetwork --allocated-ip-range-name=choreograph-sql-range --no-assign-ip --ssl-mode=ENCRYPTED_ONLY --storage-type=SSD --storage-size=10GB --storage-auto-increase --storage-auto-increase-limit=20 --backup-start-time=02:00 --backup-location=$cloudRegion --retained-backups-count=7 --enable-point-in-time-recovery --retained-transaction-log-days=7 --deletion-protection --retain-backups-on-delete --final-backup --final-backup-retention-days=7
gcloud sql databases create choreograph --instance=$cloudSql --project=$cloudProject

gcloud dns managed-zones create choreograph-run-private --dns-name=run.app. --visibility=private --networks=$cloudNetwork --description='Private Cloud Run routing for Choreograph' --project=$cloudProject
gcloud dns record-sets create run.app. --type=A --ttl=300 --rrdatas=199.36.153.8,199.36.153.9,199.36.153.10,199.36.153.11 --zone=choreograph-run-private --project=$cloudProject
gcloud dns record-sets create '*.run.app.' --type=CNAME --ttl=300 --rrdatas=run.app. --zone=choreograph-run-private --project=$cloudProject

gcloud artifacts repositories create choreograph --repository-format=docker --location=$cloudRegion --project=$cloudProject
```

The storage auto-increase cap is a capacity/cost tradeoff, not a total bill cap; storage cannot later shrink. Retention/deletion protection can retain billed storage after ordinary stops/deletion. Backups/PITR may retain guest data after app expiry. The proposed7-day retention requires owner acceptance and an actual restore rehearsal. Zonal/shared-core is a pilot availability compromise; do not imply HA/SLA. Current official [instance flags/settings](https://docs.cloud.google.com/sdk/gcloud/reference/sql/instances/create) support this proposal; enabled APIs, quotas, final selected tier and actual settings must be reverified before provisioning.

Next steps after that foundation, in order:

1. **Database administration:** owner sets passwords privately. Create administrator-installed `vector`0.8.5 and `btree_gist`1.7 in `choreograph` before restricted migrations; verify `pg_available_extension_versions` and installed versions on the actual PostgreSQL17 instance. Create separate migration owner/login and app login; application has CONNECT, schema USAGE, required DML and sequence access, no CREATE/CREATEDB/CREATEROLE or `cloudsqlsuperuser`. Revoke PUBLIC schema CREATE and grant future-object privileges for the actual migration role. Do not use default `postgres` as app user. Cloud SQL built-in users created without custom roles default to `cloudsqlsuperuser`; explicitly remove/avoid that membership. Configure and verify grants for both existing and future objects. [Supported extensions](https://docs.cloud.google.com/sql/docs/postgres/extensions), [user defaults/custom roles](https://docs.cloud.google.com/sql/docs/postgres/create-manage-users). Password input must avoid CLI command-line literals, shell history and SQL/audit logging.
2. **Identity and secret bindings:** create separate frontend/API/task-worker/migrator/dispatcher/task-delivery service accounts, no downloadable keys. Retain [iam.example.json](iam.example.json)'s resource-scoped boundaries, merge bindings without replacing unrelated members, review network-use permissions for the Cloud Run service agent on the subnet, and grant exactly the runtime secret versions/resources needed. Migration and app credentials are separate. The dispatcher gets the application URL plus queue create/get/fullView and exact delivery-account actAs; it gets no AI/HubSpot/bridge/token-key access.
3. **Private transport implementation:** update service/job/WorkerPool templates and offline renderer for Direct VPC, private DNS assumptions, internal API/worker ingress and the selected authenticated SQL path; add missing role-specific live secret references separately. Bootstrap definitions must remain health-only/no credentials. Validate render output and isolation before any deploy. Current placeholders alone cannot execute this new private design.
4. **Images and bootstrap:** build the actual source with pinned Dockerfiles; run isolated Linux smoke and save a fresh release record; authenticate Docker to the chosen registry, push the reviewed images and record registry digests. Existing local digests are not registry receipts. Bootstrap the three private stable services, discover actual URLs, then rerender exact origins/audiences. Public frontend access is a separate final rollout step. Do not expose bootstrap as a ready demo.
5. **Schema and corpus:** execute only the explicit migration job; expected current head is **0011**. Run no-provider readiness against SQL. Prepare all six fake sample slots once for restricted fake QA; verify actual versions/vector dimensions before admission. Real hosted embeddings require their own funded preparation/evaluation and profile-compatible vectors, not copied fake vectors or automatic embedding on first visit. Do not copy development guest sessions/tokens into the cloud database.
6. **Queue and background work:** apply reviewed queue overrides/OIDC/IAM; deploy full API/frontend/worker revisions and start the dispatcher **last** at count1. Use the v2 WorkerPool REST body as v2, never as v1 `gcloud ... replace` YAML. Verify health, persisted heartbeat, oldest-due/recovery counts and an actual task receipt. A running dispatcher is not proof of delivery. Keep Cloud Scheduler absent unless explicitly chosen in a new architecture decision.
7. **Hosted live configuration:** the standard runtime AI allowance is currently expired and finite CRM allowance unset. Local manual no-cap policies deliberately reject cloud targets. Set new approved hosted policy in `runtime_config.py`, verify current models/rates, fund/prepare sources and add the role-specific key references. Filling secrets alone will not make public real AI/CRM start. `FAKE_MODE=true`/`PAID_DEMO_ENABLED=false` is the initial QA lane; no silent fake fallback for live failures.
8. **Canonical URL:** begin with the actual frontend HTTPS `run.app` URL; choose the custom domain/hosting/DNS/certificate approach separately with its cost. Existing renderer appends `.run.app` and does not accept a custom domain as-is. Update canonical origin, secure cookies/CSRF/CSP, Turnstile hostname and the registered HubSpot app's exact HTTPS `/auth/hubspot/callback` redirect together. Preserve localhost as a separate developer redirect. HubSpot app/client IDs remain code-owned; visitors still select/consent to their own account.

CLI can handle those cloud resources, restricted IAM, empty-secret inventory, image builds/pushes, revisions/jobs, migrations, task configuration and metadata/rollback checks after the concrete funded plan is approved. The owner supplies secret values, the domain decision and interactive HubSpot consent/native-account acceptance. No account registration/purchase or provider authorization screen can be inferred from CLI deployment success.

### Hosted acceptance and release gate

- Confirm SQL has **only PRIVATE IP**, TLS/private transport succeeds from allowed workloads, frontend has no SQL credentials, app user cannot DDL/admin, migrations/schema0011/extensions/profile/six corpus versions pass and connection counts fit real `max_connections`. Current nominal API/worker pools total21, dispatcher needs2 (up to4 during overlap); add release/admin/rollout headroom. Measure memory/cold start and overlapping booking invariants on the chosen tier.
- Deny internet access to API/worker, unauthenticated calls and wrong identity/audience; prove frontend identity can call API through the VPC/DNS path and exact Cloud Tasks OIDC can call only the worker. Verify the app's worker JWT validation with the actual Google header/token; local tests do not prove Cloud Run ingress header behavior. Preserve guest origin/CSRF/session/version/idempotency fences.
- Exercise actual deployed duplicate/late task, crash-before-enqueue recovery, dispatcher stop/resume, expiry/private-byte purge, exhausted work and honest unknown outcomes within a bounded authorized hosted test. Confirm Continue without HubSpot creates no CRM work or calls. No real CRM export test until the owner approves that account/fictional booking.
- Perform owner HubSpot consent/token exchange/Free-plan USD/schema/record-link/cleanup acceptance, deployed Turnstile interaction behavior, funded real AI/RAG grounding and phone/laptop/desktop flows. Record limitations; do not call HubSpot the only remaining deployment test.
- Rehearse backup restore into a separately authorized instance, including schema/key compatibility. Keep image digests, numeric secret versions, migration head, vector profile, database/backup identity, IAM/queue configuration and previous compatible revisions in a private rollback record. Application rollback retains schema; populated DB downgrade is never automatic.
- Verify budget recipients in the console, actual alert delivery when appropriate, chosen Cloud Run cap CONFIGURED, service maximums and non-content logging/retention/access. Configure fixed-code error/SQL-capacity/dispatcher-stale/work-needs-attention monitoring without chat/contact/task-body leakage. Retain audit evidence; do not buy a scanner, enable paid scanning or export repository metadata implicitly.
- Public rollout is the last step: grant public invocation to **frontend only**, with internal API/worker and private SQL unchanged, then verify HTTPS/callback/real capability/rollback. If a cap pauses the dispatcher, expiry processing is also paused: database costs and pending cleanup require operator attention.

The remaining sections contain existing local release tools and older dated provider setup/evidence. Use this checkpoint for current cloud readiness; their historical examples are not a deployed receipt.

This directory owns packaging and operational recovery. Product decisions and phase/evidence remain in [the blueprint](../docs/CHOREOGRAPH.md) and SBS-010/012–015. Examples and the offline renderer prepare reviewable configuration/commands; they contain no credentials and execute no provisioning/deployment/IAM writes. AI defaults remain fake; public CRM is disabled until real visitor HubSpot OAuth is configured. Fake CRM is reserved for isolated tests. Explicit live AI and independent visitor CRM code paths are implemented and tested with injected transports. Hosted examples remain restricted fake QA candidates until separately funded real/hosted acceptance. Hosting fakes and the continuously running WorkerPool still cost money.

## Implemented readiness and acceptance tools

Run Python module commands below from `apps/backend` with `../../.venv/Scripts/python.exe` on Windows (the corresponding `.venv/bin/python` on Linux). The ignored app-local files hold only keys, connection settings and the two standard mode controls. Fixed provider policy and finite authorization records live in `choreograph/runtime_config.py`; these are not env variables. Local setup migrates old aliases explicitly while preserving credentials. Runtime loaders reject removed/fixed env settings. Frontend holds only its API URL, origin and bridge secret. No sibling or former root env file is loaded; no secrets are printed.

```powershell
../../.venv/Scripts/python.exe -B -m choreograph.readiness
../../.venv/Scripts/python.exe -B -m choreograph.readiness --env-file .env.local --database --require-ready
../../.venv/Scripts/python.exe -B -m choreograph.acceptance ai evaluate
../../.venv/Scripts/python.exe -B -m choreograph.acceptance crm sync
../../.venv/Scripts/python.exe -B -m choreograph.cloud_plan
```

Readiness constructs no provider clients; only `--database` performs SQL reads. It checks configuration, checked-in corpus/tokenizer hashes, current migration head0011, PostgreSQL17, vector0.8.5/btree_gist1.7, six ready sample slots and matching vector dimensions/profile. `python -m choreograph.release readiness` uses explicit container environment and exits2 if any check fails, without composing provider clients. Missing names/fixed error codes are safe; secret values and credential URLs are omitted.

Acceptance defaults to a no-network plan even if an env path is supplied. `--execute` is an explicit operation switch, **not owner authorization**. Execution requires the later approved lane, unique run UUID, exact account/grant and cleanup choices. Durable `acceptance_runs` records cannot be replayed or removed by downgrade. Failed/ambiguous work consumes its reserved allowance. Actual reported token counts, unknown-usage counts, phase latency, fixed failures and opaque source/page references remain separate from conservative reservations. The injected test mode is labelled and cannot be selected through the CLI.

The AI lane is local only, on the owned port45862, using a uniquely named `choreograph_acceptance_*` database. After authorization, `ai init-db --execute --run-id UUID` creates and migrates that disposable database using only the local DB setting; output contains its name. Then `ai prepare` and `ai evaluate` require **different** unique run UUIDs, `--execute --database-name NAME --max-cost-micros INTEGER`, a reviewed private `.env.local`, code-owned model/tokenizer/dimension/rates and one durable finite AI grant in `runtime_config.py`. Neither step creates a cloud resource or invokes HubSpot. `prepare` indexes the six canonical sources once; `evaluate` runs18 authored cases plus absent evidence, two replacements and policy→week→supplies continuity, at most two guests. It retires those guests/purges private sources before success. A real unsupported answer stops the run and stays failed. The CLI never silently retries or substitutes a fake result. Dropping a disposable DB is a later explicit, identity-verified cleanup action; development data is never dropped.

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

The downgrade role requires `--target` and never chooses a target for the operator. Migration `0006` introduced private purge completion; migration0010 preserves acceptance-run receipts against downgrade and current head is0011. Downgrades can discard state and older migrations can remove whole tables. A container exit code does not prove backup restoration or safe deployed rollback. Record image digest, source/input fingerprints, migration head, target, backup reference and actual result without secret values. Keep the previous verified image and matching secret versions available through the authorized rollback window; key rotation must account for still-encrypted tokens.

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

## Free HubSpot account and real OAuth setup (updated24 October2026)

### What HubSpot does, and how to test it —25 October2026

**Current connected onboarding:** after destination verification, review and explicitly tick the fictional-record sharing checkbox, then click **Allow sharing and continue**. A successful server acknowledgement opens the front desk automatically. There is no pre-consent Continue action on the HubSpot path. A failed/unknown sharing response remains on setup with an inline error. A restored already-approved connection resumes chat without another consent request. Continue without HubSpot remains a separate choice that detaches this workspace before entering. Connection management is one **Uninstall HubSpot** action in **Business → Connections**; its confirmation includes optional demo-record cleanup.

**Navigation recovery:** Opening the front desk now includes the shared animated Spinner only while a navigation attempt is active. If client routing remains stuck for8seconds, the app makes one ordinary same-origin document navigation to the workspace. The guest cookie restores the saved workspace/sharing choice; this does not re-authorize exports or reset records. If another8seconds pass without departure, the spinner stops and an explicit **Open the front desk** link remains available. Timers are cancelled after departure, and an already-approved session needs no repeated sharing click. This corrects the owner's reported indefinite label; local component/type/HTML evidence is distinct from the owner's actual browser acceptance.

**Current Verify destination repair:** the owner successfully reached destination setup, but the first two Verify clicks hit a404 currency endpoint and showed its misleading non-USD notice above the visible form. The owner's Company Currency screenshot and a matching-account read confirm USD. The app now reads company currency through `/account-info/2026-09/details` using existing OAuth, verifies the returned account ID, and distinguishes a missing response from a real currency mismatch. No account currency change is needed for this owner's account. After the owned API/runner reload, refresh the page, select the existing pipeline/open stage, authorize ID fields if needed and Verify again. A spinner appears during verification and any error appears directly below the button. Success shows the fictional-data review and separate Allow sharing/Continue controls. The three diagnostic provider calls were read-only and accounted; the agent did not create fields or records or uninstall anything. Actual setup/export acceptance remains the owner's next action.

**Before public release:** coordinate removal of unused `settings.currencies.read` from the actual registered required scopes and the code/manifest, then test a fresh install. Removing it from only our URL while HubSpot still requires it would break installation. This repair adds no permission and preserves the current registered contract; it does not submit a listing or mutate app registration.

**Owner-observed first-install blocker,25 October:** HubSpot displayed “the app developer has not signed the acceptable use policy.” Successful native installation/token exchange remains unverified. HubSpot's [Senior Community Moderator's current instructions](https://community.hubspot.com/t/installation-app-failure/155107/3) locate this under the **app's Distribution tab → Begin publishing / Continue publishing → review and sign the AUP**, rather than general account settings. Open the registered Choreograph project in developer account149626293, select its app component, and follow that route. The owner reviews/accepts the terms personally; do not submit a Marketplace listing just to finish this prerequisite. Then return to Choreograph and begin a fresh Continue with HubSpot attempt so the short-lived OAuth state is current. No credential change, app re-registration or backend restart is indicated by this message. Acceptance is not yet observed and the agent has not signed terms, installed an app or bypassed the gate.

**Marketplace checklist versus local testing:** the [three active, unique installs requirement](https://developers.hubspot.com/docs/apps/developer-platform/list-apps/listing-your-app/app-marketplace-listing-requirements) gates Marketplace listing submission. Those qualifying installs must be unaffiliated production accounts with successful activity in the past30 days; the owner does not need three accounts to test this integration. Current [marketplace-distribution limits](https://developers.hubspot.com/changelog/new-marketplace-distribution-app-install-limits) allow25 installs before listing approval. Signing the developer AUP does not require completing or submitting the Marketplace listing checklist.

**Sample install URL:** this is a template OAuth authorization URL, using the app's public client ID, redirect URI and configured scopes. It opens HubSpot's account choice and access approval; successful connection also requires the server-side code/token exchange. See the [current OAuth flow](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/oauth/working-with-oauth). For the actual Choreograph test, always start from **Continue with HubSpot** in the app. Our server creates a short-lived, single-use state tied to the current guest workspace; the callback intentionally rejects a bare sample URL without that matching state. The developer dashboard's Test URL is not a replacement for the integrated connection flow or evidence that a guest is connected. Do not publish a local callback as an external visitor install route.

**Purpose:** Choreograph reserves the cleaning appointment in its own calendar/database, then shares a CRM summary with the HubSpot account you selected. HubSpot lets a business see the booked work alongside the customer record and sales pipeline. This implementation creates a **contact + associated deal**. Appointment start/end are stored in the deal's **Description**. It does not create a HubSpot Meeting/Appointment calendar object, book a Google/Microsoft calendar or send an invitation. The API implementations for [deals](https://developers.hubspot.com/docs/api-reference/crm-deals-v3/guide) and [meeting activities](https://developers.hubspot.com/docs/api-reference/crm-meetings-v3/guide) are distinct; the current transport invokes only the reviewed contact/deal operations.

| Action in Choreograph | Expected result in HubSpot |
| --- | --- |
| Connect/account approval | Account authorization and pipeline options; no contact/deal export yet. |
| Verify destination | Validate your chosen existing pipeline/open stage, USD currency and demo ID fields. With your separate checkbox, create one `choreograph_demo_key` property on Contacts and one on Deals if missing. |
| Allow sharing | Authorize this workspace's sample contact/reviewed bookings. Already booked/completed/cancelled records with an actual reservation are included; unreserved requests are excluded. |
| Ask questions, get a quote or select a time | No new booking record is exported merely for these actions. |
| Explicitly Book this clean | Save the authoritative reservation and sync work together; the runner then creates/updates a synthetic **Demo Guest** contact and one deal for that booking. |
| Reschedule | Update the **same deal**, preserving its identity and contact link; description shows the new start/end/cleaner. |
| Complete/cancel | Update the same deal's description to `Status: completed` / `Status: cancelled`. Cancellation releases the time in Choreograph; it does not delete the deal. |
| Choose Continue without HubSpot | Ordinary booking still works; no HubSpot calls or CRM outbox work. |

The deal name starts **[Choreograph demo]** followed by the quoted service name. Amount is the exact quote total in **USD**. Description includes fictional-demo label, status, start/end with the saved local numeric UTC offset, cleaner, duration, amount and no-real-service/payment notice. The linked sample contact is **Demo Guest**, with **no email address**. The consent preview makes this explicit. HubSpot rejected the previous `.invalid` email domain during the owner's25 October test; the contact now uses firstname/lastname plus its opaque unique demo key. It does not use the owner's email or a real customer. Repeated deliveries reuse opaque unique demo IDs, rather than duplicating records. HubSpot's [current contact API](https://developers.hubspot.com/docs/api-reference/crm-contacts-v3/guide) and [unique property guide](https://developers.hubspot.com/docs/api-reference/crm-properties-v3/guide) support this identity model. The owner's25 OctoberUSD80 booking produced actual verified native contact/deal/association readback, then its demo records were removed by the workspace's existing two-hour expiry cleanup. This is historical create/readback and expiry-cleanup evidence, not a still-active record. Start a fresh demo for further lifecycle/uninstall testing.

**Status placement matters:** the deal stays in the pipeline/open stage you chose during setup. Booking lifecycle status lives in Description; the app does not automatically move it to Closed won/lost or mark a payment. Scheduling changes are **one-way from Choreograph to HubSpot**. Editing the HubSpot deal does not reschedule Choreograph, and the next authorized sync can restore the app-owned fields. No HubSpot workflow, appointment object or two-way webhook synchronization is implemented.

Owner walkthrough:

1. Use `http://localhost:45860/demo` and choose **Continue with HubSpot**. On HubSpot, select the intended empty Free CRM account and approve Choreograph. No upgrade/calendar connection is required for this contact/deal test. Keep this guest workspace open through the test.
2. Back in Choreograph, confirm the displayed account ID matches the account you intended. Choose an existing **Pipeline** and **open Stage** where you want the demo deal. The account company currency must be USD; the app never changes it. If your active business account uses another currency, use a separate empty USD account or skip CRM.
3. For a fresh account, explicitly tick **Create Choreograph ID fields in contacts and deals if needed**, then **Verify destination**. This permits the two deduplication fields, not arbitrary account/schema changes. Review the displayed fictional contact and destination, tick the sharing checkbox and select **Allow sharing and continue**. After the server confirms sharing, chat opens automatically. Existing booked records in this workspace may begin exporting at this point; this is disclosed separately from OAuth approval.
4. Continue to the front desk. Get a quote and choose a time; check the details and explicitly book. The initial **Booking saved. CRM sync is pending** message is normal. Local runner cycles and browser polls are approximately2seconds each, plus provider latency; this is not an exact completion guarantee. On success the app says **HubSpot sync verified** and exposes **Open contact in HubSpot** / **Open booking in HubSpot** links. Use those links to avoid choosing the wrong account or similarly named record.
5. In HubSpot, the booking link opens a **deal**. Alternatively navigate **CRM → Deals** (possibly under **More**) and search `[Choreograph demo]` in the selected pipeline. Open the record, compare Amount and its associated Demo Guest contact, and inspect **Description** for the service's exact start/end/offset, cleaner, quote, duration and status. If Description is hidden, choose **Actions → View all properties** and search for Description. [HubSpot's record layout guide](https://knowledge.hubspot.com/records/understand-the-default-record-layout) explains this control. The deal's default Close date is not the appointment date; the app doesn't populate it as a schedule field.
6. In Choreograph, reschedule the booking. Once its new revision syncs, refresh the **same HubSpot deal URL** and compare the new time. Its record ID should remain the same. Then either mark that booking completed or cancel it; after sync, check its Description status. To inspect both outcomes, create a second booking deliberately. No real cleaning, payment, message or invitation occurs.
7. To remove the connection, choose **Business → Connections → Uninstall HubSpot**. Confirm the selected account in our dialog. Keep **Also remove this demo’s contact and booking records** selected to clean those records first, or clear it to retain them. Local bookings stay in Choreograph. Wait for the separate record/uninstall results, then check HubSpot Connected Apps. HubSpot sends its own admin notification. Another active demo using the account blocks uninstall; reset that other demo first. Reset/expiry still queues owned-record cleanup while access remains available, without automatically uninstalling. ID property definitions remain. Revoked access or ambiguous failures must stay visible honestly.

**What has been checked before your click:** current code path, real HubSpot transport with injected HTTP, actual isolated PostgreSQL lifecycle/duplicate/recovery/consent/skip/security checks, native-link gating and read-only local configuration/database readiness. Sync is claimed only after matching property readback **and** verified contact/deal association. A failed CRM sync preserves the local booking and exposes pending/reconciling/needs-attention state; it never creates a fake successful receipt. Native token exchange, actual Free-account ID-field/email acceptance, your real record display and cleanup still require the owner's live test. A passing injected test is not that live receipt. Current detailed results belong to [SBS-024](../docs/tickets/SBS-024-hubspot-free-readiness.md).

The dated setup history below describes the earlier registration steps; the app is now registered and local configuration is ready. You do not need to register it again.


**25 October2026 local manual AI:** SBS-028 records the owner's explicit request for no aggregate budget or duration while they test manually. The validated local loader uses `LOCAL_MANUAL_AI_GRANT_ID` from `runtime_config.py` with no expiry/ceilings and retains durable usage accounting and request safeguards. Historical AI grants and standard container/automated acceptance stay finite. The two env switches and keys stay as configured. This changes no HubSpot prerequisite or CRM allowance; agent-run paid tests still require separate specific authorization. Use the documented local launcher and read-only readiness/health checks to start, without generating an AI request.

Choreograph's visitor choices are **Continue with HubSpot** and **Continue without HubSpot**. Connecting uses HubSpot's real account-selection/authorization screen. Public simulated-account approval is removed. The Choreograph OAuth app is registered and local configuration is ready. Missing credentials still disable CRM honestly. AI can remain fake independently, so testing the CRM transport itself needs no OpenAI credits.

[SBS-024](../docs/tickets/SBS-024-hubspot-free-readiness.md) owns provider research; [SBS-025](../docs/tickets/SBS-025-local-configuration.md) owns the simplified configuration. Native visitor-account acceptance is still unverified. The backend env contains only the confidential OAuth app secret for this provider; public app IDs and fixed policy are in backend code. App registration is performed once for Choreograph, then every visitor chooses their account through the normal Connect button.

HubSpot currently documents a permanent Free CRM tier with two users,1,000 contacts and a1,000-record allowance across other standard object types. Standard API access has Free-plan limits; no paid API increase, workflow, custom object, marketing contact, payment or multi-currency subscription is selected by this integration. [Current free limits](https://www.hubspot.com/pricing/crm), [API limits](https://developers.hubspot.com/docs/developer-tooling/platform/usage-guidelines). Actual installation, free-account scope/property capacity and native record verification remain account acceptance, not an inferred success or a promise that every HubSpot feature is free.

### 1. Choose the Free CRM account to connect

Start with [HubSpot Free CRM](https://www.hubspot.com/products/crm) and select Get free CRM. Use your real registration details and actual country; do not buy a subscription, API increase or paid trial for this demo.

For **Free-plan acceptance**, use a separate empty standard Free CRM account. Developer test accounts can temporarily include Enterprise features, so successful installation there alone cannot prove the standard Free plan works. Juniper's catalogue is USD: this test account's company currency must be USD. HubSpot allows changing the single company currency in Free accounts; multiple currencies require a paid plan. Set USD manually in **Settings → Account defaults → Currency** on the empty test account. Do not change an active business account's company currency for this demo. Choreograph only reads currency and fails closed on mismatch; it never changes currency, converts quotes or buys multi-currency. [Official currency guidance](https://knowledge.hubspot.com/account-management/add-and-edit-your-account-currencies).

Egypt appears supported: HubSpot's own [Egypt directory](https://ecosystem.hubspot.com/marketplace/solutions/egypt) lists local partners. This is evidence of service presence, not a completed test of your individual signup or verification.

An optional developer fixture can be created through **Development → Testing → Test Accounts → Create developer test account**. Name it **Choreograph Testing**, then open it from that list or the account picker. This optional separate portal is useful for development, but is not required for the normal Connect button. Use fictional contacts and deals in the account selected for testing.

HubSpot's [account-types documentation](https://developers.hubspot.com/docs/getting-started/account-types) describes up to ten free developer test accounts, with 90-day access to many Enterprise features. The separate Standard Sandbox requires Enterprise and is unnecessary here. Manage the test portal through Actions, including Renew trials; HubSpot also documents expiry after 90 days without qualifying API activity. A Free CRM account itself is distinct from these temporary test features.

### 2. Register Choreograph's OAuth app

The CRM account you select supplies the data; Choreograph's registered OAuth app supplies the integration identity. Register it once as the application operator. A visitor then connects an ordinary HubSpot account through the website; they do not create an app or paste a private/static token.

Use HubSpot's current [CLI app-creation guide](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/create-an-app), rather than old tutorials that create a legacy public app in the UI. After installing the supported CLI using that guide:

```text
hs account auth
hs project create
```

Choose App, OAuth authentication and Marketplace distribution for the intended visitor-installable integration. Configure the generated app metadata with Choreograph's name/description and this exact local redirect:

```text
http://localhost:45860/auth/hubspot/callback
```

The prepared [app manifest](hubspot/app-hsmeta.json) contains the required OAuth configuration and exact backend scopes. Place its contents in the generated project's `src/app/app-hsmeta.json`; retain the generated project configuration. Add actual owner support/contact metadata if HubSpot requests it. No fictitious support domain, account ID or client secret is embedded. This local manifest is not a registered or uploaded HubSpot app, and was not built by an authenticated HubSpot CLI in this run.

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
settings.currencies.read
```

Match the app's OAuth permissions to that contract. No payments, marketing email, workflows or extra enterprise objects are needed. Once its configuration is reviewed, the official workflow uses `hs project upload`, then `hs project open`; open the app component and its Auth section to obtain App ID, Client ID and Client Secret. These commands create/update the HubSpot app; none was run by this guide's preparation.

The current [unlisted Marketplace distribution cap](https://developers.hubspot.com/changelog/new-marketplace-distribution-app-install-limits) is 25 account installs before listing approval. Private OAuth distribution normally permits ten selected customers. These are app-distribution limits, not a payment requirement for creating your test portal, and not unlimited public installs.

### 3. Configure the local app, then connect

HubSpot [permits HTTP localhost redirects but rejects IP-address redirects](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/oauth/working-with-oauth). When enabling OAuth, set `CHOREOGRAPH_ORIGIN=http://localhost:45860` consistently in both app-local files and browse that host throughout the connection. Keep the same frontend/API/database ports; do not mix localhost and 127.0.0.1 guest cookies.

**One-time Choreograph operator setup:** put the registered app's public `HUBSPOT_APP_ID` and `HUBSPOT_CLIENT_ID` in [runtime_config.py](../apps/backend/choreograph/runtime_config.py). Put only its confidential `CHOREOGRAPH_HUBSPOT_CLIENT_SECRET` in the backend `.env.local`. This is Choreograph's OAuth app secret, not a visitor's CRM API key. The client ID identifies Choreograph on HubSpot's consent screen; the server uses its secret to exchange the returned authorization code. [Official OAuth flow](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/oauth/working-with-oauth).

The same backend file owns fixed distribution/capacity, schema policy and the separately authorized finite CRM acceptance allowance. On25October the owner separately approved local manual HubSpot without a request quota or expiry; only the validated local loader selects `LOCAL_MANUAL_CRM_GRANT_ID`. Automated/container/hosted acceptance still requires its own finite authorization, never a rolling grant. Durable counters and account/session/app binding remain. Real CRM availability derives from the registered app settings plus its client secret. There is no second CRM enable switch or public simulated-account fallback. Callback is derived from `CHOREOGRAPH_ORIGIN` and must match the registered localhost callback above.

If the owner approves automatic ID-field setup, enable that fixed backend schema policy; the visitor must still explicitly check **Create Choreograph ID fields** and submit Verify destination. Only one unique `choreograph_demo_key` property per contacts/deals object is created. Otherwise prepare compatible fields manually. Free property-capacity failure never buys an upgrade.

Agent-run native CRM acceptance still needs a fresh finite HTTP allowance and explicit account/export scope. Historical suggested500-call/100-per-workspace test bounds are not the owner's approved local manual policy. The paid AI master remains independent; testing with fake AI and real HubSpot needs no OpenAI spending. Do not revive an expired OpenAI grant merely to test CRM.

Before enabling/restarting, run the credential-safe CRM-only diagnostic from the repository root:

```powershell
Push-Location apps/backend
../../.venv/Scripts/python.exe -m choreograph.readiness --hubspot-only --env-file .env.local
Pop-Location
```

This implemented command reports fixed codes/missing field names and the public localhost callback with `provider_calls:0`. It constructs no provider and opens no database; an expired AI grant does not hide the HubSpot diagnosis. `CRM_CONFIGURATION_VALID` establishes configuration shape only, not a successful account installation or export.

Keep the client secret out of chat, browser code and Git. Visitors never enter app IDs, app secrets or private-account tokens: after this one-time operator setup they only click Connect and approve their account in HubSpot. AI mode remains independent. A changed frontend origin needs its normal restart; reload only the owned services whose configuration changed.

Keep all app-local env assignments unquoted, including empty secrets and the two boolean controls. Setup must never re-add wrapping quotes. Current values round-trip through Python and Node unchanged; if a future credential needs comment/expansion syntax, line breaks or significant surrounding whitespace, stop with a secret-free diagnostic instead of altering or quoting it.

Continue with HubSpot then opens HubSpot immediately. Select the account you intend to test, review the requested access and authorize the app there. HubSpot may show its own unverified-app confirmation. On return, select/verify the booking destination and explicitly allow fictional-record exports. Those actual account/data approvals remain; the removed step is the pretend-account confirmation. Continue without HubSpot creates no HubSpot calls or exports.

Use the prepared bounded real-acceptance tools above to verify one reviewed contact/deal, native record links and cleanup. Developer test portals include trial features: successful testing there alone does not establish every Free-plan scope/property entitlement. No account creation, credentials, live OAuth exchange, export, cleanup or app registration has been performed by preparing this guide.

Current export behavior: Allow sharing queues any **already booked** records plus later reviewed lifecycle changes. Repeated consent/replayed commands do not duplicate exports; unreserved/declined requests remain excluded. Each export verifies company currency USD, writes exact Amount plus `deal_currency_code=USD`, local appointment/end with numeric offset, duration, cleaner and current status in Description, and preserves the explicitly selected pipeline/stage. Rescheduling/cancellation updates the same app-owned deal; it does not guess a new sales stage. Fresh contact/deal/association readback is required before Synced/native links appear. Reset/two-hour expiry schedules removal of app-created records while authorization remains available, so these test records are intentionally temporary; uninstall remains separate and HubSpot notifies admins.

The official unmodified HubSpot wordmark comes from the [HubSpot newsroom logo pack](https://www.hubspot.com/newsroom), used to identify this integration under the [Developer Terms branding rules](https://legal.hubspot.com/hs-developer-terms). No partnership/certification claim is made.
