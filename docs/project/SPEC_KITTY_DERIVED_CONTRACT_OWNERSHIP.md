# Spec Kitty-Derived Orchestra Contract Ownership

> [!NOTE]
> **Design Status:** `DESIGN_COMPLETE`
> **Runtime Status:** `IMPLEMENTED_MERGED`
> **Release Status:** `NOT_RELEASED`
> **Merged PR:** `#208`
> **Merge Commit SHA:** `1e2992b94abe67a76c1e6ec0b98f8b712ae256e4`
> **External Source Commit:** `8466727ebbbc01fcaf43575657c9b1b9553784d9` (`Priivacy-ai/spec-kitty` v3.2.6)

---

## 1. Scope & Ownership Principles

This document defines canonical placement, single specialist ownership, and architectural boundaries for the Spec Kitty-derived Orchestra upgrade contracts.

1. **Single Source of Truth Invariant:** No new contract creates a second source of truth for existing state or policy.
2. **Single Canonical Owner Invariant:** Every contract has exactly ONE canonical specialist owner. Secondary consumers or validators are recorded separately.
3. **No Inferred Authority Invariant:** Machine-readable formats, correlation headers, retrospective artifacts, worktree contracts, and status projections track execution; they do NOT grant execution, merge, release, or policy mutation authority.

---

## 2. Canonical Phase 2 Contract Ownership Matrix

| Contract Name | Canonical Specification | Canonical Owner | Secondary Consumers | Validation Owner | Continuity Consumer | Design Status | Implementation Status | Policy Integration Status | Release Status |
|---|---|---|---|---|---|---|---|---|---|
| **OrchestraRuntimeEnvelope** | `docs/project/ORCHESTRA_RUNTIME_ENVELOPE.md` | Clockwork | Conductor, Arbiter | Overseer | Arbiter | `DESIGN_SPECIFIED` | `IMPLEMENTED_MERGED` | `NOT_APPLICABLE` | `NOT_RELEASED` |
| **OrchestraCorrelationID** | `docs/governance/CORRELATION_ID_PROTOCOL.md` | Chronicler | Conductor, Overseer | Overseer | Arbiter | `DESIGN_SPECIFIED` | `IMPLEMENTED_MERGED` | `NOT_APPLICABLE` | `NOT_RELEASED` |
| **OrchestraPhaseRetrospective** | `docs/governance/PHASE_RETROSPECTIVE_PROTOCOL.md` | Overseer | Conductor, Scribe | Overseer | Arbiter | `DESIGN_SPECIFIED` | `MODEL_AND_BUILDER_IMPLEMENTED_MERGED` | `NOT_APPLICABLE` | `NOT_RELEASED` |
| **OrchestraUnitRecord extension** | `docs/project/ORCHESTRA_UNIT_RECORD_EXTENSION.md` | The Steward | Conductor, Ponytail | Overseer | Arbiter | `DESIGN_SPECIFIED` | `MODEL_AND_CONTEXTUAL_VALIDATOR_IMPLEMENTED_MERGED` | `DEFERRED` | `NOT_RELEASED` |

---

## 2.1 Candidate Phase 3 Contract Ownership Matrix (Design Baseline)

| Contract Name | Canonical Specification | Canonical Owner | Secondary Consumers | Validation Owner | Continuity Consumer | Design Status | Implementation Status | Policy Integration Status | Release Status |
|---|---|---|---|---|---|---|---|---|---|
| **OrchestraStatusProjection** | `docs/project/ORCHESTRA_STATUS_PROJECTION.md` | Scribe | Conductor, Arbiter, Overseer, Ponytail | Overseer | Arbiter | `DESIGN_SPECIFIED` | `NOT_IMPLEMENTED` | `NOT_APPLICABLE` | `NOT_RELEASED` |
| **OrchestraWorktreeContract** | `docs/project/ORCHESTRA_WORKTREE_CONTRACT.md` | Ponytail | Conductor, Arbiter, Overseer, Host Adapters | Overseer | Arbiter | `DESIGN_SPECIFIED` | `NOT_IMPLEMENTED` | `NOT_APPLICABLE` | `NOT_RELEASED` |

---

## 3. Specialist Responsibilities

### 3.1 Clockwork (Engineering & Code Structure Specialist)
- **Canonical Contract:** `OrchestraRuntimeEnvelope` (`docs/project/ORCHESTRA_RUNTIME_ENVELOPE.md`).
- **Responsibility:** Owns typed JSON result envelope serialization profiles (`json:orchestra-envelope`) across `execution_result`, `transition_decision`, and `audit_event` variants.

### 3.2 Chronicler (Data Persistence & Audit Logging Specialist)
- **Canonical Contract:** `OrchestraCorrelationID` (`docs/governance/CORRELATION_ID_PROTOCOL.md`).
- **Responsibility:** Owns RFC 9562 UUIDv7 correlation header format specifications, event stream propagation rules, and privacy controls.

### 3.3 Overseer (QA, Validation & Release Readiness Specialist)
- **Canonical Contract:** `OrchestraPhaseRetrospective` (`docs/governance/PHASE_RETROSPECTIVE_PROTOCOL.md`).
- **Responsibility:** Owns structured phase closeout retrospective schemas, evidence validation rules, and gate evaluation metrics.

### 3.4 The Steward (Business Alignment & Policy Governance Authority)
- **Canonical Contract:** `OrchestraUnitRecord extension` (`docs/project/ORCHESTRA_UNIT_RECORD_EXTENSION.md`).
- **Responsibility:** Owns machine-readable JSON schema extensions embedded inside `ApprovedUnitPlan`, scope path restrictions, and predecessor dependency rules.

### 3.5 Scribe (Documentation & Knowledge Transfer Specialist)
- **Canonical Contract:** `OrchestraStatusProjection` (`docs/project/ORCHESTRA_STATUS_PROJECTION.md`).
- **Responsibility:** Owns read-only status summary formats, state projection JSON schemas, knowledge base alignment, and presentation formats.

### 3.6 Ponytail (Implementation & Navigation Specialist)
- **Canonical Contract:** `OrchestraWorktreeContract` (`docs/project/ORCHESTRA_WORKTREE_CONTRACT.md`).
- **Responsibility:** Owns codebase navigation, targeted file changes, Git worktree operations, path confinement validation, and safe workspace boundaries.

---

## 4. Rejected & Deferred Dispositions

- **Rejected:** Standalone unit state files (`.orchestra/units/`), duplicate manual doctrine packs, workflow-state merge authority, automatic policy mutation, SQLite event stores, RPC network services, background daemons.
- **Deferred (Phase 2 Implementations):** Cross-session correlation restoration, durable correlation persistence, automatic retrospective closeout generation, durable retrospective retention, automatic Steward planning/dispatch integration, revision-history ordering, `DELEGATED_EXECUTION_POLICY.md` Section 4 normative integration.
- **Promoted for Phase 3 Design:** `OrchestraStatusProjection` (Phase 3B target), `OrchestraWorktreeContract` (Phase 3C target).
- **Out of Scope:** `OrchestraProviderContract` (separate unscheduled concept).
