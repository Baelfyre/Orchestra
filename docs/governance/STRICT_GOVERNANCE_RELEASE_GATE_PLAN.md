# Strict Governance Release Gate Plan

## Purpose

Define the policy and enforcement plan for moving Orchestra from advisory governance checks to strict merge and release gates.

This document began as planning-only. Phase 6 Stage 1 enabled strict deterministic CI failures. Phase 7 now adds a repository-level `main` ruleset requirement for pull requests, review, conversation resolution, and strict required status checks. CI remains non-deployment and non-release, Dagger remains simulation-only and unpromoted, and no release automation was added.

## Phase 6 Stage 1 Status

Phase 6 Stage 1 implements strict deterministic governance gates in CI for:

- invalid or missing `plugin.json`
- missing required governance validation scripts
- `scripts/governance_check.py --strict` deterministic failures
- Dagger guardrail expectation regressions
- behavior validation failure
- metadata and structure drift
- significant changes without `CHANGELOG.md`
- forbidden generated artifacts, runtime logs, cache files, or local runtime folders
- missing required governance documentation

These areas remain advisory in Stage 1:

- broad but present changelog entries
- wording precision in docs
- external GitHub runner warnings
- Node runtime deprecation warnings from official GitHub Actions
- Arbiter conclusions that still require human judgment
- signed commit policy
- branch protection policy
- pull request review policy
- release approval policy

## Current Advisory Governance State

Current confirmed baseline:

- `Governance Check` runs on pull requests, pushes to `main`, and manual dispatch.
- The workflow passes on `ubuntu-latest` and uploads `governance-validation-report`.
- `main` is covered by an active repository ruleset named `Protect main`.
- The active ruleset requires pull requests, one approval, conversation resolution, and strict required status checks before merge.
- The required GitHub status-check contexts are `governance-check`, `validate`, `Analyze (actions)`, and `Analyze (python)`.
- Those contexts correspond to the `Governance Check`, `validate`, and `CodeQL` workflows currently used by the repository.
- CI remains non-deployment and non-release.
- Dagger remains simulation-only and unpromoted.
- Arbiter Phase 4 calibration and output alignment are complete.
- Repository-role and integration bypass entries still exist on the active ruleset and should remain a documented maintainer-control concern.

## Phase 5 Scope

Phase 5 plans:

- which checks should become blocking
- which checks should remain advisory
- which branch protections should be required for `main`
- when signed commits should be required
- when Arbiter review should be required before merge or release
- what conditions must be met before any future release automation

Phase 5 does not:

- enable strict CI
- change repository settings
- promote Dagger
- enable live destructive execution
- add release or deployment automation

## Required Merge Gates

Recommended strict merge gates for `main`:

1. `Governance Check` workflow must pass.
2. `plugin.json` must be valid JSON.
3. `scripts/governance_check.py` must pass.
4. `scripts/test_dagger_guardrail.py` must pass.
5. `tests/behavior/evaluate_governance.py` must pass.
6. `tests/behavior/run_tests.py` must pass.
7. Significant repository changes must include a `CHANGELOG.md` update.
8. No generated artifacts, runtime logs, cache files, `.agents/`, `.amalgam/`, or other local runtime folders may be committed.
9. Plugin, skill, command, and output-format metadata must remain consistent.
10. Dagger live destructive execution must remain blocked.

## Required Release Gates

Recommended release gates before any public release, distribution, or release automation:

1. `Governance Check` passes on `main`.
2. No critical Arbiter findings.
3. No major Arbiter findings unless explicitly waived by the maintainer.
4. `CHANGELOG.md` is updated.
5. Versioning policy is applied consistently.
6. Release notes are generated or manually reviewed.
7. Marketplace and Codex compatibility validation remain green.
8. No secrets, generated artifacts, runtime logs, or local cache state are included.
9. Dagger remains unpromoted unless a later promotion phase explicitly clears it.

## Checks Proposed for Strict Enforcement

These checks are now blocking in Stage 1 strict CI:

- workflow pass/fail for `Governance Check`
- manifest and metadata consistency
- governance behavior conformance
- Dagger guardrail simulation pass
- full repository validation suite pass
- changelog freshness for significant changes
- artifact hygiene and forbidden-file detection
- Dagger live-execution block remaining intact

## Checks That Should Remain Advisory

These should remain advisory unless a later phase proves they are stable and low-noise:

- wording precision in docs
- broad or imprecise changelog bullets when a changelog entry still exists
- external platform warnings in GitHub-hosted actions, such as Node runtime deprecation notices
- local preflight sync verification, because CI cannot fully prove whether a contributor followed a local-session rule before editing
- Arbiter recommendations that depend on human governance judgment rather than deterministic repository facts

## Branch Protection Recommendations

Recommended `main` branch protection policy:

- require pull requests before merge
- require status checks before merge
- require the `Governance Check`, `validate`, and `CodeQL` workflow outcomes through the active check contexts `governance-check`, `validate`, `Analyze (actions)`, and `Analyze (python)`
- require the branch to be up to date before merge
- restrict direct pushes to `main`
- require conversation resolution before merge
- add code owner review later if `CODEOWNERS` is introduced
- use linear history only if the maintainer wants a stricter commit graph

Phase 7 implementation status:

- applied: pull request requirement, one approval, conversation resolution, strict required status checks, no force pushes, no branch deletion
- already active before Phase 7 and left unchanged: required signed commits, required linear history
- still deferred from this phase: code owner review, admin-bypass tightening, signed-commit tooling rollout planning, deployment automation, release automation, auto-merge

Bypass policy recommendation:

- for this solo-maintainer repository, bypass should remain enabled as an emergency recovery path for the maintainer
- normal development should still use a branch and pull request workflow
- bypass is not the default development path and should not be used for routine convenience
- bypass use should be documented afterward in the implementation report or `CHANGELOG.md` when it affects governance behavior, CI behavior, or release state

## Signed Commit Recommendation

Signed commits are recommended, but should not be expanded or changed until the maintainer confirms the operational model:

- which signature mechanism will be accepted
- whether all human and automation paths can produce verified signatures
- who is allowed to bypass signature requirements in emergencies

Current state and recommendation:

- the repository ruleset currently includes `required_signatures`
- this phase did not broaden or remove that existing setting
- confirm maintainer and contributor signing readiness before making signed-commit policy a broader rollout requirement in later phases

## Dependabot Auto-Merge Readiness

Current repository state:

- `.github/dependabot.yml` currently enables weekly pull-request creation for `github-actions`
- repository auto-merge is not enabled by this phase
- required checks still apply to Dependabot pull requests the same way they apply to human pull requests

Recommended later policy:

- consider auto-merge only for low-risk patch or minor dependency pull requests after all required checks pass
- keep major version updates manual
- keep governance-sensitive changes manual even if the change originated from dependency tooling

Do not auto-merge if any of these are touched:

- `.github/workflows/**`
- `docs/governance/**`
- `scripts/**`
- `skills/**`
- `commands/**`
- `plugin.json`
- Dagger guardrail files or specialist routing files

## Pull Request Review Recommendation

Recommended policy:

- require at least one pull request review before merge to `main`
- require conversation resolution before merge
- require a fresh review if critical governance files change after approval

Governance-sensitive paths that should likely require review:

- `.github/workflows/**`
- `scripts/**`
- `skills/**`
- `commands/**`
- `docs/governance/**`
- `plugin.json`

## Arbiter Review Requirement

Arbiter should be required before merge or release when any of these are true:

- branch divergence or continuity risk exists
- source of truth is unclear
- validation evidence is incomplete
- governance artifacts changed materially
- release readiness is being evaluated

Recommended Arbiter responsibilities:

- review governance artifacts and validation evidence
- classify findings by severity
- recommend merge readiness
- recommend release readiness
- block release when critical findings exist

Arbiter should not become a hard GitHub-required status check until its review input is represented in a deterministic, reviewable way.

## Dagger Promotion Restriction

Dagger must remain simulation-only and unpromoted through Phase 5.

Strict merge or release gates must not be used to imply that Dagger is approved for live destructive execution. A later promotion phase must explicitly approve any change to that status.

## Rollback and Emergency Bypass Policy

Recommended emergency policy:

- do not use routine bypass for convenience
- allow emergency bypass only for repository owners or explicitly named maintainers
- record the reason, scope, and affected commit or release
- require a corrective follow-up change if a gate was bypassed
- require a postmortem when bypass occurs during release or security-sensitive work

## Acceptance Criteria Before Enforcement

Before Phase 6 implements strict enforcement, the maintainer should confirm:

1. `Governance Check` is stable across repeated runs on `main` and pull requests.
2. Arbiter severity classification is accepted as accurate enough for merge and release planning.
3. The branch protection policy for `main` is chosen and documented.
4. The signed-commit decision is made.
5. The maintainer agrees on who can bypass branch protection, if anyone.
6. Dagger remains explicitly unpromoted.
7. Release automation remains deferred until strict merge gates are working as intended.

## Deferred Items

Deferred to later phases:

- changing repository bypass scope beyond the current maintainer-controlled entries
- changing signed-commit policy beyond the current pre-existing ruleset state
- enforcing Arbiter as a hard repository status check
- promoting Dagger beyond simulation-only mode
- adding deployment or release automation

## Recommended Next Phase

Phase 6 should implement strict enforcement only after this plan is accepted.
