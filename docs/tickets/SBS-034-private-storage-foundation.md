# SBS-034 — No-database private storage and deployed-app identity

Status: Complete private storage/identity foundation —26 October2026. No application deployment or data promotion.

The owner reports all six secrets populated and requests setting up the private bucket and app access. They explicitly clarified **deployed app access**, not GitHub Actions. This authorizes the selected private bucket, necessary IAM API enablement, API/worker runtime identities and exact-bucket permission bindings. Continue using `DATABASE_ENABLED=false`; no SQL, GitHub federation, service-account keys, signed browser URLs, application deployment, paid provider calls, grant renewal, image push or Git commit is part of this slice. Preserve local services, env values, state and the stopped PostgreSQL volume.

## Concrete resource plan

- Project: `choreograph-512713` /729503363583; always pass the project explicitly and preserve the global CLI configuration.
- Region: `europe-west1`, following the current hosting plan/CLI setting and announced before creation.
- Bucket: `gs://choreograph-512713-private-state`, Standard regional storage, public-access prevention enforced, uniform bucket-level access enabled, versioning disabled, soft delete0, no retention lock or lifecycle deletion. The exact name already lives in backend `runtime_config.py`.
- Identities: `choreograph-api@choreograph-512713.iam.gserviceaccount.com` and `choreograph-worker@choreograph-512713.iam.gserviceaccount.com`.
- Role definition: `projects/choreograph-512713/roles/choreographPrivateObjects`, with exactly `storage.buckets.get`, `storage.objects.get`, `storage.objects.create`, `storage.objects.delete`. Bind only on this bucket to the two runtime identities; no project-wide storage grant.
- Original guides remain repo/backend-image assets. This bucket is for encrypted canonical source/search packs and authoritative application state. No local guest/account/outbox/ledger state or secret payload is uploaded by this slice.
- Backend `GCSObjects` already uses Google Application Default Credentials. At service deployment, attach the corresponding service account to API and worker. No URL signing or browser permission is needed; source previews remain authorized server routes.

## Work and validation

Inspect for existing/conflicting resources before each creation. Reuse exact matching resources; stop on unexpected configuration rather than replacing policies. Merge bucket role additions with gcloud's IAM binding command, preserving unrelated administration bindings. Verify the bucket's actual raw policy against runtime checks, exact custom-role permissions and bucket bindings, absence of public principals and absence of user-managed identity keys. Retain content-free receipts under ignored `.runtime/sbs034-*`.

Secret metadata readback is already complete: all six required names have enabled version1, without reading values. The two removed SQL secrets remain unnecessary. Cloud Run/Tasks/Scheduler/service-secret access and canonical-only data promotion are separate remaining setup; do not claim an empty bucket means hosted RAG is initialized or the application deployed.

## File allocation

This ticket owns current resource/scope/results. `infra/README.md` owns the current inventory and usage instructions; `infra/object-foundation.json` will record actual nonsecret resource identities/policy/version metadata after successful readback. AGENTS/blueprint/README/queue receive concise current pointers. No application source or dependency change is needed.

## Actual result

Settled verification:11 offline cloud-plan tests pass;45 changed documents and54 new relative links/anchors validate; cloud JSON/YAML and edited inline scripts parse; current-tree known-private-value scan is clean. The200-input object release fingerprint is unchanged/current, and `git diff --check` passes. Owned API/runner/frontend remain running, PostgreSQL remains stopped, global CLI project remains unchanged, and final service inventory confirms only IAM was added among this slice's candidate APIs.

Completed26 October2026 at09:54:18UTC. IAM API was enabled, the two reviewed user-managed service accounts and four-permission role definition were created, and the regional private bucket was created with the required history/retention settings. Bucket-only role bindings were added for API and worker. Readback confirms the expected policy and exact permissions, no user-managed identity keys and no project-wide runtime-account role bindings. Existing project administrator/viewer bucket bindings were preserved. An actual anonymous metadata request returns401. An owner-authorized content-free object inventory confirms the bucket is empty.

All six required secrets have enabled version1 by metadata; values were not read or validated. No secret accessor role was granted in this slice. `infra/object-foundation.json` is the public nonsecret resource receipt. Detailed ignored receipts: `.runtime/sbs034-foundation-result.json`, `sbs034-bucket-metadata.json`, `sbs034-bucket-iam.json`, `sbs034-secret-version-metadata.json` and `sbs034-private-storage-check.json`.

The API/worker must later be attached to the corresponding identities in Cloud Run configuration; current GCS code already uses runtime ADC. No application source change, Docker/SQL startup, local env/state edit, deployed revision, GitHub access, service-account key, secret payload read, source upload, paid provider call or Git write occurred. Actual IAM readback and anonymous denial are scoped configuration evidence; runtime data-plane acceptance is not claimed. Remaining setup is in the runbook, with no post-provision test matrix in the owner’s list.

## Subsequent canonical/secret setup

The later owner continuation [SBS-035](SBS-035-canonical-promotion.md) populated the private store with only the six canonical guides/23 prepared vectors and configured resource-scoped runtime secret access. The empty-bucket/no-accessor observations above remain the actual SBS-034 checkpoint; use SBS-035 and the current runbook for present state. No application deployment occurred.
