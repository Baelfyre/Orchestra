# Orchestra v1.4.0 Final Release-Readiness Evidence

## Verdict

`READY_FOR_SEPARATE_ORCHESTRA_V1_4_0_PUBLICATION_GATE`

This record captures the trusted Registry publication and real network-provenance evidence required before Orchestra v1.4.0 may be presented for its separate public release authorization. It is evidence of readiness, not release authority.

## Orchestra source baseline tested

- Repository: `Baelfyre/Orchestra`
- Canonical branch: `main`
- Exact runtime/source baseline exercised by network validation: `b5d0790fc714f53c4561a91b158c13c625768e05`
- Package version: `1.4.0`
- Current public release: `v1.3.0`
- Target public release: `v1.4.0`

The dedicated network-provenance workflow asserted that its parent was exactly `b5d0790fc714f53c4561a91b158c13c625768e05` and that `scripts/compliance_registry.py` was unchanged from that canonical parent. The validation therefore exercised the canonical Orchestra Registry client, not a modified test implementation.

## Trusted Registry release boundary

Repository: `Baelfyre/Orchestra-Compliance-Registry`

Canonical Registry readiness commit: `3821bcb55125b4d8864f28b6423650e6e17ac67b`

Published release:

- release id: `370610859`
- tag: `registry-v0.1.0`
- target commit: `3821bcb55125b4d8864f28b6423650e6e17ac67b`
- draft: `false`
- prerelease: `false`
- immutable: `true`
- published at: `2026-08-14T14:44:51Z`
- Registry version: `0.1.0`
- release sequence: `1`

The tag ref `refs/tags/registry-v0.1.0` resolves exactly to the canonical Registry readiness commit.

## Published asset integrity

The immutable release exposes exactly the reviewed publication assets:

1. `orchestra-compliance-registry.zip`
   - SHA-256: `b64889933d30a8dea27bcbbb95c952e4f053c14a4f345e1e04b27777b5025ec0`
2. `orchestra-compliance-registry.zip.sha256`
   - asset SHA-256: `7aa1030a357d1514bb333b064b77e3fc68e93f85d8885b33bf6bc85a89d89ac2`
3. `release-manifest.json`
   - SHA-256: `9922ddcce77dfac0c01cac80fe6669aaffe37636826a56a4b54a8312558ee2d1`
4. `release-manifest.sha256`
   - asset SHA-256: `938696ead67476f39eecaf8cef332e30816b6089b64dbf4a8ff3f22d9f663a1e`

The network-provenance run independently downloaded the real published ZIP and reproduced the reviewed bundle SHA-256.

## Real Orchestra network-provenance validation

Workflow run: `31811353512`

Job: `94802485762`

Conclusion: `SUCCESS`

The live validation proved all of the following against the immutable release boundary:

- `IMMUTABLE_RELEASE_BOUNDARY=PASS`
- `NETWORK_SYNC=PASS`
- `FRESHNESS=PASS`
- `QUERY=PASS`
- `PIN=PASS`
- `UPDATE_CHECK=PASS`
- `IDEMPOTENT_RESYNC=PASS`
- `NETWORK_PROVENANCE_VALIDATION=PASS`

Observed active Registry identity after network sync:

- canonical repository: `Baelfyre/Orchestra-Compliance-Registry`
- Registry version: `0.1.0`
- release sequence: `1`
- release tag: `registry-v0.1.0`
- release-manifest SHA-256: `9922ddcce77dfac0c01cac80fe6669aaffe37636826a56a4b54a8312558ee2d1`

## Freshness, query, and project pinning evidence

The live active cache verified:

- Registry status: `VERIFIED`
- freshness state: `CURRENT`
- tracked source count: `4`
- stale source ids: none
- attention source ids: none
- all four bounded source records: `VERIFIED_CURRENT`

The source query for `PH-DPA-RA10173` returned the exact requested source and six source-linked obligations.

Project pinning produced a lock for jurisdiction `PH` with the exact release tag and manifest identity. No providers were selected by that bounded pin test.

`update-check` reported the active and latest release as `registry-v0.1.0` and `update_available: false`. A second network synchronization resolved to the same release sequence, tag, and manifest identity, demonstrating idempotent re-sync against the current trusted release.

## Final Orchestra exact-head gate

This readiness record must be merged only from a fresh branch based on canonical Orchestra `main`, with the repository's complete required validation matrix green at the exact PR head and an independent post-merge canonical verification.

Required final matrix:

- README Impact Gate / Governance Check
- behavior `validate`
- runtime tests and coverage
- CodeQL Analyze (actions)
- CodeQL Analyze (python)
- native Ubuntu
- native macOS
- native Windows

Passing that matrix proves the release candidate is internally consistent at the reviewed revision. It does not create public release authority.

## Historical evidence preserved

`docs/validation/V1_4_0_PREPUBLICATION_READINESS_EVIDENCE.md` remains the historical record of the state before the trusted Registry release existed. It is intentionally not rewritten to pretend that later provenance evidence existed earlier.

## Remaining protected transition

The trusted Registry publication gate is satisfied. The Registry release is published and immutable, and real Orchestra network provenance is verified.

The remaining public transition is the separate Orchestra `v1.4.0` publication gate. Until explicitly authorized, do not create or publish the Orchestra `v1.4.0` tag/GitHub Release or perform marketplace/package publication, installed-integration refresh, deployment/production mutation, policy activation, destructive cleanup, branch deletion, force push, or history rewrite.

`TRUSTED_REGISTRY_RELEASE_PUBLISHED_IMMUTABLE_VERIFIED = TRUE`

`REAL_NETWORK_PROVENANCE_VALIDATED = TRUE`

`PACKAGE_VERSION_1_4_0 != PUBLIC_RELEASE_V1_4_0`

`VALIDATION_SUCCESS != RELEASE_AUTHORITY`

## State

`V1_4_IMPLEMENTATION_COMPLETE`

`TRUSTED_REGISTRY_PUBLICATION_COMPLETE`

`NETWORK_PROVENANCE_COMPLETE`

`FINAL_EXACT_HEAD_MATRIX_REQUIRED`

`ORCHESTRA_V1_4_0_PUBLICATION_GATE_PENDING`
