# Amalgamatic Orchestra Routing Map

This file provides a lightweight, scanner-friendly map of common tasks to the correct specialist skill. Load this file when routing is unclear or when multi-skill coordination is required.

## Routing Map Flow

All requests pass through the following routing sequence:

```text
Request
  ↓
Intent Classification (Determine user objective)
  ↓
Mode Selection (Select: Ideation, Prototype, Implementation, Audit, Release)
  ↓
Need-Based Governance (Dynamic checks by The Steward & The Governor when applicable)
  ↓
Conductor or Specialist Routing (Route task to destination skill)
```

If either governance authority returns `BLOCKED`, the Conductor stops. If `human_review_required: true` is flagged, the Conductor pauses until human review completes. In `Ideation` or `Prototype` modes, governance returns `ADVISORY_ONLY` or `NOT_APPLICABLE` and does not block orchestration.

## Routing Rules

| Task Type | Target Skill | Condition |
|-----------|--------------|-----------|
| Business alignment, scope, requirements review | `the-steward` | Validating project direction or SDLC |
| Legal, compliance, privacy, IP, licensing review | `the-governor` | Validating compliance or legal risk |
| UI/UX review, accessibility, frontend layout | `cloak-meister` | Reviewing user-facing visible layers |
| README, documentation, final submission | `scribe-meister` | Source evidence is available to verify claims. **Fallback**: if source evidence is unavailable, Scribe Meister must stop, report the missing evidence, and return control to the Conductor. It must not generate speculative documentation. |
| SQL, schemas, database testing, migrations | `meister-chronicler` | Analyzing data layers or database relationships |
| QA, release readiness, test cases, defects | `acme-overseer` | Normal quality assurance |
| Security, privacy, RBAC, defensive review | `cipher-meister` | Evaluating defensive posture |
| UML, ERD visuals, architecture workflows | `meister-weaver` | Creating or reviewing system models |
| OOP, SOLID, code structure, architecture, refactoring | `clockwork-meister` | Reviewing architecture, layering, or object-oriented design |
| Gated resilience or negative testing | `hidden-dagger` | Requires explicit approval and safe environment |
| Broad, unclear, or multi-skill tasks | `amalgam-conductor` | When ownership overlaps or dependencies exist |

## Conductor Authority

`amalgam-conductor` retains routing authority for complex requests, subject to governance gates. The Conductor will evaluate the project constraints and select the smallest effective skill stack from this map. The Conductor **cannot override** governance decisions from The Steward or The Governor.

## Conflict Resolution

- Assign one owner per output and sequence dependencies.
- Prefer `acme-overseer` for normal QA and `cipher-meister` for normal security/privacy review.
- Use `hidden-dagger` only after its safety gate and never as the default QA, security, database, or UI reviewer.
- For ERDs, use `meister-chronicler` for database semantics and `meister-weaver` for visual notation.
- Do not load or route specialists whose output is not required.
