# SBS-035 — Canonical RAG promotion and runtime secret access

Status: Complete canonical promotion and runtime secret IAM —26 October2026. No app deployment or provider spending.

The owner says continue after the completed private bucket/app-identity setup, whose explicit next step was canonical index promotion and runtime secret access. This slice copies only verified fictional canonical data from the existing local object snapshot into the fresh private hosted store and grants per-secret runtime access. It may read only deployment `CHOREOGRAPH_TOKEN_KEY` version1 into process memory to re-encrypt canonical data; provider/bridge secret payloads are not read, printed or copied. No SQL, local private-state mutation, paid provider call, new embeddings, grant renewal, GitHub access, image push, app deployment or Git commit is authorized.

## Concrete plan and file allocation

- Add `scripts/promote-canonical.py`, an operator-only dry-run/apply tool excluded from image inputs. Construct a three-table export: one current live embedding profile, six repo-hash-matching ownerless ready document versions and their exact re-parsed passages with already-prepared finite compatible vectors. No workspaces, tokens, manifests, bookings, counters, accounts, grants or outbox records. Validate with the existing object unit of work.
- Add focused `apps/backend/tests/test_canonical_promotion.py` for strict source/passage/profile/vector admission, private-record exclusion, encrypted fresh-store copy, existing-store preservation, replay and unknown-write acknowledgement recovery. Use isolated atomic files and injected vectors only.
- Initialize only the fresh `choreograph-512713-private-state` GCS store with the verified canonical snapshot under deployment key version1. Content-addressed canonical bytes and the fresh state pointer are generation-conditional. Reject a used/private destination; exact canonical-only replay is read-only. Read back/decrypt using a fresh engine and compare the full filtered snapshot.
- Create `choreograph-frontend` service identity if absent. Bind `roles/secretmanager.secretAccessor` at individual secret resources: frontend only bridge; API all six; worker bridge/token/HubSpot only. Grant no project-wide secret role, frontend bucket access, downloadable key or provider spending authority.
- Record only nonsecret version/resource/count/hash metadata in `infra/canonical-promotion.json` and `infra/runtime-secret-access.json`. Update current runbook/AGENTS/blueprint/README/queue; preserve SBS-034 as its dated empty-bucket evidence.

The worker has no AI generation task and keeps AI mode fake/off in reviewed service configuration; CRM remains independent and still needs a valid release policy before activation. Granting secret access does not renew historical AI authority or populate hosted CRM grants.

## Validation boundary

No tests inherit owner live providers or SQL. Verify the filtered candidate locally before cloud mutation, repeat with current destination/key metadata before apply, inspect per-secret role readback, verify exact hosted row counts and absence of all private tables, and preserve local source snapshot bytes. Actual cloud copy/readback proves data promotion, not deployed inference or native CRM acceptance. Current Linux application image inputs should remain unchanged because only operator tooling/tests/docs are added.

## Actual result and settled validation

Local filtered dry-run selected exactly one current OpenAI embedding profile, six repo-matching fictional guides and23 prepared1536-dimensional passages. Re-parsing validates every page/section/content tuple before copying any vector.13 isolated no-SQL tests pass: private-record exclusion; source/passage/metadata/profile/missing/extra/vector-dimension/NaN rejection; encrypted copy/read-only replay/source preservation; used or previously initialized empty destination refusal; and committed-write/unknown-acknowledgement recovery without repeating the write. Full configured Ruff passes. Tests use injected vectors/temporary encrypted files; they do not load owner provider credentials.

The actual cloud copy reports `promoted`, with fresh-engine readback matching snapshot SHA256 `8c68f1e7c821624a51024787ea297a253d05d1dc6f54d241c67e4f99745a4084`. Immutable canonical digest is `1b880f84c20e4c7642b38beb55bf58bcd20e92601c904b2880b104bfe3a42815`; the two encrypted objects are219064bytes and460bytes. Final object inventory confirms only the pack/state pointer; anonymous pack media request returns401. No private table, old grant or counter was imported. Only `CHOREOGRAPH_TOKEN_KEY` version1 was read into memory; no key bytes were printed/written, and provider/bridge payloads were not accessed.

Created only the missing frontend service identity. Ten resource-level Secret Accessor bindings were merged and read back across six secrets: frontend bridge only; API six resources; worker bridge/token/HubSpot. All version1 metadata is enabled; no frontend storage grant, project-wide runtime role or user-managed key exists. Worker AI is kept fake/off in later service configuration because it performs CRM/cleanup and has no OpenAI key permission. IAM availability does not activate providers or renew grants.

`infra/canonical-promotion.json` and `infra/runtime-secret-access.json` record nonsecret actual results. SBS-034 foundation receipt remains its dated initial state and links to these follow-ups. Ignored detailed receipts: `.runtime/sbs035-canonical-promotion-result.json`, `sbs035-cloud-readback.json`, `sbs035-runtime-secret-result.json`, `sbs035-secret-policy-readback.json`.

The200-input Linux application fingerprint remains current/unchanged (`fd2c4d159d77f8c6d2c8f36cfbbc59dcab39a0339726f7ae108c6b68c431d802`): this slice adds only operator tooling/tests/docs, not image code. Owned local API/runner/frontend remain running; PostgreSQL remains stopped. No SQL, new embeddings, AI/HubSpot call, grant renewal, local state/env edit, GitHub access, app deployment, image push or Git write occurred. Service configuration, other hosting resources, public URLs/provider activation and operational setup remain in the current runbook’s setup-only list.

Final documentation/integrity checks:46 changed documents and61 new relative links/anchors validate; cloud JSON/YAML and edited inline scripts parse; the current-tree known-private-value scan is clean; release source fingerprint remains unchanged/current and `git diff --check` passes. No staged or committed files were created.
