# Scope, Change Control, and SDLC Alignment Guide

Load this guide when a proposed delta may affect an approved baseline, business objective, roadmap boundary, or required delivery artifact.

## Establish the Baseline

Before judging scope, identify:

- repository, branch, and exact baseline revision;
- governing objective and authorized phase;
- allowed paths and protected boundaries;
- required outputs and explicit non-goals;
- acceptance criteria and evidence plan;
- decision owner and next human gate.

If the baseline or authority cannot be identified, return `REVISION_REQUIRED` for governed implementation or release work instead of guessing.

## Classify the Delta

- `IN_SCOPE_CORRECTION`: fixes a demonstrated defect without changing intent or boundaries.
- `IN_SCOPE_ELABORATION`: adds detail necessary to satisfy an approved criterion.
- `SCOPE_CHANGE`: adds or removes behavior, users, data, dependencies, contracts, paths, or obligations.
- `POLICY_CHANGE`: changes an enforced rule, gate, authority, or protected action.
- `UNRELATED`: has no traceable requirement in the active work unit.

Only the first two may remain inside an existing bounded implementation envelope, and only when its reduction-only limits still hold. Scope and policy changes require the appropriate human decision.

## Change-Control Record

Record the initiator, reason, old baseline, proposed delta, impacted requirements, acceptance/evidence changes, affected owners, risk, rollback boundary, disposition, and superseded records. A tracker entry is evidence of state, not authority unless it contains or references current human authorization.

## Business and Roadmap Alignment

Check whether the delta:

- advances the named outcome for target users;
- preserves explicit exclusions and phase ordering;
- avoids complexity without a requirement;
- fits dependency and release sequencing;
- preserves operational, support, and rollback expectations;
- has one owner for every decision and output.

Do not approve work solely because it is technically useful or CI is green.

## SDLC Artifact Sufficiency

Select artifacts by risk and lifecycle stage, not by a universal checklist. Material implementation may require a requirement source, acceptance criteria, design or ADR, test plan and results, security/privacy review, migration or rollback plan, operations notes, documentation, and immutable closeout evidence.

Classify each required artifact as `CURRENT`, `MISSING`, `STALE`, `NOT_APPLICABLE`, or `SUPERSEDED`. Explain `NOT_APPLICABLE`; do not use it to hide missing evidence.

## Re-entry Triggers

Re-enter The Steward when intent, users, scope, acceptance criteria, roadmap placement, protected boundaries, or required SDLC artifacts materially change. Re-enter other owners only for their affected decisions. Do not restart every specialist when the change is isolated.
