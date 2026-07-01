# Strict Governance Release Gate Plan

## Purpose

Define the policy and enforcement plan for moving Orchestra from advisory governance checks to strict merge and release gates.

This document is planning-only. It does not make CI strict, does not change branch protection, does not promote Dagger, and does not add deployment or release automation.

## Current Advisory Governance State

Current confirmed baseline:

- `Governance Check` runs on pull requests, pushes to `main`, and manual dispatch.
- The workflow passes on `ubuntu-latest` and uploads `governance-validation-report`.
- CI remains advisory and non-deployment.
- Dagger remains simulation-only and unpromoted.
- Arbiter Phase 4 calibration and output alignment are complete.
- `main` branch-rule bypasses were observed on the last push: direct-push protection and unverified-signature protection were bypassed. This is a governance planning concern for Phase 5, not a current workflow failure.

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

These checks are good candidates to become blocking in a later implementation phase:

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
- require the `Governance Check` workflow specifically
- require the branch to be up to date before merge
- restrict direct pushes to `main`
- require conversation resolution before merge
- add code owner review later if `CODEOWNERS` is introduced
- use linear history only if the maintainer wants a stricter commit graph

Bypass policy recommendation:

- bypass should be limited to the repository owner or explicitly named maintainers
- every bypass should require a written reason
- every bypass should trigger follow-up review or postmortem if governance protections were skipped

## Signed Commit Recommendation

Signed commits are recommended, but should not be enforced until the maintainer confirms the operational model:

- which signature mechanism will be accepted
- whether all human and automation paths can produce verified signatures
- who is allowed to bypass signature requirements in emergencies

Recommendation:

- plan for verified signatures on merges to `main`
- do not enforce the setting until contributor workflow and maintainer tooling are ready

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

- turning advisory warnings into blocking workflow failures
- changing GitHub branch protection settings
- requiring signed commits
- enforcing Arbiter as a hard repository status check
- promoting Dagger beyond simulation-only mode
- adding deployment or release automation

## Recommended Next Phase

Phase 6 should implement strict enforcement only after this plan is accepted.
