# Compliance Registry Integration

## Canonical registry

Orchestra's reusable compliance-intelligence source is `Baelfyre/Orchestra-Compliance-Registry`. Normal IDE governance uses a verified local snapshot managed by `scripts/compliance_registry.py`.

The public registry is readable by anyone. Canonical mutation authority is a separate repository-control concern. A fork, pull request, source-monitor result, arbitrary `main` snapshot, or self-consistent local ZIP is not a trusted registry release.

A trusted network distribution must come from a non-draft, non-prerelease, immutable GitHub Release in the canonical registry repository. An air-gapped or pre-downloaded ZIP must be bound to a separately verified release-manifest SHA-256 supplied out of band. Internal hashes prove content integrity; the immutable canonical release or external manifest digest supplies provenance.

## Local-first rule

Governor and Steward should use the verified active local registry for ordinary compliance review. Network access is reserved for synchronization, update checks, or authoritative-source verification when the registry cannot resolve a material currentness question.

Record these identities whenever a compliance decision relies on registry knowledge:

- canonical repository
- registry version
- release sequence
- release tag
- release manifest SHA-256
- selected jurisdictions and providers
- applicable source IDs and obligation IDs

## Governor

Governor owns applicability, authoritative-source state, legal/regulatory/privacy/licensing/IP/provider-policy governance, and material interpretation escalation. Governor must not treat a registry record as legal advice or blanket compliance approval.

At Audit or Release boundaries, missing registry integrity, unresolved review-required source state, or materially stale applicable source evidence requires `REVISION_REQUIRED`, `WAIT_FOR_EVIDENCE`, or `human_review_required: true` as appropriate. Domain membership alone does not require escalation.

## Steward

Steward owns translating applicable registry obligations into project requirements and SDLC evidence. Compliance-derived requirements should remain traceable through:

`registry obligation -> project FR/NFR -> acceptance criterion -> implementation -> exact-state evidence`

An implementation reference is not compliance evidence by itself.

## Arbiter

Arbiter verifies that the compliance decision, registry identity, project state, and validation evidence are mutually current. A changed registry release does not automatically mean the project is non-compliant, but it invalidates prior compliance evidence when an applicable source or obligation changed materially or freshness can no longer be established.

Unknown or mismatched registry identity fails closed. Registry content never expands execution authority.

## Conductor

Conductor routes the applicable governance owners. It does not interpret compliance records and must not treat Governor approval as deployment, publication, or release authority.
