# Orchestra v1.3.0 Release Readiness Evidence

## Verdict

```text
V1_3_0_RELEASE_PREPARATION=MERGED_VERIFIED
V1_3_0_RELEASE_STATE=PUBLISHED_VERIFIED
CURRENT_PUBLIC_RELEASE=v1.3.0
TARGET_VERSION=1.3.0
TARGET_TAG=v1.3.0
V1_3_0_PUBLICATION=COMPLETE_VERIFIED
```

This record preserves the revision-bound v1.3.0 preparation and validation chain and records the independently verified publication outcome. Publication authority was granted separately from preparation and validation.

## Canonical Preparation Identity

- Pre-preparation Orchestra `main`: `650b8bff00d7808bc13fd82a51c7bf0cffa7616e`
- Reviewed signed preparation head: `f63daf49add4887d7fbd1b581959ebf8654150db`
- Reviewed tree: `0fdf39920a8c48a779971c8c97690985bb875d42`
- Canonical preparation PR: #255
- Canonical Squash: `32257723d6ca72847e4581d8b927c7b14c77039e`
- Canonical parent: `650b8bff00d7808bc13fd82a51c7bf0cffa7616e`
- Canonical tree: `0fdf39920a8c48a779971c8c97690985bb875d42`
- Reviewed/canonical tree equivalence: `EXACT`
- Canonical GitHub signature: `VERIFIED_VALID`
- Expected-head merge guard: `USED`
- Branch deletion: `NOT_PERFORMED`
- Force push/history rewrite: `NOT_PERFORMED`

The signed reviewed head and canonical Squash have the same tree. Squash rewrote commit identity as expected, not reviewed content.

## Superseded Candidate Evidence

The first 13-file signed candidate was materialized as `5238abe2c41782e8fe411e178a75b3ec8d7e323b` and opened as PR #253.

PR #253 failed closed at Stage 1 Strict Governance because significant package/test changes had no matching `CHANGELOG.md` update:

```text
Significant changes were detected without a matching CHANGELOG.md update.
Significant paths: plugin.json, tests/runtime/test_release_version_surfaces.py
```

PR #253 was closed unmerged. Its validation was invalidated and not reused.

The corrected work tree added a focused v1.3.0 preparation changelog entry and restored an accidentally touched historical changelog phrase before signed rematerialization. The canonical compare shows the release-preparation changelog change as additive only.

## Exact PR #255 Scope

The canonical preparation changed exactly 14 files:

1. `.claude-plugin/marketplace.json`
2. `.claude-plugin/plugin.json`
3. `.codex-plugin/plugin.json`
4. `CHANGELOG.md`
5. `adapters/cursor/package.json`
6. `adapters/jetbrains/package.json`
7. `adapters/jetbrains/plugin.xml`
8. `adapters/neovim/package.json`
9. `adapters/vscode/package.json`
10. `adapters/windsurf/package.json`
11. `adapters/zed/package.json`
12. `docs/releases/v1.3.0-specialist-intelligence-release-candidate.md`
13. `plugin.json`
14. `tests/runtime/test_release_version_surfaces.py`

The package/version change was additive release preparation. It did not graduate a scaffold-only host, change runtime authority, activate policy, deploy software, or publish an integration.

## Package Version Surface

The deterministic runtime regression validates these 11 live package/version surfaces as `1.3.0`:

- `plugin.json`
- `.codex-plugin/plugin.json`
- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json` plugin entry
- `adapters/cursor/package.json`
- `adapters/jetbrains/package.json`
- `adapters/jetbrains/plugin.xml`
- `adapters/neovim/package.json`
- `adapters/vscode/package.json`
- `adapters/windsurf/package.json`
- `adapters/zed/package.json`

The test `tests/runtime/test_release_version_surfaces.py` passed on the exact reviewed head.

## Exact-Head GitHub Checks

Exact reviewed preparation head: `f63daf49add4887d7fbd1b581959ebf8654150db`

All nine observed checks completed successfully:

| Check | Result |
|---|---|
| `governance-check` | PASS |
| `validate` | PASS |
| `runtime-tests` | PASS |
| `native-windows-latest` | PASS |
| `native-ubuntu-latest` | PASS |
| `native-macos-latest` | PASS |
| `Analyze (actions)` | PASS |
| `Analyze (python)` | PASS |
| `CodeQL` | PASS |

CodeQL reported no new alerts in code changed by PR #255. PR #255 had zero unresolved review threads and was mergeable on the exact reviewed head immediately before the expected-head Squash merge.

## Runtime and Repository Validation

The exact reviewed release-preparation head recorded:

```text
542 passed
Required coverage: 90%
Observed coverage: 94.33%
```

The new v1.3.0 version-parity regression was included in those 542 runtime tests and passed.

The exact-head workflows also passed behavior validation, repository structure and manifest validation, IDE/scaffold packaging validation, prompt-load thresholds, project-context validation, Stage 1 Strict Governance after changelog remediation, Dagger guardrail simulation, governance/general behavior tests, native Windows/Ubuntu/macOS validation, action/Python static analysis, and CodeQL.

The Stage 1 remediation demonstrates that stale or incomplete release evidence was not accepted merely because earlier package tests were green.

## Specialist Campaign Basis

v1.3.0 packages the completed SK1-SK10 Specialist Knowledge Layer campaign. Before release preparation began, canonical campaign closeout recorded all phases as `MERGED_VERIFIED` and final SK10 assurance included:

- 10 adversarial routing, coordination, invalidation, handoff, and protected-action scenarios;
- complete authoritative behavior validation;
- 541 runtime tests at 94.31 percent coverage;
- strict governance at 0 errors and 0 warnings;
- prompt-load budgets passing;
- Codex source/export parity passing;
- nine of nine exact-head checks passing; and
- zero unresolved review threads.

Release preparation raised the runtime-suite count to 542 and coverage to 94.33 percent.

## Revision-Bound Readiness Closeout

PR #257 bound the release-readiness record and stable continuity to canonical preparation state:

```text
REVIEWED_HEAD=266e4de66e4bb76016c3771229feb11321c3da9d
CANONICAL_SQUASH=db351796684789987eb5bce85e641ce31c91993b
EXACT_HEAD_CHECKS=PASS_9_OF_9
REVIEW_THREADS=0
EXPECTED_HEAD_GUARD_USED=true
CANONICAL_SIGNATURE=VERIFIED_VALID
```

At that checkpoint, `v1.3.0` remained absent and v1.2.0 remained the public release.

## README Pre-Publication Gate

Before publication, README alignment was treated as a hard gate. PR #259 changed `README.md` only and aligned the public surface with the completed Specialist Intelligence campaign while keeping publication wording neutral.

```text
README_PR=259
REVIEWED_HEAD=b7b8bfeced7c0719558eb95c0797f0685f0c98f2
REVIEWED_TREE=5ae72f6ab9ddf5284afdc3d8675f67fc23c24281
CANONICAL_RELEASE_COMMIT=3c6155c111981632649a3c3207fac8ac1edcea74
CANONICAL_RELEASE_TREE=5ae72f6ab9ddf5284afdc3d8675f67fc23c24281
TREE_EQUIVALENCE=EXACT
CANONICAL_SIGNATURE=VERIFIED_VALID
EXACT_HEAD_CHECKS=PASS_9_OF_9
REVIEW_THREADS=0
EXPECTED_HEAD_GUARD_USED=true
```

The tagged source snapshot therefore includes the aligned README.

## Publication State

Separate explicit maintainer authority was granted for the v1.3.0 annotated tag and GitHub Release after README alignment.

Independent GitHub reads after publication established:

```text
CURRENT_PUBLIC_RELEASE=v1.3.0
V1_3_0_TAG_EXISTS=YES
V1_3_0_TAG_REF_TYPE=tag
V1_3_0_TAG_OBJECT=c66afec49990036d9deb2f07e3363cd664e2dcb1
V1_3_0_TAG_TARGET_TYPE=commit
V1_3_0_TAG_TARGET=3c6155c111981632649a3c3207fac8ac1edcea74
V1_3_0_TAG_OBJECT_SIGNATURE=UNSIGNED
V1_3_0_RELEASE_COMMIT_SIGNATURE=VERIFIED_VALID
V1_3_0_GITHUB_RELEASE_EXISTS=YES
V1_3_0_GITHUB_RELEASE_ID=369402941
V1_3_0_GITHUB_RELEASE_DRAFT=false
V1_3_0_GITHUB_RELEASE_PRERELEASE=false
V1_3_0_GITHUB_RELEASE_IMMUTABLE=true
V1_3_0_GITHUB_RELEASE_PUBLISHED_AT=2026-08-12T17:08:41Z
LATEST_PUBLIC_RELEASE=v1.3.0
V1_3_0_PUBLICATION=COMPLETE_VERIFIED
```

The annotated tag object itself is unsigned. This is recorded accurately rather than represented as a signed tag. The prior v1.2.0 annotated tag object is also unsigned; the release trust anchor is the exact tag target plus the GitHub-verified signed release commit.

See `docs/validation/V1_3_0_PUBLICATION_CLOSEOUT.md` for the publication execution and independent verification record.

## Protected Actions

The separately authorized publication performed:

- annotated tag creation for `v1.3.0`; and
- GitHub Release publication for `Orchestra v1.3.0: Specialist Intelligence`.

The following were not performed:

- deployment or production mutation;
- marketplace publication;
- installed-integration refresh;
- policy activation;
- destructive cleanup;
- branch deletion;
- force push; or
- history rewrite.

```text
VALIDATION_SUCCESS != RELEASE_AUTHORITY
MERGEABILITY != PUBLICATION_AUTHORITY
PACKAGE_VERSION_1_3_0 != PUBLIC_RELEASE_V1_3_0
```

These invariants remain true even though the separate publication gate has now completed.

## Post-Publication Boundary

The `v1.3.0` tag is fixed at release commit `3c6155c111981632649a3c3207fac8ac1edcea74`. Later documentation or development commits on `main` do not move or redefine the release tag.
