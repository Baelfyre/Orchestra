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

## Markdown and Links
- [ ] Heading hierarchy, generated anchors, reference links, images, code fences, lists, and tables render under the target Markdown engine.
- [ ] Relative links resolve from the containing file with correct case and fragments.
- [ ] External links identify authoritative sources and inaccessible targets are marked unverified.

## Traceability
- [ ] Objectives map to requirements, implementation, tests, and readiness evidence.
- [ ] Decisions and changes have stable references where useful.

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
