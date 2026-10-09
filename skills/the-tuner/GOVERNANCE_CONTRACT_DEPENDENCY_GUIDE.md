# Governance Contract Dependency Guide

OR-GOV-6 integrates the canonical governance contracts with the existing
Tuner `CollaborationGraph`, dependency edges, invalidation events, and
`Re-entry Recommendation` output. It does not create a second graph or grant
the Tuner routing authority.

## Contract owners

Use immutable references to the existing contracts and preserve ownership:

| Contract | Owner | Tuner treatment |
| --- | --- | --- |
| `ArchitectureGovernanceIntake` | `conductor` | identifies implicated domains and route composition |
| `ProductIntentContract` | `the-steward` | supplies accepted product and scope assumptions |
| `CapacityEnvelope` | `the-steward` | supplies only the workload dimensions a decision consumed |
| `ArchitectureComplexityDecision` | `clockwork` | owns architecture and complexity conclusions |
| `MigrationRiskContract` | `chronicler` | owns persistence and migration conclusions |
| `ProjectArchitectureGovernanceProfile` | project governance | affects only explicitly dependent decisions |

`ArchitectureValidationContract` remains an OR-GOV-7 concern. The Tuner may
identify stale validation evidence, but it does not manufacture validation
contracts or release conclusions.

## Declared dependency rule

An edge must identify its source, target, target kind, and the exact consumed clauses
from the source contract. Participation in the same session is not a
dependency. Unknown owners, targets, clauses, or edge shapes fail closed.

Use the existing dependency and invalidation fields. Sequence dependencies
describe order. Invalidation dependencies describe revalidation reachability
and may point backward or form a finite cycle.

## Semantic and identity changes

Compare the consumed clauses before traversing an edge.

- A consumed clause change opens semantic invalidation and produces a minimal
  re-entry recommendation.
- An identity-only reference refresh, caused by a revision, hash, or reference
  change with equivalent consumed clauses,
  requires packet or reference refresh, but does not re-enter a domain owner.
- An unchanged consumed clause does not propagate invalidation.

Traverse declared invalidation edges only. Deduplicate converging paths and
terminate cycles with a finite visited set. The upstream owner is not re-entered
just because it issued a revised contract. Include that owner only when an
implementation delta explicitly invalidates the owner's own contract.

Mark dependent evidence, artifacts, documentation, or diagrams stale through
their declared target edges. Stale evidence is not failed evidence. A stale
contract is not automatically a contradiction.

## Authority and routing

The Tuner returns `recommended_next_route: conductor`. It never dispatches
Clockwork, Chronicler, Overseer, Scribe, Weaver, or any other specialist.
Conductor remains the exclusive router, Arbiter remains the transition
authority, and Overseer remains the validation and evidence owner.

OR-GOV-4's `MigrationRiskContract` boolean `production_data` gap remains
unchanged. Unknown production presence stays an explicit pre-contract schema
gap and must never be coerced to `false` during dependency analysis.

This guide adds no OR-GOV-7 or OR-GOV-8 behavior, no AR-3 work, and no release,
deployment, policy, provider, Dagger, or migration-execution authority.
