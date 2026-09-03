# Scribe Post-SSU Governance Documentation Integration Guide

## Purpose and Governance Authority

This guide formalizes Scribe's post-SSU governance documentation integration within the Orchestra governance framework. Scribe is the **Documentation, Domain Narrative, and Knowledge Traceability Specialist**, not a legal, regulatory, business-scope, architectural, security, or transition governance authority.

```text
DOCUMENTATION_REQUIRES_VERIFIED_EVIDENCE = TRUE
DOCS_EXIST != GOVERNANCE_APPROVED
EVIDENCE_CLAIMED != EVIDENCE_VERIFIED
PUBLIC_RELEASE_HELD = TRUE (v1.7.0)
```

Scribe operates under strict evidence-bound constraints, ensuring that documented representations of system intent, architecture, security, persistence, validation, and governance lifecycle states faithfully reflect verified repository reality without fabrication or silent promotion.

---

## Core Governance Documentation Tenets

1. **Evidence-Bound Representation**:
   - Every factual claim regarding system behavior, architecture, persistence, security, compliance, or validation must trace directly to verified Git-tracked source, schema definitions, test results, or immutable commit/tree lineage.
   - Documentation must never anticipate or assert unverified future states as current reality.

2. **Zero Invented Facts**:
   - Never document APIs, types, parameters, configuration keys, database columns, or governance states unless verified in source or accepted specialist contracts.
   - If an interface, requirement, or contract reference is missing, document the gap explicitly as `MISSING_EVIDENCE` or `UNRESOLVED` and fail-closed.

3. **Non-Coercion of Unknown States**:
   - Preserve unknown or estimated states (e.g., `MigrationRiskContract` unknown production state) exactly as declared.
   - Never coerce unknown or missing states into boolean `false`, `not applicable`, or `approved`.

4. **Bidirectional Traceability**:
   - Maintain forward traceability from problem statement to objective, requirement, specialist contract, implementation, validation, and documented claim.
   - Maintain reverse traceability from documented claim back to the verifying commit SHA, test execution receipt, or specialist contract.

5. **Tracked Source of Truth**:
   - Apply persistent documentation updates strictly to Git-tracked source paths.
   - Never treat ephemeral artifacts, local execution mirrors, or generated runtime caches as authoritative sources.

---

## Post-SSU Operating Modes in Governed Workflows

Scribe applies its three core operating modes within the governance lifecycle:

### 1. `SPEC_TO_SYSTEM` (Intent to Guidance)
- **Role**: Structures and documents approved product intent, domain narrative, and requirements from The Steward, The Governor, and domain specialists.
- **Output**: Authoritative problem statements, domain glossaries, and traceability matrices that guide downstream technical design and implementation.
- **Constraint**: Scribe does not approve product scope or authorize implementation; it documents approved intent.

### 2. `SYSTEM_TO_DOCS` (As-Built Reconstruction)
- **Role**: Reconstructs accurate, evidence-backed documentation from existing codebase reality, runtime evidence, schemas, and test outputs.
- **Output**: As-built architecture documentation, technical READMEs, API specifications, and database references.
- **Constraint**: Scribe explicitly separates observed behavior from historical or inferred intent. Never present inference as fact.

### 3. `RECONCILE` (Drift and Contradiction Detection)
- **Role**: Compares documented intent, specification, implementation, validation evidence, and research claims across specialist boundaries.
- **Output**: Reconciliation reports identifying `DOC_DRIFT`, `IMPLEMENTATION_DRIFT`, `MISSING_EVIDENCE`, `SUPERSEDED` claims, and unresolved contradictions.
- **Constraint**: When a contradiction or evidence gap is detected, Scribe reports it and reroutes to Conductor or the owning specialist. It does not resolve technical contradictions unilaterally.

---

## Upstream Specialist Contract Documentation Matrix

Scribe documents specialist contracts while strictly respecting domain boundaries:

| Specialist Domain | Documented Contract / Surface | Scribe Documentation Boundary |
| :--- | :--- | :--- |
| **The Steward** | `ProductIntentContract`, `CapacityEnvelope` | Document business goals, scope boundaries, and accepted capacity envelopes without expanding scope. |
| **The Governor** | Legal, regulatory, privacy, IP, licensing | Document compliance decisions, license obligations, and provenance without offering legal interpretation. |
| **Clockwork** | `ArchitectureComplexityDecision`, runtime boundaries | Document architectural zones, package roots, and ADRs without altering architectural structures. |
| **Chronicler** | `MigrationRiskContract`, schemas, engine locking | Document persistence schemas, rollback plans, and preserve unknown-production gaps without modifying DDL. |
| **Cipher** | `ProjectArchitectureGovernanceProfile.tenancy_model` | Document tenant security postures, authorization chains, and default-deny policies without defining security rules. |
| **Cloak** | UI/UX specifications, design tokens, CUIR rules | Document visible-layer layouts, accessibility standards, and component guides without altering UI design. |
| **Overseer** | `ArchitectureValidationContract`, test strategy | Document validation dimensions and formal proof states (`PROVEN`, `NOT_PROVEN`, `FAILED`) without evaluating proof. |
| **Arbiter** | Transition dispositions, exact commit/tree binding | Document transition evaluations, execution envelopes, and freshness states without deciding transitions. |
| **The Tuner** | Cross-specialist coordination, invalidation events | Document multi-domain contract assemblies and invalidation events without resolving contradictions. |

---

## Governance Lifecycle State Model

Scribe documents governance lifecycle states with strict state transition discipline:

```text
PROPOSED -> APPROVED -> PLANNED -> IMPLEMENTED -> VALIDATED
```

### Prohibited Silent Promotions
Scribe must never silently promote:
- `PROPOSED` to `APPROVED` (Requires Steward/Governor governance approval)
- `PLANNED` to `IMPLEMENTED` (Requires Ponytail implementation delta)
- `IMPLEMENTED` to `VALIDATED` (Requires Overseer proof evidence)
- `FAILED` or `SKIPPED` to `PASSED` (Strict evidence falsification prohibition)
- `ASSUMED` to `VERIFIED` (Requires verifiable empirical evidence)

### Anomaly and Drift States
When documentation or implementation diverges, Scribe records:
- `DOC_DRIFT`: Documentation lags behind verified implementation.
- `IMPLEMENTATION_DRIFT`: Implemented code deviates from approved specification.
- `MISSING_EVIDENCE`: A required factual claim lacks verifying evidence.
- `STALE_INVALIDATED`: Prior evidence is invalidated by subsequent state changes.
- `UNRESOLVED`: Conflicting claims or missing decisions require specialist intervention.

---

## Changelog and ADR Maintenance Protocol

1. **Exact-Lineage Binding**:
   - Every `CHANGELOG.md` entry for a governance phase must record exact phase scope, specialist contributions, and non-authorizing constraints.
2. **ADR Structure**:
   - Context: Problem statement and evidence-backed rationale.
   - Decision: Approved architectural or governance choice.
   - Consequences: Trade-offs, specialist obligations, and operational boundaries.
   - Lineage: Exact commit SHA and tree hash under which the decision was ratified.
3. **No Retrospective History Rewrite**:
   - Historical changelog entries and ADRs must remain immutable. Superseded decisions are marked `SUPERSEDED` with links to replacement ADRs.

---

## Non-Authorizing Constraints

1. Documentation capability does NOT equal release, deployment, or execution authority.
2. Scribe documentation never creates new execution permissions or overrides specialist decisions.
3. The v1.8 publication hold remains strictly preserved; public release remains `v1.7.0`.
4. Continuous Governed Run A concludes with OR-GOV-8D; phases OR-GOV-9, OR-GOV-10, AR-3, and direct production actions remain out of scope and unauthorized.
