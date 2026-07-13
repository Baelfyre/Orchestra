# Authority and Capability Implementation Plan

Status: Phase 6B-A and Phase 6B-B implemented locally for Issue #178. RuntimeExecutor integration has not started.

## Purpose

Sequence specialist-owned implementation of the approved authority, runtime capability, delegation, and lifecycle architecture. Each batch requires separate Butler authorization, a clean preflight, focused tests, and review before the next batch begins. Phase 6B-A and Phase 6B-B have started implementation, so the four related promotion records are `IMPLEMENTING`.

## Current Implementation Checkpoint

- Phase 6B-A: immutable shared, authority, capability, delegation, lifecycle, error, interface, and serialization contracts complete.
- Phase 6B-B: trusted policy loading, authority evaluation and intersection, capability manifest resolution and intersection, typed enforcement, and event creation complete.
- Delegation validation behavior: not started.
- Lifecycle transition behavior: not started.
- `RuntimeExecutor` integration: not started.
- Active compatibility policy: not created.
- Next separately authorized batch: Phase 6B-C.

## Phase 6B-A - Core Domain Foundation

Scope:

- Immutable authority, capability, delegation, lifecycle, provenance, decision, signal, and audit-event domain models.
- Typed errors defined by the architecture contract.
- Focused service interfaces.
- Deterministic serialization helpers where persistence or audit boundaries need them.
- Unit tests for validation, equality, ordering, immutability, intersections, and error contracts.
- No `RuntimeExecutor` integration.

Exit gate: domain contracts are isolated from adapters and infrastructure, all models fail closed on invalid construction, and focused tests pass.

Completion: passed focused Phase 6B-A contract tests. No delegation validator, lifecycle controller, or RuntimeExecutor integration was added.

## Phase 6B-B - Authority and Capability Enforcement

Scope:

- Trusted repository-owned root authority loading through runtime composition.
- Authority target, operation, and constraint evaluator.
- Immutable runtime capability manifest builder and resolver.
- Deterministic collision rejection and effective-grant calculation.
- Authority and capability decision audit events.
- Focused unit and service-integration tests.

Exit gate: prompt and adapter metadata cannot expand authority, manifests freeze after initialization, denials occur before invocation, and audit evidence is complete.

Completion: passed the combined focused suite with 55 tests and 97.12% focused coverage. Trusted file loading is repository-contained and fail-closed; evaluators accept no prompt or adapter metadata.

## Phase 6B-C - Delegation and Lifecycle

Scope:

- Registered-specialist validation.
- Bounded delegation with parent-child authority and capability intersection.
- Context allowlisting, minimization, and sensitive-context exclusion.
- Lifecycle controller, transition table, structured signals, and terminal results.
- Idempotent duplicate terminal signals and deterministic conflicting-signal rejection.
- Focused unit and service-integration tests.

Exit gate: child grants never exceed parent grants, invalid delegation creates no child run, and only validated lifecycle signals change state.

## Phase 6B-D - Runtime Integration

Scope:

- `RuntimeExecutor` composition with authority, capability, delegation, lifecycle, and audit services.
- Existing adapter compatibility through trusted constructor dependencies.
- Separation of `GovernanceValidator` from authority and capability decisions.
- Structured audit integration and result mapping.
- Backward-compatible construction through an explicit finite compatibility policy.
- Full runtime integration tests.

Exit gate: existing supported adapter paths remain functional under trusted composition, active authority mode fails closed, and governance cannot grant runtime authority.

## Phase 6C - Adversarial Validation

Required cases:

- Prompt authority escalation.
- Adapter metadata authority escalation.
- Undeclared target.
- Undeclared capability.
- Manifest mutation.
- Unknown specialist.
- Delegation depth overflow.
- Context over-inheritance.
- Invalid lifecycle transition.
- Duplicate terminal signal.
- Conflicting terminal signal.
- Distinct timeout, cancellation, and waiting behavior.
- Fail-closed initialization.

Exit gate: every case fails at its owning boundary, preserves state, produces typed evidence, and grants no partial authority.

## Phase 6D - Lifecycle and Release Finalization

Scope:

- Change a promotion to `IMPLEMENTING` only when its authorized implementation begins.
- Change a promotion to `IMPLEMENTED` only after implementation and verification complete.
- Manually synchronize the Pattern Catalog after canonical promotion changes.
- Run release-readiness, licensing, security, compatibility, and governance review.
- Prepare target patch `v1.1.2` without changing the current release during Phase 6A.

## Planned File Ownership

These paths are planning targets, not Phase 6A deliverables. Final scope requires a new implementation preflight.

| Likely path | Planned ownership |
| --- | --- |
| `orchestra_runtime/authority.py` | Authority scope, provenance, decisions, evaluator implementation. |
| `orchestra_runtime/capabilities.py` | Runtime capability definitions, immutable manifest, resolver. |
| `orchestra_runtime/delegation.py` | Delegation requests, decisions, validation, intersections. |
| `orchestra_runtime/lifecycle.py` | States, signals, controller, structured terminal results. |
| `orchestra_runtime/errors.py` | Shared typed authority, capability, delegation, and lifecycle errors. |
| `orchestra_runtime/models.py` | Shared run identity, audit-event, and result integration only when broadly shared. |
| `orchestra_runtime/interfaces.py` | Stable service boundaries after domain contracts are proven. |
| `orchestra_runtime/services.py` | Runtime composition and existing service integration in Phase 6B-D. |
| `orchestra_runtime/__init__.py` | Public exports only after contracts stabilize. |
| `tests/runtime/**` | Focused unit, integration, compatibility, and adversarial coverage owned by each batch. |

`orchestra_runtime/repositories.py`, `factories.py`, adapters, and protocol files are changed only if a later evidence-backed preflight proves they are required. PRAP `AdapterCapabilities` remains separate.

## Verification Matrix

| Proposal requirement | Owning batch | Unit test category | Integration test category | Adversarial test category | Expected audit evidence | Failure behavior |
| --- | --- | --- | --- | --- | --- | --- |
| Prompts cannot widen declared authority. | 6B-B | Authority request reduction | Adapter context through evaluator | Prompt escalation | `AUTHORITY_DECIDED` denial | Stop before privileged action. |
| Undeclared targets are rejected before privileged action. | 6B-B | Target matcher denial | Routed command target evaluation | Undeclared target | `AUTHORITY_DECIDED` denial | Raise typed authority denial. |
| Undeclared capabilities are denied before invocation. | 6B-B | Missing grant and operation | Executor pre-invocation evaluation | Undeclared capability | `CAPABILITY_DECIDED` denial | Raise typed capability denial. |
| Capability manifests cannot mutate after initialization. | 6B-A/6B-B | Frozen manifest and collection | Run initialization then access | Manifest mutation | `CAPABILITY_MANIFEST_CREATED` | Reject mutation; manifest unchanged. |
| Child authority is never broader than parent authority. | 6B-C | Scope intersection | Parent-child creation | Broader child scope | `DELEGATION_REJECTED` or accepted effective scope | Reject empty/invalid intersection or use strict subset. |
| Delegation depth is bounded. | 6B-C | Depth policy boundary | Nested delegation | Depth overflow | `DELEGATION_REJECTED` | No child run; typed depth error. |
| Unknown specialists are rejected. | 6B-C | Registry lookup | Delegation through runtime registry | Unknown specialist | `DELEGATION_REJECTED` | No child run. |
| Unauthorized context inheritance is rejected. | 6B-C | Context allowlist | Parent-child context assembly | Context over-inheritance | `DELEGATION_REJECTED` | No child context or run. |
| Sensitive context is minimized or filtered. | 6B-C | Exclusion and minimization | Delegated context creation | Sensitive-key request | Accepted effective keys or `DELEGATION_REJECTED` | Exclude denied data or reject request. |
| Invalid lifecycle transitions fail deterministically. | 6B-C | Transition table | Executor lifecycle integration | Invalid transition | Rejected `LIFECYCLE_TRANSITIONED` evidence | Preserve prior state; typed transition error. |
| Duplicate completion signals are idempotent. | 6B-C | Signal replay | Terminal result replay | Duplicate terminal signal | One terminal transition plus duplicate evidence | Return original result; no second transition. |
| Timeout, cancellation, and waiting states are distinct. | 6B-C | State-specific signal tests | Controller with execution | Timeout/cancellation/waiting cases | Distinct transition and terminal events | Preserve distinct state and result semantics. |
| Ordinary text cannot complete an agent. | 6B-C/6B-D | Signal type validation | Adapter output through executor | Text completion attempt | Invalid signal evidence when submitted | Ignore as output or reject as signal; state unchanged. |
| Invalid or empty trusted authority fails closed. | 6B-B/6B-D | Root validation | Runtime construction | Missing and empty policy | `INITIALIZATION_FAILED` | Stop before adapter context. |
| Denials and transitions create auditable evidence. | 6B-B/6B-C/6B-D | Event shape and reason codes | Audit sink integration | Denial and transition matrix | Typed events linked to run and decisions | Preserve denial/state even if audit sink fails; surface audit failure. |

## Batch Validation Discipline

Each future batch must run focused unit tests first, then affected runtime integration tests, full behavior and strict-governance checks, runtime coverage, `git diff --check`, and an exact authorized-scope audit. Failures stop the batch. Tests, validators, promotion records, and Catalog content are not weakened to accommodate implementation.

## Revisability

This plan fixes safety boundaries and verification obligations, not final module layout. Phase 6B preflight may refine file ownership, method signatures, or batch splits when current code evidence requires it. Any scope expansion needs Butler approval before edits.
