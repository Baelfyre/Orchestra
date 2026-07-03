# Data Dictionary

- Database objective: Support employee identity and employment-profile workflows.
- Source revision: `[verified schema revision]`
- Environment: Logical documentation only

| Table | Purpose | Owner | Primary Key | Sensitive Data | Lifecycle |
|---|---|---|---|---|---|
| `employee_core` | Stable employee identity | Employee module | `employee_id` | Name and contact identifiers | Retained per project policy |
| `employment_profile` | Employment attributes for one employee | HR module | `employee_id` | Employment details | Updated during employment |

## Relationship: employee_core to employment_profile

- Business meaning: One confirmed core employee record owns one employment profile.
- Cardinality: One to one in the supplied schema.
- Optionality: Not confirmed.
- Foreign key: `employment_profile.employee_id` to `employee_core.employee_id`.
- Update behavior: Not documented.
- Delete behavior: Not documented.
- Evidence: Versioned schema file.

## Missing Evidence
- Referential actions
- Retention rule source
- Sensitive-data classification policy
