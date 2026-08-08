# R7 Live Installed-Host Validation Evidence

## Reconciliation status

```text
Status: VERIFIED / RECONCILED LOCALLY
Repository: Baelfyre/Orchestra
Orchestra evidence base: bf444e696376ed637185d928140496afa9148a5d
KB evidence base: 4af1083053b10f3278f9a9059fc101124c36ef59
Evidence source: locally installed hosts and local validators, not GitHub CI
Reconciliation branch: reconcile/r7-live-host-evidence
Canonical merge state: NOT MERGED; maintainer review pending
```

This record reconciles the accepted R7 host evidence against the unchanged R6
runtime/plugin candidate. The host runs were obtained against
`bf444e696376ed637185d928140496afa9148a5d`. The reconciliation worktree adds
documentation only and must not be treated as if the host runs executed against
a future reconciliation commit.

## Evidence boundary

The repository fixture remains repository-simulated evidence. It intentionally
retains:

```text
tests/behavior/delegated-host-reliability-fixtures.json
live_validation.status = PENDING_LOCAL_HOST_VALIDATION
live_validation.records = []
```

The canonical validator remains unchanged and continues to enforce that
repository simulation cannot fabricate installed-host validation. The accepted
live records are stored here as a separate source-controlled summary. The
fixture itself is not live-validated by this record.

The `D:\Dev\Evidence\...` paths below are source references on the validating
machine. They are not repository-portable artifacts. The source JSON artifact
SHA-256 values are included for local traceability. Secrets, credentials, raw
private prompts, and unrelated project data were not copied into this record.

## Accepted R7 evidence

### R7-E2: Antigravity same-host reset/resume

```text
Scenario: Antigravity -> Antigravity same-host reset/resume
Evidence level: LIVE_HOST_EVIDENCE
Host maturity: ACTIVE -> ACTIVE
AGY plugin version: 1.2.0
Evidence path: D:\Dev\Evidence\Orchestra-R7E2-AGY-20260808-071535\R7E2_AGY_SAME_HOST_RESET_RESUME_EVIDENCE.json
Source JSON SHA-256: c1aa412d40c4e267c37fe9886d5c75a9768da93d1d6bd69f06466c38b7363562
Runtime bundle SHA-256: ea9167791aa5c9af775078c60f3676014d43914094f005b8f5d9d4eb7bfe331e
Correlation ID: corr-r7e2-32199ad21a9c469988a5f9ce1a599cef
Run ID: run-r7e2-29fd377a91ac48a9a560adc4dd01d73b
Checkpoint ID: cp-r7e2-32811e70b9614317a3c713bdd7567e56
Input envelope SHA-256: 6e409027c2ab83127d12691eeaa334db579c640f2b0e196e791f2bd362b1361c
Evidence packet SHA-256: c7d5d4feb69ee00baa3f1694cf7636ad4165c613efeb404d3cd7444152499d49
Output envelope SHA-256: b62db9e12e4f0b08af49e9d3ae40ca0534bf7cc83aac41c8ec56055eede889ee
Accepted verdict: R7_E2_AGY_PROTOCOL_COMPLETE_RESET_RESUME_VERIFIED
```

Observed invariants: checkpoint and resume identities were preserved;
`RESUME_OK = true`; workspace was unchanged after checkpoint and resume; no
Antigravity plugin or Codex mutation occurred; no tag, release, deployment, or
policy activation occurred.

### R7-F: Codex same-host reset/resume

```text
Scenario: Codex -> Codex same-host reset/resume
Evidence level: LIVE_HOST_EVIDENCE
Host maturity: ACTIVE -> ACTIVE
Codex CLI: codex-cli 0.144.0
Evidence path: D:\Dev\Evidence\Orchestra-R7F-Codex-20260808-170907\R7F_CODEX_SAME_HOST_RESET_RESUME_EVIDENCE.json
Source JSON SHA-256: 1cc11631742e02bcd872a87dc2cd4f5b75cff2182c2baebe5dc6b444dd5deb95
Codex runtime bundle SHA-256: d2f107b152ac70892c064bd3271b0e8e144cf47d8a4c0f64fe05148ddb126610
Codex thread ID: 019fe0a2-427a-7121-b061-5e80f4531cce
Resumed Codex thread ID: 019fe0a2-427a-7121-b061-5e80f4531cce
Correlation ID: corr-r7f-f65963c17d7940028e6863676660905e
Run ID: run-r7f-65b061ab52174b21bc2828b4239d197d
Checkpoint ID: cp-r7f-d921d86574d94f4bab49b0716a7074af
Input envelope SHA-256: 3dfd8ce540db0542bbbfa1ba15ee549519544c93d68969b20361011bf29e7de2
Evidence packet SHA-256: c5d83baaf189b0dd18e9a0c6b466fd04541629c36ca3a1539e787d513376889a
Output envelope SHA-256: 231903536a29b92b2d2072819a5b0f9c0dc6cb393b507bff4ef6e6798251b34c
Accepted verdict: R7_F_CODEX_PROTOCOL_COMPLETE_RESET_RESUME_VERIFIED
```

Observed invariants: thread, checkpoint, correlation, run, and token
identities were preserved; `RESUME_OK = true`; workspace was unchanged after
checkpoint and resume; no Codex skill or Antigravity mutation occurred; no tag,
release, deployment, or policy activation occurred.

The R7-F runtime-bundle identity is preserved exactly as recorded. It is not
normalized against another R7 run.

### R7-G: Codex to Antigravity portable active-host handoff

```text
Scenario: Codex -> Antigravity portable cross-host handoff
Evidence level: LIVE_HOST_EVIDENCE
Host maturity: ACTIVE -> ACTIVE
Expected disposition: AUTO_CONTINUE
Evidence path: D:\Dev\Evidence\Orchestra-R7G-CrossHost-20260808-173355\R7G_CODEX_TO_ANTIGRAVITY_PORTABLE_HANDOFF_EVIDENCE.json
Source JSON SHA-256: 88eea125bb4f945199112287c993ebe90044b8ef28cb000309fa2de39603e08e
Codex runtime bundle SHA-256: 3892b0e3459f0477d3d49fc8cc7dcfe2cd11c6589578a3ef1d2b0235f5a7ff70
Antigravity runtime bundle SHA-256: ea9167791aa5c9af775078c60f3676014d43914094f005b8f5d9d4eb7bfe331e
AGY plugin version: 1.2.0
Codex thread ID: 019fe0b8-d1c6-73f0-b252-4b5f0f07e058
Correlation ID: corr-r7g-0c83843340e74278b55d43588a86f12c
Run ID: run-r7g-c1adbd72460542cbad5a81d4b6645284
Checkpoint ID: cp-r7g-ea42c8e3caf04e2ba19f0873376044a5
Capacity handoff ID: handoff-r7g-bd2aec1fbc804f0a986ccd9438558499
Input envelope SHA-256: 3b7e0c5c62e0a7a7fb2775f0db9c458bf9167247933f0538144b681d9568af07
Evidence packet SHA-256: 5f51cd00b4b8252664f9a210b4d95542513f0f4ebdeb951d835ba4732b2a9338
Portable handoff packet SHA-256: 00d524db05dd2f5b045bceb5f56bf0792de91ea18325f8b375d66201b44e42ce
Output envelope SHA-256: ad87541c0f096478805afe0c032f4527280f3db088dde9c4ef10c258a8050c58
Accepted verdict: R7_G_CODEX_TO_ANTIGRAVITY_PORTABLE_HANDOFF_VERIFIED
```

Observed invariants: sender and receiver identities were preserved;
`HANDOFF_READY = true`; `CROSS_HOST_RESUME_OK = true`; receiver disposition was
`AUTO_CONTINUE`; authority was preserved; context was minimized; no side effect
was replayed; sender and receiver workspaces were unchanged; no Codex or
Antigravity mutation, tag, release, deployment, or policy activation occurred.

The R7-G Codex and Antigravity bundle identities are preserved exactly as
recorded. No cause is inferred for any difference between successful run
bundle identities.

### R7-H: Claude Code packaging and contract compatibility

```text
Scenario: Claude Code packaging and contract compatibility
Evidence level: LIVE_LOCAL_COMPATIBILITY_EVIDENCE
Host maturity: SCAFFOLD_ONLY
Active runtime continuity claimed: false
Claude process started: false
Evidence path: D:\Dev\Evidence\Orchestra-R7H-Claude-Compatibility-20260808-173753\R7H_CLAUDE_CODE_COMPATIBILITY_EVIDENCE.json
Source JSON SHA-256: 268b5debcbcb034288b22916eab97a91b211d0d55881d2ddd81a9548e686ecd8
Claude plugin version: 1.2.0
Claude marketplace version: 1.2.0
Validator SHA-256: b7c52ec94ac2a032020c1b5c0e8e79326d5367cf61e0e53fe3079f67cd627d24
Validator output SHA-256: 66bfed344daaafc833cfd00e0430f355fe242e3400918043a0d65cdd668a4595
Plugin manifest SHA-256: a37b2507490ecf816c4328b7400f82de3c83c4c1ea0db63bb11bf0a0d1c7150c
Marketplace manifest SHA-256: ce9b88c2528cd9acb5f71c8e3d3d2f471d717c4221a43feed46efe8f896e89ae
Host-reliability fixture SHA-256: 5f7c08b5f17d50db42bbf7a22c29839b1809c0fe2e2e531c0d1f3d85eb0c36e1
Canonical Claude plugin validator exit: 0
Accepted verdict: R7_H_CLAUDE_CODE_PACKAGING_CONTRACT_COMPATIBILITY_VERIFIED
```

The accepted R7-H result covers package and contract compatibility only. It
does not claim Claude reset/resume, cross-host active-runtime continuity, or
runtime maturity beyond `SCAFFOLD_ONLY`.

## Diagnostic history excluded from passing evidence

Historical capacity interruptions and broken harness attempts remain diagnostic
history only. They are not host-continuity failures and do not count toward the
accepted R7 matrix:

```text
R7_F_NOT_EVALUATED_CAPACITY_BLOCKED_BEFORE_CHECKPOINT
R7-G attempt 1: NOT_EVALUATED; harness subprocess argument collision; no host started
R7-G V2: NOT_EVALUATED; thread-ID parser failure after sender checkpoint
R7-G V3: NOT_EVALUATED; PowerShell syntax error; no host started
```

No historical failed-attempt evidence was deleted or rewritten by this
reconciliation.

## Accepted active-host matrix

| Scenario | Accepted state |
|---|---|
| Antigravity -> Antigravity same-host | `VERIFIED` |
| Codex -> Codex same-host | `VERIFIED` |
| Codex -> Antigravity portable handoff | `VERIFIED` |
| Claude Code package/contract compatibility | `VERIFIED` |
| Claude Code active runtime continuity | `NOT CLAIMED / NOT APPLICABLE UNDER SCAFFOLD_ONLY MATURITY` |

## Release and authority boundary

```text
R7 live-host validation: VERIFIED, pending repository reconciliation merge / post-merge verification
R8 publication: BLOCKED pending independent post-R7 release verification and separate authorization
CURRENT_PUBLIC_RELEASE=v1.1.2
TARGET_RELEASE=v1.2.0
RELEASE_STATE=PREPARED_NOT_RELEASED
POLICY_ACTIVATION=NOT_PERFORMED
TAG_CREATED=false
RELEASE_CREATED=false
DEPLOYMENT_PERFORMED=false
```

This R7 reconciliation grants no merge, release, deployment, publication,
policy-activation, host-maturity, or external-action authority. The KB remains
untouched and requires its own later governed synchronization.

## Reconciliation readiness

The working-tree change is limited to this evidence record and current-state
documentation. No runtime implementation, adapter, plugin manifest, skill,
command, fixture live record, or canonical validator behavior changes. Fresh
repository validation is required against the reconciliation worktree before
maintainer review.

```text
VERDICT=READY_FOR_MAINTAINER_REVIEW
NEXT=Return this report and the complete diff for immutable review. Do not commit or push.
```
