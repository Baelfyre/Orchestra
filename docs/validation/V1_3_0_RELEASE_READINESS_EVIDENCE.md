# Orchestra v1.3.0 Release Readiness Evidence

## Verdict

`V1_3_0_RELEASE_PREPARATION=MERGED_VERIFIED`

`V1_3_0_RELEASE_STATE=PREPARED_NOT_RELEASED`

`CURRENT_PUBLIC_RELEASE=v1.2.0`

`TARGET_VERSION=1.3.0`

`TARGET_TAG=v1.3.0`

This record is revision-bound release-preparation evidence. It does not authorize tag creation or GitHub Release publication.

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

The signed reviewed head and the canonical Squash have the same tree. Squash rewrote commit identity as expected, but not reviewed content.

## Superseded Candidate Evidence

The first 13-file signed candidate was materialized as `5238abe2c41782e8fe411e178a75b3ec8d7e323b` and opened as PR #253.

PR #253 failed closed at Stage 1 Strict Governance because significant package/test changes had no matching `CHANGELOG.md` update. The finding was:

```text
Significant changes were detected without a matching CHANGELOG.md update.
Significant paths: plugin.json, tests/runtime/test_release_version_surfaces.py
```

PR #253 was closed unmerged. Its validation was invalidated and not reused.

The corrected work tree added a focused v1.3.0 preparation changelog entry and restored an accidentally touched historical changelog phrase before signed rematerialization. The final canonical compare shows the release-preparation changelog change as additive only.

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

The package/version change is additive release preparation. It does not graduate any scaffold-only host, change runtime authority, activate policy, deploy software, or publish an integration.

## Package Version Surface

The new deterministic runtime regression validates these 11 live package/version surfaces as `1.3.0`:

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

Exact reviewed head: `f63daf49add4887d7fbd1b581959ebf8654150db`

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

CodeQL reported no new alerts in code changed by PR #255.

PR #255 had zero unresolved review threads and was mergeable on the exact reviewed head immediately before the expected-head Squash merge.

## Runtime and Repository Validation

The exact reviewed release-preparation head recorded:

```text
542 passed
Required coverage: 90%
Observed coverage: 94.33%
```

The new v1.3.0 version-parity regression was included in those 542 runtime tests and passed.

The exact-head workflows also passed:

- behavior validation;
- repository structure validation;
- manifest validation;
- IDE/scaffold packaging validation;
- prompt-load measurement and thresholds;
- project context validation;
- Stage 1 Strict Governance after changelog remediation;
- Dagger guardrail simulation;
- governance behavior tests;
- general behavior tests;
- native Windows/Ubuntu/macOS validation;
- action and Python static analysis; and
- CodeQL.

The Stage 1 remediation demonstrates that stale or incomplete release evidence was not accepted merely because earlier package tests were green.

## Specialist Campaign Basis

v1.3.0 packages the completed SK1-SK10 Specialist Knowledge Layer campaign. Before release preparation began, canonical campaign closeout recorded all phases as `MERGED_VERIFIED` and the final SK10 assurance included:

- 10 adversarial routing, coordination, invalidation, handoff, and protected-action scenarios;
- complete authoritative behavior validation;
- 541 runtime tests at 94.31 percent coverage;
- strict governance at 0 errors and 0 warnings;
- prompt-load budgets passing;
- Codex source/export parity passing;
- nine of nine exact-head checks passing; and
- zero unresolved review threads.

The release-preparation regression raises the current runtime-suite count to 542 and current coverage to 94.33 percent.

## Public Release Boundary

After canonical package preparation, independent GitHub reads established:

```text
CURRENT_PUBLIC_RELEASE=v1.2.0
V1_3_0_TAG_EXISTS=NO
V1_3_0_GITHUB_RELEASE_EXISTS=NO
```

GitHub returned `404 Not Found` for both the `refs/tags/v1.3.0` reference and the release-by-tag `v1.3.0` endpoint at this checkpoint.

The existing `v1.2.0` release/tag history is not modified by v1.3.0 preparation.

## Protected Actions

The following were not performed and remain separately gated:

- annotated tag creation;
- GitHub Release publication;
- deployment or production mutation;
- marketplace publication;
- installed-integration refresh;
- policy activation;
- destructive cleanup;
- branch deletion;
- force push; and
- history rewrite.

```text
VALIDATION_SUCCESS != RELEASE_AUTHORITY
MERGEABILITY != PUBLICATION_AUTHORITY
PACKAGE_VERSION_1_3_0 != PUBLIC_RELEASE_V1_3_0
```

## Publication Gate

The repository may be described as **prepared for v1.3.0 publication**, not as already released.

Required next authority state:

```text
V1_3_0_PUBLICATION=AWAITING_SEPARATE_AUTHORIZATION
```

A future publication action must independently re-read live Orchestra `main`, verify this readiness state has not drifted, verify no newer release/version conflict exists, and then follow the separately authorized tag/release publication procedure. Validation or this evidence file alone does not grant that authority.
