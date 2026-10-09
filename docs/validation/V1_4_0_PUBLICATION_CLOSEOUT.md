# Orchestra v1.4.0 Publication Closeout

## Verdict

```text
V1_4_0_PUBLICATION=COMPLETE_VERIFIED
RELEASE_STATE=PUBLISHED_VERIFIED
CURRENT_PUBLIC_RELEASE=v1.4.0
RELEASE_NAME=Orchestra v1.4.0: Governance & Compliance Registry Cross-Integration
RELEASE_COMMIT=93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50
RELEASE_TREE=1ef60b00e3ac6deba5da57c47d2a0850872d41a9
TAG=v1.4.0
TAG_REF_TYPE=commit
TAG_TARGET=93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50
GITHUB_RELEASE_ID=370658917
GITHUB_RELEASE_IMMUTABLE=true
GITHUB_RELEASE_PUBLISHED_AT=2026-08-14T15:21:25Z
PUBLISH_WORKFLOW_RUN=31814065248
PUBLISH_WORKFLOW_JOB=94811383024
```

The separately authorized Orchestra v1.4.0 publication gate completed after the trusted Registry release, real network-provenance validation, final exact-head matrix, signed canonical readiness merge, and independent post-merge verification were complete.

## Release Identity

GitHub Release id `370658917`, `Orchestra v1.4.0: Governance & Compliance Registry Cross-Integration`, is non-draft, non-prerelease, immutable, and independently verified as the latest public release.

Tag ref `refs/tags/v1.4.0` has object type `commit` and resolves directly to exact release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`. This v1.4.0 tag is therefore a lightweight tag, not an annotated tag; there is no separate tag object. The release commit itself is GitHub-verified with a valid signature and tree `1ef60b00e3ac6deba5da57c47d2a0850872d41a9`.

The fixed release tag remains anchored to that exact source snapshot. Post-publication documentation commits must not move or rewrite it.

## Pre-Publication Assurance Chain

### Compliance Registry integration

- Orchestra Compliance Registry client/governance integration: PR #262, canonical `f32df60cf9963ac678d8467c32d7761021500cde`.
- README Registry rationale: PR #266, canonical `2023525a322e5d17f71d1bcb88ebd9ffec16392b`.
- v1.4 package/governance preparation and README Impact Gate: PR #267, canonical `64b9e6f20aa3510fcfc3eb4c60b0074739f284c2`.
- Registry candidate compatibility: PR #268, canonical `6e1859f2362978228e7119114abe96e35fddaf4c`.
- terminology closeout: PR #269, canonical `8008eeb87f54b12136fab1563e0c97061459cf61`.
- prepublication readiness: PR #270, canonical `b5d0790fc714f53c4561a91b158c13c625768e05`.

### Trusted Registry release

The canonical Registry release `registry-v0.1.0` is published from exact Registry commit `3821bcb55125b4d8864f28b6423650e6e17ac67b`, non-draft, non-prerelease, and immutable. Its reviewed release-manifest SHA-256 is `9922ddcce77dfac0c01cac80fe6669aaffe37636826a56a4b54a8312558ee2d1`; the reviewed bundle SHA-256 is `b64889933d30a8dea27bcbbb95c952e4f053c14a4f345e1e04b27777b5025ec0`.

### Real Orchestra network provenance

Workflow run `31811353512`, job `94802485762`, exercised the canonical Orchestra Registry client and passed:

```text
IMMUTABLE_RELEASE_BOUNDARY=PASS
NETWORK_SYNC=PASS
FRESHNESS=PASS
QUERY=PASS
PIN=PASS
UPDATE_CHECK=PASS
IDEMPOTENT_RESYNC=PASS
NETWORK_PROVENANCE_VALIDATION=PASS
```

### Final Orchestra release readiness

PR #271 reviewed exact head `2a677c8ea33292d846b09bbf2b95897a925661d3`, 0 behind, with the bounded readiness scope and no blocking review threads. The exact-head matrix passed Governance/README, behavior validate, 568 runtime tests at 94.33% coverage, CodeQL actions/Python, and native Ubuntu/macOS/Windows.

PR #271 then Squash-merged with the expected-head guard as signed canonical release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`. Canonical post-merge validation passed Governance, behavior validate, 568 runtime tests at 94.31% coverage, CodeQL actions/Python, and native Ubuntu/macOS/Windows.

## Publication Execution

The connected GitHub application did not expose a direct release-creation mutation. After explicit user authorization for the Orchestra v1.4.0 public release, publication used a one-shot GitHub Actions publisher on isolated branch `ops/publish-orchestra-v1-4-0-20260814`.

Publisher commit: `563fbcdfd32b48ac9d27b0b21eb309bda73f5ddc`.

Workflow run `31814065248`, job `94811383024`, succeeded. Before mutation it required canonical `main` to equal exact release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`, required `v1.4.0` GitHub Release to be absent, and required `refs/tags/v1.4.0` to be absent.

It then created the release with exact `target_commitish` equal to the release commit and verified the resulting release as non-draft, non-prerelease, immutable, latest, and exact-targeted.

Independent GitHub reads outside the publisher confirmed:

```text
RELEASE_ID=370658917
RELEASE_TAG=v1.4.0
RELEASE_TARGET_COMMITISH=93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50
RELEASE_DRAFT=false
RELEASE_PRERELEASE=false
RELEASE_IMMUTABLE=true
TAG_REF_TYPE=commit
TAG_REF_SHA=93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50
LATEST_PUBLIC_RELEASE=v1.4.0
```

## Protected Actions Not Performed

Publication authority was limited to the `v1.4.0` tag and GitHub Release plus ordinary documentation/continuity closeout.

The following were not performed:

- marketplace/package publication;
- installed-integration refresh;
- deployment or production mutation;
- policy activation;
- destructive cleanup;
- branch deletion;
- force push; or
- history rewrite.

The publication and closeout do not graduate scaffold-only hosts or expand specialist, routing, runtime, or legal authority.

## Post-Publication Rule

The `v1.4.0` tag remains fixed at release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`. Later documentation or development commits must not move or rewrite the release tag.
