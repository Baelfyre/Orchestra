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

## Exact scope for the Issue #937 F3 JEV successor

The AQ6 scope job retains its original exact AQ6 implementation inventory. It
also reports `AQ6_SCOPE=PASS` for the Issue #937 F3 JEV successor only when the
changed paths exactly equal the 18-path inventory in
`scripts/validation/classify_f3_jev_successor_scope.py`, including the approved
`CHANGELOG.md` correction. Partial, mixed, duplicate, unknown, and superset
inventories never match this lane; all fallback behavior remains the existing
AQ6 classifier and exact-inventory logic. This recognition applies only to the
exact-scope job; the AQ6 runtime, behavior, and contract checks still run,
test-to-code coverage is unchanged, and statement and branch coverage floors
remain 97 percent and 95 percent.
