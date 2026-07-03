# Prompt Load Threshold Checker

## Purpose
This document describes the Prompt Load Threshold Checker (`scripts/check_prompt_load_thresholds.py`), which automates the validation of contextual prompt payloads against the established soft thresholds.

## Scope
The checker targets the exact same files and grouping logic defined in `measure_prompt_load.py`, isolating Core Router-First Context (Group A) from secondary governance and documentation groups.

## Dry-Run Mode
Currently, the checker operates exclusively in **dry-run/report-only mode**. It will always exit with a successful `0` status code, even if multiple thresholds are exceeded. This ensures that CI is not arbitrarily broken while the team calibrates baseline stability.

## What It Checks
- **Group A (Core Context)**: Total token approximation against a soft limit.
- **Grand Total**: Total token approximation across all defined groups against a global soft limit.
- **Group A Growth Rate**: Verifies that Group A has not expanded by more than 10% over the recorded baseline.
- **Conductor Growth Rate**: Verifies that the Conductor skill payload has not expanded by more than 15% over its recorded baseline.

## Threshold Sources
All limits, watch triggers, and review conditions are defined in `PROMPT_LOAD_THRESHOLD_POLICY.md`.

## Status Levels
The script outputs one of the following statuses for each check:
- `[PASS]`: The metric is healthy and below all warning triggers.
- `[WATCH]`: A growth trigger (e.g., >10%) has been breached. Maintainers should be aware.
- `[REVIEW]`: A significant component (like Conductor) has grown beyond healthy bounds. Maintainers should review and refactor.
- `[EXCEEDED]`: A documented soft limit has been surpassed.

## How to Run
```bash
python scripts/check_prompt_load_thresholds.py
```

## Expected Output
The script prints the current metrics compared to the limits, followed by a clear status report for Group A, Grand Total, and the Conductor skill.

## CI Usage
This script is executed automatically during the GitHub Actions governance workflow (`governance-check.yml`). Its report is saved and published as part of the `governance-validation-report` CI artifact, providing visibility into prompt load degradation over time. For details on accessing and interpreting this artifact, see the [CI Artifact Index](../testing/CI_ARTIFACT_INDEX.md).

## Failure Behavior
Because this is a dry-run checker, it will **not** block pull requests or fail CI runs upon threshold breaches.

## Future Enforcement
Once baseline variance is understood over multiple release cycles, this script may be updated to exit with a non-zero code when soft limits are exceeded, converting them into hard CI failures.

## Non-Goals
This checker does not evaluate downstream specialist prompt loads, session history management, or user inputs.

## Checker Result
PROMPT_LOAD_THRESHOLD_CHECKER_DEFINED

## Related Documents
- [Prompt Load Threshold Policy](PROMPT_LOAD_THRESHOLD_POLICY.md)
- [CI Artifact Index](../testing/CI_ARTIFACT_INDEX.md)
