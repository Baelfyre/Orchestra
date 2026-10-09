# UIX-9C Execution Audit

Status: `PROTOCOL_INVALID`

The six authorized Codex sessions were executed in the frozen order with the
frozen provider/model selection, isolated fixture copies, and the governed
UIX-1 through UIX-8 bundle supplied only to arm B. Each session completed the
project's deterministic setup/typecheck/test/build checks, and independent
reruns of typecheck, component tests, and build passed for all six trees.

The campaign cannot be counted as valid scientific evidence because the frozen
UIX-9B package does not contain a runnable deterministic evaluator for the
thirteen live primary metrics. `scripts/uix9_live_proof_runner.py` validates
the fixture, guidance manifest, plan, schemas, and zero-call canaries, but it
does not evaluate a completed model-produced tree. The fixture's component
contract test is also not a complete live-output metric evaluator. Assigning
metric values after observing the six outputs would therefore introduce
outcome-dependent adjudication logic.

Accordingly, every observation preserves the observed build/test/validator
evidence but is classified `PROTOCOL_BREACH` with the shared failure code
`MISSING_FROZEN_LIVE_METRIC_EVALUATOR`. No observation is counted as a valid
run, no paired repetition is valid, and no behavioral conclusion is claimed.
The required `primary_metrics` objects retain the conservative contract-level
static observations needed for schema completeness; they are explicitly
non-adjudicating and must not be interpreted as frozen live metric results.

The missing evaluator is not repaired after observation because changing the
metric logic after results exist would violate the frozen protocol. A future
campaign requires a new preparation/re-freeze cycle that defines and validates
the evaluator before any live call.

The `git_diff_digest` values in the observation files are deterministic hashes
of sorted records containing each changed relative path and its canonical
before/after content digests. The fixture tree digests use the frozen
UIX-9B tree-record rules and exclude only `fixture-manifest.json`, `project/dist`,
and `project/node_modules`.
