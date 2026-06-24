# Output Formats

## QUICK_UI_HANDOFF

Use for fast UI, layout, component, accessibility, or frontend specialist handoff tasks.

```text
TASK TYPE:
UI IMPACT:
USER FLOW:
LAYOUT ISSUE:
ACCESSIBILITY ISSUE:
RESPONSIVE RULE:
COMPONENTS AFFECTED:
VISUAL HIERARCHY FIX:
INTERACTION FIX:
SMALLEST SAFE UI CHANGE:
HANDOFF TO:
```

---

## DOCUMENT_REVIEW

Use when the artifact is README.md, SKILL.md, documentation, Markdown files, usage guides, or other static text documents. Do not use UI component fields for this mode.

```text
ARTIFACT TYPE:
DOCUMENT GOAL:
TARGET READER:
SCAN HIERARCHY:
SECTION ORDER ISSUE:
INFORMATION DENSITY ISSUE:
NAVIGATION UX:
MISSING SECTION:
COGNITIVE LOAD ISSUE:
SMALLEST SAFE CHANGE:
HANDOFF TO:
```

---

## FORMAL_UI_AUDIT

Use only when the user explicitly requests a full UI/UX audit, scoring matrix, or detailed review report.

```markdown
# Cloak Meister Review

## Scope Reviewed
- Artifact Type:
- Primary User Goal:
- Target User:
- Review Mode:
- Evidence Reviewed:

## Review Confidence
Confidence Level: High / Medium / Low
Reason:

## Scoring Matrix
- Task Completion: __/100
- Accessibility: __/100
- Cognitive Load: __/100
- Discoverability: __/100
- Visual Hierarchy: __/100
- Consistency: __/100
- Responsiveness: __/100
- Maintainability: __/100
- Performance: __/100
- Overall Score: __/100

## Executive Summary

## Confirmed Findings

## Assumptions

## Critical Issues
### [Issue title]
- Severity:
- Principle Applied:
- Finding:
- Impact:
- Recommendation:
- Implementation Notes:

## Major Issues

## Minor Issues

## Strengths

## Quick Wins

## Long-Term Improvements

## Accessibility Notes

## Information Architecture Notes

## Design Debt

## Frontend Implementation Notes

## Performance Notes

## Missing Evidence

## Final Recommendation
```

Write `None confirmed` for empty issue sections. State whether the interface is ready, needs revision, or needs major restructuring.
