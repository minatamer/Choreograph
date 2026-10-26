# SBS-040 — Build the published Python security runtime without waiting for its image tag

Status: Runtime resolved, validated and privately uploaded —26 October2026. Clean baseline `95706a00446e2bcfadb28ba79b5020425a28fc75`.

The owner asks why the Python Docker blocker is not being fixed. The existing deployment/Git authorization persists. Treat this as authorization to resolve the runtime directly, not a request for the owner to operate Docker. Earlier advice made the absent prebuilt tag unnecessarily decisive: the official source release and Docker maintainers' updated recipe are already available. This ticket supersedes the earlier wait-only recommendation with a reviewed same-series/same-distribution source build. No custom TLS patch, app behavior change, database, paid-provider grant renewal or secret exposure.

## Verified inputs and scope

- Official Python3.11.18 release archive SHA256 `9120e0a653868f6e3698d36cdd99e5a58903ec9469e448f21d98f7b16d8fa290`.
- Official Docker Python recipe commit `83054588043b3a7ac1ce8324c9242164b632beb9`, path `3.11/slim-bookworm/Dockerfile`, raw SHA256 `479fe3f860c7742df5c081e956368b43beae8a2ad16b6af2152fe66ef8c218fb`.
- Official release GPG fingerprint `A035C8C19219BA821ECEA86B64E628F8D684696D`; preserve the recipe's archive checksum and signature verification.
- Verified Debian Bookworm-slim image index `sha256:7ff6ba31527b9e336162fa061746c366c4b2032f4d2cff2078bea43f78efe3f8`; same distribution/interpreter minor line, no dependency migration.

Sources: [Python release](https://www.python.org/downloads/release/python-31118/), [immutable official Docker recipe](https://github.com/docker-library/python/blob/83054588043b3a7ac1ce8324c9242164b632beb9/3.11/slim-bookworm/Dockerfile). The prebuilt3.11.18 tag still returns not-found, which does not prevent building those authenticated published sources.

## File allocation before source changes

`infra/Dockerfile.backend` vendors the reviewed official runtime recipe before the existing unchanged application layer. Pin Debian/Python inputs, bound download/keyserver work and compile concurrency, preserve optimizations, remove compiler/dev packages and source in the same build step, assert the actual interpreter version. No application source or lock-version changes. `.dockerignore` admits exactly the required recipe license; `infra/licenses/python-docker.MIT.txt` preserves the upstream permission notice in source and the resulting image. `infra/python-runtime-source.json` records immutable provenance/adaptations and later actual runtime checks. `infra/release-object-evidence.json` receives fresh actual no-database Linux acceptance. Existing guides, reports/queue and COMMIT_PLAN own resolution/current state/exact staging. Build progress remains in the main blueprint.

Cold-build timing allocation: the measured authenticated optimized source build exceeds the old15minute backend build allowance. `scripts/release-smoke.mjs` may use a finite45minute image-build ceiling, and `.github/workflows/ci.yml` a75minute overall no-key job ceiling, so the normal cold release command and CI remain runnable. These are build/test bounds, not provider spending or runtime timeout changes. Cached builds retain normal speed; revert unnecessary extra build headroom when returning to an equivalent official prebuilt base.

## Validation and acceptance

1. Authenticate source with the official SHA256 and GPG signature during the build. Never bypass either check on failure. Use only public build inputs, no owner environment/provider credentials.
2. Read actual Python3.11.18/TLS/native-module versions inside the resulting non-root image. Confirm no compiler/source tree/build cache is left, dependencies pass compatibility and the original bounded document parser still works.
3. Run production no-database Linux acceptance including six frontend routes/assets/headers, RAG originals/retrieval, quote/booking/replay/reschedule/refresh and authenticated separate-process Scheduler sync/browser-closed cleanup. PostgreSQL remains stopped; no paid calls.
4. Run meaningful isolated backend security/storage/Scheduler cases under the new container interpreter, with SQL forbidden/network disabled. Preserve old records, profiles, grants and source identities. Inspect final diff read-only, confirm/fix/revalidate material findings, update actual receipts and exact local commit plan; no Git push.
5. Only after validation, remove SEC-038-02's runtime blocker and prepare/upload the verified backend image under existing deployment authority. Distinguish resolved Python runtime from the separate hosted finite-paid-policy/origin/consent conditions. Do not falsely claim public paid deployment or renew grants.

The source-build fallback adds build time, not an always-running service or database. OS build/runtime packages follow the official signed Debian repositories; record final inventory/image digest rather than claiming bit-for-bit reproducibility. Once an equivalent verified official prebuilt image exists, the same validated runtime may return to that simple pinned base in a later scoped change. Current local fake services/keys/data stay untouched.

## Actual results and scoped validation

The optimized source build completed with the exact archive checksum and a good signature from pinned release key A035C8C19219BA821ECEA86B64E628F8D684696D. Python3.11.18, OpenSSL 3.0.22 25 Aug 2026, expat_2.9.0 run as UID10001; compiler/download/GPG tools and `/usr/src/python` are absent. Normal CA/hostname verification remains enabled; native wheel/parser/compression imports and pip compatibility pass. Docker lint flags the public GPG fingerprint name as a secret heuristic and upstream legacy ENV syntax; neither is a credential or functional defect.

Actual production Linux gate passes six frontend HTTP checks and13 encrypted-object/RAG/booking/Scheduler scenarios, including separate-process authenticated sync and browser-closed cleanup; zero PostgreSQL resources or paid calls. Packaged Python security/storage/domain checks pass: 144 selected, 32 SQL cases excluded, network disabled, owner env/state absent and Engine.connect trapped.165 Node checks pass, no skips. Source `d2f4f9314ab9c53fe9eacf8f6c65192b3d6b85845563a06f443735122442bc30` (201 inputs); backend `sha256:d0509343532ff443a5dcf53d62f2a55a72d029699b10c650e2f69094f33ebb03`. Existing application layer is byte-identical from ENV onward, requirements/package locks and provider policy unchanged.

The first additional packaged-test attempt failed collection because bind-mounted Windows `__pycache__` retained Windows source paths; no tests from that attempt counted. The temporary harness now mounts source-only test fixtures, and the final rerun passes. No product source fix was needed.

Read-only scoped validation meets the ticket with no actionable finding: pinned recipe/base/source, checksum+signature fail-closed, same-minor native compatibility, same-layer compiler/source cleanup, upstream MIT inclusion, narrow build context, finite cold-build bounds and fresh actual release receipt. No new runtime/application defect confirmed. AFK quality/security decisions remain provisional personal acceptance.

Verified backend digest `sha256:d0509343532ff443a5dcf53d62f2a55a72d029699b10c650e2f69094f33ebb03` and frontend digest `sha256:d777f237d728263d0dbca9c5ec9a999728a4bcd89a52ac0e1de7d2806d7acec2` are read back from the private europe-west1 registry; anonymous manifests return401/403, no public artifact binding, exact temporary token config removed. No Cloud Run service or Scheduler job exists; paid mode remains disabled. SEC-038-02 is resolved; missing prebuilt-tag publication requires no owner action. SBS-039 still owns fresh finite hosted AI/CRM authority and real provider-origin/visitor consent conditions. No owner local restart/key/data change, database, secret payload read, provider spending or Git push.

The runtime build adds cold-build time, without changing running service costs. Local Git checkpoint uses the exact file-level COMMIT_PLAN allocation and staged/committed private-byte/hash/path/parent/whitespace checks.
