# Arbiter Calibration Plan

Phase 4 calibrates Arbiter against the advisory CI/CD governance layer before any strict enforcement is introduced.

## Objective

Verify that Arbiter can:

- interpret governance reports and workflow evidence correctly
- distinguish real governance gaps from acceptable advisory warnings
- assign consistent severity
- recommend minimal remediation without overstating risk

## Current Baseline

The current clean governance baseline was verified from local source, validation scripts, and the latest pushed GitHub Actions run:

- Local preflight sync check reports `main` aligned with `origin/main`.
- Local Phase 1-3 validation passes in advisory mode.
- GitHub Actions workflow `Governance Check` succeeded on `ubuntu-latest` for push run `28516067241` on 2026-07-01.
- The `governance-validation-report` artifact uploaded successfully.
- Dagger remains simulation-only and unpromoted.
- CI remains advisory and non-deployment.

Expected baseline Arbiter result:

```text
Result:
READY
```

No critical or major findings should be reported against the current baseline.

## Governance Review Output Standard

When Arbiter is asked to review governance effectiveness, CI governance behavior, or governance artifact interpretation, it should use this result scale:

- `READY`
- `READY_WITH_MINOR_FIXES`
- `READY_WITH_REQUIRED_FIXES`
- `BLOCKED`

Findings must be grouped into:

- `Critical findings`
- `Major findings`
- `Minor findings`
- `Cleanup findings`

Continuity reviews still use Arbiter's existing continuity verdicts, including `HOLD`, when validation or source-of-truth evidence is incomplete.

## Calibration Scenarios

| Scenario | Expected Result | Expected Severity | Expected Arbiter Behavior |
|----------|-----------------|-------------------|---------------------------|
| Healthy baseline | `READY` | None or cleanup only | Confirms advisory CI is healthy and does not invent blockers. |
| Missing changelog update for significant files | `READY_WITH_REQUIRED_FIXES` | Major | Flags changelog freshness gap and recommends updating `CHANGELOG.md` plus process evidence. |
| Dagger guardrail bypass or destructive path allowed | `BLOCKED` | Critical | Treats unsafe destructive execution or bypassed runtime guardrail as release-blocking. |
| Dagger remains simulation-only with guardrail blocking live mode | `READY` or `READY_WITH_MINOR_FIXES` | None or Minor | Confirms current safety posture is acceptable and does not falsely report live execution risk. |
| CI advisory wording accurately mentions warnings and non-blocking findings | `READY` | None | Accepts advisory wording when it does not claim unconditional success. |
| Preflight sync rule missing from contributor or agent process | `READY_WITH_REQUIRED_FIXES` | Major | Flags missing local sync governance rule and recommends restoring validation-only preflight guidance. |
| Generated governance reports, logs, or cache files committed | `READY_WITH_MINOR_FIXES` or `READY_WITH_REQUIRED_FIXES` | Cleanup or Major | Classifies hygiene issues without overstating them unless they materially affect governance trust. |
| Plugin, skill, or command registration drift | `READY_WITH_REQUIRED_FIXES` | Major | Flags mismatched manifests, commands, or skill files as governance-integrity issues. |

## Severity Guidance

### Critical

Use for unsafe or integrity-breaking conditions:

- live destructive behavior allowed without required guardrails
- missing or bypassed Dagger safety enforcement
- broken governance workflow that prevents checks from running

### Major

Use for governance gaps that materially weaken review quality:

- missing changelog update for significant changes
- missing governance validation script
- manifest, skill, or command drift
- missing required governance documentation
- CI wording that falsely implies unconditional success
- missing local preflight sync rule

### Minor

Use for non-blocking clarity or consistency issues:

- ambiguous wording
- overly broad changelog bullets
- advisory warnings needing better classification
- documentation present but imprecise

### Cleanup

Use for repository hygiene issues:

- obsolete stash references in tracked docs
- generated artifacts, logs, or cache files committed
- naming inconsistencies such as `CHANGELOGS.md` versus `CHANGELOG.md`

## Evaluation Method

1. Review current governance source files and workflow definitions.
2. Review the latest GitHub Actions governance run and artifact when available.
3. Compare Arbiter's output to the expected severity and result for each scenario.
4. Record false positives, missed findings, severity drift, and remediation drift.
5. Refine Arbiter guidance only when the mismatch is repeated or material.

## Acceptance Criteria

Phase 4 is considered calibrated enough to close when:

- the healthy baseline produces no critical or major false positives
- critical Dagger bypass scenarios are always classified as `BLOCKED`
- changelog, sync-rule, and manifest drift scenarios are consistently classified as `Major`
- cleanup-only issues are not escalated into critical or major findings without evidence
- remediation recommendations remain minimal, specific, and advisory-aware

## Phase Boundary

This calibration plan does not make CI strict, does not promote Dagger, and does not add deployment or release automation.

Strict governance enforcement should be evaluated in a later phase only after Arbiter results are stable across repeated reviews.
