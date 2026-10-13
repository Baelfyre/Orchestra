# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

import pytest

from orchestra_runtime.domain.adaptive.capability_coverage import (
    CapabilityClaim,
    CapabilityCoverageResult,
    CapabilityCoverageStatus,
    CapabilityDeclaration,
    CapabilityEvidenceFreshness,
    CapabilityEvidenceLevel,
    CapabilitySourceKind,
    TaskCapabilityFacet,
    TrustedCapabilityEvidence,
    evaluate_capability_coverage,
)


AS_OF = "2026-10-14T08:00:00Z"
VALID_UNTIL = "2026-10-15T08:00:00Z"
STALE_AT = "2026-10-13T08:00:00Z"


def facet(facet_id: str = "ui", *capabilities: str) -> TaskCapabilityFacet:
    return TaskCapabilityFacet(facet_id, capabilities or ("accessibility",))


def declaration(
    source_kind: str = "INTERNAL",
    source_id: str = "cloak",
    claim: str = "SUPPORTS",
    *,
    facet_id: str = "ui",
    capability_id: str = "accessibility",
    evidence_refs: tuple[str, ...] = ("skill:cloak/accessibility",),
    valid_until: str | None = None,
) -> CapabilityDeclaration:
    return CapabilityDeclaration(
        facet_id,
        capability_id,
        source_kind,
        source_id,
        claim,
        evidence_refs,
        valid_until,
    )


def trusted_evidence(
    claim: str = "SUPPORTS",
    *,
    source_kind: str = "EXTERNAL",
    source_id: str = "impeccable",
    producer_id: str = "host-capability-audit",
    facet_id: str = "ui",
    capability_id: str = "accessibility",
    evidence_refs: tuple[str, ...] = ("receipt:tool-accessibility",),
    valid_until: str | None = VALID_UNTIL,
) -> TrustedCapabilityEvidence:
    return TrustedCapabilityEvidence(
        facet_id,
        capability_id,
        source_kind,
        source_id,
        producer_id,
        claim,
        evidence_refs,
        valid_until,
    )


def assess(
    facets: tuple[TaskCapabilityFacet, ...] = (facet(),),
    declarations: tuple[CapabilityDeclaration, ...] = (),
    evidence: tuple[TrustedCapabilityEvidence, ...] = (),
) -> CapabilityCoverageResult:
    return evaluate_capability_coverage(facets, declarations, evidence, evaluated_at=AS_OF)


def test_declared_coverage_and_missing_capability_are_distinct() -> None:
    result = assess(
        (facet("ui", "accessibility", "visual-audit"),),
        (declaration(),),
    )

    assert [(item.capability_id, item.status) for item in result.items] == [
        ("accessibility", CapabilityCoverageStatus.DECLARED),
        ("visual-audit", CapabilityCoverageStatus.MISSING),
    ]
    assert result.items[0].evidence[0].evidence_level is CapabilityEvidenceLevel.DECLARED
    assert result.items[0].evidence[0].source_kind is CapabilitySourceKind.INTERNAL


def test_verified_evidence_requires_the_separate_trusted_producer_input() -> None:
    declared = assess(declarations=(declaration(claim="SUPPORTS"),))
    verified = assess(evidence=(trusted_evidence(),))

    assert declared.items[0].status is CapabilityCoverageStatus.DECLARED
    assert verified.items[0].status is CapabilityCoverageStatus.VERIFIED
    assert verified.items[0].evidence[0].producer_id == "host-capability-audit"
    assert verified.items[0].evidence[0].freshness is CapabilityEvidenceFreshness.CURRENT


def test_unknown_and_stale_evidence_never_count_as_verified_coverage() -> None:
    unknown = assess(evidence=(trusted_evidence(valid_until=None),))
    stale = assess(declarations=(declaration(valid_until=STALE_AT),))

    assert unknown.items[0].status is CapabilityCoverageStatus.UNKNOWN
    assert unknown.items[0].evidence[0].freshness is CapabilityEvidenceFreshness.UNKNOWN
    assert stale.items[0].status is CapabilityCoverageStatus.STALE
    assert stale.items[0].evidence[0].freshness is CapabilityEvidenceFreshness.STALE


def test_conflicting_sources_remain_unresolved_without_source_priority() -> None:
    internal = declaration("INTERNAL", "cloak", "SUPPORTS")
    external = declaration(
        "EXTERNAL",
        "impeccable",
        "DOES_NOT_SUPPORT",
        evidence_refs=("report:impeccable-limit",),
    )

    result = assess(declarations=(internal, external))

    assert result.items[0].status is CapabilityCoverageStatus.CONFLICT
    assert {item.source_kind for item in result.items[0].evidence} == {
        CapabilitySourceKind.INTERNAL,
        CapabilitySourceKind.EXTERNAL,
    }
    assert not hasattr(result.items[0], "selected_source")
    assert not hasattr(result.items[0], "selected_strategy")

    both_support = assess(
        declarations=(
            internal,
            declaration("EXTERNAL", "impeccable", "SUPPORTS"),
        )
    )
    assert both_support.items[0].status is CapabilityCoverageStatus.DECLARED
    assert len(both_support.items[0].evidence) == 2


def test_multiple_sources_can_supply_complementary_coverage() -> None:
    result = assess(
        (facet("ui", "accessibility", "visual-audit"),),
        (
            declaration("INTERNAL", "cloak", "SUPPORTS", capability_id="accessibility"),
            declaration(
                "EXTERNAL",
                "impeccable",
                "SUPPORTS",
                capability_id="visual-audit",
                evidence_refs=("report:visual-audit",),
            ),
        ),
    )

    assert [item.status for item in result.items] == [
        CapabilityCoverageStatus.DECLARED,
        CapabilityCoverageStatus.DECLARED,
    ]
    assert [item.evidence[0].source_kind for item in result.items] == [
        CapabilitySourceKind.INTERNAL,
        CapabilitySourceKind.EXTERNAL,
    ]


def test_explicit_unknown_claim_is_distinct_from_missing() -> None:
    result = assess(declarations=(declaration(claim="UNKNOWN"),))

    assert result.items[0].status is CapabilityCoverageStatus.UNKNOWN


def test_result_is_invariant_to_facet_and_evidence_input_order() -> None:
    facets = (facet("ui", "accessibility"), facet("research", "source-review"))
    declarations = (
        declaration("EXTERNAL", "impeccable", "SUPPORTS", capability_id="accessibility"),
        declaration(
            "EXTERNAL",
            "impeccable",
            "SUPPORTS",
            facet_id="research",
            capability_id="source-review",
            evidence_refs=("report:impeccable-source-review",),
        ),
        declaration(
            "INTERNAL",
            "arbiter",
            "DOES_NOT_SUPPORT",
            facet_id="research",
            capability_id="source-review",
            evidence_refs=("skill:arbiter/source-review",),
        ),
    )
    evidence = (trusted_evidence(facet_id="ui"),)

    forward = assess(facets, declarations, evidence)
    reversed_inputs = assess(tuple(reversed(facets)), tuple(reversed(declarations)), tuple(reversed(evidence)))

    assert forward == reversed_inputs
    assert forward.items[0].facet_id == "research"
    assert forward.items[0].status is CapabilityCoverageStatus.CONFLICT
    assert forward.items[1].facet_id == "ui"
    assert forward.items[1].status is CapabilityCoverageStatus.VERIFIED


def test_malformed_and_duplicate_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="source_kind"):
        declaration(source_kind="PLUGIN")
    with pytest.raises(ValueError, match="claim"):
        declaration(claim="SUPPORTED_VERIFIED")
    with pytest.raises(ValueError, match="canonical identifier"):
        facet("../ui")
    with pytest.raises(ValueError, match="unique identifiers"):
        facet("ui", "accessibility", "ACCESSIBILITY")
    with pytest.raises(ValueError, match="evidence_refs must be unique"):
        declaration(evidence_refs=("ref:one", "ref:one"))
    with pytest.raises(ValueError, match="unique facet_id"):
        assess((facet(), facet()))
    duplicate = declaration()
    with pytest.raises(ValueError, match="must not contain duplicates"):
        assess(declarations=(duplicate, duplicate))
    with pytest.raises(TypeError, match="must contain CapabilityDeclaration"):
        evaluate_capability_coverage(
            (facet(),),
            ({"claim": "SUPPORTED_VERIFIED"},),  # type: ignore[arg-type]
            evaluated_at=AS_OF,
        )


def test_claim_objects_cannot_be_promoted_by_a_verification_label() -> None:
    result = assess(declarations=(declaration(claim=CapabilityClaim.SUPPORTS.value),))

    assert result.items[0].status is CapabilityCoverageStatus.DECLARED
    assert not hasattr(declaration(), "verified")
