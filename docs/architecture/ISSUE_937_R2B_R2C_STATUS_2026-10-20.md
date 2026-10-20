# Orchestra Issue #937 R2B/R2C Continuation Status

**Status:** `PARTIAL_FIX_REQUIRES_NEXT_UNIT`
**Evidence as of:** 2026-10-20
**Scope:** Bounded tests and design only. No protected policy, validator, whitelist, production authority source, production resolver, or MCP authority wiring was changed.

## Fresh state

- `origin/main`: `b215a48b678e8708a8a6e7123f5ee1893d3f4f15`, tree `fac2140e41e81bdf243ddc6c389b38c0453ad28c`.
- Issue [#937](https://github.com/Baelfyre/Orchestra/issues/937) remains open; last update observed `2026-10-07T10:26:24Z`.
- Frozen draft [PR #977](https://github.com/Baelfyre/Orchestra/pull/977) remains open at head `ec0c99dd634dc98588b722d07dc2badf63865122`, tree `c38482c126bc2616cf9fe0fb0879c268153671ab`, base `b215a48b678e8708a8a6e7123f5ee1893d3f4f15`. Its source branch was not changed.
- Optional preview source was readable and identity-checked at `d23fc66accc3f3a52a2ab494e8ce655b42ae57b5`, tree `5aa714e88c0f3e4739e564c4008b2974125cbe34`. This is source-skill evidence, not installed-host parity.
- Four implementation worktrees began clean at the fresh main SHA and passed `scripts/preflight_sync_check.py`. The original source checkout's dirty/untracked files were preserved.

## Gap matrix

| Unit | Status | Evidence and remaining gap |
| --- | --- | --- |
| R2A runtime identity | COMPLETE | PR #976 is merged into the fresh main baseline. PR #977's further review-result binding remains a separate frozen draft. |
| R2B-2A read-only Cipher execution | PARTIAL | Added file-link and directory-link traversal regression tests at commit `065fabff5b188117e1bf5270c5025d8f4ea58b0c` / tree `09635c9c8f7b0c738701ac33045ed0cce7d3d859`. No production Cipher engine/provider or qualified process isolation was found; default MCP remains route-only. |
| R2B-2B typed findings | PARTIAL | Added a test that rejects `NOT_REQUIRED` as a substantive review status and a draft versioned-finding design at commit `2b2c2083b96f6bfedec4ae711779437829519855` / tree `a909fef4167eed587c9601fc1234d4fd0ab8bdda`. Typed finding records are not implemented. Cipher was blocked; Clockwork returned only a routing acknowledgement. |
| R2C-2A receipt lifecycle | PARTIAL | Test-only SQLite transaction fixture at test commit `15112d46afd6a3e2eea55177660cf56798ae669f` / tree `3175844c07082c916d801378c3e97652730e2d6e`, with a documentation commit `c0f75d96dda045c59f1415693ea527ab8bda1209` / tree `d8c4daec332d03ad0bbb78005285f9790bec58df`. No production store, independent authority source, resolver, host context provider, or MCP receipt reference was found. |
| R2D readiness / GOV-937 | PARTIAL | Human decision packet is schema-valid and recommends `REQUEST_MORE_EVIDENCE`. No human decision or substantive independent governance review exists. |

## Root-cause revision

Current main does not support a client-set Boolean as authority for the registered read-only review route. `DEFENSIVE_SECURITY_REVIEW` is `NONE` / `REVIEW_ONLY`, and `GovernanceValidator.validate` requires the exact host-created `OperationGovernanceContext`, operation, route, rule, and host profile. The remaining R2B defect is missing production substantive Cipher execution and qualified isolation; the default MCP surface remains route-only.

R2C has domain contracts, ports, and a verifier, but no production resolver/store/context wiring or independent human-authority source. The verifier consumes a single-use receipt and then writes the audit separately; the existing `test_audit_failure_denies_even_after_atomic_consumption` shows audit failure denies after consumption, which can strand a receipt. This run leaves production behavior unchanged and fail-closed.

Frozen PR #977 changes the review result to v2 with runtime identity in its digest but does not add a v2 schema; the current v1 result schema remains strict. This gap is reported without modifying PR #977.

## Validation

The following full runtime coverage command ran in each of the three implementation worktrees:

```text
python -m pytest tests/runtime --cov=orchestra_runtime --cov-branch --cov-report=term-missing --cov-report=json:artifacts/runtime/coverage.json --junitxml=artifacts/runtime/runtime-junit.xml --cov-fail-under=0
```

| Worktree | Runtime result | Statement / branch coverage | Machine evidence |
| --- | ---: | ---: | --- |
| R2B-2A | 3,575 passed, 0 failed, 0 skipped | 97.62% / 95.01% | `test_evidence` PASS; critical inventory ready, no critical failures |
| R2B-2B | 3,574 passed, 0 failed, 0 skipped | 97.61% / 95.00% | `test_evidence` PASS; critical inventory ready, no critical failures |
| R2C-2A | 3,576 passed, 0 failed, 0 skipped | 97.61% / 95.00% | `test_evidence` PASS; critical inventory ready, no critical failures |

Additional checks:

- Focused R2B snapshot, operation-boundary, MCP specialist, and MCP transport suites: 76 passed.
- Focused R2C receipt foundation and synthetic lifecycle suites: 45 passed.
- Post-commit new-test checks: R2B-2A 2 passed; R2B-2B 1 passed; R2C-2A 3 passed.
- `python scripts/validation/validate_architecture_boundaries.py`: PASS in all four worktrees.
- `python scripts/governance_check.py`: exit 0, 0 errors and 0 warnings in R2D.
- Protected governance escalation, governance protocol consistency, and routing validators: PASS.
- Signed materialization: 9 passed. TrueSheet specialist reference: PASS.
- Packet schema check: `python -m jsonschema --instance docs/governance/issue-937/GOV-937-escalation-packet-2026-10-20.json machine/schemas/protected-governance-escalation.v1.schema.json`: exit 0.
- `git diff --check`: PASS in each worktree before commit; commits also passed the repository pre-commit guardrail.
- `python tests/behavior/run_tests.py`: BLOCKED before test execution because an explicit approved baseline was required and unavailable. No baseline was substituted.

## Hosted CI on the initial draft PR heads

Fresh Actions reads on 2026-10-20 show PR #977 green on `validate`, `Governance Check`, `Required Analysis Compatibility`, and `Cross-platform Validation`. PRs #978-#981 each passed `validate`, `Required Analysis Compatibility`, and `Cross-platform Validation`; only `Governance Check` failed.

The failed runs all reached `Run Stage 1 Strict Governance Check` and failed the changelog freshness rule. The exact significant path reported was `tests/runtime/test_specialist_snapshot_binding.py` on #978, `tests/runtime/test_specialist_operation_boundaries.py` on #979, `tests/runtime/test_governance_receipt_atomic_lifecycle.py` on #980, and `docs/governance/issue-937/GOV-937-escalation-packet-2026-10-20.json` on #981. The CI remediation explicitly requested a focused `CHANGELOG.md` entry. No governance threshold, validator, or workflow configuration was changed.

The four branches now each contain a focused changelog entry. `python scripts/governance_check.py --strict` passed locally on each branch with 0 errors and 0 warnings. Since these changelog repairs change all four heads, hosted CI on the repaired exact heads is pending. Initial failed Governance Check run IDs: #978 `39413834981`, #979 `39413841113`, #980 `39413845196`, #981 `39413848367`.

No review submissions or inline review threads were present on PRs #977-#981 at the latest read. No macOS/Linux installed-host parity or production runtime activation is claimed.

## Specialist and human decision state

- Cipher/security-check: `BLOCKED_PENDING_VALIDATION`; no substantive security assessment.
- Conductor, Arbiter, Overseer, Clockwork, and Chronicler commands: `NOT_REQUIRED` routing acknowledgements only, not substantive assessments or transition decisions.
- Governor: `NOT_FOUND`; the exposed compliance-review command routes to Conductor and is not a Governor assessment.
- The escalation packet records the unavailable originating run ID as `NOT_FOUND`, no decision digest, and no claim that an empty dissent list means reviewers found no dissent.
- A final Scribe review attempt was blocked because the review tool inspected the source checkout at `JEO/r5-p1-clean-acceptance-20261017` / `e9196a16358839ccddaff1ce37f11633f697d329`, not this R2D worktree. No final Scribe assessment is claimed.
- Human decision remains required before any protected authorization/source change, production receipt activation, policy or validator mutation, or authority expansion.

## Pending work and risks

1. Obtain substantive Cipher review and host-owned process-isolation evidence before implementing a production read-only assessment engine.
2. Obtain Clockwork/Cipher decisions for typed finding severity, evidence-reference grammar, and versioned result schemas. Reconcile the PR #977 v2 schema gap in a separately authorized candidate; keep its branch frozen.
3. Obtain Chronicler/Clockwork persistence contracts and Governor/Cipher/Arbiter/Overseer assessments before production receipt-source, resolver, context, or consumption wiring.
4. Supply or verify an approved behavior baseline, then rerun the behavior suite.
5. Await exact-head GitHub CI and independent human review. No merge, activation, or protected governance change is authorized by these results.
