# Adaptive Specialist Context A2

## Status

A1 and A2 are canonical on `main`.

- canonical A1: `d3b98ecd127f8da562df8cf21385beca33b520f9`, tree `61e17acfa7b370814ea2f22da1550d0ebe0440c7`;
- canonical A2: `0bae83812bdab17ac4cf346d1b35b84c8e361a79`, tree `8a67a13a994c5cc6ed59d24c7908ffdc1ba03063`.

A2 completed governed source validation, signed materialization, protected exact-head validation, Squash merge, GitHub signature verification, and canonical tree readback. The current pre-A3 hardening unit may refine A1/A2 invariants and stale status documentation, but it does not implement A3 behavioral learning.

A3 and later phases remain separately governed under issue #340.

## Purpose

A2 provides opt-in, read-only adaptive context to the already selected specialist. The context may help the specialist use known user preferences and bounded governed outcome evidence, but it cannot select a different specialist, expand authority, grant capabilities, alter governance, change lifecycle permissions, or promote inferred patterns.

## Runtime attachment

A2 does not modify the default `RuntimeExecutor`. It adds `AdaptiveRuntimeExecutor`, an opt-in subclass that uses the existing runtime operation hook.

The runtime order remains:

```text
coordination validation
  -> trusted initialization
  -> context assembly
  -> command parsing
  -> deterministic routing
  -> trusted runtime binding
  -> authority evaluation
  -> capability evaluation
  -> governance validation
  -> A2 advisory context compilation
  -> lifecycle operation
  -> audit/evidence/result
```

The adaptive provider is therefore not called when routing is unbound, authority is denied, capability is denied, or governance blocks execution.

A2 does not attach adaptive context to delegated child executions. Supplying `adaptive_context` to delegated execution entry points fails closed. Delegated adaptive context remains deferred until a later phase explicitly defines how it intersects the delegation context contract.

The operation receives a copy of the existing `RouteDecision` with `metadata.adaptive_context` attached. The route returned in the canonical `ExecutionResult` remains the original route decision and is not mutated by A2.

## Invocation identity and bounds

A2 adaptive compilation requires an explicit `AdaptiveInvocationContext` containing the user identity and any applicable project or task/session identity.

The caller also controls finite context bounds:

- `max_items`, default `16`;
- `max_outcome_evidence`, default `8`;
- optional `min_candidate_confidence`.

A2 does not invent a universal inferred-candidate confidence threshold. If the caller supplies no threshold, inferred candidates are excluded from specialist context.

`repository_refs` and `current_instruction_refs` are caller-curated references. A2 does not copy the raw prompt into the adaptive packet.

## Scope isolation

Every candidate pattern remains subject to the A1 scope model:

1. `global_user`
2. `project`
3. `specialist`
4. `task_session`

The user identity must always match. Project, specialist, and task/session identifiers must match when the stored scope carries those constraints.

A specialist-scoped record cannot be attached to a different specialist. A task/session record with a specialist constraint also requires that exact specialist. A task/session record without a specialist constraint remains task/session scoped and may be shared only inside that exact task/session identity.

## Precedence

For the same adaptive subject, A2 applies this precedence:

1. explicit current user instruction;
2. explicit scoped user preference;
3. confirmed learned pattern;
4. inferred candidate;
5. deterministic default behavior.

At equal precedence, the more specific matching scope wins:

1. task/session;
2. specialist;
3. project;
4. global user.

The final deterministic tie break uses the record update timestamp and stable pattern identity.

An inferred lifecycle event must never replace, downgrade, suppress, or otherwise displace an explicit preference for the same exact scope and subject in the materialized profile. The inferred event may remain in append-only observation evidence for later shadow evaluation, but A2 must continue to consume the explicit materialized preference. If that explicit preference is later removed, stale ignored candidate evidence is not silently resurrected; a later governed inference must establish a new candidate.

A2 does not create confirmed learned patterns. It can only consume a confirmed pattern if a separately governed process created one under a later authorized phase.

## Profile and evidence integrity

A2 reads the A1 machine-local store through `JsonlAdaptiveStore`.

Compilation requires:

- a hash-valid observation log;
- a materialized profile using the current A1 memory rule version;
- `profile.source_head_digest` equal to the current observation-log head.

Missing, stale, or incompatible profile state results in deterministic fallback with no partial learned items.

Provider failures are converted into a generic advisory fallback packet. Exception details are not copied into specialist context.

## Governed outcome evidence

`GOVERNED_OUTCOME_RECORDED` observations may be attached as bounded structured advisory evidence when their scope matches.

Governed outcomes do not become preferences automatically and do not grant authority. A2 does not derive new performance, cost, token, or latency claims from unavailable measurements.

## Privacy boundary

A2 inherits the A1 storage and validation boundary:

- machine-local store outside the repository by default;
- credential-like values and sensitive key fragments rejected by A1;
- raw conversation records are not authoritative adaptive evidence;
- adaptive state remains user scoped;
- deletion and expiry behavior remains owned by A1.

The A2 packet adds no provider transmission or training path.

## Deterministic fallback

Adaptive state is optional. If no invocation context is supplied, `AdaptiveRuntimeExecutor` runs the ordinary base operation without adaptive metadata.

When adaptive compilation is requested but the profile is missing, stale, incompatible, cross-user, or unavailable, the runtime supplies a bounded `DETERMINISTIC_FALLBACK` packet. Routing, authority, capability, governance, and lifecycle behavior remain unchanged.

## A2 validation contract

A2 validation must prove at minimum:

- exact user, project, specialist, and task/session scope isolation;
- explicit-current versus scoped versus inferred precedence;
- an inferred lifecycle cannot displace an explicit preference at the same exact scope and subject;
- specialist-scoped state cannot leak to another specialist;
- inferred candidates require an explicit caller threshold;
- stale profile state fails to deterministic fallback without partial adaptive items;
- A2 packets validate against `machine/schemas/adaptive-context.schema.json`;
- the adaptive provider is not invoked when governance blocks execution;
- provider failure exposes only generic fallback state;
- operation-time adaptive metadata does not mutate the canonical runtime route;
- delegated adaptive context fails closed in A2;
- the default `RuntimeExecutor` remains unchanged;
- A3 behaviors are absent unless separately authorized.

## Post-A2 future adaptive behavior boundary

Issue #340 defines A3 specifically as behavioral-pattern learning in shadow mode. A3 may infer and record scoped candidate patterns and shadow recommendations, but those candidates do not silently control execution or create new permission.

The following behaviors remain outside A2 and are not implicitly authorized by the A3 label:

- adaptive route ranking;
- worker or model selection;
- strategy ranking that controls execution;
- automatic pattern promotion;
- provider integration;
- training;
- recursive or test-time compute;
- learned Tuner topology.

Those capabilities belong to separately governed later phases in issue #340, including A4 and beyond where applicable, and require their own entry and exit gates.