# Database Documentation Templates

Replace placeholders only with confirmed schema and requirement evidence.

## Data Dictionary

```markdown
# Data Dictionary
- Database objective:
- Source revision:
- Environment:

| Table | Purpose | Owner | Primary Key | Sensitive Data | Lifecycle |
|---|---|---|---|---|---|
```

## Table Documentation

```markdown
## Table: [name]
- Purpose:
- Source of truth:
- Primary key:
- Candidate keys:
- Relationships:
- Lifecycle and retention:
- Common verified queries:
- Known limitations:
```

## Column Documentation

```markdown
| Column | Type | Nullable | Default | Domain meaning | Constraints | Sensitive |
|---|---|---|---|---|---|---|
```

## Constraint Documentation

```markdown
| Constraint | Table | Type | Columns | Enforced rule | Referential action | Evidence |
|---|---|---|---|---|---|---|
```

## Relationship Documentation

```markdown
## Relationship: [parent] to [child]
- Business meaning:
- Cardinality:
- Optionality:
- Foreign key:
- Update behavior:
- Delete behavior:
- Evidence:
```

## Seed Data Documentation

```markdown
## Seed Set: [name]
- Purpose:
- Source file:
- Canonical key strategy:
- Repeatability behavior:
- Environment scope:
- Duplicate-prevention rule:
- Validation query:
```

## Migration Notes

```markdown
# Migration: [identifier]
- Objective:
- Preconditions:
- Schema changes:
- Data transformation:
- Compatibility impact:
- Lock or runtime impact:
- Recovery or rollback:
- Verification:
- Approval status:
```

## Database Validation Report

```markdown
# Database Validation Report
## Scope and Environment
## Source Revision
## Checks Run
| Check | Query or Method | Result | Evidence |
|---|---|---|---|
## Integrity Findings
## Seed and Reference Data Findings
## Migration Findings
## Performance Evidence
## Missing Evidence
## Recommendation
```
