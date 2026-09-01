# Orchestra Runtime Architecture Refoundation

## Status

`AR-0/AR-1 — VALIDATION-FIRST / MIGRATION-AWARE`

This document defines the pre-v1.8 runtime architecture refoundation for Orchestra. The migration is incremental and compatibility-preserving: existing validated runtime behavior remains intact while new code is mechanically prevented from expanding the current flat runtime structure.

## Objectives

1. Organize runtime code by bounded context and architectural responsibility.
2. Separate domain policy, application use cases, services, ports, infrastructure, persistence objects, entrypoints, composition, and resources.
3. Prevent new flat runtime modules from accumulating during migration.
4. Preserve public behavior and import compatibility while modules move.
5. Keep `machine/`, `skills/`, `commands/`, `adapters/`, `assets/`, `docs/`, and `internal/` as distinct repository zones.
6. Make architectural placement mechanically testable rather than convention-only.

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
├── entrypoints/
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

Permitted direction is inward:

```text
entrypoints -> application -> domain
                    ^
                    |
infrastructure -> ports/domain
```

Rules:

- `domain` must not import application, infrastructure, entrypoints, repository `internal/`, host SDKs, MCP transports, filesystem implementations, or provider implementations.
- `application` may depend on domain and application ports, but not concrete infrastructure.
- `infrastructure` implements ports and may depend inward on application/domain contracts.
- `entrypoints` translate external interaction into application requests/use cases.
- production runtime must not import repository `internal/`.
- runtime composition belongs under `bootstrap/` rather than hidden concrete construction inside domain/application modules.

## Initial Bounded Contexts

- governance — authority, admission, pre-execution gates, remediation;
- orchestration — coordination, task lifecycle, specialist routing and handoff;
- execution — specialist/delegated execution and execution state;
- context — context state, compilation, correlation, communication budgets;
- adaptive — observations, profiles, memory, ranking, selection and shadow evaluation;
- providers — provider qualification/execution contracts and implementations;
- registry — capability/registry consumption and projections;
- evaluation — benchmark, evidence, testing, retrospective and readiness evaluation.

Context ownership is preferred over global technical buckets. New global `methods/`, `models/`, `services/`, `repositories/`, or `utils/` dumping grounds are prohibited.

## Methods

A `methods/` package is valid only beneath the bounded domain context it serves. It is for deterministic algorithms or strategies with little or no I/O. Filesystem, network, MCP, Git, provider and persistence operations belong to infrastructure.

## DTO / DPO / Domain Object Rules

- Domain entities/value objects carry Orchestra semantics and invariants.
- DTOs are boundary-transfer objects under `application/dto/`; DTOs do not own business rules.
- DPOs are persistence representations under `infrastructure/persistence/dpo/`; DPOs do not cross the infrastructure boundary.
- Domain-to-DPO conversion occurs through persistence mappers.
- Repository interfaces belong under `application/ports/repositories/`; concrete implementations belong under `infrastructure/persistence/repositories/`.

## Repository Resource Zones

- `machine/` — canonical machine-readable contracts, schemas, governance, provenance and evidence. It remains outside runtime resources.
- `assets/` — static visual/branding assets.
- `docs/` — human-readable documentation and plans.
- `skills/` — specialist source instructions; not hidden runtime business logic.
- `commands/` — command surfaces that delegate into application/runtime boundaries.
- `adapters/` — host/distribution projections. Executable Python integrations belong under runtime infrastructure.
- `internal/` — experiments, proofs and research. Production runtime must not depend on it.
- `orchestra_runtime/resources/` — only package resources actually consumed at runtime and not already canonical under `machine/`.

## Compatibility Strategy

Use a strangler migration:

1. enforce placement before moving code;
2. create target packages only when the first owned slice moves;
3. move one coherent ownership slice at a time;
4. retain legacy modules as thin compatibility facades where public imports require them;
5. migrate internal callers;
6. prove behavior and import compatibility;
7. shrink the legacy allowlist after every successful migration;
8. retire facades only after consumers and tests have migrated.

## Refactor Campaign

### AR-0 — Inventory and Dependency Baseline

Capture current modules, imports, public entry points, machine/resource dependencies, test ownership, and migration matrix. No behavior changes.

### AR-1 — Placement Guardrails

Introduce executable architecture validation before source movement. Current flat modules are migration-allowlisted; newly introduced flat runtime modules fail validation.

### AR-2 — Domain Extraction

Create the target package skeleton as needed and extract pure authority, governance, lifecycle, capability, context, workflow and policy semantics. Preserve compatibility facades. Update `README.json` machine-index parity in the same PR because runtime paths change.

### AR-3 — Application / Use-Case Extraction

Decompose coordination, services, delegation, specialist execution and preexecution into focused use cases/services.

### AR-4 — Infrastructure Extraction

Move MCP, provider, host, registry, Git/worktree, serialization, repository and persistence implementations outward.

### AR-5 — Adaptive Normalization

Refactor adaptive code into domain/application/persistence/method boundaries without changing advisory semantics.

### AR-6 — Resource and Internal Cleanup

Formalize machine/assets/resources/internal ownership and eliminate production dependencies on experimental/proof code.

### AR-7 — Test Architecture and Compatibility

Add unit, integration, contract and architecture validation while retaining current behavior/regression coverage during migration.

### AR-8 — Compatibility-Facade Retirement

Remove only facades proven unused by repository and supported external surfaces.

### AR-9 — Pre-release Requalification

Run full governed qualification on the final architecture candidate before release freeze.

## Future Development Placement Gate

Every new runtime file or feature must answer before implementation:

1. Which bounded context owns the behavior?
2. Is it domain policy, application use case/service, port, infrastructure, interface, DTO, DPO, composition, or runtime resource?
3. What direction do its imports take?
4. Does it introduce mutable state and, if so, who owns it?
5. Does it cross persistence, provider, host, MCP, security, UI, or machine-contract boundaries requiring specialist review?
6. Can it reuse an existing owned abstraction instead of creating another cross-cutting bucket?

A file that cannot be placed confidently must stop at architecture review rather than being added to the flat runtime root.

## Enforcement

Executable validation lives at:

`tests/runtime/test_runtime_architecture_boundaries.py`

AR-1 deliberately keeps the contract in the test while no runtime structure is changed. When AR-2 creates the first canonical runtime packages, the placement contract may be promoted into `machine/governance/` together with the required `README.json` machine-index update. This sequencing preserves the repository's existing documentation-impact gate rather than bypassing it.
