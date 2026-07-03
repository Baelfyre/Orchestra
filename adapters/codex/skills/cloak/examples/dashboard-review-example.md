# Cloak Review

## Scope Reviewed
- Artifact Type: Sales performance dashboard screenshot
- Primary User Goal: Detect underperforming regions this month
- Target User: Regional sales manager
- Review Mode: Dashboard Review
- Evidence Reviewed: Dashboard screenshot

## Review Confidence
Confidence Level: Medium

Reason:
- Primary dashboard available
- Data source, interaction states, and code unavailable

## Scoring Matrix
- Task Completion: 70/100
- Accessibility: 62/100
- Cognitive Load: 78/100
- Discoverability: 72/100
- Visual Hierarchy: 80/100
- Consistency: 82/100
- Maintainability: 74/100
- Responsiveness: 70/100
- Performance: 75/100
- Overall Score: 74/100

## Executive Summary
Regional results are visible, but a truncated bar axis and missing reporting context make comparison unreliable.

## Confirmed Findings
- The revenue bar chart begins at 80,000 without an axis-break indicator.
- Cards say `This month` without a date range or refresh time.

## Assumptions
- The screenshot reflects the default filter state.

## Critical Issues
None confirmed.

## Major Issues
### Bar chart exaggerates regional differences
- Severity: Major
- Principle Applied: Accurate data visualization; Nielsen - match between system and real world
- Finding: The bar chart's quantitative axis does not start at zero and provides no break indicator.
- Impact: Small differences appear materially larger and can distort decisions.
- Recommendation: Start the bar axis at zero or use a dot plot for narrow-range comparison.
- Implementation Notes: Preserve exact value labels and expose chart data in an accessible table.

## Minor Issues
### Reporting period is ambiguous
- Severity: Minor
- Principle Applied: Nielsen - visibility of system status; information architecture
- Finding: `This month` lacks exact dates and freshness information.
- Impact: Users cannot tell whether results are complete or current.
- Recommendation: Show the applied date range and last refresh time near global filters.
- Implementation Notes: Bind both labels to the same query and refresh state as the cards.

## Strengths
- Regions use the same ordering across the chart and table.
- The exception table supports follow-up.

## Quick Wins
- Correct the chart baseline.
- Add date range and freshness labels.

## Long-Term Improvements
- Add drill-down from a regional exception to affected accounts when supported by the workflow.

## Accessibility Notes
Do not rely on red and green alone. Provide keyboard access, data summaries, and a table alternative for charts.

## Information Architecture Notes
Global date and region filters should govern all dependent cards and charts visibly.

## Design Debt
Chart configuration permits misleading baselines; centralize safe quantitative-axis defaults if the pattern recurs.

## Frontend Implementation Notes
Change the chart scale and freshness labels through existing chart and filter configuration.

## Performance Notes
No load timing or query evidence was supplied. Check data-fetch and chart-render timing before optimization.

## Missing Evidence
- Loading, empty, stale, and error states
- Filter behavior
- Accessible chart output
- Query and refresh timing
- Mobile layout

## Final Recommendation
Needs revision before use for operational decisions.
