# Output Formats

## Caveman

```markdown
# Cipher Quick Risk Review

## Objective
-

## Evidence Reviewed
-

## Confirmed Findings
1. **[severity] finding**
   - Evidence:
   - Boundary/control gap:
   - Impact:
   - Confidence:
   - Optional mapping: CWE / ASVS versioned ID / OWASP API / RFC
   - Remediation owner:

## Missing Evidence
-

## Defensive Next Action
-
```

Use optional standards/taxonomy mapping only when supported by evidence.

## Full Security Review

```markdown
# Cipher Security and Privacy Review

## Scope
- Project:
- Objective:
- Review mode:
- Evidence reviewed:

## Confidence
- Overall:
- Material missing evidence:

## Executive Summary

## Assets and Trust Boundaries

## Confirmed Strengths

## Findings

### Finding CIPHER-001
- Status: Confirmed / Needs verification / Hardening / False positive
- Severity:
- Confidence:
- Evidence:
- Security objective:
- Trust boundary:
- Technical impact:
- Existing safeguards:
- Optional weakness/standard mapping:
- Remediation boundary:
- Implementation owner:
- Verification handoff:

## Authentication / Session / OAuth Notes

## Authorization / RBAC / Tenant Notes

## Web and API Notes

## Secrets / Cryptography Notes

## Dependency and Security-Tool Notes

## Logging / Auditability Notes

## Technical Privacy-Exposure Notes

## Threat / Abuse-Case Notes

## Missing Evidence

## Prioritized Defensive Actions

## Specialist Handoffs

## Final Recommendation
```

### Finding Rules

- A scanner result is not automatically a confirmed finding.
- Severity and confidence are separate.
- CWE/ASVS/OWASP/RFC mappings are contextual, not proof.
- Do not include exploit payloads or secret values.
- Route implementation and validation ownership rather than absorbing them into Cipher.