# Output Formats

## QUICK_UI_HANDOFF

Use for fast UI, layout, component, accessibility, or frontend specialist handoff tasks.

```text
TASK TYPE:
EVIDENCE REVIEWED:
ARTIFACT SOURCES:
UI IMPACT:
USER FLOW:
DESIGN-SYSTEM FINDING:
LAYOUT ISSUE:
ACCESSIBILITY ISSUE:
FORM / VALIDATION REVIEW:
STATE COVERAGE REVIEW:
PERMISSION-STATE REVIEW:
RESPONSIVE RULE:
COMPONENTS AFFECTED:
VISUAL HIERARCHY FIX:
INTERACTION FIX:
BLUEPRINT CLARITY:
SMALLEST SAFE UI CHANGE:
HANDOFF BOUNDARIES:
HANDOFF TO:
```

---

## DOCUMENT_REVIEW

Use when the artifact is README.md, SKILL.md, documentation, Markdown files, usage guides, or other static text documents. Do not use UI component fields for this mode.

```text
ARTIFACT TYPE:
EVIDENCE BASIS:
ARTIFACT REFERENCES:
DOCUMENT GOAL:
TARGET READER:
SCAN HIERARCHY:
DESIGN-SYSTEM EVIDENCE GAP:
SECTION ORDER ISSUE:
INFORMATION DENSITY ISSUE:
NAVIGATION UX:
FORM / VALIDATION FINDING:
STATE COVERAGE GAP:
MISSING SECTION:
COGNITIVE LOAD ISSUE:
ROUTING BOUNDARY ISSUE:
SMALLEST SAFE CHANGE:
HANDOFF TO:
```

---

## FORMAL_UI_AUDIT

Use only when the user explicitly requests a full UI/UX audit, scoring matrix, or detailed review report.

```markdown
# Cloak Review

## Scope Reviewed
- Artifact Type:
- Artifact Sources:
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

## Design-System Evidence Notes

## Form and Validation Notes

## State Coverage Notes

## Routing Boundary Notes

## Design Debt

## Frontend Implementation Notes

## Performance Notes

## Missing Evidence

## Final Recommendation
```

Write `None confirmed` for empty issue sections. State whether the interface is ready, needs revision, or needs major restructuring.
