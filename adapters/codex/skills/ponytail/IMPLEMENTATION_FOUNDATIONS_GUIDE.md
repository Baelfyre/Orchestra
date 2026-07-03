# Implementation Foundations Guide

## Safe Code-Change Principles

- **Inspect before editing**: Always read the target files and relevant dependencies before applying changes.
- **Identify source of truth**: Ensure you are editing the correct Git-tracked file before making changes.
- **Preserve user intent and approved specialist decisions**: Do not silently override architectural, security, database, or UI decisions made by the user or other specialists.
- **Make the smallest safe code change**: Fix the specific issue without rewriting adjacent logic.
- **Avoid broad rewrites without approval**: Stick to targeted edits unless a broader refactor was explicitly requested and approved.
- **Avoid unrelated formatting churn**: Do not reformat code or change spacing in areas you are not directly editing.
- **Avoid modifying runtime/generated folders**: Do not edit `.agents/`, `node_modules/`, `build/`, `dist/`, or similar directories unless explicitly required.
- **Isolate changes to approved files**: Only modify the files directly relevant to the task.
- **Keep source changes in Git-tracked source files**: Ensure all persistent updates are applied to the primary repository.
- **Maintain existing conventions and naming patterns**: Follow the established style of the project.
- **Preserve public APIs unless change is approved**: Do not break existing API contracts without explicit permission.
- **Avoid hidden behavior changes**: Keep logic transparent.
- **Avoid swallowing exceptions silently**: Do not catch exceptions without handling or logging them properly.
- **Avoid adding placeholder logic as final implementation**: Implement real logic unless a placeholder is explicitly requested.
- **Avoid hardcoded secrets, credentials, tokens, or private paths**: Ensure secrets are passed via environment variables or secure configuration.
- **Avoid destructive commands or data mutation unless explicitly approved**: Do not drop tables, delete files, or truncate data unless instructed.

## Validation and Workflow
- **Check branch and git status before editing**: Know your working state.
- **Review diff before commit**: Ensure your changes match the requested scope.
- **Validate after edits**: Run the necessary tests, linters, or build commands to verify your work.
- **Stop before stage/commit/push unless explicitly approved**: Never assume approval for source control operations.
