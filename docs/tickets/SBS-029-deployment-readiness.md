# SBS-029 — Prepare deployment and the private cloud foundation

Status: **Research/runbook complete; empty secrets and project alerts created; paid provisioning and release remain gated**

Owner request,25 October2026: assess readiness while native HubSpot testing is deferred; research/document the deployment sequence, CLI capabilities, sibling-style budget alerts, same-name empty secrets and private managed PostgreSQL/backend connectivity. This authorizes the named secret metadata and matching alert setup. It supplies no chosen SQL size/monthly infrastructure allowance, public rollout, agent-run provider acceptance, Git write or sibling changes.

## Owning files and actual work

- `infra/README.md` owns the current deployment assessment, dated cloud inventory, private network/SQL design, secret consumers, CLI order, costs, remaining implementation gates, acceptance and recovery.
- `infra/budget-cloud-run-cap.example.json` is an unapplied REST-body example matching the sibling USD5 gross monthly Cloud Run cap. The amount must be reviewed against the continuously running dispatcher. It is not a gcloud flag file or spending permission.
- `docs/CHOREOGRAPH.md` and the queue point to this continuation; historical implementation/provider grants remain readable.

Read-only gcloud588.0.0 inspection found the existing `choreograph-512713` project, number729503363583, with billing enabled. The global CLI remains pointed at ScreenPilot; all Choreograph cloud writes used explicit project/account arguments. Secret Manager was already enabled. Cloud SQL Admin and Cloud Run were absent from the enabled API inventory; their resources were not provisioned. A SQL-list attempt reported SERVICE_DISABLED without enabling that API. No database absence claim is inferred from an API failure.

Created eight automatically replicated **empty** Secret Manager resources: CHOREOGRAPH_DATABASE_URL, CHOREOGRAPH_DB_PASSWORD, CHOREOGRAPH_BRIDGE_SECRET, CHOREOGRAPH_TOKEN_KEY, OPENAI_API_KEY, TURNSTILE_SITE_KEY, TURNSTILE_SECRET_KEY and CHOREOGRAPH_HUBSPOT_CLIENT_SECRET. Metadata readback confirmed **zero versions for all eight**. No env contents were read/copied, values added, runtime secret bindings granted or local settings changed.

Enabled only the Cloud Billing Budget API and created **Choreograph project USD10 alerts**, scoped to this project's number, monthly, including credits, CURRENT_SPEND thresholds50/80/100%, default billing IAM recipients enabled. First calls failed during disabled-API/propagation; a fresh list found no matching budget before the successful create. Final describe verified amount/scope/rules. No notification delivery or actual billed spend was tested. Budget identity and cloud metadata receipts stay ignored under `.runtime`.

Read-only sibling billing metadata confirmed Retailor/Roomedy/Retrosum/ClipBuilder have USD5 Cloud Run gross caps (CONFIGURED) plus USD10 project alerts; ScreenPilot's USD5 service budget is alerts-only. Sibling billing/keys/resources were unchanged. Choreograph uses a different currently linked billing account; no account relinking was performed.

Official paginated Catalog API inspection completed five Cloud SQL SKU pages. For europe-west1, current public on-demand worker CPU/RAM SKU rates imply **USD31.172022/730h** for1vCPU/0.5GiB before credits. PostgreSQL zonal micro/small compute is USD0.0105/0.035 per hour: **USD7.665/25.55 per730h**, excluding storage/backups/traffic/taxes. Backup SKU is USD0.08/GiB-month. These are estimates, not caps, measurements or a funded choice. The public pricing page's lower worked worker example is not substituted for the currently returned SKU rates. A USD5 cap is therefore prepared, **not applied**. Monthly budget/SQL size/region approval remains pending; no paid SQL/Run/VPC/DNS/registry resource was created.

## Readiness disposition

The prior committed local evidence remains366 backend/122 Node tests, types/Ruff/contracts and actual Linux44HTTP/291assertions at source fingerprint `f9fc9254884c5e7e7adddae9dd640740d4fa9642c45ba4b65249df45a89fa940`. No application source changed here. The tracked older Linux receipt remains historical; no hosted run is implied.

New deployment inspection identifies real implementation work before a private rollout: current service examples use IAM with ingress all; no Direct VPC/DNS path is rendered; managed SQL socket references alone don't select private IP; a tested private-IP/TLS transport is missing; current standard runtime AI grant is expired and hosted CRM finite grant is unset; real-provider secrets/preparation are absent from fake-only release templates. These are not all external prerequisites. Follow the concrete runbook gates before claiming ready.

Native HubSpot consent/token exchange/schema/record links/cleanup, real hosted Turnstile, real hosted AI allowance/quality, Cloud SQL roles/extensions/capacity/backups/restore, internal ingress/IAM/Tasks/WorkerPool recovery, domain/certificate and owner manual visual acceptance remain separate. No paid model request, HubSpot call, sample re-embedding, local restart, push, deployment or new commit occurred.

## Verification

Actual cloud metadata: eight secret resources/zero versions; one project-scoped monthly USD10 alert budget with the reviewed three thresholds; billing enabled; Budget API enable completion. Secret values were never accessed. Final checks passed: cap-body JSON and required scope/threshold fields, new relative document links, all eight zero-version metadata receipts, parse-only PowerShell AST validation and `git diff --check`. `node scripts/release-fingerprint.mjs` confirms the same195-input source hash as the prior actual Linux smoke; application tests were not rerun for documentation/metadata-only changes. The private setup receipt is `.runtime/gcp-deployment-setup-20261025.json`. Current installed gcloud parser inspection corrected the proposed storage auto-increase limit to an integer GB value (`20`, not `20GB`); no create command was executed to test syntax. No code/CSS tests are invented for this documentation/metadata-only continuation.


## Owner alert follow-up —25 October2026

The owner explicitly requested the usual USD5/USD10 alerts through CLI. Rechecked Retrosum source guidance and actual Retrosum/ScreenPilot budget metadata: Retrosum has a USD5 gross Cloud Run cap plus USD10 project alerts; ScreenPilot has a notification-only USD5 Cloud Run budget plus USD10 project alerts. Follow the requested **alerts** behavior, matching ScreenPilot's service scope/credit treatment without enabling a cap.

The existing Choreograph project USD10 budget was retained. Created **Choreograph Cloud Run USD5 alerts**, monthly, this project plus service152E-C115-5142 only, INCLUDING credits, CURRENT_SPEND50/80/100%, default billing IAM recipients. A separate list readback verifies exactly two Choreograph budgets, reviewed amounts/scopes/thresholds and no spendCap on either. The service alert thresholds are USD2.50/4/5; project thresholds remain USD5/8/10. Receipt: `.runtime/gcp-budget-alerts-20261025.json`; notification delivery/billed spend was not tested. No SQL/Run provisioning, secret access, sibling edit, cap activation, local restart or Git mutation occurred. Infrastructure allowance/tier/region remain undecided; setting alerts supplies no such funding.


## Owner exact-name secret follow-up —25 October2026

The owner requested recording the completed alerts, creating the secret names exactly as `.env.local`, and explaining the required values. The USD5 Cloud Run/USD10 project notification-only alerts remain documented above and in the operations checkpoint. A names-only parse of both actual app-local files found the same eight secret identifiers already present in Secret Manager; no duplicate, prefix/suffix rename or additional secret was created. No secret value was displayed or accessed through Secret Manager. Version-count readback is recorded in `.runtime/gcp-env-name-secrets-20261025.json`.

`infra/README.md` now distinguishes the four reusable provider-key values, new deployment bridge/token/admin values, the cloud application database URL that must wait for SQL setup, and four ordinary non-secret mode/address settings. It provides owner-run private-terminal generators without generating/collecting values in this task; token-key encoding retains44-character/32-byte padding. The DB admin password resource is not injected into the runtime, and saving it alone does not establish a SQL login. No local env changes, credential upload, database creation or application restart occurred.
