# Spec Kitty-Derived Orchestra Phase 2 Implementation Plan

## Status
```text
IMPLEMENTATION PLAN
IMPLEMENTATION NOT STARTED
POLICY NOT INTEGRATED
NOT RELEASED
VERDICT: READY_FOR_PHASE_1_AND_2A_DOCUMENTATION_COMMIT_REVIEW
```

## Purpose
This document provides a comprehensive, repository-grounded technical implementation plan for executing the four accepted Phase 1 Spec Kitty-derived design specifications within the Orchestra framework. It establishes implementation touchpoints, validation requirements, subphase sequencing, compatibility guarantees, security controls, and human authorization boundaries for Phase 2B through Phase 2G.

## Scope
- Runtime model definition, serialization, parsing, adapter integration, and test coverage for `OrchestraRuntimeEnvelope` (Phase 2B).
- Generator evaluation, propagation, persistence, and test coverage for `OrchestraCorrelationID` (Phase 2C).
- Generation trigger, model definition, provenance verification, and retention bounds for `OrchestraPhaseRetrospective` (Phase 2D).
- Machine-readable extension integration, validation rules, routing consumption, and policy amendment for `ApprovedUnitPlan` (Phase 2E).
- Consolidated behavior, governance, security, packaging, documentation, and backward-compatibility validation (Phase 2F).
- Maintainer implementation review, commit authorization, post-commit validation, push authorization, and remote verification (Phase 2G).

## Non-Goals
- Executing runtime code edits, test edits, adapter edits, script edits, template edits, or policy amendments during Phase 2A/2A.1.
- Introducing Spec Kitty as a direct PyPI dependency or copying external source code/schemas.
- Creating standalone mutable unit-state files (`.orchestra/units/`).
- Granting runtime execution authority, capability creation, or automatic workflow progression based on envelope, correlation, retrospective, or unit extension fields.
- Bumping repository version numbers or modifying `README.md` claims before implementation completion.

## Accepted Phase 1 Designs
1. **OrchestraRuntimeEnvelope**: Specified in `docs/project/ORCHESTRA_RUNTIME_ENVELOPE.md`. Canonical owner: Clockwork. Standalone UTF-8 JSON result envelope profile across 3 discriminated variants (`EXECUTION_RESULT`, `TRANSITION_DECISION`, `AUDIT_EVENT`).
2. **OrchestraCorrelationID**: Specified in `docs/governance/CORRELATION_ID_PROTOCOL.md`. Canonical owner: Chronicler. RFC 9562 UUIDv7 wire format selected. Generator implementation strategy unresolved; 0 external PyPI dependencies authorized.
3. **OrchestraPhaseRetrospective**: Specified in `docs/governance/PHASE_RETROSPECTIVE_PROTOCOL.md`. Canonical owner: Overseer. Source-backed 16-field closeout evidence artifact (`replacement_effect: none`) with `MIXED_RETENTION_MODEL`.
4. **OrchestraUnitRecord Extension**: Specified in `docs/project/ORCHESTRA_UNIT_RECORD_EXTENSION.md`. Canonical owner: The Steward. Proposed 15-field machine-readable extension to `ApprovedUnitPlan` (11 universally required, 1 conditionally required `allowed_paths`, 3 optional).

## Current Repository Baseline
```text
repository: C:\conductor
branch: design/spec-kitty-derived-contracts
base_HEAD: 317c9449b2c6d264d0e826f229808439f1549ceb
base_origin_main: 317c9449b2c6d264d0e826f229808439f1549ceb
sync_state: aligned (ahead 0, behind 0)
working_tree: dirty by authorized tracked synchronization edits (CHANGELOG.md, DECISION_LOG.md, docs/project/ROADMAP.md), untracked Phase 1 design/handoff artifacts, and Phase 2A/2A.1 planning artifacts
staged_changes: none
```

## Validation Baseline
- **Preflight Sync Check**: `python scripts/preflight_sync_check.py origin/main` -> PASS (Aligned)
- **Deterministic Governance Check**: `python scripts/governance_check.py --strict` -> PASS (0 Errors, 0 Warnings across 9 check groups)
- **Governance Protocol Consistency**: `python scripts/validate_governance_protocol_consistency.py` -> PASS (Exit 0)
- **Routing Contract Validation**: `python scripts/validate_routing_contract.py` -> PASS (Exit 0)
- **Git Diff Formatting**: `git diff --check` -> PASS (Clean formatting)
- **Runtime Coverage Gate**: `python -m pytest tests/runtime --cov=orchestra_runtime --cov-report=term-missing --cov-fail-under=90` -> PASS (276 passed in 6.07s; 93.84% total coverage vs 90% threshold)
- **Canonical Behavior Suite**: `python tests/behavior/run_tests.py` (with `$env:ORCHESTRA_APPROVED_BASE_SHA`) -> PASS (Structure, Manifest, Packaging, Reference, Codex Export, 27/27 Static Behavioral Expectation checks passed)
- **Manifest, Structure & Packaging Validators**: `validate_structure.py`, `validate_manifest.py`, `validate_ide_packaging.py`, `validate_artificer_internal.py`, `validate_artificer_records.py`, `validate_artificer_governance_records.py`, `validate_artificer_pattern_catalog.py`, `validate_prompt_load_budget.py` -> ALL PASS (Exit 0)
- **Reconciled Skipped Test**: `tests/behavior/test_artificer_governance_records.py:500` -> `PERMITTED_PREEXISTING_SKIP` (Temp dir case-sensitivity check on Windows NTFS).

## Supported Runtime Matrix
- **Python Version Baseline**: Minimum supported: Python 3.11. Local environment: `LOCAL_VERIFIED` (Python 3.11.9 on Windows 11 x86_64).
- **Python Runtimes 3.11–3.13**: `DECLARED_SUPPORT_MATRIX` / `CI_VERIFIED`. Standard library `uuid` module lacks native `uuid7()`. 0 external dependencies authorized. Generator implementation strategy remains unresolved for Phase 2C.1 gate.
- **Python Runtime 3.14+**: `DESIGN_TARGET`. Native standard library `uuid.uuid7()` available.
- **Operating Systems**: Windows 10/11 (`LOCAL_VERIFIED`), Linux (`CI_VERIFIED`), macOS (`CI_VERIFIED`).
- **Architectures**: x86_64 (`LOCAL_VERIFIED`), arm64 (`CI_VERIFIED`).
- **Packaging & Installation**: Standard Python package layout (`pyproject.toml` / `setup.py`), zero runtime dependency expansion.

## Runtime and Policy Touchpoint Classification
| Design Contract | Target File Path | Touchpoint Classification | Target Policy Touchpoints | Target Test Touchpoints | Owner |
|---|---|---|---|---|---|
| RuntimeEnvelope | `orchestra_runtime/models.py` | `EXISTING_CANONICAL_FILE` | None (Non-authorizing profile) | `tests/unit/test_runtime_envelope.py` | Clockwork |
| RuntimeEnvelope | `orchestra_runtime/serialization.py` | `PROPOSED_NEW_FILE` | None | `tests/behavior/test_adapter_envelope.py` | Clockwork |
| CorrelationID | `orchestra_runtime/correlation.py` | `PROPOSED_NEW_FILE` | None (Optional header) | `tests/unit/test_correlation_id.py` | Chronicler |
| CorrelationID | `orchestra_runtime/coordination.py` | `EXISTING_CANONICAL_FILE` | None | `tests/behavior/test_correlation_propagation.py` | Chronicler |
| PhaseRetrospective | `orchestra_runtime/retrospective.py` | `PROPOSED_NEW_FILE` | None (Supplementary evidence) | `tests/unit/test_phase_retrospective.py` | Overseer |
| UnitRecord Extension | `orchestra_runtime/models.py` | `EXISTING_CANONICAL_FILE` | `docs/governance/DELEGATED_EXECUTION_POLICY.md` Section 4 (Phase 2E.4 only) | `tests/unit/test_unit_plan_extension.py` | The Steward |
| UnitRecord Extension | `orchestra_runtime/routing.py` | `EXISTING_CANONICAL_FILE` | None | `tests/behavior/test_routing_unit_consumption.py` | Conductor |

## Runtime Envelope Plan
- **Phase 2B.1 (Model & Serialization)**: Define frozen Python dataclasses / Pydantic models for `OrchestraRuntimeEnvelope` across the 3 discriminated variants (`EXECUTION_RESULT`, `TRANSITION_DECISION`, `AUDIT_EVENT`). Implement UTF-8 JSON serializer with strict field validation.
- **Phase 2B.2 (Parser & Negative Tests)**: Implement JSON parser with strict schema validation, version matching (`schema_version: "1.0"`), reason-code transcription, and negative test cases (missing required fields, unknown message types, invalid JSON, secret/prompt leakage rejection).
- **Phase 2B.3 (Adapter Integration)**: Wire envelope serialization into adapter execution outputs (`adapters/codex/`, `adapters/gemini/`) as optional machine-readable output wrapper alongside human-readable text.

## Correlation ID Plan
- **Phase 2C.1 (Generator Strategy Decision Gate)**: Evaluate 4 generator implementation options:
  1. *Option A (Python 3.14 Native)*: Standard library `uuid.uuid7()`. Requires Python 3.14+ runtime.
  2. *Option B (Project-Owned Standard Library Implementation)*: Zero-dependency Python 3.11–3.13 helper using `time.time_ns()` + `os.urandom()`.
  3. *Option C (External PyPI Dependency)*: `uuid6` or `uuid7` PyPI package. (Currently NOT authorized).
  4. *Option D (Feature-Gated / Deferred)*: Generate random UUIDv4 fallback on Python <3.14, native UUIDv7 on Python 3.14+.
- **Phase 2C.2 (Generator & Format Validation)**: Implement chosen generator option with strict RFC 9562 timestamp-first layout, 48-bit millisecond check, version 7 bit assertions, and variant 1 bit assertions.
- **Phase 2C.3 (Propagation & Persistence Tests)**: Test correlation ID header flow across root runs, delegated child runs, retry loops, transition decision records, and audit events.

## Phase Retrospective Plan
- **Phase 2D.1 (Model & Provenance Contract)**: Define 16-field `OrchestraPhaseRetrospective` schema, requiring verified source provenance references, outcome summaries, and neutral execution metrics.
- **Phase 2D.2 (Trigger & Generation Boundary Gate)**: Implement retrospective generation trigger at phase closeout for material multi-unit runs, enforcing `MIXED_RETENTION_MODEL` (sanitized summary in public repo; detailed execution traces in local artifact storage).
- **Phase 2D.3 (Partial & Retention Tests)**: Test retrospective rendering across completed, failed, blocked, cancelled, and timed-out phases.

## Unit Extension Plan
- **Phase 2E.1 (Model & Legacy Plan Parsing)**: Implement 15-field extension schema on `ApprovedUnitPlan` (11 universally required, 1 conditionally required `allowed_paths`, 3 optional). Support backward-compatible parsing of legacy unit plans without extension fields.
- **Phase 2E.2 (Scope & Dependency Validation)**: Enforce scope validation rules (`scope_ref` canonical reference; `allowed_paths` mandatory for `FILE_MUTATION` units; non-file unit classes supported). Validate predecessor dependency acceptance.
- **Phase 2E.3 (Routing Consumption)**: Integrate extended unit records into Conductor routing and Arbiter transition checks.
- **Phase 2E.4 (Policy Amendment Gate)**: Amend `DELEGATED_EXECUTION_POLICY.md` Section 4 only after all runtime models, validators, and tests pass, under explicit maintainer authorization.

## Migration and Compatibility
- **Backward Compatibility**: All legacy records (without envelopes, correlation IDs, retrospectives, or unit extensions) remain valid and readable.
- **Forward Compatibility**: Schema parsers use strict major-version checking (`1.x`) and ignore unknown additive fields in minor revisions.
- **Zero Retroactive Reconstruction**: No existing git history, decision logs, or handoff records will be rewritten or retroactively transformed.

## Test Strategy
- Runtime coverage gate: `tests/runtime` with coverage >= 90% (Current baseline: 93.84%).
- Behavior suite: `python tests/behavior/run_tests.py` (27 static behavioral expectation checks passed).
- Governance & Packaging validators: 8 script validators verified.

## Security and Privacy Gates
- **Secret Redaction**: Zero API keys, authorization tokens, or credentials allowed in envelopes, correlation headers, retrospectives, or unit records.
- **UUIDv7 Timestamp Exposure**: Unix millisecond timestamp in UUIDv7 is accepted as operational correlation metadata; user privacy is preserved by prohibiting PII in correlation payloads.
- **Path Traversal Protection**: All paths in `allowed_paths` and `prohibited_paths` must resolve strictly within workspace boundaries.

## Ownership
- `OrchestraRuntimeEnvelope`: Clockwork (Design & Runtime Model)
- `OrchestraCorrelationID`: Chronicler (Design & Persistence)
- `OrchestraPhaseRetrospective`: Overseer (Design & Validation)
- `OrchestraUnitRecord extension`: The Steward (Design & Policy)
- Routing Integration: Conductor
- Transition Governance: Arbiter

## Implementation Sequence
1. **Phase 2A / 2A.1**: Implementation Planning, Baseline Definition, and Canonical Validation Repair (Current Phase - Planning Only).
2. **Documentation Commit Review Gate**: Maintainer review and single documentation-only commit of Phase 1 design package and Phase 2A/2A.1 planning artifacts.
3. **Phase 2B**: OrchestraRuntimeEnvelope runtime model, serializer, parser, and adapter compatibility tests.
4. **Phase 2C**: OrchestraCorrelationID UUIDv7 generator decision, implementation, propagation, and persistence.
5. **Phase 2D**: OrchestraPhaseRetrospective model, trigger evaluation, renderer, and retention integration.
6. **Phase 2E**: ApprovedUnitPlan extension, schema validation, routing consumption, and policy amendment.
7. **Phase 2F**: Consolidated runtime, behavior, governance, security, packaging, and compatibility validation.
8. **Phase 2G**: Maintainer implementation review, commit authorization, post-commit validation, push authorization, and remote verification.

## Branch, Worktree & Documentation Commit Gate
- Current status: Branch `design/spec-kitty-derived-contracts` contains uncommitted Phase 1 synchronization edits, untracked Phase 1 design specifications, and untracked Phase 2A/2A.1 planning artifacts.
- Proposed documentation commit scope: Single documentation-only commit containing:
  - Tracked modifications: `CHANGELOG.md`, `DECISION_LOG.md`, `docs/project/ROADMAP.md`
  - Untracked Phase 1 design specifications: `docs/project/ORCHESTRA_RUNTIME_ENVELOPE.md`, `docs/governance/CORRELATION_ID_PROTOCOL.md`, `docs/governance/PHASE_RETROSPECTIVE_PROTOCOL.md`, `docs/project/ORCHESTRA_UNIT_RECORD_EXTENSION.md`, `docs/project/SPEC_KITTY_DERIVED_CONTRACT_OWNERSHIP.md`, `docs/project/SPEC_KITTY_DERIVED_UPGRADE_ROADMAP.md`
  - Untracked promotion records & historical handoffs: `docs/artificer/promotions/spec-kitty/*.md`, `docs/artificer/external-sources/SPEC_KITTY_*.md`
  - Untracked Phase 2A/2A.1 planning artifacts: `docs/project/SPEC_KITTY_DERIVED_PHASE_2_IMPLEMENTATION_PLAN.md`, `docs/project/SPEC_KITTY_DERIVED_PHASE_2_COMPATIBILITY_MATRIX.md`, `docs/project/SPEC_KITTY_DERIVED_PHASE_2_MIGRATION_AND_TEST_PLAN.md`, `docs/artificer/external-sources/SPEC_KITTY_PHASE_2A_HANDOFF.md`, `docs/artificer/external-sources/SPEC_KITTY_PHASE_2A1_CORRECTION_HANDOFF.md`
- Implementation branch strategy: Following maintainer documentation commit review and authorization, launch Phase 2B code edits on a clean feature branch `feature/spec-kitty-derived-runtime` or isolated worktree created from the committed baseline.

## Release and Versioning Considerations
- Zero version bump during design (Phase 1) and implementation planning (Phase 2A/2A.1).
- Implementation changes in Phase 2B–2E represent non-breaking additive extensions (minor version candidate for Phase 2G release review).

## Risk Register
1. *Python 3.11 UUIDv7 Generator Constraint*: Mitigated by evaluating project-owned generator vs native Python 3.14+ in Phase 2C.1 before code edits.
2. *Context Drift / Scope Overreach*: Mitigated by strict phase boundaries, zero runtime file edits in Phase 2A/2A.1, and mandatory preflight checks.
3. *Legacy Unit Record Incompatibility*: Mitigated by making unit extension fields optional on legacy schema parsers while requiring them for new unit plans.

## Rollback Strategy
- Every implementation phase (2B through 2E) is bounded by clean git commit checkpoints.
- If a phase fails validation, changes can be cleanly reverted using standard git operations without corrupting prior design specifications.

## Human Authorization Gates
- Maintainer authorization required for Phase 1 & Phase 2A documentation package commit review.
- Maintainer authorization required for Candidate Phase 2B authorization.
- Maintainer authorization required for Phase 2C.1 UUIDv7 generator strategy selection.
- Maintainer authorization required for Phase 2E.4 `DELEGATED_EXECUTION_POLICY.md` policy amendment.
- Maintainer authorization required for Phase 2G commit, push, and release.

## Open Questions (Deferred to Respective Phase Gates)
1. Which UUIDv7 generator implementation strategy (Option A, B, or D) will maintainers approve for Python 3.11–3.13 runtimes during Phase 2C.1? (Deferred to Phase 2C.1 gate).
2. Should `OrchestraPhaseRetrospective` rendering be triggered automatically by Arbiter at phase closeout, or invoked on-demand by Overseer? (Deferred to Phase 2D.1 gate).

## Maintainer Decision Boundary
Phase 2A.1 evidence correction is complete. Maintainers must review the documentation package and decide whether to grant authorization for:
1. Documentation-only commit of the Phase 1 & Phase 2A design and planning package.
2. Authorization of Candidate Phase 2B (OrchestraRuntimeEnvelope Runtime Model & Serialization).
