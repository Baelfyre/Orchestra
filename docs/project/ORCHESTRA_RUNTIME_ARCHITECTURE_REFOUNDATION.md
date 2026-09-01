# Orchestra Runtime Architecture Refoundation

## Status

`AR-0/AR-1 — ACTIVE / MIGRATION-AWARE`

This document defines the pre-release runtime architecture refoundation for Orchestra. The refactor is intentionally incremental: existing validated runtime behavior remains compatible while new code is required to enter through explicit architectural boundaries.

## Objectives

1. Organize runtime code by bounded context and architectural responsibility.
2. Separate domain policy, application use cases, infrastructure, interface/transport code, persistence objects, and resources.
3. Prevent new flat runtime modules from accumulating during migration.
4. Preserve public behavior and import compatibility while modules move.
5. Keep `machine/`, `skills/`, `commands/`, `adapters/`, `assets/`, `docs/`, and `internal/` as distinct repository zones with explicit ownership.
6. Make architecture placement mechanically testable rather than convention-only.

## Target Runtime Structure

```text
orchestra_runtime/
├── domain/
│   ├── governance/
│   ├── orchestration/
│   ├── execution/
│   ├── context/
│   ├── adaptive/
│   ├── capabilities/
│   ├── registry/
│   └── evaluation/
├── application/
│   ├── use_cases/
│   ├── services/
│   ├── dto/
│   └── ports/
├── infrastructure/
│   ├── persistence/
│   │   ├── repositories/
│   │   ├── dpo/
│   │   ├── mappers/
│   │   ├── stores/
│   │   └── serialization/
│   ├── hosts/
│   ├── providers/
│   ├── mcp/
│   ├── registry/
│   ├── git/
│   ├── machine/
│   └── evidence/
├── interfaces/
│   ├── cli/
│   ├── mcp/
│   ├── api/
│   └── presentation/
├── bootstrap/
├── resources/
├── shared/
└── __init__.py
```

## Dependency Direction

The permitted architectural direction is inward:

```text
interfaces -> application -> domain
                    ^
                    |
infrastructure -> ports/domain
```

Rules:

- `domain` must not import application, infrastructure, interfaces, or repository `internal/` code.
- `application` may depend on domain and application ports, but not concrete infrastructure.
- `infrastructure` implements ports and may depend inward on application/domain contracts.
- `interfaces` translate external interaction into application requests/use cases.
- production runtime code must not import from repository `internal/`.
- runtime composition occurs under `bootstrap/` rather than through hidden concrete construction inside domain/application modules.

## Bounded Contexts

Initial runtime contexts are:

- governance — authority, admission, pre-execution gates, remediation;
- orchestration — coordination, task lifecycle, specialist routing and handoff;
- execution — specialist/delegated execution and execution state;
- context — context state, compilation, correlation, communication budgets;
- adaptive — observations, profiles, memory, ranking, selection and shadow evaluation;
- providers — provider qualification/execution contracts and implementations;
- registry — capability/registry consumption and projections;
- evaluation — benchmark, evidence, testing, retrospective and readiness evaluation.

Context ownership should be preferred over global technical buckets. A global `methods/`, `models/`, or `services/` dumping ground is prohibited.

## Methods

A `methods/` package is allowed only beneath the bounded domain context it serves. It is for deterministic algorithms or strategies with little or no I/O. Filesystem, network, MCP, Git, provider and persistence operations belong to infrastructure.

## DTO / DPO / Domain Object Rules

- Domain entities/value objects carry Orchestra semantics and domain invariants.
- DTOs are boundary-transfer objects and live under `application/dto/`; DTOs do not own business rules.
- DPOs are persistence representations and live under `infrastructure/persistence/dpo/`; DPOs do not cross the infrastructure boundary.
- Domain-to-DPO conversion occurs through persistence mappers.
- Repository interfaces live under `application/ports/repositories/`; concrete implementations live under `infrastructure/persistence/repositories/`.

## Repository Resource Zones

- `machine/` — canonical machine-readable contracts, schemas, governance, provenance and evidence. It remains outside runtime resources.
- `assets/` — static visual/branding assets.
- `docs/` — human-readable documentation and plans.
- `skills/` — specialist source instructions; not hidden application logic.
- `commands/` — command surfaces that delegate to application/runtime boundaries.
- `adapters/` — host/distribution projections. Runtime Python integrations belong in infrastructure.
- `internal/` — experiments, proofs and research. Production runtime must never depend on it.
- `orchestra_runtime/resources/` — only package resources actually consumed at runtime and not already canonical under `machine/`.

## Compatibility Strategy

Refactoring uses a strangler migration:

1. establish new packages and dependency rules;
2. move one coherent ownership slice at a time;
3. retain legacy modules as thin compatibility facades where public imports require them;
4. migrate internal callers;
5. prove behavior and import compatibility;
6. retire facades only after consumers and tests have migrated.

No broad rewrite is implied by this plan.

## Refactor Campaign

### AR-0 — Inventory and Dependency Baseline

Capture current modules, imports, public entry points, machine/resource dependencies, test ownership, and migration matrix. No behavior changes.

### AR-1 — Boundary Skeleton and Enforcement

Create canonical package boundaries and enforce new-file/dependency placement. Existing flat modules are migration allowlisted; new flat modules are rejected.

### AR-2 — Domain Extraction

Extract pure authority, governance, lifecycle, capability, context, workflow and policy semantics. Preserve compatibility facades.

### AR-3 — Application / Use-Case Extraction

Decompose coordination, services, delegation, specialist execution and preexecution into focused use cases/services.

### AR-4 — Infrastructure Extraction

Move MCP, provider, host, registry, Git/worktree, serialization, repository and persistence implementations outward.

### AR-5 — Adaptive Normalization

Refactor adaptive code into domain/application/persistence/method boundaries without changing advisory semantics.

### AR-6 — Resource and Internal Cleanup

Formalize machine/assets/resources/internal ownership and eliminate production dependencies on experimental/proof code.

### AR-7 — Test Architecture and Compatibility

Add unit, integration, contract and architecture validation while retaining existing behavior/regression coverage during migration.

### AR-8 — Compatibility-Facade Retirement

Remove only facades proven unused by repository and supported external surfaces.

### AR-9 — Pre-release Requalification

Run full governed qualification on the final architecture candidate before release freeze.

## Future Development Placement Gate

Every new runtime file or feature must answer these questions before implementation:

1. Which bounded context owns the behavior?
2. Is the code domain policy, an application use case/service, a port, infrastructure, an interface, a DTO, a DPO, or a runtime resource?
3. What direction do its imports take?
4. Does it introduce mutable state and, if so, who owns it?
5. Does it cross persistence, provider, host, MCP, security, UI, or machine-contract boundaries requiring specialist review?
6. Can it reuse an existing owned abstraction instead of creating another cross-cutting bucket?

A file that cannot be placed confidently must stop at architecture review rather than being added to the flat runtime root.

## Enforcement Source

Machine-readable enforcement is defined by:

`machine/governance/runtime-architecture-boundaries.v1.json`

Executable validation is defined by:

`tests/runtime/test_runtime_architecture_boundaries.py`

During migration, the contract allows the explicitly enumerated legacy flat modules but rejects newly introduced flat Python modules. The allowlist is expected to shrink as AR-2 through AR-8 progress.
