# ADAPT-QA Phase Separation Policy

**Policy authority:** `ORCHESTRA_ADAPT_QA_PHASE_SEPARATION_FRAMEWORK_AQ10_AQ14_HUMAN_POLICY_20260911`  
**Authority class:** `HUMAN_POLICY`  
**Canonical authority:** `https://github.com/Baelfyre/Padayon/blob/384f78dd27da52a3fff99fe40379ae3c3273e12f/projects/orchestra/10-approved/decisions/ADAPT_QA_Phase_Separation_Framework_AQ10_AQ14_Human_Policy_Decision_20260911.md`

## Purpose

This policy provides a reusable, deterministic separation mechanism between historical exact-scope assurance inventories and later human-approved ADAPT-QA phases. It prevents complete later-phase work from being misclassified as a partial mutation of an earlier phase without weakening historical gates.

## Deterministic rule

```text
EXACT COMPLETE REGISTERED PHASE INVENTORY -> NOT_APPLICABLE to historical exact inventories when phase separation is required
PARTIAL / MIXED / SUPERSET / UNKNOWN / DUPLICATE -> APPLICABLE or FAIL CLOSED
UNREGISTERED FUTURE PHASE -> APPLICABLE
```

The machine registry is `machine/governance/adapt-qa-phase-separation.v1.json`. Registry mutation is protected `HUMAN_POLICY`; autonomous runs may consume approved entries but may not add or broaden them.

## Registered phases

AQ10 through AQ14 are registered exactly as approved by the primary maintainer. Each phase contains exactly nine implementation paths. Any implementation need outside the applicable inventory freezes that phase for fresh human review. AQ15 and later phases remain unregistered.

## Non-authority

Phase separation is not a lifecycle whitelist, assurance bypass, threshold reduction, release authority, deployment authority, provider authority, credential authority, telemetry authority, or production authority. PRAI, Covenant, specialist review, signed materialization, tree attestation, repository rulesets, and human-only whitelist boundaries remain unchanged.
