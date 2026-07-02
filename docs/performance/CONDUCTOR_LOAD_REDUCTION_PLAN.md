# Conductor Load Reduction Plan

## Purpose
Create a safe reduction plan for the Conductor skill payload based on prompt load metrics, aiming to decrease the token footprint of `skills/conductor/SKILL.md` while preserving critical governance behavior and routing rules.

## Scope
This plan covers documentation and structural changes to `skills/conductor/SKILL.md` only. It focuses on removing duplicated explanatory text and relying on canonical routing and policy documents, without altering runtime routing logic or weakening governance.

## Current Measurement
According to `scripts/measure_prompt_load.py`, the `skills/conductor/SKILL.md` currently stands at:
- Lines: 77
- Words: 779
- Chars: 6258
- Estimated Tokens: 1564

## Why Conductor Is Still Large
Conductor is still the largest file in Group A because it carries the burden of explicitly defining routing gates, governance safety constraints, multi-stage workflow preservation, and specific escalation paths. Much of this text duplicates definitions now formally housed in standalone routing policy documents in order to guarantee strict adherence by the agent.

## Behavior-Test Required Text
The following phrases must remain perfectly intact as they are validated by `tests/behavior/governance-conformance-fixtures.json`:
- `Steward.*BLOCKED.*stops` or `halts`
- `Governor.*BLOCKED.*stops` or `halts`
- `human_review_required.*true.*pauses`
- `APPROVED.*proceeds`
- `NOT_APPLICABLE.*proceeds`
- `classify.*SPECIALIST_REROUTE_REQUIRED.*must not allow a specialist to execute outside`
- `Cloak Workflow Preservation.*multi-stage design workflow`
- `must not route data-aware, auth-aware, API-backed, payment, integration, storage, or compliance-sensitive frontend work directly from \`cloak\` to \`ponytail\``
- `Route to \`clockwork\` before implementation when the frontend design affects API shape, data flow, service boundaries, backend validation, auth boundary placement, or architectural layering`
- `Route to \`cipher\` before implementation when the frontend design affects authorization, privacy, destructive actions, secrets, security-sensitive workflows, payments, or compliance-sensitive user journeys`
- `Route to \`chronicler\` before implementation when the frontend design affects persistence, schema, migrations, reporting data, ORM behavior, or stored records`

## Governance-Required Text
- Destructive Action Controls
- Arbiter Continuity Gate requirements
- Workspace Boundary Gates
- Audit Mode / No-Edit Gates

## Router-First Required Text
- The Router First Principle definition
- The Default Execution Flow sequence (Intake & Intent, Mode Selection, Context Selection, Skill Selection, Governance Escalation, Execution Routing)

## Duplication Candidates
- **Execution Modes**: The definitions for FAST, STANDARD, GOVERNED, AUDIT, and DESTRUCTIVE modes, as well as the Escalation Behavior rules, duplicate what is comprehensively defined in `docs/routing/EXECUTION_MODES_POLICY.md`.

## Unsafe Removals
- It is absolutely unsafe to remove or alter the wording of any rule tracked by `governance-conformance-fixtures.json`.
- Removing the core step-by-step Execution Flow is unsafe as it anchors the Conductor's procedural logic.

## Safe Reference Candidates
- Explanatory detail surrounding Execution Modes and Escalation Behavior can be reduced to simple canonical references pointing to `docs/routing/EXECUTION_MODES_POLICY.md`.

## Proposed Reduction Strategy
1. **Target Duplications**: Strip the verbose "Execution Modes" and "Escalation Behavior" sections from `SKILL.md`.
2. **Implement Canonical Pointers**: Replace the removed sections with strict pointers to `docs/routing/EXECUTION_MODES_POLICY.md`.
3. **Preserve Exact Phrasing**: Ensure all rules listed in the "Behavior-Test Required Text" and "Governance-Required Text" remain character-for-character identical in `SKILL.md`.
4. **Consolidate Safety Constraints**: Merge and tighten the phrasing around remaining governance rules without triggering regex failures in the test suite.

## Target Outcome
- Reduce Conductor line count and character count by approximately 15-25%.
- Preserve all required regex-compatible phrases to pass governance conformance.
- Move explanatory detail into canonical docs only when it is safe to reference them.

## Validation Plan
Once the implementation phase begins, the following validation sequence will be required:
1. Run `python scripts/measure_prompt_load.py` to confirm payload size reduction.
2. Run `python tests/behavior/evaluate_governance.py` to ensure behavioral conformance phrases are fully intact.
3. Run `python tests/behavior/run_tests.py` to verify no regressions in guardrail routing.
4. Run `python scripts/validate_manifest.py` for metadata parity.
5. Run `python scripts/governance_check.py --strict` to ensure policy compliance.

## Non-Goals
- Changing Conductor's actual runtime execution behavior.
- Altering `plugin.json` or skill frontmatter.
- Weakening governance behavior or removing required compliance checks.

## Canonical References
- `docs/routing/EXECUTION_MODES_POLICY.md`
- `docs/routing/CONTEXT_RETRIEVAL_RULES.md`
- `docs/routing/MINIMAL_PROMPT_FORMAT.md`
- `tests/behavior/governance-conformance-fixtures.json`

## Plan Result
CONDUCTOR_LOAD_REDUCTION_PLAN_DEFINED
