# Orchestra Pattern Catalog

This document is the registry for all external design patterns that have been successfully audited, approved by governance, and adapted into Orchestra.

> [!NOTE]
> All candidate patterns begin as raw `PATTERN_SCHEMA.json` instances located within bundle directories in `internal/artificer/records/`. Only governance-approved patterns are manually promoted to this catalog. Rejected, deferred, blocked, and revision-required candidates remain strictly in the decision registry. Automatic catalog editing remains prohibited in Phase 4A.
>
> The catalog uses the following promotion lifecycle statuses: `APPROVED`, `IMPLEMENTING`, `IMPLEMENTED`, `RETIRED`. Approval does not mean implementation is complete. Each entry must explicitly trace to a promotion record, decision record, source bundle, commit SHA, file, and line range.

## Catalog Index

| ID | Pattern Name | Source Repository | Approval Date | Status | Assigned Specialist |
|---|---|---|---|---|---|
| | | | | | |

---

## Catalog Entries

*(No patterns have been approved or implemented yet. Future entries will follow the template below.)*

### Template

```markdown
### [Pattern ID]: [Pattern Name]
- **Status**: [APPROVED | IMPLEMENTING | IMPLEMENTED | RETIRED]
- **Source**: [Source URL]
- **Source Bundle**: [Bundle ID]
- **Audited Commit**: [Commit SHA]
- **Source File**: [File Path]
- **Line Range**: [Line Range]
- **Decision Record**: [Decision ID]
- **Promotion Record**: [Promotion ID]
- **Original License**: [License]
- **Orchestra Specialist Owner**: [Specialist]
- **Adaptation Branch**: [Branch Name]
- **Summary**: [Brief description of how the pattern was adapted and where it is used in Orchestra.]
```
