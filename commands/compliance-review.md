---
name: compliance-review
description: "Run governed compliance review using the verified local compliance registry."
---
# Compliance Review Command

1. Run the local registry status/verification path first.
2. Use The Governor for applicability, source-state, legal/regulatory/privacy/licensing/provider-policy governance.
3. Use The Steward to translate applicable obligations into traceable functional requirements, non-functional requirements, acceptance criteria, and required SDLC evidence.
4. Bind review evidence to registry version, release sequence, manifest hash, project facts, and exact project state.
5. Use Arbiter to reject stale or mismatched compliance evidence before continuation or release readiness.

If the local registry is absent, integrity-failed, stale for a material applicable source, or insufficient for the requested jurisdiction/provider, fail closed at Audit/Release boundaries and identify the evidence or human interpretation required. Do not invent missing obligations.
