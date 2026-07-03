# Cipher Security and Privacy Review

Fictional example.

## Scope Reviewed
- Project: Fictional fitness dashboard
- Security or Privacy Objective: Review collection and retention of location history
- Review Mode: Privacy risk review
- Evidence Reviewed: Data model, mobile permissions text, retention job, and privacy notice draft

## Review Confidence
Confidence Level: Medium
Reason: Collection and storage evidence exists; third-party data flows were not supplied.

## Executive Summary
The reviewed app collects precise location for route display, but the purpose statement and retention job do not define a bounded retention period.

## Confirmed Security Strengths
- The supplied API policy limits location-history reads to the owning account.

## Confirmed Privacy Strengths
- Mobile permission text identifies route tracking as the collection purpose.

## Threat Surface
- Mobile collection, API transfer, primary storage, backups, and exports.

## Sensitive Data Handling Issues
- Retention behavior has no confirmed deletion deadline.

## Privacy Risk Notes
- Long-lived precise location history increases impact if account access is compromised.

## Assumptions
- Location data is not shared with analytics vendors; integration evidence is missing.

## Missing Evidence
- Third-party data inventory
- Backup expiry
- Account-deletion workflow

## Priority Fixes
1. Define and implement an approved retention rule.
2. Document deletion behavior across primary storage and backups.

## Defensive Recommendations
- Minimize retained precision and duration according to the verified product objective and qualified governance review.

## Final Recommendation
Resolve retention and third-party-flow evidence before asserting privacy readiness.
