# Ponytail Review Checklist

Use only the sections relevant to the selected task.

## Baseline and Stack

- [ ] repository and branch confirmed
- [ ] approved baseline/current head confirmed
- [ ] working tree or exact PR diff checked
- [ ] relevant source files and callers inspected
- [ ] language/runtime/framework versions confirmed from repository evidence when syntax depends on them
- [ ] package manager, build system, and test commands discovered rather than assumed
- [ ] generated-source ownership identified when generated files are involved

## Safe Implementation

- [ ] owning specialist contracts are clear and current
- [ ] existing helper/pattern/native capability checked before adding new code or dependencies
- [ ] smallest correct root-cause change identified and applied
- [ ] public contracts preserved unless an accepted change requires modification
- [ ] unrelated files and formatting churn avoided
- [ ] generated/runtime/cache folders avoided unless explicitly in scope
- [ ] trust-boundary validation, security, accessibility, and data-integrity requirements preserved
- [ ] new architecture, persistence, security, UI/UX, or QA decisions rerouted instead of guessed

## Validation

- [ ] narrow changed-surface check executed where applicable
- [ ] focused regression coverage added or updated for non-trivial changed behavior where the repository has an applicable test path
- [ ] repository-required validation gate run against the exact current state before transition
- [ ] exact commands and results recorded
- [ ] any post-validation source change caused affected checks to rerun
- [ ] final diff reviewed for accidental edits, debug output, placeholders, temporary files, generated drift, and secrets

## Handoff and Transition

- [ ] behavioral handoff delta produced for material multi-domain work
- [ ] changed paths and affected layers recorded
- [ ] potential contract invalidations and specialist re-entry recorded
- [ ] generated artifacts identified
- [ ] no readiness claim exceeds executed evidence
- [ ] staging, commit, push, PR, merge, release, deployment, or protected-state changes occur only under their required authority
