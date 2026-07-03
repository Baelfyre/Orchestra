# Database Standards

Apply these standards to confirmed requirements and database evidence, not hypothetical scale.

## Tables and Columns

- Give each table one coherent subject and stable ownership.
- Use consistent, descriptive names and data types that preserve the domain.
- Define nullability from business rules, not convenience.
- Avoid duplicated facts unless denormalization is justified and maintained.

## Primary Keys

- Give every entity a stable, unique, non-null identifier.
- Choose natural, composite, or surrogate keys from identity and lifecycle requirements.
- Do not expose mutable business data as a key without justification.

## Foreign Keys

- Enforce confirmed relationships with compatible types.
- Define update and delete behavior explicitly.
- Index foreign keys when workload or engine behavior justifies it.

## Constraints and Defaults

- Use unique constraints for candidate keys and duplicate-prevention rules.
- Use check constraints for stable domain rules supported by the engine.
- Use not-null constraints for required facts.
- Use defaults only when the default is valid for every omitted value.

## Indexes

- Tie indexes to known joins, filters, ordering, uniqueness, or measured bottlenecks.
- Review selectivity, column order, covering needs, write cost, and overlap.
- Avoid speculative or duplicate indexes.

## Normalization

- Remove repeating groups and verify atomic values for the intended domain.
- Check partial dependencies for composite keys and transitive dependencies among non-key facts.
- Denormalize only with measured or required read behavior plus a consistency plan.

## Reference Tables and Seed Data

- Give canonical values stable identifiers and documented meanings.
- Enforce uniqueness and active or retired lifecycle rules where required.
- Keep seed scripts deterministic, repeatable, and free of conflicting duplicates.

## Audit Tables

- Record actor, action, time, affected identity, and before or after values only when required.
- Protect audit records from ordinary update paths.
- Document retention, privacy, and access rules.

## Migration Files

- Make order, prerequisites, data transformation, rollback or recovery, and deployment impact explicit.
- Separate destructive steps and require approval.
- Test migrations against representative data and verify constraints afterward.

## Data Dictionaries and Documentation

- Document table purpose, ownership, keys, columns, constraints, relationships, lifecycle, and sensitive data classification.
- Match documentation to the authoritative revision.
- Mark inferred or proposed fields clearly.

## Database Testing

- Test valid writes, invalid writes, uniqueness, referential actions, nullability, defaults, migrations, rollback or recovery, and representative queries.
- Capture environment and pre-state before mutation.
- Use non-production data unless explicit production authority exists.
