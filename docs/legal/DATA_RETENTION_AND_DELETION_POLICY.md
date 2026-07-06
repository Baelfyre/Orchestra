# Data Retention and Deletion Policy Template

Use this template to map project data categories to retention and deletion behavior. Replace placeholders with project-specific facts. This template does not provide legal advice.

Retention should be minimized and must match the Privacy Policy.

## Retention and Deletion Table

| Data Category | Retention Period | Deletion Trigger | Deletion Method | Responsible Owner | Verification Method |
|---|---|---|---|---|---|
| Example: account profile data | Example: until account deletion plus defined support hold period | Example: user account deletion request | Example: delete primary record and downstream profile copies | Example: product engineering owner | Example: admin query plus deletion audit log |
| Example: analytics events | Example: 12 months | Example: scheduled retention window expiry | Example: provider retention setting and purge job | Example: analytics owner | Example: dashboard retention settings review |
| Example: support attachments | Example: 90 days after ticket close | Example: ticket closure retention expiry | Example: support platform purge and storage deletion | Example: support operations owner | Example: ticket export review and storage check |

## Review Notes

- Define retention in plain language.
- Record downstream systems or backups when they affect deletion timing.
- Keep deletion verification practical and repeatable.
