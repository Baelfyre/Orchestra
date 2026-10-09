# Privacy Review Checklist

Use this checklist to review app data handling before release. This checklist supports governance review and does not provide legal advice.

## How To Use

For each data category, confirm:
- what is collected
- why it is collected
- whether it is required or optional
- where it is stored
- who it is shared with
- how long it is retained
- how it is deleted
- where users are told about it

## Data Category Checklist

| Data Category | Identify What Exists | Purpose Questions | Retention Questions | Storage Questions | Sharing Questions | Deletion Questions |
|---|---|---|---|---|---|---|
| Personal data | Name, email, phone, address, identifiers | Why is this needed? Is each field required? | How long is it kept? | Which system stores it? | Which vendors or teams receive it? | How is it deleted or anonymized? |
| Device data | Device model, OS version, IP address, diagnostics | Is it needed for app function, fraud prevention, or support? | Is retention minimized? | Is it stored in app backend, vendor tools, or both? | Is it shared with hosting, analytics, or security providers? | Can it be deleted on request or on schedule? |
| Analytics | Events, session metrics, referral data | What product or business question does it answer? | How long are analytics retained? | Which analytics platform stores it? | Which third-party processor receives it? | Can event history be removed or aged out? |
| Crash logs | Stack traces, device context, user identifiers | Is user-linked logging necessary? | How long are logs kept? | Which crash platform stores them? | Who can access them? | How are logs purged or rotated out? |
| Uploaded files | Documents, images, attachments | Why are uploads needed? | What is retention rule per file type? | Where are files stored and backed up? | Are files shared with scanning or storage vendors? | How are files deleted from live and backup systems? |
| Location | Precise or approximate location | Is location required for core function? | Is location retained after use? | Where is location stored? | Is location shared with maps or analytics providers? | Can location history be deleted? |
| Photos and media | Camera uploads, gallery access, recordings | Why is media access needed? | Are unused files discarded? | Where are originals and thumbnails stored? | Are media assets sent to processors? | How are user-submitted assets removed? |
| Account data | Username, profile data, preferences, auth records | What account fields are essential? | What remains after account closure? | Which auth and app systems store it? | Which auth or support vendors receive it? | Is there a documented account deletion flow? |
| Support messages | Tickets, chat logs, email support content | Why is message history retained? | How long is support history kept? | Which support system stores it? | Is it shared with help desk vendors? | How is support history deleted or redacted? |
| Business records | Orders, invoices, audit logs, contract records | Which records are operationally required? | Which retention periods are fixed by policy or contract? | Which systems store the records? | Who receives exports or reports? | What can be deleted, archived, or anonymized? |

## Third-Party Processor Review

For each third-party processor, confirm:
- service name
- service purpose
- data categories sent
- whether the service is required or optional
- storage region, if known
- retention behavior, if known
- deletion or removal path
- user disclosure location

## Final Review Questions

- Does the data inventory match actual app behavior?
- Do user-facing disclosures match collection, sharing, retention, and deletion behavior?
- Are optional data flows clearly distinguished from required flows?
- Are account deletion steps documented when accounts exist?
- Are platform disclosure forms prepared when marketplace submission is planned?
