# Orchestra Routing Map

This file provides a lightweight, scanner-friendly map of common tasks to the correct specialist skill. Load this file when routing is unclear or when multi-skill coordination is required.

## Routing Map Flow

All requests pass through the following routing sequence:

```text
Request
  ->
Intent Classification (Determine user objective)
  ->
Mode Selection (Select: Ideation, Prototype, Implementation, Audit, Release)
  ->
Need-Based Governance (Dynamic checks by The Steward & The Governor when applicable)
  ->
Continuity Gate (Arbiter when transition, validation, branch, source-of-truth, or handoff risk exists)
  ->
Conductor or Specialist Routing (Route task to destination skill)
```

If either governance authority returns `BLOCKED`, the Conductor stops. If `human_review_required: true` is flagged, the Conductor pauses until human review completes. In `Ideation` or `Prototype` modes, governance returns `ADVISORY_ONLY` or `NOT_APPLICABLE` and does not block orchestration.

If Arbiter returns `HOLD` or `BLOCKED`, the Conductor pauses continuation, merge, handoff, or context switch until the required validation, context, or remediation is complete.

## Routing Rules

| Task Type | Target Skill | Condition |
|-----------|--------------|-----------|
| Business alignment, scope, requirements review | `the-steward` | Validating project direction or SDLC |
| Legal, compliance, privacy, IP, licensing review | `the-governor` | Validating compliance or legal risk |
| Continuity, handoff, merge readiness, branch divergence, source-of-truth review | `arbiter` | Transition, validation, or continuation safety is uncertain |
| UI/UX review, accessibility, frontend layout | `cloak` | Reviewing user-facing visible layers |
| README, documentation, final submission | `scribe` | Source evidence is available to verify claims. **Fallback**: if source evidence is unavailable, Scribe must stop, report the missing evidence, and return control to the Conductor. It must not generate speculative documentation. |
| SQL, schemas, database testing, migrations | `chronicler` | Analyzing data layers or database relationships |
| QA, release readiness, test cases, defects | `overseer` | Normal quality assurance |
| Security, privacy, RBAC, defensive review | `cipher` | Evaluating defensive posture |
| UML, ERD visuals, architecture workflows | `weaver` | Creating or reviewing system models |
| OOP, SOLID, code structure, architecture, refactoring | `clockwork` | Reviewing architecture, layering, or object-oriented design |
| Gated resilience or negative testing | `dagger` | Requires explicit approval and safe environment |
| Broad, unclear, or multi-skill tasks | `conductor` | When ownership overlaps or dependencies exist |

## Conductor Authority

`conductor` retains routing authority for complex requests, subject to governance and continuity gates. The Conductor will evaluate the project constraints and select the smallest effective skill stack from this map. The Conductor **cannot override** governance decisions from The Steward, The Governor, or Arbiter.

## Conflict Resolution

- Assign one owner per output and sequence dependencies.
- Prefer `overseer` for normal QA and `cipher` for normal security/privacy review.
- Use `dagger` only after its safety gate and never as the default QA, security, database, or UI reviewer.
- For ERDs, use `chronicler` for database semantics and `weaver` for visual notation.
- Do not load or route specialists whose output is not required.

## Legacy Routing Aliases

The Conductor maintains backwards compatibility with legacy multi-word routing keys during transitions. The following aliases are automatically resolved to the new clean slugs using the central registry:

| Legacy Key | Resolved Slug |
|------------|---------------|
| `amalgam-conductor` | `conductor` |
| `cloak-meister` | `cloak` |
| `scribe-meister` | `scribe` |
| `clockwork-meister` | `clockwork` |
| `meister-chronicler` | `chronicler` |
| `acme-overseer` | `overseer` |
| `hidden-dagger` | `dagger` |
| `cipher-meister` | `cipher` |
| `meister-weaver` | `weaver` |
