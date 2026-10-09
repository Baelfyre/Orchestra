# Changelog and ADR Guide

## Changelog Discipline

Write for users and operators. Group verified changes under Added, Changed, Deprecated, Removed, Fixed, or Security only when those categories help. Keep pending work in `Unreleased` or the repository's established pending section.

Do not create a release heading, release date, comparison link, or compatibility promise until canonical release evidence exists. A merged change is not automatically published.

Each entry should state the affected capability and observable impact. Link the issue, PR, migration, advisory, or documentation when it helps recovery or adoption. Avoid raw commit messages and internal-only refactors with no user impact.

## Architecture Decision Records

An ADR records:

- stable identifier and title;
- status such as Proposed, Accepted, Rejected, Deprecated, or Superseded;
- decision/effective date and owners where established;
- context and constraints;
- the accepted decision;
- alternatives considered and why they were not selected;
- consequences, risks, and follow-up validation;
- source artifacts and related ADRs.

Do not rewrite an accepted ADR to make history look current. Create a new ADR, mark the old one superseded, and link both directions. A proposal remains Proposed until the authorized decision owner accepts it.

Scribe records a decision supplied by Clockwork or the relevant authority; Scribe does not choose architecture or governance outcomes.
