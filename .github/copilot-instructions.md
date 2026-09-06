# GitHub Copilot Instructions for Orchestra

When assisting in the Orchestra repository or working with Orchestra-integrated workspaces, adhere strictly to the following architectural, routing, and governance principles:

## 1. Governance and Routing Architecture

1. **Governance Layer**: `The Steward` (business alignment, scope, SDLC) and `The Governor` (legal, compliance, privacy, IP, licensing) sit above the Conductor. The Conductor cannot override governance decisions.
2. **Routing Layer**: `Conductor` is the exclusive router and workflow orchestrator. Do not invent custom subagent chains or bypass the Conductor for complex tasks. Canonical command `/conductor` invokes Conductor for task classification, routing, and specialist orchestration.
3. **Specialist Ownership**: Domain specialists exclusively own their respective domains:
   - `clockwork`: Architecture, OOP, layering, refactoring.
   - `cloak`: UI/UX, accessibility, design patterns.
   - `cipher`: Security, tenant isolation, access control, secrets review.
   - `chronicler`: Data persistence, schema, migrations.
   - `weaver`: Visual modeling, Mermaid/PlantUML diagrams.
   - `scribe`: Documentation, domain narrative, traceability.
   - `overseer`: QA, test strategy, validation, release readiness.
   - `dagger`: Chaos, adversarial, and resilience testing (destructive execution strictly blocked).
   - `arbiter`: Workflow continuity, validation, and transition governance.
   - `the-tuner`: Cross-specialist coordination.
4. **Implementation Layer**: `Ponytail` handles focused implementation, strictly keeping code minimal, reversible, and free of over-engineering. Canonical command `/ponytail` invokes Ponytail for bounded code edits within established architecture.
5. **Simplicity Filter**: `Caveman` ensures the smallest safe change set, avoiding broad refactors during bug fixes.

## 2. Core Invariants

- `CONDUCTOR != PONYTAIL`
- `ROUTING_AUTHORITY != IMPLEMENTATION_AUTHORITY`
- `CUSTOM_AGENT_CAPABILITY != ORCHESTRA_ROUTING_AUTHORITY`
- `HOST != PROVIDER`
- `PROVIDER != SPECIALIST`
- `HOST_IDENTITY != AUTHORITY`
- `HOST_CAPABILITY != EXECUTION_AUTHORITY`
- `PROVIDER_CAPABILITY != PROVIDER_SELECTION_AUTHORITY`
- `AVAILABLE_TOOL != PERMISSION`
- `INSTALL_SUCCESS != SUPPORTED_INTEGRATION`
- `TRANSPORT != WORKFLOW`
- `MODEL_SELECTION != GOVERNANCE`
- `UAI_TRANSPORT_SELECTION != AWF_SPECIALIST_ROUTING`

## 3. Code Modification Rules

1. Inspect relevant files before proposing modifications.
2. Produce targeted, syntax-correct, and codebase-aware changes with minimal diffs.
3. Apply persistent project updates only to Git-tracked repo source paths, not `.agents/` or generated mirrors.
4. Run project validations after changes:
   - `python scripts/governance_check.py --strict`
   - `python scripts/preflight_sync_check.py`
   - `python scripts/validation/validate_architecture_boundaries.py`
5. Do not remove files, rename files, change public APIs, change database schemas, or run destructive commands without explicit user approval.
6. Keep secrets, tokens, credentials, and private data out of code, logs, and prompt artifacts.
