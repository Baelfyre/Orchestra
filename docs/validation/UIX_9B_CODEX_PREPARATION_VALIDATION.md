# UIX-9B Codex Preparation Validation

Status: `UIX_9B_HOST_REMEDIATION_COMPLETE_WAITING_UIX_9C_AUTHORIZATION`

Canonical SHA: `bf6f14316fa8814eeac91440c4a7d70be0d04b9e`

## Preparation checks

The preparation branch is an isolated worktree from exact `origin/main`:

```text
branch=codex/uix9b-live-proof-preparation-20260826
head=bf6f14316fa8814eeac91440c4a7d70be0d04b9e
preflight_sync_check=PROCEED, aligned with origin/main
```

Live remote checks confirmed current public release `v1.7.0`, immutable and
published from `e5305ef3e160209a0345bd2c7843c923940e62c5`. No open UIX-9 or UIX-9B
pull request was found. Canonical state records UIX-9A as repository-only and
confirms no live UIX-9 model/provider proof.

## Fixture evidence

The synthetic fixture is dependency-free and repository-contained. Its fresh
setup, typecheck, component tests, production build, asset identity, component
inventory, token inventory, state contract, accessibility contract, responsive
breakpoints, and fixture-reset equality are checked by
`scripts/uix9_live_proof_runner.py validate-fixture`.

Observed result:

```text
fresh_setup=PASS, npm install --ignore-scripts --package-lock=false --offline
typecheck=PASS, TYPECHECK_PASS files=5
component_tests=PASS, 3 passed
production_build=PASS, BUILD_PASS output=dist
fixture_reset_determinism=PASS
FIXTURE_DIGEST=280f1361eda45c2b632c37dd049ec47dec81ab1e8e9e81c61a7aa0d9fb96b978
```

The project has no runtime or development package dependencies and uses only
Node built-ins. The generated `dist` directory is excluded from the starting
fixture digest.

## Protocol evidence

```text
guidance_manifest=PASS
live_plan=PASS
S0_POSITIVE_VALIDATOR_CANARY=PASS
S1_NEGATIVE_VALIDATOR_CANARY=PASS
focused UIX-9B/UIX-9A tests=11 passed
```

An earlier focused pytest invocation ran all 10 original tests but host policy blocked the
Hypothesis native DLL during plugin teardown. The successful rerun used
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; no test code was skipped.

The previous `gpt-5.3-codex` freeze is preserved as
`UNVERIFIED_CLIENT_FAILURE` historical evidence. Before any experimental
result existed, human authorization re-froze the active model as
`gpt-5.6-luna` with `REASONING_EFFORT=xhigh` and no substitution. Host-side
validation passed and one isolated non-experimental availability probe returned
the exact expected response. The active record is
`MODEL_AVAILABILITY=AVAILABLE`, `HOST_REMEDIATION_STATUS=PASS`,
`PROBE_STATUS=PASS`, `PROVIDER_FAILURE_CLASSIFICATION=NONE`, and
`MODEL_REVISION=NOT_EXPOSED_BY_PROVIDER`. The runner has no live experimental
execution command.
The machine plan, observation/result schemas, canaries, and authorization
request are closed against unexpected fields. Model self-rating and subjective
visual scoring are excluded.

## Final host-remediation state

The repository-wide validation matrix, strict governance, secret scan, Python
compile sweep, and `git diff --check` passed after the host-remediation record
update. The active host/model pair is available for later human authorization.
No commit, push, pull request, merge, release, deployment, external mutation,
or live experimental call is authorized by this artifact. The next required
gate is `HUMAN_UIX_9C_LIVE_CALL_AUTHORIZATION`; UIX-9C remains prohibited.

Final repository evidence:

```text
full_runtime=1678 passed, 10 subtests passed
full_behavior=Validation suite PASSED
strict_governance=0 Errors, 0 Warnings
stale_references=PASS
structure_and_manifest=PASS
prompt_load_budget=PASS
readme_machine_index_and_impact=PASS
python_compile=PASS
git_diff_check=PASS
full_preparation_validator=S0 PASS; S1 PASS; zero model/provider/external calls
availability_probe=PASS; model_availability=AVAILABLE; pre_campaign_provider_calls=1; live_experimental_provider_calls=0
HOST_REMEDIATION_STATUS=PASS; ACTIVE_MODEL=gpt-5.6-luna; REASONING_EFFORT=xhigh
MODEL_REFREEZE=PASS; EXPERIMENTAL_RESULTS_EXISTED_AT_REFREEZE=false; substitution=false
MAX_MODEL_CALLS_PER_RUN=1; MAX_TOTAL_MODEL_CALLS=6; MAX_PROVIDER_CALLS=6
runtime_guardrail=SKIPPED_GUARDRAILS_DISABLED
LIVE_MODEL_CALLS_EXECUTED=0; LIVE_UIX9_TASK_CALLS_EXECUTED=0; EXTERNAL_REPO_MUTATIONS=0
NEXT_REQUIRED_GATE=HUMAN_UIX_9C_LIVE_CALL_AUTHORIZATION
```
