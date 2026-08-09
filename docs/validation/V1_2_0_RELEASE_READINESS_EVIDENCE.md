# Orchestra v1.2.0 Release-Readiness Evidence

## Disposition

```text
EVIDENCE_REVISION=2026-08-09
RELEASE_CANDIDATE=v1.2.0
RELEASE_STATE=PREPARED_NOT_RELEASED
CURRENT_PUBLIC_RELEASE=v1.1.2
RELEASE_READINESS=VERIFIED
R8_PUBLICATION=BLOCKED_REQUIRES_SEPARATE_HUMAN_AUTHORIZATION
```

This record refreshes release evidence invalidated by the R7R merge-governance remediation and Governed Autonomy Modes implementation. It records readiness for the separate R8 human gate. It does not authorize or perform publication.

## Canonical Identity

```text
PRE_GA_BASE=8163c64838d369ea5c4abf45df36f6d6504db9fd
GA_PR=232
GA_REVIEWED_HEAD=13f1f39929b4ddaa6d6a7d2290f145dd5f435c3a
GA_CANONICAL_SQUASH=900f88d7a3ed480ae8b910e6ba204008a72d2784
GA_CANONICAL_PARENT=8163c64838d369ea5c4abf45df36f6d6504db9fd
GA_REVIEWED_TREE=a439e41a9baca24a17aea814c5f3a2f01bc11144
GA_CANONICAL_TREE=a439e41a9baca24a17aea814c5f3a2f01bc11144
REVIEWED_TO_CANONICAL_CONTENT_DIFF_PATH_COUNT=0
CANONICAL_SIGNATURE=VERIFIED_VALID
RULESUITE_RESULT=PASS
```

PR #232 was merged through the normal Squash-only protected-branch path. The canonical commit has one parent, its parent is the exact pre-merge base, its tree equals the reviewed-head tree, the reviewed-to-canonical content diff is empty, its signature is valid, and the rulesuite result is `pass`.

## Exact-Head CI

All required checks completed successfully on reviewed head `13f1f39929b4ddaa6d6a7d2290f145dd5f435c3a`:

- `governance-check`
- `validate`
- `runtime-tests`
- `native-windows-latest`
- `native-ubuntu-latest`
- `native-macos-latest`
- `Analyze (actions)`
- `Analyze (python)`
- `CodeQL`

No required evidence was missing, pending, stale, skipped, cancelled, timed out, or attached to another head.

## Canonical Validation Matrix

The following commands were rerun on clean canonical `main` at `900f88d7a3ed480ae8b910e6ba204008a72d2784`:

```powershell
$env:ORCHESTRA_APPROVED_BASE_SHA='8163c64838d369ea5c4abf45df36f6d6504db9fd'
python tests\behavior\run_tests.py
python -m pytest tests\runtime --cov=orchestra_runtime --cov-report=term-missing --cov-fail-under=90
python scripts\governance_check.py --strict
python scripts\validate_claude_plugin.py
python scripts\validate_ide_packaging.py
python scripts\validate_governed_autonomy_modes_contract.py
python scripts\validate_autonomous_merge_readiness_contract.py
python scripts\validate_delegated_host_reliability_contract.py
git diff --check
```

Results:

```text
BEHAVIOR_SUITE=PASS
RUNTIME_TESTS=541_PASSED
RUNTIME_COVERAGE=94.31_PERCENT
STRICT_GOVERNANCE=PASS_0_ERRORS_0_WARNINGS
CLAUDE_PACKAGING=PASS
IDE_PACKAGING=PASS
GOVERNED_AUTONOMY_CONTRACT=PASS
AUTONOMOUS_MERGE_READINESS_CONTRACT=PASS
DELEGATED_HOST_RELIABILITY_CONTRACT=PASS
DIFF_CHECK=PASS
```

The delegated-host validator continues to describe the repository fixture as simulated with pending/empty live records by design. No R7 installed-host scenario was rerun because GA changed no host-sensitive runtime, plugin, adapter capability, manifest, fixture, skill capability, or command surface.

## Preserved R7 Evidence

Accepted source identities remain unchanged:

```text
R7_E2=VERIFIED
R7_E2_SOURCE_JSON_SHA256=c1aa412d40c4e267c37fe9886d5c75a9768da93d1d6bd69f06466c38b7363562
R7_F=VERIFIED
R7_F_SOURCE_JSON_SHA256=1cc11631742e02bcd872a87dc2cd4f5b75cff2182c2baebe5dc6b444dd5deb95
R7_G=VERIFIED
R7_G_SOURCE_JSON_SHA256=88eea125bb4f945199112287c993ebe90044b8ef28cb000309fa2de39603e08e
R7_H=VERIFIED
R7_H_SOURCE_JSON_SHA256=268b5debcbcb034288b22916eab97a91b211d0d55881d2ddd81a9548e686ecd8
```

Claude Code maturity remains `SCAFFOLD_ONLY`. Claude active runtime continuity is not claimed. Repository simulation is not live installed-host evidence.

## Publication Boundary Verification

Canonical GitHub reads established:

```text
LATEST_PUBLIC_RELEASE=v1.1.2
LATEST_PUBLIC_RELEASE_DRAFT=false
LATEST_PUBLIC_RELEASE_PRERELEASE=false
V1_2_0_TAG=NOT_FOUND
V1_2_0_GITHUB_RELEASE=NOT_FOUND
TAG_AT_GA_CANONICAL_HEAD=NONE
```

## Required Stop State

```text
RUNTIME_CODE_CHANGED=false
PLUGIN_MANIFESTS_CHANGED=false
R7_FIXTURE_LIVE_RECORDS_CHANGED=false
R7_VALIDATOR_CHANGED=false
CLAUDE_MATURITY=SCAFFOLD_ONLY
CLAUDE_ACTIVE_RUNTIME_CONTINUITY_CLAIMED=false
CURRENT_PUBLIC_RELEASE=v1.1.2
TARGET_RELEASE=v1.2.0
RELEASE_STATE=PREPARED_NOT_RELEASED
TAG_CREATED=false
RELEASE_CREATED=false
DEPLOYMENT_PERFORMED=false
MARKETPLACE_PUBLICATION_PERFORMED=false
INSTALLED_INTEGRATION_REFRESHED=false
POLICY_ACTIVATION_PERFORMED=false
R8_PUBLICATION=BLOCKED_REQUIRES_SEPARATE_HUMAN_AUTHORIZATION
```

The next permitted transition is a separately authorized human R8 publication decision. No profile or prior green evidence creates that authority.
