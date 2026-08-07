# Cross-Module Logical-Flow Integrity Checklist

Use this checklist with the [Cross-Layer Integrity Profile Protocol](../CROSS_LAYER_INTEGRITY_PROFILE_PROTOCOL.md) and the shared [Cross-Module Logic Audit Protocol](../CROSS_MODULE_LOGIC_AUDIT_PROTOCOL.md).

## Identity and scope

- [ ] Repository, branch, approved baseline, current commit, packet revision, and profile-protocol hash match.
- [ ] The entrypoint, participating modules, dependency direction, shared state, and observable outcome are identified.
- [ ] Every changed path is allowlisted and unrelated modules remain outside the frozen slice.
- [ ] The audit remains language-neutral: a module may be a class, package, function, service, job, handler, adapter, or equivalent unit.

## Workflow trace

- [ ] `ENTRYPOINT` identifies the invocation and its externally observable intent.
- [ ] `INPUT_CONTRACT` maps accepted input names, types, optionality, invariants, and caller assumptions.
- [ ] `MODULE_A_DECISION` identifies the first module's branch conditions, transformation, and owned decision.
- [ ] `HANDOFF_PAYLOAD` maps every value crossing the module boundary, including omitted/default behavior.
- [ ] `MODULE_B_DECISION` proves the receiving module interprets the handoff under the same contract.
- [ ] `SHARED_STATE_OR_SIDE_EFFECT` identifies state mutation, I/O, event publication, caching, or an explicit no-side-effect result.
- [ ] `RESULT_PROPAGATION` proves success values propagate without semantic drift.
- [ ] `ERROR_PROPAGATION` proves errors are preserved, transformed intentionally, or handled explicitly rather than swallowed.
- [ ] `FINAL_OBSERVABLE_OUTCOME` proves the caller-visible result matches the original intent.

## Logical-flow integrity

- [ ] Branch conditions are mutually compatible across modules.
- [ ] Required handoff fields cannot be silently dropped, renamed, coerced, or defaulted.
- [ ] Dependency direction follows the accepted architecture and introduces no accidental cycle.
- [ ] State mutation and side effects occur exactly once and in the required order.
- [ ] Retry/re-entry behavior cannot duplicate side effects.
- [ ] Exceptions, error objects, sentinel values, and rejected results retain deterministic meaning across boundaries.
- [ ] Async, queued, callback, or event-driven handoffs preserve correlation and ordering when applicable.
- [ ] Shared mutable state has an explicit owner and invalidation/update behavior.

## Findings and evidence

- [ ] Clockwork owns cross-module control-flow, handoff, dependency, and error-propagation decisions unless the traced decision enters another specialist's domain.
- [ ] Each finding has one owner, severity, affected stages, evidence, impact, minimal remediation, and required validation.
- [ ] Contradictions are recorded by The Tuner and routed rather than silently resolved.
- [ ] Executable happy-path and failure-path traces are current and bound to the profile-protocol identity.
- [ ] Missing evidence produces `CROSS_LAYER_EVIDENCE_INSUFFICIENT`.
- [ ] Changed identity produces `CROSS_LAYER_CONTRACT_STALE` or `SPECIALIST_REENTRY_REQUIRED`.
- [ ] No open invalidation remains before `CROSS_LAYER_ALIGNMENT_CONFIRMED`.

## Closeout

- [ ] Focused integrity validator and behavior tests pass.
- [ ] Full behavior, runtime regression, packaging, prompt-budget, governance, scope, secret, and diff checks pass.
- [ ] Overseer records current evidence and Arbiter records continuation state.
- [ ] No audit result creates implementation, Git, merge, release, deployment, or policy authority.
