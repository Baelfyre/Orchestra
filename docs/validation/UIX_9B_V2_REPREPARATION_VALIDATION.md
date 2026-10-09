# UIX-9B V2 Re-preparation Validation Record

Status: `UIX_9B_V2_DETERMINISTIC_EVALUATOR_FROZEN`

This record covers V2 preparation only. No live model task, provider availability probe, or experimental rerun was executed in this phase.

## Canonical and worktree evidence

```text
CANONICAL_SHA=bf6f14316fa8814eeac91440c4a7d70be0d04b9e
CANONICAL_TREE=5c9942036593091b2fa9bffb8b69427a26f986e2
CURRENT_WORKTREE=isolated codex/uix9b-repreparation-v2-20260826
CANONICAL_SYNC=HEAD equals origin/main
HISTORICAL_UIX9C_HANDOFF=matched supplied six observations
HISTORICAL_OBSERVATIONS_MUTATED=0
```

## Frozen identities

```text
FIXTURE_DIGEST=280f1361eda45c2b632c37dd049ec47dec81ab1e8e9e81c61a7aa0d9fb96b978
TASK_DIGEST=3708f0d7d172a424ed426a6275d5012df6a11b0718ed37cba95ba0724c0c506d
VALIDATOR_DIGEST=285494688ef105c813ef5f449f1e13b75529c8cddbf8a42ea76d283a9d5eecf3
UIX_GUIDANCE_DIGEST=f989ac579875fbcd349f812fa6e241ba5c8505f9f940abcb5e0e30006f1606ab
EVALUATOR_VERSION=uix9b-live-metric-evaluator-v2.0.0
EVALUATOR_DIGEST=d585010eb83ec23b1df2c3512868e9ff5285e7dced1393dcafb0233b835f7ae1
```

## Zero-call evidence

| Gate | Command/evidence | Result |
| --- | --- | --- |
| UIX-9A regression and fixture gate | `python scripts/uix9_live_proof_runner.py full-preparation-validation` | PASS; S0/S1 canaries pass; live model calls 0; provider calls 0; external mutations 0 |
| V2 evaluator calibration | `python -m pytest -q tests/runtime/test_uix9_live_metric_evaluator_v2.py` | PASS; positive, negative, boundary, malformed, and missing-artifact cases pass |
| V2 observation and adjudication path | same focused test module | PASS; candidate tree -> 13 metrics -> V2 observation schema -> pair adjudication |
| V2 identity gate | `python scripts/uix9b_live_proof_runner_v2.py verify-frozen-identities` | PASS |
| Machine contract validation | `python scripts/validate_machine_contracts.py` plus direct Draft 2020-12 validation of V2 artifacts | PASS |
| Behavior suite | `ORCHESTRA_APPROVED_BASE_SHA=bf6f14316fa8814eeac91440c4a7d70be0d04b9e python tests/behavior/run_tests.py` | PASS |
| Runtime suite | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/runtime -q` | PASS; 1685 passed, 10 subtests passed |
| Python compile | `PYTHONPYCACHEPREFIX=<temporary-prefix> python -m compileall -q -f orchestra_runtime scripts internal/context tests/runtime/test_uix9_live_metric_evaluator_v2.py` | PASS |
| Governance and structure | `validate_structure.py`, `validate_manifest.py`, `governance_check.py --strict`, `check_stale_references.py`, runtime guardrail | PASS |
| Cross-platform-compatible checks | Codex export, router positive/negative, prompt thresholds, plugin JSON, `git diff --check` | PASS; prompt threshold output is advisory only |

The first direct compile attempt used the source tree's default bytecode cache and encountered a host permission error. It was rerun with a temporary bytecode prefix and passed. An earlier BOM-aware in-memory compile also passed all repository Python sources. No repository source or generated runtime copy was changed to address the host cache issue.

## Post-commit exact-candidate remediation

The first signed preparation commit exposed a bounded runner defect: the V2 identity gate compared the frozen canonical base SHA to the candidate `HEAD`, which fails by definition once the preparation commit exists. The correction binds `canonical_sha` to the current `origin/main` base and permits the isolated candidate to be ahead. Regression coverage was added in `tests/runtime/test_uix9_live_proof_protocol.py`.

The preserved UIX-9A runner, schemas, fixtures, observations, and `VALIDATOR_DIGEST` remain byte-for-byte unchanged. Its historical full-preparation command is base-bound by that frozen validator identity; the V1 runtime regression tests and zero-call canaries pass on the V2 candidate without altering the historical validator.

## Calibration answers

The expected results are frozen in `tests/fixtures/ui/uix9b-live-calibration/**/expected-metric-result.json` and indexed by `machine/ui/uix9b-live-calibration-manifest.v2.json`. Positive and boundary cases emit all thirteen metrics with deterministic acceptance true. The negative case emits all thirteen metrics with structural failures and deterministic acceptance false. Malformed and missing-required-input cases return `FAIL_CLOSED` and do not emit metric values. Historical UIX-9C observations were not used.

## Authority and unresolved values

```text
PROVIDER=openai-codex
MODEL=gpt-5.6-luna
MODEL_REVISION=UNRESOLVED_PENDING_LIVE_AUTHORIZATION
CODEX_CLI_VERSION=codex-cli 0.148.0
LIVE_MODEL_CALLS_AUTHORIZED=false
PROVIDER_CALLS_AUTHORIZED=false
UIX_9C_EXECUTION_AUTHORIZED=false
MAX_NEW_LIVE_CALLS=0
```

The model revision cannot be established without a future authorized live execution and is intentionally unresolved. No provider substitution is permitted.

## Readiness disposition

The evaluator, calibration fixtures, V2 schemas, identity checks, provider-accounting repair, isolation/order plan, retry policy, resource-ceiling proposal, and zero-call validation path are scientifically and technically ready for a separately authorized UIX-9C campaign, subject to the unresolved model revision being recorded at the human authorization gate. This record makes no model behavior claim and does not authorize the campaign.
