# UIX-9B Codex Live-Proof Execution Protocol

Status: `UIX_9B_HOST_REMEDIATION_COMPLETE_WAITING_UIX_9C_AUTHORIZATION`

Recorded: 2026-08-26

Canonical entry SHA: `bf6f14316fa8814eeac91440c4a7d70be0d04b9e`

## Boundary

UIX-9B is preparation only. It extends the historical UIX-9A repository-only,
zero-call proof infrastructure with a separate synthetic frontend fixture,
live-observation schema, deterministic evaluator, frozen arm order, and a
human authorization request. No live experimental model call, experimental
provider call, external repository mutation, deployment, release, policy
activation, or production operation is performed by this package. One isolated
non-experimental availability probe was authorized for host remediation.

The preparation terminal is:

```text
UIX_9B_HOST_REMEDIATION_COMPLETE_WAITING_UIX_9C_AUTHORIZATION
```

The protocol question is exactly:

```text
Does adding canonical Orchestra UIX-1 through UIX-8 guidance materially
improve objective UI implementation fidelity when provider, model, task,
starting project, permitted dependencies, resource ceiling, validator,
acceptance requirements, and retry policy remain the same?
```

Model self-rating and a primary subjective visual score are excluded. Screenshots
may support human audit later but never become the primary deterministic score.

## Frozen inputs

| Input | Frozen identity |
| --- | --- |
| Fixture | `tests/fixtures/ui/uix9-live-project/` |
| Fixture digest | `280f1361eda45c2b632c37dd049ec47dec81ab1e8e9e81c61a7aa0d9fb96b978` |
| Task digest | `3708f0d7d172a424ed426a6275d5012df6a11b0718ed37cba95ba0724c0c506d` |
| Validator digest | `285494688ef105c813ef5f449f1e13b75529c8cddbf8a42ea76d283a9d5eecf3` |
| UIX guidance revision | `UIX_1_THROUGH_UIX_8_CANONICAL_2026-08-24` |
| UIX guidance digest | `f989ac579875fbcd349f812fa6e241ba5c8505f9f940abcb5e0e30006f1606ab` |
| Provider | `openai-codex` |
| Frozen model | `gpt-5.6-luna` |
| Model availability | `AVAILABLE`; host validation and the isolated exact-response probe passed |
| Model revision | `NOT_EXPOSED_BY_PROVIDER` |
| Reasoning effort | `xhigh` |
| Codex CLI | `codex-cli 0.148.0` |

The treatment manifest is `machine/ui/uix9-live-guidance-manifest.v1.json`.
It records the canonical content digest, role, and revision identity for each
UIX-1 through UIX-8 source document, machine contract, and UIX-8 source guidance
surface. It explicitly excludes UIX-9 plans, schemas, runners, fixtures, tests,
and result logic.

## Arms and controls

`ARM_A=BASELINE_NO_ORCHESTRA_UIX_GUIDANCE` receives the frozen fixture, task,
requirements, reference material, assets, component inventory, permitted
dependencies, validator, resource ceiling, provider/model, and retry policy.
Its guidance value is `NONE`.

`ARM_B=GOVERNED_CANONICAL_UIX_1_8_GUIDANCE` receives exactly the same inputs plus
the frozen canonical UIX-1 through UIX-8 treatment bundle. No UIX-9 result logic,
prior live result, or future outcome information is supplied.

The only intended treatment difference is canonical UIX guidance presence or
absence. Every run starts from a new copy of the same fixture. No run inherits
source modifications, generated output, conversation history, or arm-specific
behavior-changing cache state.

## Frozen repetitions

```text
3 baseline executions
3 governed executions
6 valid executions total

PAIR_1=A1_THEN_B1
PAIR_2=B2_THEN_A2
PAIR_3=A3_THEN_B3
```

This order is frozen before any live observation.

## Metrics

Primary metrics and directions are machine-frozen in
`machine/ui/uix9-live-proof-plan.v1.json`:

```text
COMPONENT_REUSE                    true is better
DUPLICATE_COMPONENT_COUNT          lower is better
TOKEN_VIOLATIONS                   lower is better
ARBITRARY_STYLE_DRIFT              lower is better
STATE_COVERAGE                     higher is better
ASSET_PROVENANCE                   true is better
ASSET_SUBSTITUTION                 false is better
RESPONSIVE_CONTAINMENT             true is better
ACCESSIBILITY_INVARIANTS           true is better
UNRESOLVED_MAPPINGS                lower is better
REVISION_MISMATCH                  false is better
VISUAL_BASELINE_REPLACEMENT        false is better
DETERMINISTIC_ACCEPTANCE           true is better
```

Secondary capture includes implementation diff size, new component count, new
arbitrary token value count, validation remediation count, wall-clock time, and
input/output/total tokens. Time and token values are `UNAVAILABLE` unless the
host provides trustworthy comparable counters. Missing counters are never
estimated. One experimental run is one fresh isolated Codex agent session, not
one internal inference step. The proposed token policy is
`OBSERVATIONAL_RESOURCE_CEILING` because this host does not expose deterministic
token enforcement. Internal model and provider call counters are
`UNAVAILABLE`.

The frozen session policy is:

```text
EXPERIMENTAL_SESSIONS_PER_RUN=1
MAX_VALID_EXPERIMENTAL_SESSIONS=6
MAX_MODEL_CALLS_PER_RUN=1
MAX_TOTAL_MODEL_CALLS=6
MAX_PROVIDER_CALLS=6
PER_RUN_TIMEOUT_SECONDS=900
TOTAL_CAMPAIGN_TIMEOUT_SECONDS=7200
MAX_RETRIES_FOR_INVALID_INFRASTRUCTURE_RUN=1
MAX_EXTERNAL_REPO_MUTATIONS=0
PYTEST_PLUGIN_AUTOLOAD=PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
```

Hard guardrails are accessibility invariants, responsive containment, reference
identity, visual-baseline preservation, asset provenance, dependency boundary,
and external mutation boundary. A visually improved result with a hard-
guardrail regression is not a governed improvement.

## Retry, invalidation, and classification

Valid unfavorable output is kept and is never retried for outcome. Provider
outages are explicitly classified and may be replaced only under the frozen
outage policy. Host crashes are invalid infrastructure runs and may be replaced
once. A resource ceiling stops the run and preserves evidence; the limit is not
extended after an observed result. Protocol breach fails closed.

The only terminal classifications are `BENEFIT_ESTABLISHED`,
`NO_BENEFIT_ESTABLISHED`, `MIXED_OR_INCONCLUSIVE`, and `PROTOCOL_INVALID`.
Benefit requires no governed hard-guardrail regression, equal-or-better governed
deterministic acceptance, multiple structural improvements across the majority
of paired repetitions, no single-metric dependency, and valid counted runs.
No benefit does not mean Orchestra made UI worse unless separate valid evidence
supports that narrower claim.

## External boundary

Live proof must not mutate external repositories, Orderly, Padayon, Registry,
production infrastructure or services, installed integrations, release tags,
GitHub Releases, or canonical `main`. It uses no deployed credentials or
customer data and performs no deployment or policy activation.

## Zero-call gate

Before requesting human authorization, the runner must pass:

```text
S0_POSITIVE_VALIDATOR_CANARY
S1_NEGATIVE_VALIDATOR_CANARY
```

The canaries enforce schema closure, arm identity, fixture digest equality,
different-only-by-treatment representation, closed result classifications,
required ceilings, frozen retry policy, and fixed endpoints. Existing UIX-9A
tests remain a regression gate. All of these checks use zero model calls and
zero provider calls.

## Human gate

The exact machine request is
`machine/ui/uix9-live-call-authorization-request.v1.json`; the human-readable
request is `docs/validation/UIX_9B_CODEX_LIVE_CALL_AUTHORIZATION_REQUEST.md`.
The prior `gpt-5.3-codex` freeze is preserved as historical
`UNVERIFIED_CLIENT_FAILURE` evidence. Before any experimental result existed,
the model was re-frozen by explicit human selection to `gpt-5.6-luna` with
`xhigh` reasoning and no substitution. Host remediation accepted the active
configuration and one isolated non-experimental probe returned
`UIX9_MODEL_AVAILABILITY_PROBE_OK`. No retry was performed. UIX-9C remains
prohibited until the human live-call authorization gate is separately granted.
