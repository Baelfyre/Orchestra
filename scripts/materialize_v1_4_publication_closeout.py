from pathlib import Path
import subprocess

EXPECTED_MAIN_SHA = "93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50"
BRANCH = "docs/v1-4-publication-closeout-20260814-v2"
WORKFLOW = ".github/workflows/materialize-v1-4-publication-closeout-v2.yml"
SCRIPT = "scripts/materialize_v1_4_publication_closeout.py"


def sh(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{path}: expected exactly one replacement target, found {n}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before_once(path: str, marker: str, block: str) -> None:
    replace_once(path, marker, block + marker)


# Fail closed on baseline movement.
parent = sh("git", "rev-parse", "HEAD^")
if parent != EXPECTED_MAIN_SHA:
    raise SystemExit(f"unexpected workflow-parent baseline: {parent}")
remote_main = sh("bash", "-lc", "git ls-remote origin refs/heads/main | awk '{print $1}'")
if remote_main != EXPECTED_MAIN_SHA:
    raise SystemExit(f"canonical main moved: {remote_main}")

# README current-facing release state.
replace_once(
    "README.md",
    "The repository/package version is prepared at `1.4.0` for the governance upgrade. **The current public GitHub release remains `v1.3.0` until a separate release/tag publication gate is explicitly authorized and completed.**",
    "The repository/package version and current public GitHub release are both `v1.4.0`. The immutable, non-draft, non-prerelease release `Orchestra v1.4.0: Governance & Compliance Registry Cross-Integration` is published from exact signed canonical commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`; tag `v1.4.0` resolves directly to that commit.",
)
replace_once(
    "README.md",
    "The Registry foundation, source/freshness pilot, deterministic packaging, and v0.1.0 release-readiness stack are canonical in `Baelfyre/Orchestra-Compliance-Registry`. The trusted `registry-v0.1.0` GitHub Release is now published as non-draft, non-prerelease, and immutable at Registry commit `3821bcb55125b4d8864f28b6423650e6e17ac67b`. Orchestra has completed real network-provenance validation from canonical source baseline `b5d0790fc714f53c4561a91b158c13c625768e05`, confirming the exact release identity, manifest and bundle hashes, `CURRENT` freshness, source query, project pinning, update-check behavior, and idempotent re-sync. The Orchestra package remains `1.4.0` while the public GitHub release remains `v1.3.0` until the separate `v1.4.0` publication gate is explicitly authorized and completed.",
    "The Registry foundation, source/freshness pilot, deterministic packaging, and v0.1.0 release-readiness stack are canonical in `Baelfyre/Orchestra-Compliance-Registry`. The trusted `registry-v0.1.0` GitHub Release is published as non-draft, non-prerelease, and immutable at Registry commit `3821bcb55125b4d8864f28b6423650e6e17ac67b`. Orchestra completed real network-provenance validation from canonical source baseline `b5d0790fc714f53c4561a91b158c13c625768e05`, confirming the exact release identity, manifest and bundle hashes, `CURRENT` freshness, source query, project pinning, update-check behavior, and idempotent re-sync. The Orchestra package and current public GitHub release are now both `1.4.0`; publication is `PUBLISHED_VERIFIED` and does not imply marketplace publication or installed-integration refresh.",
)
replace_once(
    "README.md",
    "See the [v1.4.0 governance upgrade release candidate](docs/releases/v1.4.0-governance-compliance-registry-release-candidate.md), the preserved [prepublication readiness evidence](docs/validation/V1_4_0_PREPUBLICATION_READINESS_EVIDENCE.md), and the [final release-readiness evidence](docs/validation/V1_4_0_RELEASE_READINESS_EVIDENCE.md) for the trusted Registry boundary, real network-provenance result, and remaining Orchestra publication gate.",
    "See the [v1.4.0 governance upgrade release candidate](docs/releases/v1.4.0-governance-compliance-registry-release-candidate.md), the preserved [prepublication readiness evidence](docs/validation/V1_4_0_PREPUBLICATION_READINESS_EVIDENCE.md), the [final release-readiness evidence](docs/validation/V1_4_0_RELEASE_READINESS_EVIDENCE.md), and the [v1.4.0 publication closeout](docs/validation/V1_4_0_PUBLICATION_CLOSEOUT.md) for the complete trusted Registry, provenance, release-readiness, and publication evidence chain.",
)

# CHANGELOG: convert the release-preparation block into a published block without rewriting history.
replace_once(
    "CHANGELOG.md",
    "## v1.4.0 Governance and Compliance Registry Cross-Integration - Release Preparation - Pending",
    "## v1.4.0 Governance and Compliance Registry Cross-Integration - Published 2026-08-14",
)
replace_once(
    "CHANGELOG.md",
    "- Added `docs/validation/V1_4_0_RELEASE_READINESS_EVIDENCE.md`; Orchestra `v1.4.0` public release/tag publication, marketplace publication, installed-integration refresh, deployment, policy activation, destructive cleanup, branch deletion, force push, and history rewrite remain separately gated and are not performed by this readiness closeout.",
    "- Added `docs/validation/V1_4_0_RELEASE_READINESS_EVIDENCE.md`; at that readiness checkpoint, Orchestra `v1.4.0` public release/tag publication remained a separate protected transition.\n- Published `Orchestra v1.4.0: Governance & Compliance Registry Cross-Integration` as GitHub Release id `370658917` from lightweight tag `v1.4.0`, which resolves directly to exact signed canonical release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`; independently verified non-draft, non-prerelease, immutable, and latest.\n- Added `docs/validation/V1_4_0_PUBLICATION_CLOSEOUT.md` and reconciled current-facing release, setup, roadmap, project-state, and handoff documentation without moving the fixed release tag or performing marketplace publication, installed-integration refresh, deployment, policy activation, destructive cleanup, branch deletion, force push, or history rewrite.",
)

# PROJECT_CONTEXT current state.
replace_once(
    "PROJECT_CONTEXT.md",
    "v1.4.0 - Governance and Compliance Registry Cross-Integration package/version preparation (`PREPARED_NOT_RELEASED`). Repository package surfaces are aligned to `1.4.0` for the governance upgrade while the current public release remains `v1.3.0`. The candidate cross-integrates verified Compliance Registry provenance, integrity, freshness, and project-pinning evidence across Governor, Steward, Arbiter, and Conductor/The Tuner coordination boundaries, and adds a fail-closed README Impact Gate for significant Orchestra changes. The separately governed Registry foundation remains held pending authorized `main` protection and fresh exact-head validation; no `v1.4.0` tag or GitHub Release publication is authorized by package preparation.",
    "v1.4.0 - Governance and Compliance Registry Cross-Integration (`PUBLISHED_VERIFIED`). Repository package surfaces and the current public GitHub Release are aligned to `1.4.0`. The immutable, non-draft, non-prerelease release `Orchestra v1.4.0: Governance & Compliance Registry Cross-Integration` is published from lightweight tag `v1.4.0`, which resolves directly to exact signed canonical release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`. Trusted Registry publication and real Orchestra network provenance are complete. No marketplace publication, installed-integration refresh, deployment/production mutation, or policy activation was performed.",
)
replace_once(
    "PROJECT_CONTEXT.md",
    "- Repository package metadata is prepared at `1.4.0`; public release `v1.3.0` remains independently verified until a separately authorized and validated `v1.4.0` publication transition. Later `main` commits do not move the immutable `v1.3.0` tag.",
    "- Repository package metadata and the current public GitHub Release are `1.4.0`; lightweight tag `v1.4.0` resolves directly to signed release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`. Later `main` commits must not move that fixed release tag.",
)
replace_once(
    "PROJECT_CONTEXT.md",
    "- The Compliance Registry foundation is validated but held until its repository `main` protection/ruleset is separately authorized and independently verified; trusted Registry publication is a separate protected action.",
    "- The Compliance Registry foundation, source/freshness pilot, deterministic packaging, immutable `registry-v0.1.0` publication, and Orchestra real network-provenance validation are complete; future Registry releases remain separately governed transitions.",
)

# PROJECT_STATE.
replace_once(
    "PROJECT_STATE.md",
    "- **Current Public Release:** `v1.3.0`\n- **Release Status:** `PUBLISHED_VERIFIED` on August 12, 2026 UTC / August 13, 2026 Asia/Manila\n- **Target Release:** `v1.3.0`\n- **Release-Candidate Metadata:** `1.3.0`\n- **v1.2.0 Release State:** `PUBLISHED_VERIFIED`\n- **v1.3.0 Release State:** `PUBLISHED_VERIFIED`\n- **v1.3.0 Release Commit:** `3c6155c111981632649a3c3207fac8ac1edcea74`\n- **v1.3.0 Release Tree:** `5ae72f6ab9ddf5284afdc3d8675f67fc23c24281`\n- **v1.3.0 Annotated Tag Object:** `c66afec49990036d9deb2f07e3363cd664e2dcb1` (`UNSIGNED`, exact target verified)\n- **v1.3.0 GitHub Release:** `PUBLISHED_VERIFIED`, immutable, non-draft, non-prerelease\n- **Policy Activation State:** `NOT_PERFORMED`",
    "- **Current Public Release:** `v1.4.0`\n- **Release Status:** `PUBLISHED_VERIFIED` on August 14, 2026 UTC / August 14, 2026 Asia/Manila\n- **Target Release:** `v1.4.0`\n- **Release-Candidate Metadata:** `1.4.0`\n- **v1.2.0 Release State:** `PUBLISHED_VERIFIED`\n- **v1.3.0 Release State:** `PUBLISHED_VERIFIED`\n- **v1.3.0 Release Commit:** `3c6155c111981632649a3c3207fac8ac1edcea74`\n- **v1.3.0 Release Tree:** `5ae72f6ab9ddf5284afdc3d8675f67fc23c24281`\n- **v1.3.0 Annotated Tag Object:** `c66afec49990036d9deb2f07e3363cd664e2dcb1` (`UNSIGNED`, exact target verified)\n- **v1.3.0 GitHub Release:** `PUBLISHED_VERIFIED`, immutable, non-draft, non-prerelease\n- **v1.4.0 Release State:** `PUBLISHED_VERIFIED`\n- **v1.4.0 Release Commit:** `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`\n- **v1.4.0 Release Tree:** `1ef60b00e3ac6deba5da57c47d2a0850872d41a9`\n- **v1.4.0 Tag Ref:** lightweight `commit` ref, exact target verified\n- **v1.4.0 GitHub Release:** id `370658917`, immutable, non-draft, non-prerelease, latest\n- **Policy Activation State:** `NOT_PERFORMED`",
)
insert_before_once(
    "PROJECT_STATE.md",
    "## v1.3.0 Specialist Intelligence Publication\n",
    """## v1.4.0 Governance and Compliance Registry Cross-Integration Publication

The v1.4.0 governance upgrade is `PUBLISHED_VERIFIED`. The public GitHub Release `Orchestra v1.4.0: Governance & Compliance Registry Cross-Integration` was published under separate explicit authority as release id `370658917` at `2026-08-14T15:21:25Z`. Lightweight tag `v1.4.0` resolves directly to exact signed canonical release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50` with tree `1ef60b00e3ac6deba5da57c47d2a0850872d41a9`. The release is non-draft, non-prerelease, immutable, and independently verified as latest.

The trusted Registry dependency is also complete: immutable `registry-v0.1.0` targets Registry canonical `3821bcb55125b4d8864f28b6423650e6e17ac67b`, and Orchestra network-provenance run `31811353512` / job `94802485762` passed exact release identity, real bundle integrity, `CURRENT` freshness, PH source query, project pinning, update-check, and idempotent re-sync. Final Orchestra PR #271 then passed the full exact-head matrix and merged as the signed release commit above; its canonical post-merge matrix passed Governance, validate, 568 runtime tests at 94.31% coverage, CodeQL actions/Python, and native Ubuntu/macOS/Windows.

```text
CURRENT_PUBLIC_RELEASE=v1.4.0
V1_4_0_RELEASE_STATE=PUBLISHED_VERIFIED
V1_4_0_TAG_REF_TYPE=commit
V1_4_0_TAG_TARGET=93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50
V1_4_0_RELEASE_COMMIT_SIGNATURE=VERIFIED_VALID
V1_4_0_GITHUB_RELEASE_ID=370658917
V1_4_0_GITHUB_RELEASE_IMMUTABLE=true
V1_4_0_PUBLICATION=COMPLETE_VERIFIED
```

No marketplace publication, installed-integration refresh, deployment/production mutation, policy activation, destructive cleanup, branch deletion, force push, or history rewrite was performed.

See `docs/validation/V1_4_0_PUBLICATION_CLOSEOUT.md`.

""",
)
replace_once(
    "PROJECT_STATE.md",
    "- **v1.3.0 Publication State:** Annotated tag `v1.3.0` targets exact signed release commit `3c6155c111981632649a3c3207fac8ac1edcea74`; the immutable, non-draft, non-prerelease GitHub Release `Orchestra v1.3.0: Specialist Intelligence` is `PUBLISHED_VERIFIED`. No deployment, marketplace publication, installed-integration refresh, or policy activation was performed.",
    "- **v1.3.0 Publication State:** Annotated tag `v1.3.0` targets exact signed release commit `3c6155c111981632649a3c3207fac8ac1edcea74`; the immutable, non-draft, non-prerelease GitHub Release `Orchestra v1.3.0: Specialist Intelligence` is `PUBLISHED_VERIFIED`. No deployment, marketplace publication, installed-integration refresh, or policy activation was performed.\n- **v1.4.0 Publication State:** Lightweight tag `v1.4.0` resolves directly to exact signed release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`; GitHub Release id `370658917`, `Orchestra v1.4.0: Governance & Compliance Registry Cross-Integration`, is immutable, non-draft, non-prerelease, latest, and `PUBLISHED_VERIFIED`. No marketplace publication, installed-integration refresh, deployment, or policy activation was performed.",
)

# SESSION_HANDOFF.
replace_once(
    "SESSION_HANDOFF.md",
    "- **Current Public Release:** `v1.3.0`\n- **Release-Candidate Metadata:** `v1.3.0`\n- **Target Release:** `v1.3.0`\n- **v1.2.0 Release State:** `PUBLISHED_VERIFIED`\n- **v1.3.0 Release State:** `PUBLISHED_VERIFIED`\n- **v1.3.0 Release Commit:** `3c6155c111981632649a3c3207fac8ac1edcea74`\n- **v1.3.0 Release Tree:** `5ae72f6ab9ddf5284afdc3d8675f67fc23c24281`\n- **v1.3.0 Tag Object:** `c66afec49990036d9deb2f07e3363cd664e2dcb1` (`UNSIGNED`, exact target verified)\n- **Policy Activation:** `NOT_PERFORMED`",
    "- **Current Public Release:** `v1.4.0`\n- **Release-Candidate Metadata:** `v1.4.0`\n- **Target Release:** `v1.4.0`\n- **v1.2.0 Release State:** `PUBLISHED_VERIFIED`\n- **v1.3.0 Release State:** `PUBLISHED_VERIFIED`\n- **v1.3.0 Release Commit:** `3c6155c111981632649a3c3207fac8ac1edcea74`\n- **v1.3.0 Release Tree:** `5ae72f6ab9ddf5284afdc3d8675f67fc23c24281`\n- **v1.3.0 Tag Object:** `c66afec49990036d9deb2f07e3363cd664e2dcb1` (`UNSIGNED`, exact target verified)\n- **v1.4.0 Release State:** `PUBLISHED_VERIFIED`\n- **v1.4.0 Release Commit:** `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`\n- **v1.4.0 Release Tree:** `1ef60b00e3ac6deba5da57c47d2a0850872d41a9`\n- **v1.4.0 Tag Ref:** lightweight `commit` ref targeting the exact release commit\n- **v1.4.0 GitHub Release:** id `370658917`, immutable, non-draft, non-prerelease, latest\n- **Policy Activation:** `NOT_PERFORMED`",
)
insert_before_once(
    "SESSION_HANDOFF.md",
    "## v1.3.0 Specialist Intelligence Continuity\n",
    """## v1.4.0 Governance and Compliance Registry Publication Continuity

Orchestra `v1.4.0` is now `PUBLISHED_VERIFIED`. Release id `370658917`, `Orchestra v1.4.0: Governance & Compliance Registry Cross-Integration`, was published at `2026-08-14T15:21:25Z`. Lightweight tag `v1.4.0` resolves directly to exact signed canonical release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`; the release is non-draft, non-prerelease, immutable, and latest.

Publication used the separately authorized guarded workflow run `31814065248`, job `94811383024`. That publisher first required canonical `main` to equal the exact release commit and required both the tag and release to be absent, then independently verified immutability, latest-release state, and the exact tag target. External reads after the workflow confirmed the same state.

The trusted Registry and network-provenance dependency chain is complete. `registry-v0.1.0` is immutable at Registry canonical `3821bcb55125b4d8864f28b6423650e6e17ac67b`; Orchestra run `31811353512` / job `94802485762` passed the real network path. Final readiness PR #271 merged as the release commit and passed the complete exact-head and post-merge matrix.

No marketplace publication, installed-integration refresh, deployment/production mutation, policy activation, destructive cleanup, branch deletion, force push, or history rewrite was performed.

Evidence: `docs/validation/V1_4_0_PUBLICATION_CLOSEOUT.md`.

""",
)
replace_once(
    "SESSION_HANDOFF.md",
    "V1.3-CLOSE   post-publication repository and KB continuity - current closeout",
    "V1.3-CLOSE   post-publication repository and KB continuity - complete\nV1.4-PREP    governance and Compliance Registry cross-integration - merged verified\nV1.4-REGISTRY trusted immutable registry-v0.1.0 dependency - complete verified\nV1.4-PROVENANCE real Orchestra network provenance - complete verified\nV1.4-READY   exact-head and canonical release readiness - complete verified\nV1.4-PUBLISH lightweight tag and immutable GitHub Release - complete verified\nV1.4-CLOSE   post-publication repository and Padayon continuity - current closeout",
)

# Roadmap.
roadmap_section = """## v1.4.0 Governance and Compliance Registry Cross-Integration - Published Verified

- [x] Integrate the offline-first Compliance Registry client and governance ownership boundaries.
- [x] Explain Compliance Registry cross-integration in the public README.
- [x] Normalize all 11 live package/version surfaces to `1.4.0` and enforce deterministic parity.
- [x] Add and exercise the fail-closed README Impact Gate.
- [x] Validate Registry `0.1.0` candidate compatibility, freshness propagation, source query, and project pinning.
- [x] Activate and independently verify the Registry `compliance-ruleset`, then merge foundation, source/freshness pilot, deterministic packaging, and publication-readiness phases.
- [x] Publish immutable trusted Registry release `registry-v0.1.0` at exact Registry canonical `3821bcb55125b4d8864f28b6423650e6e17ac67b`.
- [x] Run real Orchestra network provenance against the immutable Registry release and verify exact identity, bundle/manifest trust, `CURRENT` freshness, PH source query, pinning, update-check, and idempotent re-sync.
- [x] Finalize Orchestra exact-head release readiness through PR #271 and signed canonical `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50` with the complete validation matrix green.
- [x] Under separate explicit publication authority, publish lightweight tag `v1.4.0` resolving directly to the exact release commit and GitHub Release id `370658917`, then independently verify non-draft, non-prerelease, immutable, and latest state.
- [x] Confirm publication performed no marketplace publication, installed-integration refresh, deployment/production mutation, policy activation, destructive cleanup, branch deletion, force push, or history rewrite.

Publication closeout evidence is recorded in `docs/validation/V1_4_0_PUBLICATION_CLOSEOUT.md`.

"""
insert_before_once("docs/project/ROADMAP.md", "### Current `Protect main` Development Baseline\n", roadmap_section)
replace_once(
    "docs/project/ROADMAP.md",
    "- [x] Publish `v1.3.0` after the SK1-SK10 Specialist Intelligence campaign, release preparation, revision-bound readiness, README alignment, and separate publication authority completed.",
    "- [x] Publish `v1.3.0` after the SK1-SK10 Specialist Intelligence campaign, release preparation, revision-bound readiness, README alignment, and separate publication authority completed.\n- [x] Publish `v1.4.0` after Compliance Registry cross-integration, trusted immutable Registry publication, real network-provenance validation, final exact-head readiness, and separate Orchestra publication authority completed.",
)

# Installation and compatibility.
replace_once(
    "docs/setup/INSTALLATION.md",
    "The current public GitHub Release is `v1.3.0: Specialist Intelligence`, published from annotated tag `v1.3.0` at exact release commit `3c6155c111981632649a3c3207fac8ac1edcea74`. Repository manifests and the published release are normalized to version `1.3.0`. The GitHub Release is non-draft, non-prerelease, and immutable.\n\nThe annotated tag object targets the GitHub-verified signed release commit above; the tag object itself is unsigned and is not represented as a signed tag.\n\nThe latest GitHub Release remains the publication source of truth. Installing directly from `main` may include post-release documentation or later unreleased work, so use tag `v1.3.0` when exact released content is required.",
    "The current public GitHub Release is `v1.4.0: Governance & Compliance Registry Cross-Integration`, published from lightweight tag `v1.4.0` at exact signed release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`. Repository manifests and the published release are normalized to version `1.4.0`. The GitHub Release is non-draft, non-prerelease, immutable, and independently verified as latest.\n\nUnlike the historical annotated `v1.3.0` tag, `v1.4.0` is a lightweight tag ref whose object type is `commit` and whose SHA is the exact GitHub-verified signed release commit above; there is no separate tag object to represent as signed or unsigned.\n\nThe latest GitHub Release remains the publication source of truth. Installing directly from `main` may include post-release documentation or later unreleased work, so use tag `v1.4.0` when exact released content is required.",
)
replace_once(
    "docs/setup/INSTALLATION.md",
    "Accepted R7 live installed-host continuity evidence is verified and reconciled locally in `docs/validation/R7_LIVE_INSTALLED_HOST_VALIDATION_EVIDENCE.md`; repository validation does not replace that evidence. The v1.3.0 GitHub publication is complete, but the repository simulation fixture remains pending/empty by design and is not live evidence.",
    "Accepted R7 live installed-host continuity evidence is verified and reconciled locally in `docs/validation/R7_LIVE_INSTALLED_HOST_VALIDATION_EVIDENCE.md`; repository validation does not replace that evidence. The v1.4.0 GitHub publication is complete, but the repository simulation fixture remains pending/empty by design and is not live evidence.",
)
replace_once(
    "docs/setup/COMPATIBILITY.md",
    "The current public GitHub Release is Orchestra `v1.3.0: Specialist Intelligence`, published from annotated tag `v1.3.0` at exact release commit `3c6155c111981632649a3c3207fac8ac1edcea74`. The release is non-draft, non-prerelease, and immutable. Publication did not graduate scaffold-only hosts or perform marketplace publication.\n\nThe annotated `v1.3.0` tag object is unsigned and targets the GitHub-verified signed release commit above. This is consistent with the prior v1.2.0 annotated-tag pattern and is not represented as a signed tag.",
    "The current public GitHub Release is Orchestra `v1.4.0: Governance & Compliance Registry Cross-Integration`, published from lightweight tag `v1.4.0` at exact signed release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`. The release is non-draft, non-prerelease, immutable, and latest. Publication did not graduate scaffold-only hosts or perform marketplace publication.\n\nThe `v1.4.0` tag is a lightweight `commit` ref resolving directly to the GitHub-verified signed release commit above; there is no separate tag object. Historical v1.2.0/v1.3.0 annotated-tag evidence remains unchanged.",
)

# Immutable publication-closeout evidence.
Path("docs/validation/V1_4_0_PUBLICATION_CLOSEOUT.md").write_text(
    """# Orchestra v1.4.0 Publication Closeout

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
""",
    encoding="utf-8",
)

# Remove only the transient scaffolding introduced on this isolated branch.
Path(WORKFLOW).unlink()
Path(SCRIPT).unlink()

# Net scope must be the nine current-facing/evidence paths only.
subprocess.check_call(["git", "diff", "--check"])
expected = sorted([
    "CHANGELOG.md",
    "PROJECT_CONTEXT.md",
    "PROJECT_STATE.md",
    "README.md",
    "SESSION_HANDOFF.md",
    "docs/project/ROADMAP.md",
    "docs/setup/COMPATIBILITY.md",
    "docs/setup/INSTALLATION.md",
    "docs/validation/V1_4_0_PUBLICATION_CLOSEOUT.md",
])
actual = sorted(sh("git", "diff", "--name-only", EXPECTED_MAIN_SHA).splitlines())
if actual != expected:
    raise SystemExit(f"scope mismatch\nexpected={expected}\nactual={actual}")

subprocess.check_call(["git", "config", "user.name", "JEO"])
subprocess.check_call(["git", "config", "user.email", "192281269+Baelfyre@users.noreply.github.com"])
subprocess.check_call(["git", "add", "-A"])
subprocess.check_call(["git", "commit", "-m", "docs: record v1.4.0 publication closeout"])
subprocess.check_call(["git", "push", "origin", f"HEAD:{BRANCH}"])
