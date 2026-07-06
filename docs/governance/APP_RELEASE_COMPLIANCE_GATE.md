# App Release Compliance Gate

This document defines the App Release Compliance Gate for Release Mode.

It applies before:
- public release
- client delivery
- app store submission
- production deployment
- open-source distribution

This gate is a documentation and governance control. It does not provide legal advice.

## Release Mode Hard Gate

Release Mode must not proceed when required app release compliance artifacts are missing.

The Governor must review this gate before approving release work that includes an app, public distribution, client delivery, production deployment, or marketplace submission.

## Required Artifacts

| Artifact | Required When | Minimum Evidence |
|---|---|---|
| Privacy Policy | Personal data, device data, analytics, crash logging, support data, or other disclosed data exists | Draft or published policy linked from release record |
| Terms of Use or Terms of Service | Public, client-facing, hosted, downloadable, or account-based release | Draft or published terms linked from release record |
| Data Inventory | Any app data, device data, analytics, uploaded content, or business records are collected, processed, stored, or shared | Completed inventory table |
| Data Retention and Deletion Policy | Any retained data exists | Completed retention and deletion policy |
| Account Deletion Flow | User accounts exist | Documented user flow or support process |
| Third-Party Service Disclosure | Third-party SDKs, APIs, hosting, analytics, crash logging, messaging, payments, auth, or databases are used | Service list mapped to user disclosures |
| Apple App Privacy Details | App Store submission | Draft submission answers aligned to data inventory |
| Google Play Data Safety | Google Play submission | Draft submission answers aligned to data inventory |
| GDPR and CCPA applicability screening | Personal data processing may apply to covered users, jurisdictions, or release targets | Short screening note with outcome |
| IP, trademark, asset, dependency, and license clearance | Any public, client, marketplace, or distributed release | Completed IP clearance checklist |

## Required Checks

The Governor must verify:

1. A Privacy Policy exists when applicable and matches actual disclosed data use.
2. Terms exist when applicable and match the release model.
3. A Data Inventory exists and covers:
   - personal data
   - device data
   - analytics
   - crash logs
   - uploaded files
   - account data
   - support or business records
4. A retention and deletion policy exists and is consistent with the Privacy Policy.
5. An account deletion flow is documented when accounts exist.
6. Third-party SDKs, APIs, hosting, analytics, crash logging, and database providers are disclosed when applicable.
7. Apple App Privacy Details are prepared when submitting to the App Store.
8. Google Play Data Safety answers are prepared when submitting to Google Play.
9. GDPR and CCPA screening is documented as "may apply" unless project-specific facts confirm applicability.
10. IP, trademark, app name, logo, asset, dependency, and license clearance is documented.

## Decision Outcomes

| Outcome | Meaning |
|---|---|
| `PASS` | Required artifacts exist for current release context and no blocking gaps were found |
| `REVISION_REQUIRED` | Release artifacts are incomplete, inconsistent, or need correction before approval |
| `BLOCKED` | Required release artifacts are missing or release risk is too high to proceed |

## Mandatory Block Conditions

For Release Mode, `BLOCKED` is mandatory when any of these required items are missing:
- Privacy Policy
- Data Inventory
- Data Retention and Deletion Policy
- Account deletion documentation, when accounts exist
- IP clearance

`BLOCKED` is also mandatory when release documentation materially conflicts with known data handling or third-party service usage.

## Suggested Review Record

```text
RELEASE_CONTEXT:
DECISION:
MISSING_ARTIFACTS:
OPEN_DISCLOSURES:
JURISDICTION_SCREENING:
IP_CLEARANCE_STATUS:
REQUIRED_ACTIONS:
```

## Related Documents

- [Privacy Review Checklist](PRIVACY_REVIEW_CHECKLIST.md)
- [Data Inventory Template](DATA_INVENTORY_TEMPLATE.md)
- [IP Clearance Checklist](IP_CLEARANCE_CHECKLIST.md)
- [Privacy Policy Template](../legal/PRIVACY_POLICY_TEMPLATE.md)
- [Terms of Use Template](../legal/TERMS_OF_USE_TEMPLATE.md)
- [Data Retention and Deletion Policy](../legal/DATA_RETENTION_AND_DELETION_POLICY.md)
