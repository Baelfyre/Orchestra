# Data Inventory Template

Use this reusable template to document app data handling. Replace placeholder examples with project-specific facts. Do not treat example rows as actual Orchestra data collection.

## Template

| Data Category | Specific Data Point | Source | Purpose | Required or Optional | Stored Where | Shared With | Retention Period | Deletion Method | User Disclosure Location |
|---|---|---|---|---|---|---|---|---|---|
| Account data | Example: email address | Example: account signup form | Example: create user account and send login notices | Required | Example: primary app database | Example: email delivery provider | Example: until account deletion plus support hold period | Example: delete from account table and queued mail lists | Example: Privacy Policy, Account Signup notice |
| Analytics | Example: feature usage event | Example: in-app event tracker | Example: understand feature adoption | Optional | Example: analytics dashboard | Example: analytics provider | Example: 12 months | Example: provider retention setting plus event purge job | Example: Privacy Policy, in-app analytics notice |
| Uploaded files | Example: support screenshot | Example: support upload form | Example: troubleshoot user issue | Optional | Example: object storage bucket | Example: support ticket vendor | Example: 90 days after ticket close | Example: ticket purge workflow and storage deletion | Example: Privacy Policy, support form notice |

## Notes

- Add one row per specific data point when practical.
- Split shared systems into separate rows if retention or disclosure differs.
- Keep wording factual and specific.
