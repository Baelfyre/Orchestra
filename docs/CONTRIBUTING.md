# Contributing

- Keep examples fictional, generic, and project-agnostic.
- Exclude private projects, personal data, local paths, credentials, and client details.
- Do not vendor external plugin code or claim unsupported compatibility or compliance.
- Do not add offensive security content or instructions for unauthorized access.
- Before starting a new local development phase or repository-editing session, run `python scripts/preflight_sync_check.py` against `origin/main`. Do not begin edits if the local branch is behind, diverged, dirty, or unverifiable. Ahead-only state may proceed, but the unpublished commits must be reported.
- Preserve specialist ownership, evidence-first findings, progressive disclosure, and local-first safety.
- Preserve Dagger's explicit activation, non-production requirement, approval gate, rollback, cleanup, and stop conditions.
- Update `CHANGELOG.md` for significant source, workflow, governance, documentation, skill, command, or security changes. If a changelog update is intentionally not needed, document why in the implementation report.
- Run the validation scripts before submitting changes.
