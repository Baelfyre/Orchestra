# Authority and Capability Contracts

Status: Phase 6B-C implementation-refined contract definition.

## Contract Rules

- All authority, capability, delegation, lifecycle, decision, and provenance records are immutable values.
- Stable identifiers and enum values are serialized as exact strings.
- Collections use deterministic ordering by stable identity and reject duplicate identities.
- Missing, empty, malformed, or contradictory trusted configuration fails closed.
- Requests may reduce an effective grant. They cannot expand one.

## Authority Contracts

### `AuthorityProvenance`

Required fields:

- `source_type`: trusted composition or trusted repository policy.
- `source_id`: stable repository-owned policy identifier.
- `policy_version`: exact policy version.
- `loaded_by`: trusted runtime component identity.
- `parent_run_id`: parent run for delegated scope, otherwise absent.
- `parent_decision_id`: accepting delegation decision, otherwise absent.

Prompt text, adapter metadata, routes, governance results, and audit records are invalid provenance sources.

### `AuthorityScope`

Required fields:

- `scope_id`: stable identity.
- `targets`: non-empty, normalized target selectors.
- `operations`: non-empty allowed operation identifiers.
- `constraints`: immutable typed key/value constraints with defined comparison semantics.
- `provenance`: `AuthorityProvenance`.
- `parent_scope_id`: required for delegated scopes and absent for a root scope.

Target matching is exact by default. A selector may cover descendants only when its type explicitly defines that relation. String-prefix matching is prohibited. An action is authorized only when both target and operation match and every constraint passes. No match means denial.

Scope intersection retains only targets and operations allowed by both parent and request and selects the more restrictive compatible constraint. Incompatible constraints produce no grant. A child scope records the parent scope and accepting delegation decision.

### `AuthorityDecision`

Required fields:

- `decision_id`, `run_id`, `scope_id`.
- requested `target`, `operation`, and constraints.
- `allowed`: boolean.
- `reason_code`: stable enum.
- `matched_targets`, `matched_operations`, and evaluated constraints.
- provenance reference.

Default decision is denial. Evaluation cannot mutate the scope.

## Runtime Capability Contracts

Runtime execution permissions use `RuntimeCapability`, `RuntimeCapabilityGrant`, `RuntimeCapabilityManifest`, and `CapabilityDecision`. These names are intentionally distinct from PRAP `AdapterCapabilities`, which describes host support only.

### `RuntimeCapability`

Required fields:

- `capability_id`: stable, repository-owned identity.
- `owner`: registered Orchestra component or specialist.
- `operations`: non-empty supported operation identifiers.
- `description`: non-empty contract summary.

### `RuntimeCapabilityGrant`

Required fields:

- `capability`: `RuntimeCapability`.
- `allowed_operations`: non-empty subset of capability operations.
- `provenance`: trusted root policy or accepted delegation decision.
- `constraints`: immutable typed constraints.

### `RuntimeCapabilityManifest`

Required fields:

- `manifest_id`, `run_id`, and `policy_version`.
- ordered immutable grants.
- creation provenance.

The builder sorts grants by `(capability_id.casefold(), capability_id)`. Two grants with the same stable identity are rejected even if their fields match. Storage becomes immutable after run initialization. Effective capability calculation intersects requested grants with parent grants for delegated runs, retains only mutually allowed operations, applies the more restrictive compatible constraints, and rejects an empty required result.

### `CapabilityDecision`

Required fields:

- `decision_id`, `run_id`, `manifest_id`, `capability_id`, and requested operation.
- `allowed`: boolean.
- `reason_code`: stable enum.
- evaluated grant and constraint references.

Missing capability, disallowed operation, failed constraint, collision, or malformed manifest produces denial or typed initialization failure before invocation.

## Delegation Contracts

### `DelegationRequest`

Required fields:

- `request_id`, `parent_run_id`, requested child run identity, and registered specialist slug.
- structured requested task with objective and acceptance criteria.
- requested `AuthorityScope` reduction.
- requested runtime capability grants.
- explicit context-key allowlist.
- explicit sensitive-context exclusions.
- requested depth and parent delegation provenance.

### `DelegationDecision`

Required fields:

- `decision_id`, `request_id`, `parent_run_id`, and child run identity when accepted.
- `allowed`: boolean.
- registered specialist result.
- parent authority and capability decision references.
- effective child scope and capability manifest references when accepted.
- effective context keys.
- `reason_code` and provenance.

### `DelegationResolution`

The immutable resolution contains the decision plus the effective child `AuthorityScope` and `RuntimeCapabilityManifest` only when validation succeeds. Rejected resolutions contain neither effective contract. Accepted delegation provenance is created only after parent, registry, depth, authority, capability, and context validation succeeds.

Validation requires a known specialist, valid parent run, structured task, depth not greater than the trusted maximum, explicit context allowlisting, sensitive-context exclusion, and non-empty effective authority and capabilities. Unknown specialists, depth overflow, broader child requests, unauthorized context, or invalid provenance are rejected before child creation. Child authority and capabilities are always intersections, never copies or unions.

## Lifecycle Contracts

### States

| State | Meaning | Terminal |
| --- | --- | --- |
| `INITIALIZING` | Trusted configuration and immutable run contracts are being validated. | No |
| `ACTIVE` | Run may perform authorized work. | No |
| `WAITING` | Run is parked pending an explicit resumable condition. | No |
| `COMPLETED` | Validated work result completed successfully. | Yes |
| `FAILED` | Execution ended because work failed. | Yes |
| `CANCELLED` | Authorized cancellation ended the run. | Yes |
| `TIMED_OUT` | Trusted timeout policy ended the run. | Yes |
| `BLOCKED` | A non-recoverable policy or governance gate ended this run. | Yes |

### Allowed Transitions

| From | Allowed destinations |
| --- | --- |
| `INITIALIZING` | `ACTIVE`, `FAILED`, `CANCELLED`, `TIMED_OUT`, `BLOCKED` |
| `ACTIVE` | `WAITING`, `COMPLETED`, `FAILED`, `CANCELLED`, `TIMED_OUT`, `BLOCKED` |
| `WAITING` | `ACTIVE`, `FAILED`, `CANCELLED`, `TIMED_OUT`, `BLOCKED` |
| Any terminal state | None |

### `LifecycleSignal`

Required fields:

- `signal_id`, `run_id`, signal type, expected current state, requested next state.
- structured reason code and evidence references.
- source component identity and trusted provenance.
- terminal result payload only for a terminal signal.

Only `ILifecycleController` applies a signal. Ordinary text, prompt content, adapter output, model prose, or tool prose is never a signal.

An exact replay of the accepted terminal `signal_id` with identical content returns the existing terminal result without another transition. Reuse of an identifier with different content, or any different terminal signal after termination, raises a conflicting-terminal-signal error and records the conflict. Invalid transitions and malformed signals leave state unchanged. Timeout, cancellation, failure, blocking, and completion remain distinct. `WAITING` requires an explicit validated resume signal to return to `ACTIVE`.

Each lifecycle snapshot retains the accepted signal identifier and its deterministic content fingerprint. Terminal replay compares both values, so identical replay is idempotent while altered or different terminal signals conflict.

## Audit Contracts

Structured audit event types:

- `ROOT_AUTHORITY_CREATED`
- `AUTHORITY_DECIDED`
- `CAPABILITY_MANIFEST_CREATED`
- `CAPABILITY_DECIDED`
- `DELEGATION_ACCEPTED`
- `DELEGATION_REJECTED`
- `LIFECYCLE_TRANSITIONED`
- `TERMINAL_RESULT_RECORDED`
- `INITIALIZATION_FAILED`

Every event requires `event_id`, `event_type`, `run_id`, related decision or transition identity, stable reason code, provenance references, and structured details. Child events include `parent_run_id`. Ordering uses the sink's append order plus stable event identity; timestamps may describe occurrence but are never authority inputs. Audit failures must not create a grant or hide the underlying denial.

## Proposed Interfaces

### `IAuthorityEvaluator`

- `validate_root(scope) -> AuthorityScope`
- `evaluate(scope, target, operation, constraints) -> AuthorityDecision`
- `intersect(parent, requested, provenance) -> AuthorityScope`

### `ICapabilityResolver`

- `build_manifest(run_id, grants, provenance) -> RuntimeCapabilityManifest`
- `evaluate(manifest, capability_id, operation, constraints) -> CapabilityDecision`
- `intersect(parent_manifest, requested_grants, child_run_id, provenance) -> RuntimeCapabilityManifest`

### `IDelegationValidator`

- constructor dependencies: authority evaluator, capability resolver, skill registry, and immutable delegation policy.
- `validate(request, parent_scope, parent_manifest) -> DelegationResolution`

### `ILifecycleController`

- `initialize(run_id) -> LifecycleSnapshot`
- `apply(snapshot, signal) -> LifecycleSnapshot`
- `terminal_result(snapshot) -> StructuredTerminalResult | None`

Interfaces are domain-facing boundaries. Implementations depend on immutable models and trusted policy; adapters and prompts do not implement or configure them.

## Error Taxonomy

| Error | Trigger | Required behavior |
| --- | --- | --- |
| `InvalidAuthorityConfigurationError` | Missing, empty, malformed, or untrusted root scope. | Stop initialization and audit typed failure. |
| `AuthorityDeniedError` | Target, operation, or constraint not granted. | Stop before privileged action and audit denial. |
| `InvalidCapabilityConfigurationError` | Malformed grant or manifest. | Stop initialization or child creation. |
| `CapabilityCollisionError` | Duplicate stable capability identity. | Reject entire manifest deterministically. |
| `CapabilityDeniedError` | Capability or operation not granted. | Stop before invocation and audit denial. |
| `DelegationRejectedError` | Invalid specialist, task, context, authority, capability, or provenance. | Do not create child run. |
| `DelegationDepthViolationError` | Requested depth exceeds trusted maximum. | Reject delegation and audit reason. |
| `InvalidLifecycleTransitionError` | Transition absent from allowed table. | Preserve state and audit rejection. |
| `InvalidLifecycleSignalError` | Signal malformed, untrusted, or mismatched to run/state. | Preserve state and audit rejection. |
| `ConflictingTerminalSignalError` | A terminal signal conflicts with accepted terminal state or signal content. | Preserve first terminal result and audit conflict. |

## Core Invariants

```text
effective_child_scope is a subset of parent_scope
effective_child_capabilities is a subset of parent_capabilities
prompt_authority_gain == impossible
adapter_metadata_authority_gain == impossible
runtime_manifest_mutation_after_initialization == prohibited
ordinary_text_terminal_transition == prohibited
```

Subset checks cover target, operation, and constraint semantics, not only identifier membership.

## Compatibility Contract

Trusted runtime composition supplies a finite repository-owned default root policy for existing construction paths. Existing adapters initially remain unchanged. Authority, capability, delegation, and lifecycle enforcement enter through constructor dependencies. Compatibility mode is explicit and temporary, and its policy identity is auditable. Active authority mode fails closed without trusted policy. Missing policy is never interpreted as unlimited authority, and adapter metadata cannot populate trusted contracts.
