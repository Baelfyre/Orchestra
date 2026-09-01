# Cloak UI Reference Corpus — CUIR-4 Pattern Intelligence Integration

Status: `IMPLEMENTATION_CANDIDATE_PENDING_CANONICALIZATION`

CUIR-4 integrates the canonical CUIR-3 normalized pattern catalog into Cloak through progressive disclosure. The full corpus is not injected into every task.

## Integration model

Cloak first preserves project-native requirements, then classifies the current UI problem into a bounded problem class, retrieves only matching normalized categories, caps the selected set at five patterns, and preserves provenance and reuse classification in the resulting guidance.

The integration has three surfaces:

- `machine/knowledge/cloak-ui-pattern-intelligence-cuir4.v1.json` — deterministic problem-class and category retrieval contract;
- `skills/cloak/CUIR_PATTERN_INTELLIGENCE_GUIDE.md` — specialist progressive-disclosure instructions;
- `scripts/retrieve_cloak_patterns.py` — reproducible helper used by tests and maintainers to inspect the same retrieval policy.

## Authority boundary

Pattern retrieval is advisory. It does not transfer frontend implementation authority from Ponytail, architecture ownership from Clockwork, security ownership from Cipher, or readiness ownership from Overseer. It creates no merge, release, deployment, provider-routing, or policy authority.

## Source and rights boundary

CUIR-4 consumes only the already-canonical CUIR-3 normalized catalog. It performs no new external repository inspection, dependency installation, source copying, asset copying, or external code execution. Existing `REFERENCE_ONLY`, `REUSE_WITH_NOTICE`, and `REUSE_WITH_RIGHTS_REVIEW` distinctions remain unchanged.

## CUIR-5 boundary

CUIR-5 remains not started in this candidate. CUIR-5 will evaluate whether this bounded retrieval mechanism improves measurable task coverage and provenance behavior relative to the no-retrieval baseline.
