# Runtime Architecture Boundaries

## Status

This document defines the canonical source-code placement and dependency contract for `orchestra_runtime/`.

The contract is machine-enforced by:

- `machine/architecture/runtime-boundaries.v1.json`
- `scripts/validation/validate_architecture_boundaries.py`
- `tests/behavior/test_architecture_boundaries.py`
- the required `validate` workflow
- the required `Governance Check` workflow

The architecture refoundation uses a strangler migration: existing public import paths remain available through compatibility facades while implementation moves into bounded packages. A compatibility facade is not a location for new behavior.

## Architecture model

Orchestra uses bounded runtime contexts with explicit layered ownership. The package-level dependency direction is:

```text
entrypoints
    |
    v
application  ---> domain
    |             ^
    v             |
  ports <--- infrastructure

bootstrap wires concrete dependencies.
shared is dependency-light and may be consumed by inward layers.
```

The repository-level `adapters/`, `machine/`, `skills/`, `commands/`, `docs/`, `assets/`, `templates/`, and `internal/` trees remain separate from the Python runtime package and keep their existing source-of-truth roles.

## Canonical runtime roots

New runtime implementation must be placed under one of these roots:

```text
orchestra_runtime/
├── domain/
├── application/
├── infrastructure/
├── entrypoints/
├── bootstrap/
├── shared/
└── resources/
```

`adaptive/` and `protocol/` are grandfathered legacy package roots pending bounded migration. Existing flat `orchestra_runtime/*.py` modules are explicitly enumerated in the machine policy and may be migrated incrementally. New flat runtime modules are prohibited unless the architecture policy itself is intentionally reviewed and changed.

## Layer responsibilities

### `domain/`

Owns stable Orchestra semantics, entities, value objects, deterministic policies, lifecycle rules, and pure methods.

Domain code must not depend on:

- concrete infrastructure;
- application orchestration;
- entry points;
- dependency-composition/bootstrap code;
- `internal/` experiment or proof code;
- transport, subprocess, socket, database, or HTTP-client details.

Domain methods are deterministic algorithms or policies. A global `methods/` dumping ground is not permitted; methods belong under the bounded domain context that owns them.

### `application/`

Owns use cases, workflow coordination, application services, DTOs, and ports.

Recommended substructure:

```text
application/
├── use_cases/
├── services/
├── dto/
└── ports/
    ├── repositories/
    ├── providers/
    ├── hosts/
    ├── evidence/
    ├── registry/
    └── persistence/
```

Application code may depend on domain and shared contracts. It must not import concrete infrastructure implementations.

### `infrastructure/`

Owns concrete external-effect implementations:

```text
infrastructure/
├── persistence/
│   ├── repositories/
│   ├── dpo/
│   ├── stores/
│   ├── mappers/
│   └── serialization/
├── hosts/
├── providers/
├── mcp/
├── registry/
├── git/
├── machine/
└── evidence/
```

Infrastructure implements application ports. It may depend inward on application/domain/shared contracts, but inward layers must not depend back on infrastructure.

### `entrypoints/`

Owns externally initiated runtime interaction surfaces such as CLI, MCP request handling, API-style request translation, and presentation/output adapters.

`entrypoints` is used instead of creating an `interfaces/` package during migration because the historical public module `orchestra_runtime/interfaces.py` is being retained as a compatibility facade for application ports.

### `bootstrap/`

Owns the composition root. Concrete repositories, host adapters, provider implementations, services, and use cases are wired here rather than instantiated inside domain/application code.

### `shared/`

Owns a deliberately small shared kernel such as stable cross-layer errors, IDs, clocks, or typing helpers. Shared code must remain dependency-light and must not become a general `utils/` dumping ground.

### `resources/`

Owns only package resources that are consumed as runtime resources. Canonical machine contracts remain under repository-level `machine/`; branding/static repository assets remain under `assets/`; specialist knowledge remains under `skills/`; command definitions remain under `commands/`.

## DTO, DPO, domain, and persistence separation

### Domain objects

Domain objects represent Orchestra semantics and may contain domain behavior.

### DTOs

DTOs cross application or external boundaries and belong under:

```text
orchestra_runtime/application/dto/
```

DTOs carry data. They must not become hidden business-rule containers.

### DPOs

Data Persistence Objects belong only under:

```text
orchestra_runtime/infrastructure/persistence/dpo/
```

DPOs model persistence representation. They must not leak into domain/application contracts. Mapping between domain objects and persistence representation belongs under infrastructure persistence mappers.

### Repositories

Repository contracts belong under:

```text
orchestra_runtime/application/ports/repositories/
```

Concrete persistence implementations belong under:

```text
orchestra_runtime/infrastructure/persistence/repositories/
```

## Repository-level resource boundaries

The following repository roots are intentionally not collapsed into `orchestra_runtime/resources/`:

- `machine/` — canonical machine-readable policy, contracts, evidence, indexes, schemas, and projections;
- `skills/` — specialist knowledge and behavior source;
- `commands/` — user-visible command definitions;
- `adapters/` — host/package projections and integration packaging;
- `docs/` — human-readable maintained documentation;
- `assets/` — visual/static repository assets;
- `templates/` — repository templates;
- `internal/` — experiments, proofs, research, and tooling not owned by production runtime.

Production `orchestra_runtime/` code must not import from repository-level `internal/`.

## Compatibility facade rule

A migrated historical module may remain at its old import path only as a compatibility facade.

A facade:

- contains the `ARCHITECTURE_COMPATIBILITY_FACADE` marker;
- re-exports canonical symbols;
- defines no classes, functions, lambdas, or business behavior;
- must not be used as the location for new implementation.

Current migrated facades:

| Historical path | Canonical implementation |
|---|---|
| `orchestra_runtime/correlation.py` | `orchestra_runtime/domain/context/correlation.py` |
| `orchestra_runtime/errors.py` | `orchestra_runtime/shared/errors.py` |
| `orchestra_runtime/interfaces.py` | `orchestra_runtime/application/ports/runtime.py` |
| `orchestra_runtime/repositories.py` | `orchestra_runtime/infrastructure/persistence/repositories/` |

## Automated enforcement

Run locally before proposing runtime structure changes:

```text
python scripts/validation/validate_architecture_boundaries.py
python tests/behavior/test_architecture_boundaries.py
```

The validator fails closed on:

- unapproved new top-level runtime modules or package roots;
- runtime imports from `internal/`;
- inward-layer imports of forbidden outer layers;
- prohibited domain I/O dependencies;
- DTO/DPO/repository classes placed outside their owned boundaries;
- runtime package resources placed outside `resources/`;
- missing or behavior-bearing compatibility facades.

Changing the machine policy to make a violation pass is an architecture-contract change and must be reviewed as such; the policy is not an escape hatch.

## Refactor campaign

The refoundation is intentionally incremental:

1. **AR-0 — inventory and dependency map**: enumerate legacy modules, public imports, runtime/resource roots, and migration ownership.
2. **AR-1 — architecture skeleton and enforcement**: establish canonical roots, machine policy, CI checks, and first safe compatibility migrations.
3. **AR-2 — domain extraction**: authority, lifecycle, capabilities, context, governance policy, workflow contracts, and other pure semantics.
4. **AR-3 — application extraction**: decompose coordination, services, delegation, specialist execution, and pre-execution into use cases/services/ports.
5. **AR-4 — infrastructure extraction**: MCP, providers, hosts, registries, Git/worktrees, serialization, persistence, and evidence implementations.
6. **AR-5 — adaptive normalization**: separate adaptive domain methods, use cases, persistence, and runtime adapters.
7. **AR-6 — resource/internal cleanup**: formalize runtime resources and keep experiments/proofs out of production imports.
8. **AR-7 — test architecture and compatibility**: align tests with domain/application/infrastructure/contract/regression responsibilities while preserving required CI evidence.
9. **AR-8 — facade retirement**: retire a compatibility facade only after repository consumers and supported external imports have migrated.
10. **AR-9 — pre-release requalification**: exact-head cross-platform, governance, runtime, compatibility, coverage, and release-readiness validation before the next version release.

Broad modules such as `coordination.py`, `services.py`, and `worktree.py` must be decomposed by responsibility rather than moved wholesale into a differently named folder.
