# Orchestra v1.8.0 Release Candidate Qualification

Status: `SOURCE_QUALIFICATION_IN_PROGRESS`

Pull request: `#693`

Canonical base at qualification start:

- commit: `2f11f17742e68560d2a435bcab3f247b52d351ab`
- tree: `0f114c13d8f5f54ee5ecf1e9deb156ae6fe6e24b`
- state: signed CUIR-6 canonical closeout, post-merge qualified

## Candidate scope

The v1.8.0 candidate normalizes the repository package and declared host/plugin version surfaces to `1.8.0`, adds the bounded v1.8.0 release candidate notes, and aligns human and machine release-state projections. The latest published release remains immutable `v1.7.0` until a separately authorized publication step.

## Required qualification

The source candidate must pass fresh exact-head Governance Check, validate/runtime validation, Required Analysis Compatibility and CodeQL, Windows/Ubuntu/macOS cross-platform validation, and applicable confidence or mutation checks. Review-thread state must be reconciled to zero unresolved threads.

After source qualification, the reviewed tree must be preserved through the repository's signed-materialization lane. The signed materialized head must receive fresh qualification before canonical merge. After merge, canonical tree identity, signature validity, parent identity, and post-merge required checks must be independently verified.

## Publication boundary

This qualification record does not authorize publication. It does not create or move the `v1.8.0` tag, publish a GitHub Release, deploy, mutate production, activate or bypass policy/rulesets, route or fallback providers, refresh installed integrations, delete branches, force push, or rewrite history.

Publication remains blocked until the candidate is fully qualified and the user gives explicit final-review approval.
