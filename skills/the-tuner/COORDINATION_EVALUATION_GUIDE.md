# Coordination Evaluation Guide

Use this guide to evaluate contract assembly, contradiction handling, invalidation, and minimal re-entry. For the OR-GOV-6 contract-owner and clause-sensitivity rules, load [GOVERNANCE_CONTRACT_DEPENDENCY_GUIDE.md](GOVERNANCE_CONTRACT_DEPENDENCY_GUIDE.md).

## Required Assertions

Verify one owner per clause; immutable contract references; explicit dependency and invalidation edges; current baseline and authority references; acceptance/evidence ownership; contradiction detection without choosing a winner; and one canonical coordination status.

## Re-entry Minimality

For a change event, traverse only declared dependencies. Re-enter the owner of each invalidated clause plus downstream evidence/artifact owners. Do not re-enter unrelated specialists, and do not omit an owner merely to reduce the route.

## Adversarial Cases

Evaluate missing owner, duplicate owner, incompatible clauses, undeclared dependency, stale contract revision, invalidated diagram or documentation, matching content with mismatched identity, unknown status, and an implementation request directed to The Tuner.

Expected results remain the canonical Tuner statuses. The Tuner reports the conflict or re-entry set to Conductor; it does not dispatch, resolve, validate, or transition.

## OR-GOV-6 governance dependency evaluation

Use the existing `CollaborationGraph` and declared invalidation dependencies.
Require exact consumed clauses on governance-contract edges, distinguish
semantic changes from identity-only reference refresh, and traverse only
declared edges. Invalidation cycles are finite revalidation sets, not sequence
cycles. The trigger owner is excluded from ordinary downstream re-entry and is
included only when an implementation delta explicitly invalidates that owner's
contract. Return the recommendation to Conductor; do not dispatch specialists.
