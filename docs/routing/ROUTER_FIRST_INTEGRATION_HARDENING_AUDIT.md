# Router-First Integration Hardening Audit

## Purpose
This document provides a comprehensive audit of the router-first architecture's integration across the Orchestra framework. It reviews documentation consistency, test coverage, prompt-load tracking, and CI artifact generation to identify gaps before concluding Phase 8.

## Scope
This audit covers:
- Core routing documentation (`ROUTER_FIRST_ARCHITECTURE.md`, `CONTEXT_RETRIEVAL_RULES.md`, `EXECUTION_MODES_POLICY.md`)
- Conductor and Skill Index integration
- Router Benchmark definitions and validation runners
- Prompt-load metric extraction and threshold checking
- CI workflow integration and artifact indexing

## Current System Summary
The router-first model is actively operating and validated by a 24-case benchmark fixture. Prompt load metrics are actively generated and checked against soft thresholds during CI runs. The negative validation suite successfully defends the benchmark schema.

## Router-First Components Reviewed

### Conductor Integration
The `conductor` skill implements the dynamic model effectively but currently lacks explicit documentation cross-links to the canonical `ROUTER_FIRST_ARCHITECTURE.md` document.

### Skill Index Integration
`SKILL_INDEX.md` accurately describes the routing behavior but does not cross-link to the underlying routing execution modes or prompt-load policies.

### Routing Map Integration
`ROUTING_MAP.md` is active and successfully guides ambiguous task resolution without full repository context loads.

### Execution Mode Integration
All five execution modes (`FAST`, `STANDARD`, `GOVERNED`, `AUDIT`, `DESTRUCTIVE`) are correctly mapped in documentation and fully covered by the benchmark suite.

### Context Retrieval Integration
`CONTEXT_RETRIEVAL_RULES.md` is clearly defined, and benchmark coverage verifies the boundary between implementation context and governance context.

### Benchmark Fixture Integration
The JSON fixture correctly holds 24 benchmark cases aligned exactly to the `ROUTER_BENCHMARK_FIXTURE_SCHEMA.md`.

### Benchmark Runner Integration
`router_benchmark_runner.py` successfully parses all 24 cases and strictly enforces validation logic in CI.

### Negative Fixture Validation Integration
`test_router_benchmark_fixture_validation.py` actively guards against malformed JSON additions or schema violations.

### Prompt Load Metrics Integration
`measure_prompt_load.py` consistently calculates tokens and context length for reporting.

### Threshold Checker Integration
`check_prompt_load_thresholds.py` compares metrics against the soft targets in `PROMPT_LOAD_THRESHOLD_POLICY.md`. However, it currently operates as a report-only check, lacking a hard CI failure switch.

### CI Artifact Integration
`governance-check.yml` correctly generates and bundles 8 distinct artifact reports (including benchmark, prompt-load, and negative fixture results) as documented in `CI_ARTIFACT_INDEX.md`.

### Governance Preservation Review
Strict deterministic validation gates successfully prevent degradation of the routing logic. Governance check scripts remain intact.

### Documentation Consistency Review
- `README.md` documentation map is missing critical links to Phase 7/8 additions (Routing Architecture, Performance Policies, and Benchmark schemas).
- `ROUTER_FIRST_ARCHITECTURE.md` acts as a documentation island without sufficient outbound links to the benchmark verification strategy or performance metrics.

## Integration Gaps
The audit identified the following gaps:
1. **README Documentation Map**: Missing major Phase 7 and Phase 8 routing/performance references.
2. **Missing Cross-Links**: `SKILL_INDEX.md`, `skills/conductor/SKILL.md`, and `ROUTER_FIRST_ARCHITECTURE.md` are insufficiently linked, creating fragmented canonical sources.
3. **Threshold CI Enforcement**: Prompt load thresholds are reported in CI artifacts but there is no mechanism to explicitly fail a build on extreme context bloat, making the check advisory only.
4. **Terminology**: Minor duplicate terminology exists across earlier routing docs that should be standardized around "router-first architecture".

## Recommended Hardening Actions
To close these gaps in Phase 8B, the following actions are recommended:
1. Update `README.md` to include a new section in the Documentation Map for **Routing & Performance**.
2. Add explicit cross-links connecting `ROUTER_FIRST_ARCHITECTURE.md` to `SKILL_INDEX.md` and `PROMPT_LOAD_METRICS.md`.
3. Add explicit cross-links connecting `skills/conductor/SKILL.md` to the core routing architecture docs.
4. Introduce a `--strict` flag (or similar mechanism) to `check_prompt_load_thresholds.py` to enable formal CI failure on prompt-load boundary violations.
5. Standardize terminology across `MINIMAL_PROMPT_FORMAT.md` and `EXECUTION_MODES_POLICY.md`.

## Phase 8 Completion Criteria
- [x] Phase 8A: Hardening Audit completed and gaps identified.
- [ ] Phase 8B: Recommended hardening actions applied and verified.

## Audit Result
ROUTER_FIRST_INTEGRATION_HARDENING_AUDIT_DEFINED

## Related Documents
- [Router-First Architecture](ROUTER_FIRST_ARCHITECTURE.md)
- [Context Retrieval Rules](CONTEXT_RETRIEVAL_RULES.md)
- [Prompt Load Metrics](../performance/PROMPT_LOAD_METRICS.md)
- [CI Artifact Index](../testing/CI_ARTIFACT_INDEX.md)
