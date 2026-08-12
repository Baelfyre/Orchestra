# Coordination Evaluation Guide

Use this guide to evaluate contract assembly, contradiction handling, invalidation, and minimal re-entry.

## Required Assertions

Verify one owner per clause; immutable contract references; explicit dependency and invalidation edges; current baseline and authority references; acceptance/evidence ownership; contradiction detection without choosing a winner; and one canonical coordination status.

## Re-entry Minimality

For a change event, traverse only declared dependencies. Re-enter the owner of each invalidated clause plus downstream evidence/artifact owners. Do not re-enter unrelated specialists, and do not omit an owner merely to reduce the route.

## Adversarial Cases

Evaluate missing owner, duplicate owner, incompatible clauses, undeclared dependency, stale contract revision, invalidated diagram or documentation, matching content with mismatched identity, unknown status, and an implementation request directed to The Tuner.

Expected results remain the canonical Tuner statuses. The Tuner reports the conflict or re-entry set to Conductor; it does not dispatch, resolve, validate, or transition.
