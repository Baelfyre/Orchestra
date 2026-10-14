# Pre-Development Blueprint Coverage Guide

**Status:** Optional Scribe guidance for material project preparation.
**Authority:** This guide structures evidence and documentation. It does not approve requirements or grant implementation, merge, release, deployment, or governance-transition authority.

## Purpose and core rule

Use this guide when a new or existing software project needs a clear view of its applicable pre-development decisions and their evidence.

The six dimensions below are **coverage areas, not six mandatory files**. Reuse approved or equivalent existing artifacts, and reference one artifact from more than one dimension when its contents support each mapping. A single existing artifact may cover more than one dimension. Do not create duplicate requirements, decisions, approval records, or qualification records to fill the crosswalk.

The crosswalk is a documentation aid. Its presence or apparent completeness does not create a new readiness state or gate, authorize implementation, or replace an existing human decision.

## Select an existing Scribe mode

- **New project: SPEC_TO_SYSTEM.** Structure supplied intent into proposed or approved objectives, requirements, acceptance criteria, and specialist-owned decisions. Preserve each item's actual state and source.
- **Existing project: SYSTEM_TO_DOCS.** Reconstruct what current verified source, configuration, tests, records, and specialist findings support. Keep observed behavior separate from inferred or historical intent.
- **Intent and current evidence disagree: RECONCILE.** Compare the relevant claims, preserve competing evidence, and route unresolved decisions to Conductor and the fact owner.

Do not activate Scribe for documentation-neutral code, test, or evidence work when current documentation remains accurate. Assess material documentation obligations per DOC-L1 and its existing-record boundary.

## Six coverage dimensions and fact owners

| Dimension | Consider when applicable | Fact owner |
| --- | --- | --- |
| PRD — Product Requirements Document | Product goals, stakeholders, scope, requirements, and acceptance criteria | The Steward |
| TRD — Technical Requirements Document | Architecture, selected stack, integration, technical constraints, and runtime boundaries | Clockwork |
| APPLICATION_FLOW — Application Flow | Screens and interactions, transitions, errors, recovery, and workflow sequence | Cloak and Clockwork, for their respective facts |
| DESIGN_BRIEF — Design Brief | Brand, typography, layout, responsive behavior, components, and accessibility expectations | Cloak |
| DATA_SCHEMA — Backend and Data Schema | Entities, contracts, storage, API/data relationships, ownership, and security/privacy requirements | Chronicler and Cipher, for their respective facts |
| IMPLEMENTATION_PLAN — Implementation Plan | Sequence, dependencies, delivery ownership, acceptance/QA evidence, and rollout constraints | Conductor and Overseer, for their respective facts |

Scribe organizes the representation and evidence links. The named fact owners retain authority over their conclusions; specialist review is engaged only for material facts within that specialist's domain.

## Optional coverage crosswalk

Reuse Scribe's existing traceability matrix or another existing task/candidate evidence surface. Create one consolidated view only when it improves review. A practical row contains:

| Field | Record |
| --- | --- |
| Dimension | One of the six stable dimension IDs above |
| DOC-L1 applicability | REQUIRED, CONDITIONAL, NOT_APPLICABLE, or UNRESOLVED, with the trigger or reason |
| Existing equivalent artifacts | Source path or record reference and revision; one artifact may support multiple rows |
| Requirement IDs | Existing project-native requirement identifiers |
| Acceptance-criterion IDs | Existing project-native acceptance identifiers |
| Source / evidence references | Owner, source location, revision, and evidence supporting the claim |
| Authority/status | PROPOSED, APPROVED, IMPLEMENTED, or VALIDATED, as supported by its source |
| Scribe interpretation | Clearly labeled synthesis or inference, separate from source-backed fact |
| Unresolved issue and owner next action | Conflict, missing evidence, decision owner, or the reason no action is required |

Preserve existing requirement and acceptance-criterion identifiers verbatim. Never invent a source, historical approval, owner decision, or evidence link. Bind revision-sensitive claims to the exact repository, commit/tree, record revision, or validation output that supports them.

## DOC-L1 applicability

- REQUIRED: record the material documentation obligation before the existing decision or validation that relies on it.
- CONDITIONAL: Evaluate a CONDITIONAL trigger against the current project scope and evidence; resolve it to REQUIRED or NOT_APPLICABLE when the relevant lifecycle decision is made.
- NOT_APPLICABLE: use only after checking the trigger or obligation. A NOT_APPLICABLE outcome requires a reason in the existing task or evidence surface.
- UNRESOLVED: preserve uncertainty when scope, evidence, or ownership is insufficient; route the question through Conductor to its owner.

Use MISSING_EVIDENCE when required support is absent and UNRESOLVED when evidence, scope, or authority conflicts. Neither state silently becomes NOT_APPLICABLE, APPROVED, or satisfied. DOC-L1 outcomes classify documentation obligations; they do not satisfy another gate by implication.

## Specialist authority and evidence discipline

Every material claim in the crosswalk must make four things legible: its **Source**, the source-supported **Authority** or lifecycle state, any **Scribe interpretation**, and an **Unresolved issue** or owner next action when one exists.

Scribe may analyze completeness, ambiguity, traceability, and drift. It preserves competing claims and evidence, explains the conflict, and routes resolution to the appropriate owner. Conflicting specialist findings remain unresolved until the fact owner or governance authority provides an authorized disposition. Scribe does not choose the winning technical position.

Scribe cannot independently approve product requirements.
Scribe cannot choose or approve system architecture.
Scribe cannot decide database or persistence design.
Scribe cannot approve UI/UX design decisions.
Scribe cannot establish security or privacy controls.
Scribe cannot determine QA sufficiency.
Scribe cannot approve governance transitions.
Scribe cannot promote inferred facts into verified facts.

Never silently promote PROPOSED to APPROVED, PLANNED to IMPLEMENTED, or IMPLEMENTED to VALIDATED. An existing approved artifact may be referenced by multiple dimensions only when its content supports each claim and the relevant fact owners remain attributable.

## Reuse existing lifecycle records

- **Feature Admission:** cite the existing FeatureDecisionRecord or eligible inline rationale for admission evidence and approved requirements. Admission does not itself grant implementation authority.
- **Candidate maturity and freeze:** reference the existing CandidateMaturityRecord for the exact candidate identity, scope, and acceptance evidence.
- **Qualification:** reference the existing QualificationGatePlan and its evidence for risk-proportional qualification. Do not create a competing readiness or validation gate.

The coverage crosswalk can inform these existing records, but does not replace them or grant authority. Do not require Scribe for documentation-neutral tasks or trigger unnecessary specialist reviews.

## Examples

- **Artifact reuse:** the same architecture or design record can be referenced in TRD and APPLICATION_FLOW when its content supports both. Keep each row's applicable requirements, evidence, and fact owners explicit.
- **Conditional obligation:** identify the actual trigger from project scope, evaluate it, and record the outcome in the existing task or evidence surface.
- **Not applicable:** preserve the checked trigger and concise reason; do not use NOT_APPLICABLE as a substitute for missing information.
- **Conflict or missing evidence:** retain both source references, mark UNRESOLVED or MISSING_EVIDENCE, and state which owner must respond.
- **No invented identifiers:** where existing requirement or acceptance IDs exist, retain them. If a project has no established ID scheme, follow its existing approved traceability convention; do not infer identifiers from prose.

These examples describe documentation handling only. They do not establish project facts, prescribe a particular architecture or schema, or authorize development.
