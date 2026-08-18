# A4 Shadow Execution Attachment

## Status

This source candidate is the smallest A4 execution-attachment unit after canonical A4.1.

Canonical entry state:

- branch: `main`
- head: `14f6b0dca28f013b2e0561074a312f0050574115`
- tree: `13f36a478a483854dfaffadac28c71a0f033450d`
- A4.1 state: shadow ranker implemented with no execution control

This unit does not promote adaptive selection into execution authority.

## Why the attachment is post-execution

The canonical `RuntimeExecutor` produces one deterministic `RouteDecision`, then applies runtime binding, authority, capability, governance, lifecycle activation, and the runtime operation.

A4.1 accepts an already-filtered immutable eligibility envelope and returns a structurally non-authorizing shadow decision. Passing that decision into the operation would create an execution influence path even if the decision still declared `selection_effective=false`.

The bounded attachment therefore runs only after the deterministic runtime result has returned. The runtime operation never receives the A4 shadow recommendation, ranked candidate order, evidence packet, or attachment metadata.

## Opt-in runtime surface

`AdaptiveSelectionRuntimeExecutor` is an opt-in subclass of `RuntimeExecutor`.

Default `RuntimeExecutor` behavior is unchanged.

When no A4 invocation is supplied, the subclass returns the ordinary deterministic `ExecutionResult` without an adaptive attachment.

When a valid A4 invocation is supplied, the sequence is:

```text
deterministic RuntimeExecutor
  -> deterministic route
  -> trusted runtime binding
  -> authority
  -> capability
  -> governance
  -> lifecycle activation
  -> runtime operation
  -> deterministic ExecutionResult
  -> A4 shadow ranker
  -> non-authorizing result attachment
```

The attachment records the existing runtime `run_id`, authority decision reference, capability decision reference, lifecycle state, and the A4 selection decision.

## External eligibility remains authoritative

This unit does not construct an eligible option set.

The caller must supply the existing A4.1 `SelectionEligibilityEnvelope` and `SelectionEvidencePacket`. Those records remain immutable inputs to the shadow ranker.

The runtime attachment verifies that the envelope command and routed specialist match the deterministic runtime route before ranking. It does not add a candidate, restore a filtered candidate, infer eligibility from execution success, or change candidate ownership or capabilities.

The existing A4.1 evidence and eligibility validation remains authoritative for the selection decision.

## Execution isolation

The attachment is explicitly non-authorizing:

```text
execution_controlled_by = DETERMINISTIC_ORCHESTRA
selection_effective = false
shadow_influenced_execution = false
operation_inputs_received_shadow_data = false
runtime_outcome_used_as_selection_evidence = false
performance_attribution = NONE
```

The deterministic output, route, validation result, authority decision, capability decision, lifecycle state, terminal result, and runtime audit-event identifiers are copied unchanged into the attached result wrapper.

A shadow recommendation may disagree with the actual deterministic option. The disagreement is comparison evidence only. It cannot change the operation that already ran.

## Fail-closed behavior

If deterministic runtime gates do not complete, A4 shadow evaluation is not run and the attachment status is `NOT_EVALUATED`.

If the A4 provider, envelope binding, evidence packet, or ranking call is unavailable or invalid, the completed deterministic result is preserved and the attachment status is `UNAVAILABLE`.

Provider exception details are not exported through the attachment.

This first unit does not enable A4 attachment for delegated execution.

## Attribution boundary

A generic successful or failed runtime result is not automatically evidence that a specialist strategy, model, or worker caused that outcome.

This unit therefore does not convert the terminal runtime result into new `GOVERNED_SELECTION_OUTCOME`, validation, remediation, or telemetry evidence. Any future option-performance evidence still requires its own exact-option governed evidence path under the frozen A4 contracts.

## Persistence boundary

The attachment is returned with the opt-in runtime result. It is not persisted as a new runtime audit event by this unit.

Persistent audit integration would be a separate bounded unit because it would require an explicit audit contract and event-type decision. Absence of audit persistence does not grant execution authority.

## Validation target

The focused runtime regression proves that:

1. the A4 provider runs only after the deterministic operation;
2. operation inputs never receive shadow-selection data;
3. deterministic route and output remain unchanged;
4. a `SHADOW_RANKED` decision can be attached without changing execution;
5. blocked deterministic governance prevents A4 evaluation;
6. provider failure cannot change a completed deterministic result;
7. route or specialist mismatch fails the adaptive attachment closed; and
8. delegated A4 attachment remains disabled.

## Future boundary

This unit does not authorize execution-effective adaptive selection, eligibility construction, authority or capability expansion, governance changes, provider/model/worker eligibility expansion, automatic promotion, persistent audit integration, A5-A8 behavior, release, deployment, or publication.

Any execution-effective A4 promotion still requires a separate explicit promotion decision and fresh exact-head evidence under the canonical A4 promotion boundary.
