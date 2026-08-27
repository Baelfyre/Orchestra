# UIX-9 Candidate Maturation Test Manifest

Status: `T1_T2_ZERO_CALL_VALIDATED_WAITING_UIX_9C_HUMAN_GATE`

This manifest binds candidate-maturation validation to the candidate head
listed below. It covers engineering regression and synthetic failure
injection only. It does not authorize or record a UIX-9C provider execution.

## Bound state

```text
REPOSITORY=Baelfyre/Orchestra
ACTIVE_BRANCH=codex/uix9b-v2-execution-pipeline-remediation-20260826
PR=572
PR_STATE=DRAFT
CANONICAL_ORIGIN_MAIN=7e08a1d4aa09cbdf7632f5a86461fb3cd3e50fe9
CANDIDATE_HEAD_SHA=f04c5230fb616d75d843ceed41067377eae8848c
FROZEN_EXPERIMENT_BASE=bf6f14316fa8814eeac91440c4a7d70be0d04b9e
FIXTURE_DIGEST=280f1361eda45c2b632c37dd049ec47dec81ab1e8e9e81c61a7aa0d9fb96b978
TASK_DIGEST=3708f0d7d172a424ed426a6275d5012df6a11b0718ed37cba95ba0724c0c506d
VALIDATOR_DIGEST=285494688ef105c813ef5f449f1e13b75529c8cddbf8a42ea76d283a9d5eecf3
UIX_GUIDANCE_DIGEST=f989ac579875fbcd349f812fa6e241ba5c8505f9f940abcb5e0e30006f1606ab
EVALUATOR_DIGEST=d585010eb83ec23b1df2c3512868e9ff5285e7dced1393dcafb0233b835f7ae1
PRE_REPORT_T2_WORKTREE_DIFF_DIGEST=db81954f0407dcc1d094bf5fcd93f543574fc738ac8916686bfbffb3d1ece9ca
```

The pre-report worktree digest covers the uncommitted T2 test additions at
the time those tests ran. The validation documents and changelog entry are
added afterward and are not part of that digest.

## T1 engineering regression manifest

Every result below was run with `CANDIDATE_HEAD_SHA=f04c5230fb616d75d843ceed41067377eae8848c`.

| Gate | Exact command | Result |
| --- | --- | --- |
| UIX focused protocol, evaluator, and historical tests | `python -m pytest -q -p no:cacheprovider tests/runtime/test_uix9_proof_protocol.py tests/runtime/test_uix9_live_proof_protocol.py tests/runtime/test_uix9_live_metric_evaluator_v2.py` | PASS; 46 passed |
| Full runtime suite | `python -m pytest -q -p no:cacheprovider tests/runtime` | PASS; 1703 passed, 10 subtests passed |
| Behavior validation | `$env:ORCHESTRA_APPROVED_BASE_SHA='7e08a1d4aa09cbdf7632f5a86461fb3cd3e50fe9'; python tests/behavior/run_tests.py` | PASS |
| Strict governance | `python scripts/governance_check.py --strict` | PASS; 0 errors, 0 warnings |
| Machine contracts | `python scripts/validate_machine_contracts.py` | PASS |
| Structure | `python scripts/validate_structure.py` | PASS |
| Manifest | `python scripts/validate_manifest.py` | PASS |
| IDE/package | `python scripts/validate_ide_packaging.py` | PASS |
| Stale references | `python scripts/check_stale_references.py` | PASS |
| Python compilation | `python -m compileall -q -f orchestra_runtime scripts internal tests/runtime/test_uix9_proof_protocol.py tests/runtime/test_uix9_live_proof_protocol.py tests/runtime/test_uix9_live_metric_evaluator_v2.py` | PASS |
| Diff check | `git diff --check` | PASS |
| Fixture setup, build, and reset determinism | `python -c "from scripts.uix9_live_proof_runner import validate_fixture; import json; print(json.dumps(validate_fixture(), sort_keys=True))"` | PASS; frozen fixture digest and reset determinism confirmed |
| Historical zero-call canaries | `python -c "from scripts.uix9_live_proof_runner import validate_zero_call_canaries; import json; print(json.dumps(validate_zero_call_canaries(), sort_keys=True))"` | PASS; S0 and S1 |
| V2 frozen identity gate | `python scripts/uix9b_live_proof_runner_v2.py verify-frozen-identities` | PASS; frozen base, canonical preparation lineage, and all frozen digests confirmed |
| V2 dry-run gate | `python scripts/uix9b_live_proof_runner_v2.py execute --execution-mode=dry-run` | PASS as fail-closed refusal; `UIX_9C_EXECUTION_REFUSED_EXPLICIT_LIVE_GATE_REQUIRED` |

The historical `python scripts/uix9_live_proof_runner.py full-preparation-validation`
entrypoint was intentionally not counted from this candidate checkout because
its V1 plan requires `HEAD=bf6f143...`. The direct candidate-local canary and
fixture functions above validate those zero-call controls without weakening
the historical base identity.

## T2 zero-call failure-injection manifest

The following 35 focused tests use synthetic runners and monkeypatched failure
points. They do not invoke `codex`, a provider, a model, a network endpoint,
or an external repository.

| Failure or control path | Test | Result |
| --- | --- | --- |
| Successful process exit without scientific validity | `test_successful_codex_exit_alone_does_not_count_as_valid` | PASS |
| Evaluator failure | `test_evaluator_failure_is_invalid_session` | PASS |
| Incomplete thirteen-metric vector | `test_incomplete_metric_vector_is_invalid_session` | PASS |
| Observation schema failure | `test_observation_schema_failure_is_invalid_session` | PASS |
| Persistence failure | `test_persistence_failure_is_invalid_session` | PASS |
| Missing final artifact | `test_missing_final_artifact_is_invalid_session` | PASS |
| Malformed session evidence | `test_malformed_session_evidence_is_invalid_session` | PASS |
| Process failure and bounded retry | `test_process_failure_is_invalid_and_retries_only_under_frozen_policy` | PASS |
| Malformed raw output | `test_malformed_raw_output_is_invalid_session` | PASS |
| Invalid candidate tree | `test_invalid_candidate_tree_is_invalid_session` | PASS |
| Incomplete validator evidence | `test_incomplete_validator_evidence_is_invalid_session` | PASS |
| Complete valid chain | `test_complete_valid_chain_sets_valid_session_only_after_adjudication` | PASS |
| Partial evidence never counted | `test_partial_evidence_is_never_counted` | PASS |
| Incomplete evidence surface | `test_incomplete_evidence_surface_is_invalid_session` | PASS |
| Crash before pair finalization | `test_simulated_crash_before_pair_finalization_is_invalid_and_not_promoted` | PASS |
| Partial-state restart rejection | `test_restart_with_partial_state_is_rejected_without_session_call` | PASS |
| Counter overflow | `test_counter_overflow_attempt_is_rejected_without_advancing_counters` | PASS |
| Frozen identity mismatch | `test_wrong_frozen_identity_is_rejected_before_session` | PASS |
| Preparation lineage mismatch | `test_wrong_preparation_identity_is_rejected_before_session` | PASS |
| Duplicate session/restart attempt | `test_restart_cannot_double_count_run` | PASS |
| Historical and new counters remain separated | `test_campaign_counters_are_experimental_only_and_historical_counters_unchanged` | PASS |
| Codex command ordering and rule application | `test_codex_0148_approval_flag_precedes_exec_and_rules_apply` | PASS |
| Remaining V2 identity, arm, schema, canary, and plan controls | 14 companion tests in the same module | PASS |

```text
T2_MODEL_CALLS_EXECUTED=0
T2_PROVIDER_CALLS_EXECUTED=0
T2_NETWORK_CALLS_EXECUTED=0
T2_EXTERNAL_REPO_MUTATIONS=0
```

## Immutable historical evidence check

The six files `docs/validation/uix9b-live-evidence/{A1,A2,A3,B1,B2,B3}.json`
remain unchanged. Each remains `PROTOCOL_BREACH` with
`MISSING_FROZEN_LIVE_METRIC_EVALUATOR`; none is used as a calibration case or
assigned a post-hoc metric value.

## Gate disposition

T1 and T2 are complete for the bound candidate state. T3 resource-accounting
resolution is recorded separately as a proposal and is not active authority.
UIX-9C remains blocked pending a fresh human scientific and policy
authorization envelope that freezes the revised resource limits, model
revision, and all live evidence controls.

```text
LIVE_MODEL_CALLS_AUTHORIZED=false
PROVIDER_CALLS_AUTHORIZED=false
UIX_9C_EXECUTION_AUTHORIZED=false
LIVE_MODEL_CALLS_EXECUTED=0
PROVIDER_CALLS_EXECUTED=0
BENEFIT_CLAIM=NONE
HARM_CLAIM=NONE
DIRECTIONAL_MODEL_BEHAVIOR_CLAIM=NONE
```
