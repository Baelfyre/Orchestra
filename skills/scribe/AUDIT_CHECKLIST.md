# Documentation Audit Checklist

## Objective Alignment
- [ ] Project objective is explicit, current, and supported by each major section.
- [ ] Scope and limitations are stated.

## Audience Alignment
- [ ] Intended reader and assumed knowledge are clear.
- [ ] Terminology and detail fit the reader.

## Completeness
- [ ] Required rubric or deliverable sections exist.
- [ ] Missing sections are listed instead of fabricated.

## Technical Accuracy
- [ ] Commands, paths, versions, configuration, features, and architecture match current files.
- [ ] Contradictions with code, diagrams, or database artifacts are identified.

## Evidence Support
- [ ] Technical claims cite current artifacts.
- [ ] Test results identify real commands or evidence.
- [ ] Assumptions and unverified claims are marked.
- [ ] Drift-prone claims record source revision, last-verified date, and effective date when relevant.
- [ ] Implementation evidence is not presented as empirical effectiveness evidence without a qualifying study or evaluation.

## Domain Narrative
- [ ] Domain context, stakeholders, vocabulary, rules, assumptions, constraints, and boundaries are evidence-backed where required.
- [ ] Candidate concepts are clearly distinguished from validated technical entities, classes, aggregates, tables, services, or components.
- [ ] Noun extraction is treated only as a discovery heuristic.
- [ ] Formal architecture, persistence, UML, security, UI, and QA decisions are attributed to the owning specialists.

## Requirements and Traceability
- [ ] Requirements have stable identifiers where traceability is needed.
- [ ] Requirement source and rationale are recorded when material.
- [ ] Acceptance criteria are observable or testable where applicable.
- [ ] Requirements map forward to design/implementation/validation and backward to objectives/problems where evidence exists.
- [ ] `NOT_APPLICABLE` is used rather than fabricating a relationship.
- [ ] Proposed, approved, planned, implemented, validated, deprecated, superseded, missing-evidence, and unresolved states are not conflated.
- [ ] Orphaned requirements, undocumented implementation, and validation gaps are surfaced.

## Documentation-System Reconciliation
- [ ] The active direction is identified when relevant: `SPEC_TO_SYSTEM`, `SYSTEM_TO_DOCS`, or `RECONCILE`.
- [ ] Compared artifacts and exact revisions are identifiable.
- [ ] Documented state and observed state are compared explicitly.
- [ ] `DOC_DRIFT` and `IMPLEMENTATION_DRIFT` are distinguished.
- [ ] Missing documentation, unsupported claims, obsolete models, superseded references, stale research claims, and unresolved conflicts are reported rather than silently repaired.
- [ ] A technical conflict is routed to the correct owner before Scribe rewrites the documented truth.

## Research and Capstone Documentation
- [ ] Institution, course, adviser, panel, journal, or research-office formatting requirements are treated as authoritative for the submission.
- [ ] Generic Orchestra guidance is mapped into, not substituted for, the required institutional template.
- [ ] Research questions, objectives, requirements/capabilities, implementation evidence, evaluation method, results, and claims are traceable where the project requires it.
- [ ] Existing-system documentation distinguishes historical intent, current implementation, validated behavior, and empirical findings.
- [ ] Results, discussion, conclusions, participant data, datasets, citations, and evaluation outcomes are not invented.
- [ ] Planned, implemented, validated, and empirically demonstrated claims remain distinct.

## Markdown and Links
- [ ] Heading hierarchy, generated anchors, reference links, images, code fences, lists, and tables render under the target Markdown engine.
- [ ] Relative links resolve from the containing file with correct case and fragments.
- [ ] External links identify authoritative sources and inaccessible targets are marked unverified.

## Traceability
- [ ] Objectives map to requirements, implementation, tests, and readiness evidence where applicable.
- [ ] Decisions and changes have stable references where useful.
- [ ] Documented claims can be traced backward to qualifying evidence when the claim requires evidence.

## Setup Instructions
- [ ] Prerequisites and supported versions are explicit.
- [ ] Secrets use placeholders.
- [ ] Run, test, build, and troubleshooting steps are ordered and verified.

## Test Evidence
- [ ] Planned, passed, failed, blocked, and skipped checks are distinct.
- [ ] Commands and results are reproducible.

## Known Issues
- [ ] Issues state impact, status, and workaround without minimizing risk.
- [ ] Known failures link to next actions.

## Versioning
- [ ] Current status, version, branch, or release is identifiable when needed.
- [ ] Stale version claims and screenshots are removed or updated.
- [ ] Current, supported-previous, archived, deprecated, and removed content are distinguished.
- [ ] Redirects, canonical URLs, migration guidance, and sunset/effective dates match approved evidence.

## Changelog, ADR, and API Reference
- [ ] Changelog entries describe verified user impact and do not imply an unpublished release.
- [ ] ADR identifiers, status, context, decision, consequences, and supersession links are complete.
- [ ] API operations, parameters, schemas, examples, errors, and authentication references match the exact documented contract revision.

## Diagrams Referenced Correctly
- [ ] Diagram names, links, legends, scope, and current or proposed status match written claims.

## Database Documentation Referenced Correctly
- [ ] Entities, constraints, relationships, and integration notes match schema evidence.

## Final Submission Readiness
- [ ] Rubric items map to evidence.
- [ ] Required files, naming, format, citations, links, and media are correct.
- [ ] Local Codex files, prompts, secrets, and temporary artifacts are excluded.
- [ ] Git status is reviewed before any commit recommendation.
