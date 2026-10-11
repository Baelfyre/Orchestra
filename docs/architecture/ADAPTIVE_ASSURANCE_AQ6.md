# AQ-6 Gate Coverage Truthfulness

AQ-6 answers one bounded question:

DID_EACH_DECLARED_GATE_EXECUTE_AND_REACH_THE_CHANGED_BEHAVIOR?

orchestra_runtime.domain.adaptive.gate_coverage is a pure, deterministic
evaluator. It binds a coverage manifest and execution receipts to the current
repository, source, candidate, tree, and work item identities. It checks:

- declared assurance and risk coverage;
- exact changed-path coverage;
- workflow presence and declared commands;
- known test references and executed test references;
- test-to-changed-code coverage;
- gate result, execution scope, duplicate execution, and stale evidence;
- legacy functional-only coverage and generic security coverage where stronger
  assurance is required.

The result is a canonical SHA-256-bound evidence decision. Its authority model
is EVIDENCE_ONLY_NON_AUTHORIZING: it cannot execute a gate, expand scope, or
authorize a transition.

The CLI in scripts/validation/validate_gate_coverage.py is the I/O adapter. It
requires current identity arguments and reads only the supplied manifest,
execution, workflow, and test-coverage evidence. The AQ-6 workflow runs the
runtime, behavior, contract-entry-point, coverage, and exact-scope checks.

The runtime suite keeps controlled negative fixtures for missing execution,
missing workflow commands, unknown tests, tests that do not reach changed code,
stale evidence, insufficient legacy or tenant assurance, failed execution, and
uncovered changed paths.

## Current PR scope applicability (protected governance correction)

The historical AQ6 twelve-path implementation inventory remains an exact
regression reference, not a general requirement that every future PR must
reproduce all original implementation files.

AQ6's scope job now uses the dedicated
`scripts/validation/classify_aq6_scope.py` classifier, **not** the shared
historical AQ7 classifier. It validates the full changed-path inventory and
distinguishes:

- `HISTORICAL_AQ6_EXACT`: the original registered twelve-path inventory,
  still compared byte-for-byte at the path-list level.
- `AQ6_MAINTENANCE`: AQ6-owned workflow, documentation, scope-classifier
  and behavior-test changes only, with mandatory review/test/changelog anchors.
- `AQ6_FUNCTIONAL_CHANGE`: AQ6-owned runtime, schema or validator changes;
  targeted tests and changelog are required in the same change.
- `NOT_APPLICABLE`: changes with no AQ6-owned files, including use of the
  shared `orchestra_runtime/domain/adaptive/__init__.py` facade.
- `INVALID_AQ6_SCOPE`: mixed or incomplete AQ6-owned changes, rejected.

An AQ6 maintenance/functional classification **does not independently
certify its own protected-policy amendment**. Human-authorized change review,
independently attributable evidence, and current-identity verification remain
required before governance promotion. The scope check cannot waive a failed
runtime, CLI behavior, contract, freshness, coverage, or other applicable CI
check. The AQ6 runtime contract retains 97% statement / 95% branch floors.
This change does not change the shared AQ5/AQ7/PRAI classifiers or introduce
special exceptions for individual feature PRs.
