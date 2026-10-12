from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import pickle
import socket
import urllib.request
from types import SimpleNamespace
from typing import Any

import pytest

from orchestra_runtime.application.services.jev_provider_projection import (
    JEV_PROVIDER_PROJECTION_CONTRACT,
    JEV_PROVIDER_SEMANTIC_PROJECTION_CONTRACT,
    JevProjectionError,
    JevProjectionMappingContext,
    ReviewedJevEvidenceAnnotations,
    ReviewedJevTextBundle,
    _KNOWN_PRODUCERS,
    _PRODUCER_EXPERTISE,
    build_offline_jev_provider_projection,
    build_offline_jev_provider_projection_with_context,
    build_offline_jev_provider_semantic_projection_with_context,
    reverse_map_offline_jev_provider_response,
)
from orchestra_runtime.domain.adaptive.jev_adjudication import (
    JEV_ADVISORY_INCONCLUSIVE,
    JevCandidateBinding,
    JevChoiceAnswer,
    JevNoulAnswer,
    JevProviderResponse,
    OrchestraJevAdjudicationState,
    OrchestraJevInterpreter,
    OrchestraJevQuestionBuilder,
    TYPESAFE_JEV_MODEL,
)


_CANDIDATE = {
    "repository": "Synthetic/PrivateRepo",
    "commit": "a" * 40,
    "tree": "b" * 40,
}
_CONSTRAINTS = {
    "protected_policy_change_allowed": False,
    "authority_change_allowed": False,
    "scope_expansion_allowed": False,
}
_FINDINGS = [
    {
        "id": "F-001",
        "producer": "Cipher",
        "status": "VERIFIED",
        "summary": "Raw local finding F-001 wording.",
        "evidence_refs": ["docs/private/finding-one.json"],
    },
    {
        "id": "F-002",
        "producer": "Clockwork",
        "status": "UNVERIFIED",
        "summary": "Raw local finding F-002 wording.",
        "evidence_refs": [r"D:\Private\evidence\two.txt"],
    },
]
_VERIFICATION = [
    {
        "id": "V-001",
        "producer": "Dagger",
        "finding_id": "F-001",
        "result": "CONFIRMED",
        "evidence_refs": ["https://synthetic.invalid/evidence-one"],
    },
    {
        "id": "V-002",
        "producer": "Cipher",
        "finding_id": "F-002",
        "result": "CONFIRMED",
        "evidence_refs": ["synthetic-secret-reference-two"],
    },
]
_OVERSEER = {
    "evidence_sufficiency": "SUFFICIENT",
    "impact": "MEDIUM",
    "residual_risk_context": "Raw local residual risk details.",
}
_DISSENT = [
    {
        "id": "D-001",
        "producer": "Cipher",
        "summary": "Raw local dissent D-001 wording.",
        "evidence_refs": ["private-evidence-three"],
    }
]


def _state(
    *,
    mitigation_count: int = 2,
    first_producer: str = "Cipher",
    first_status: str = "VERIFIED",
    first_result: str = "CONFIRMED",
    overseer: dict[str, str] | None = None,
    candidate: dict[str, str] | None = None,
) -> OrchestraJevAdjudicationState:
    findings = [dict(item) for item in _FINDINGS]
    findings[0]["producer"] = first_producer
    findings[0]["status"] = first_status
    verification = [dict(item) for item in _VERIFICATION]
    verification[0]["result"] = first_result
    mitigations = [
        {
            "id": f"M-{index:03}",
            "producers": ["Cipher", "Clockwork"],
            "summary": f"Raw local mitigation M-{index:03} wording.",
            "addresses": ["F-001"] if index % 2 else ["F-001", "F-002"],
            "tradeoffs": [
                f"Raw local tradeoff {index}a.",
                f"Raw local tradeoff {index}b.",
            ],
        }
        for index in range(1, mitigation_count + 1)
    ]
    return OrchestraJevAdjudicationState.create(
        candidate=_CANDIDATE if candidate is None else candidate,
        task={"domain": "security", "risk_level": "MEDIUM", "assurance_depth": "STANDARD"},
        findings=findings,
        verification=verification,
        overseer_assessment=_OVERSEER if overseer is None else overseer,
        mitigation_options=mitigations,
        dissent=[dict(item) for item in _DISSENT],
        constraints=dict(_CONSTRAINTS),
    )


def _reviewed_text(state: OrchestraJevAdjudicationState) -> ReviewedJevTextBundle:
    source = state.to_payload()
    return ReviewedJevTextBundle(
        source_scope_hash=source["candidate"]["scope_hash"],
        task_domain="security",
        finding_summaries={
            item["id"]: f"Reviewed synthetic finding summary {index}."
            for index, item in enumerate(source["findings"], start=1)
        },
        overseer_assessment={
            "evidence_sufficiency": "Reviewed synthetic evidence supports comparison.",
            "impact": "The synthetic impact is moderate.",
            "residual_risk_context": "A bounded residual risk remains in the synthetic scenario.",
        },
        mitigation_summaries={
            item["id"]: f"Reviewed synthetic mitigation alternative {index}."
            for index, item in enumerate(source["mitigation_options"], start=1)
        },
        mitigation_tradeoffs={
            item["id"]: [
                f"Keep synthetic alternative {index} bounded.",
                "Preserve current behavior.",
            ]
            for index, item in enumerate(source["mitigation_options"], start=1)
        },
        dissent_summaries={
            item["id"]: "Reviewed synthetic dissent identifies a compatibility concern."
            for item in source["dissent"]
        },
    )


def _build(
    state: OrchestraJevAdjudicationState,
    reviewed: ReviewedJevTextBundle | None = None,
    *,
    nonce: str = "synthetic-request-nonce-20261012",
) -> bytes:
    return build_offline_jev_provider_projection(
        state,
        _reviewed_text(state) if reviewed is None else reviewed,
        nonce=nonce,
    )


def _build_with_context(
    state: OrchestraJevAdjudicationState,
    *,
    nonce: str = "synthetic-request-nonce-20261012",
) -> tuple[bytes, JevProjectionMappingContext]:
    return build_offline_jev_provider_projection_with_context(
        state,
        _reviewed_text(state),
        nonce=nonce,
    )


def _reviewed_evidence_annotations(
    state: OrchestraJevAdjudicationState,
    *,
    finding_layers: dict[str, tuple[str, ...] | None] | None = None,
    verification_layers: dict[str, tuple[str, ...] | None] | None = None,
) -> ReviewedJevEvidenceAnnotations:
    source = state.to_payload()
    return ReviewedJevEvidenceAnnotations(
        source_scope_hash=source["candidate"]["scope_hash"],
        finding_layers=(
            {item["id"]: None for item in source["findings"]}
            if finding_layers is None
            else finding_layers
        ),
        verification_layers=(
            {item["id"]: None for item in source["verification"]}
            if verification_layers is None
            else verification_layers
        ),
    )


def _build_semantic_with_context(
    state: OrchestraJevAdjudicationState,
    evidence_annotations: ReviewedJevEvidenceAnnotations | None = None,
    *,
    nonce: str = "synthetic-request-nonce-20261012",
) -> tuple[bytes, JevProjectionMappingContext]:
    return build_offline_jev_provider_semantic_projection_with_context(
        state,
        _reviewed_text(state),
        nonce=nonce,
        evidence_annotations=evidence_annotations,
    )


def _request(body: bytes) -> dict[str, Any]:
    return json.loads(body.decode("utf-8"))


def _typed_response(
    body: bytes,
    candidate_binding: JevCandidateBinding,
    *,
    recommendation: str | None = None,
) -> JevProviderResponse:
    answers: list[tuple[str, JevNoulAnswer | JevChoiceAnswer]] = []
    for question_id, question in _request(body)["questions"].items():
        if question["type"] == "noul":
            answers.append((question_id, JevNoulAnswer(0.65)))
            continue
        criteria = list(question["criteria"])
        selected = (
            recommendation
            if question_id == "recommended_mitigation" and recommendation is not None
            else criteria[0]
        )
        probabilities = tuple(
            (criterion, 0.8 if criterion == selected else 0.2 / (len(criteria) - 1))
            for criterion in criteria
        )
        answers.append((question_id, JevChoiceAnswer(selected, 0.75, probabilities)))
    return JevProviderResponse("jev-synthetic", candidate_binding, tuple(answers))


def _assert_error(code: str, action) -> None:
    with pytest.raises(JevProjectionError) as error:
        action()
    assert error.value.code == code
    assert str(error.value) == code


def test_projection_allowlist_omits_candidate_evidence_and_source_identifiers() -> None:
    state = _state()
    source = state.to_payload()
    body = _build(state)
    request = _request(body)
    projected = request["state"]

    assert set(request) == {"state", "model", "questions"}
    assert request["model"] == TYPESAFE_JEV_MODEL
    assert projected["contract"] == JEV_PROVIDER_PROJECTION_CONTRACT
    assert set(projected) == {
        "contract",
        "task",
        "findings",
        "verification",
        "overseer_assessment",
        "mitigation_options",
        "dissent",
        "constraints",
    }
    assert "candidate" not in projected
    assert projected["task"] == {
        "domain": "security",
        "risk_level": "MEDIUM",
        "assurance_depth": "STANDARD",
    }
    assert projected["constraints"] == source["constraints"]
    assert all("evidence_refs" not in record for record in projected["findings"])
    assert all("evidence_refs" not in record for record in projected["verification"])
    assert all("evidence_refs" not in record for record in projected["dissent"])
    assert all(
        set(record) == {"id", "producer", "status", "summary"}
        for record in projected["findings"]
    )
    assert all(
        set(record) == {"id", "producer", "finding_id", "result"}
        for record in projected["verification"]
    )

    blocked = {
        *source["candidate"].values(),
        *(item["id"] for item in source["findings"]),
        *(item["id"] for item in source["verification"]),
        *(item["id"] for item in source["mitigation_options"]),
        *(item["id"] for item in source["dissent"]),
        *(item["producer"] for section in ("findings", "verification", "dissent") for item in source[section]),
        *(producer for item in source["mitigation_options"] for producer in item["producers"]),
        *(reference for section in ("findings", "verification", "dissent") for item in source[section] for reference in item["evidence_refs"]),
        *(finding_id for item in source["mitigation_options"] for finding_id in item["addresses"]),
        *(item["finding_id"] for item in source["verification"]),
    }
    assert all(value.encode("utf-8") not in body for value in blocked)
    assert b"Raw local" not in body


def test_projection_is_deterministic_and_nonce_scoped_without_mutating_source() -> None:
    state = _state()
    before = state.to_payload()

    first = _build(state, nonce="synthetic-nonce-one-0001")
    second = _build(state, nonce="synthetic-nonce-one-0001")
    other_nonce = _build(state, nonce="synthetic-nonce-two-0002")

    assert first == second
    assert first != other_nonce
    assert state.to_payload() == before


def test_v1_projection_bytes_remain_byte_identical() -> None:
    body = _build(_state())

    assert hashlib.sha256(body).hexdigest() == (
        "7fb302801eb85361e522a17cd6ed40a856129979360f8a799bce43b8ea615db8"
    )


def test_semantic_projection_is_opt_in_registry_scoped_and_round_trips() -> None:
    state = _state()
    source = state.to_payload()
    before = state.to_payload()
    annotations = _reviewed_evidence_annotations(
        state,
        finding_layers={"F-001": ("UNIT", "STATIC"), "F-002": None},
        verification_layers={"V-001": ("RUNTIME",), "V-002": None},
    )
    body, context = _build_semantic_with_context(state, annotations)
    request = _request(body)
    projected = request["state"]
    v1_request = _request(_build(state))
    semantic = projected["semantic_context"]

    assert set(request) == {"state", "model", "questions"}
    assert projected["contract"] == JEV_PROVIDER_SEMANTIC_PROJECTION_CONTRACT
    assert set(projected) == set(v1_request["state"]) | {"semantic_context"}
    v2_without_semantics = dict(projected)
    v2_without_semantics.pop("semantic_context")
    expected_v1_state = dict(v1_request["state"])
    expected_v1_state["contract"] = JEV_PROVIDER_SEMANTIC_PROJECTION_CONTRACT
    assert v2_without_semantics == expected_v1_state
    assert request["questions"] == v1_request["questions"]
    assert semantic.keys() == {"producer_expertise", "evidence_annotations"}
    assert not any(
        marker in json.dumps(semantic).casefold()
        for marker in ("authorization", "authority", "execute", "consent", "approval")
    )
    assert set(semantic["producer_expertise"].values()) == {
        "RISK_SECURITY_VALIDATION",
        "SYSTEM_DESIGN_AND_DELIVERY",
    }

    projected_producers = {
        record["producer"]
        for section in ("findings", "verification", "dissent")
        for record in projected[section]
    }
    projected_producers.update(
        producer
        for option in projected["mitigation_options"]
        for producer in option["producers"]
    )
    assert set(semantic["producer_expertise"]) == projected_producers
    assert semantic["producer_expertise"][projected["findings"][0]["producer"]] == (
        _PRODUCER_EXPERTISE["cipher"]
    )
    assert semantic["producer_expertise"][projected["findings"][1]["producer"]] == (
        _PRODUCER_EXPERTISE["clockwork"]
    )

    finding_aliases = {
        source_item["id"]: projected_item["id"]
        for source_item, projected_item in zip(source["findings"], projected["findings"])
    }
    verification_aliases = {
        source_item["id"]: projected_item["id"]
        for source_item, projected_item in zip(
            source["verification"], projected["verification"]
        )
    }
    assert ("finding", finding_aliases["F-001"], "F-001") in context._semantic_aliases
    assert (
        "verification",
        verification_aliases["V-001"],
        "V-001",
    ) in context._semantic_aliases
    assert "F-001" not in repr(context)
    with pytest.raises(TypeError):
        pickle.dumps(context)
    assert semantic["evidence_annotations"]["findings"] == {
        finding_aliases["F-001"]: {
            "status": "ANNOTATED",
            "evidence_layers": ["STATIC", "UNIT"],
        },
        finding_aliases["F-002"]: {"status": "UNKNOWN", "evidence_layers": []},
    }
    assert semantic["evidence_annotations"]["verification"] == {
        verification_aliases["V-001"]: {
            "status": "ANNOTATED",
            "evidence_layers": ["RUNTIME"],
        },
        verification_aliases["V-002"]: {"status": "UNKNOWN", "evidence_layers": []},
    }
    assert [item["status"] for item in projected["findings"]] == [
        item["status"] for item in source["findings"]
    ]
    assert [item["result"] for item in projected["verification"]] == [
        item["result"] for item in source["verification"]
    ]
    assert state.to_payload() == before

    for secret_or_identity in (
        *source["candidate"].values(),
        "F-001",
        "V-001",
        "M-001",
        "D-001",
        "Cipher",
        "Clockwork",
        "Dagger",
        "docs/private/finding-one.json",
        r"D:\Private\evidence\two.txt",
        "https://synthetic.invalid/evidence-one",
        "synthetic-secret-reference-two",
        "private-evidence-three",
    ):
        assert secret_or_identity.encode("utf-8") not in body

    recommendation_alias = next(
        item
        for item in request["questions"]["recommended_mitigation"]["criteria"]
        if item != "NO_CLEAR_PREFERENCE"
    )
    response = _typed_response(
        body,
        state.candidate_binding,
        recommendation=recommendation_alias,
    )
    restored = reverse_map_offline_jev_provider_response(state, body, context, response)
    restored_answers = dict(restored.answers)
    assert restored.candidate_binding == state.candidate_binding
    assert set(restored_answers) == set(OrchestraJevQuestionBuilder().build(state))
    assert restored_answers["recommended_mitigation"].selected == dict(
        context._mitigation_ids
    )[recommendation_alias]
    _assert_error(
        "REQUEST_MISMATCH",
        lambda: reverse_map_offline_jev_provider_response(
            state, body + b" ", context, response
        ),
    )


def test_semantic_projection_does_not_infer_evidence_from_refs_or_status() -> None:
    state = _state()
    body, _ = _build_semantic_with_context(state)
    request = _request(body)
    projected = request["state"]
    evidence = projected["semantic_context"]["evidence_annotations"]

    assert projected["findings"][0]["status"] == "VERIFIED"
    assert projected["verification"][0]["result"] == "CONFIRMED"
    assert all(item["status"] == "UNAVAILABLE" for item in evidence["findings"].values())
    assert all(item["status"] == "UNAVAILABLE" for item in evidence["verification"].values())
    assert all(not item["evidence_layers"] for item in evidence["findings"].values())
    assert all(not item["evidence_layers"] for item in evidence["verification"].values())
    assert "evidence_refs" not in json.dumps(projected)


def test_semantic_projection_is_deterministic_and_nonce_scoped() -> None:
    state = _state()
    annotations = _reviewed_evidence_annotations(state)
    before = state.to_payload()
    first, _ = _build_semantic_with_context(state, annotations, nonce="semantic-nonce-one")
    repeated, _ = _build_semantic_with_context(state, annotations, nonce="semantic-nonce-one")
    changed_nonce, _ = _build_semantic_with_context(
        state, annotations, nonce="semantic-nonce-two"
    )

    assert first == repeated
    assert first != changed_nonce
    assert state.to_payload() == before
    assert repr(annotations) == "ReviewedJevEvidenceAnnotations(<local>)"
    with pytest.raises(TypeError):
        pickle.dumps(annotations)


def test_semantic_projection_rejects_alias_collisions(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _state()
    monkeypatch.setattr(
        "orchestra_runtime.application.services.jev_provider_projection._alias",
        lambda kind, value, nonce: f"{kind}-synthetic-collision",
    )

    _assert_error("ALIAS_COLLISION", lambda: _build_semantic_with_context(state))


def test_semantic_projection_rejects_unbound_and_invalid_annotations() -> None:
    state = _state()
    valid = _reviewed_evidence_annotations(state)
    invalid_bundles = (
        (
            replace(valid, source_scope_hash="0" * 64),
            "EVIDENCE_ANNOTATIONS_UNBOUND",
        ),
        (
            replace(valid, finding_layers={"F-001": ("UNIT",)}),
            "INVALID_EVIDENCE_ANNOTATIONS",
        ),
        (
            replace(
                valid,
                finding_layers={
                    **valid.finding_layers,
                    "F-999": ("UNIT",),
                },
            ),
            "INVALID_EVIDENCE_ANNOTATIONS",
        ),
        (
            replace(valid, finding_layers={**valid.finding_layers, "F-001": ("PRAI",)}),
            "INVALID_EVIDENCE_ANNOTATIONS",
        ),
        (
            replace(valid, finding_layers={**valid.finding_layers, "F-001": ()}),
            "INVALID_EVIDENCE_ANNOTATIONS",
        ),
        (
            replace(
                valid,
                verification_layers={**valid.verification_layers, "V-001": ("UNIT", "UNIT")},
            ),
            "INVALID_EVIDENCE_ANNOTATIONS",
        ),
        (
            replace(valid, verification_layers={**valid.verification_layers, "V-001": "UNIT"}),
            "INVALID_EVIDENCE_ANNOTATIONS",
        ),
    )

    for annotations, code in invalid_bundles:
        _assert_error(
            code,
            lambda annotations=annotations: _build_semantic_with_context(state, annotations),
        )


def test_semantic_projection_rejects_non_annotation_bundle() -> None:
    state = _state()
    _assert_error(
        "INVALID_EVIDENCE_ANNOTATIONS",
        lambda: _build_semantic_with_context(state, object()),
    )


@pytest.mark.parametrize("mitigation_count", [1, 2, 4])
def test_projection_preserves_alias_relationships_and_complete_questions(
    mitigation_count: int,
) -> None:
    state = _state(mitigation_count=mitigation_count)
    source = state.to_payload()
    request = _request(_build(state))
    projected = request["state"]
    questions = request["questions"]

    finding_aliases = {
        original["id"]: projected_item["id"]
        for original, projected_item in zip(source["findings"], projected["findings"])
    }
    verification_aliases = {
        original["id"]: projected_item["id"]
        for original, projected_item in zip(source["verification"], projected["verification"])
    }
    mitigation_aliases = {
        original["id"]: projected_item["id"]
        for original, projected_item in zip(
            source["mitigation_options"], projected["mitigation_options"]
        )
    }
    dissent_aliases = {
        original["id"]: projected_item["id"]
        for original, projected_item in zip(source["dissent"], projected["dissent"])
    }

    assert all(
        alias != original
        for mapping in (
            finding_aliases,
            verification_aliases,
            mitigation_aliases,
            dissent_aliases,
        )
        for original, alias in mapping.items()
    )
    assert all(value.startswith("F-") for value in finding_aliases.values())
    assert all(value.startswith("V-") for value in verification_aliases.values())
    assert all(value.startswith("M-") for value in mitigation_aliases.values())
    assert all(value.startswith("D-") for value in dissent_aliases.values())
    assert all(
        record["producer"].startswith("P-")
        for section in ("findings", "verification", "dissent")
        for record in projected[section]
    )
    assert all(
        producer.startswith("P-")
        for option in projected["mitigation_options"]
        for producer in option["producers"]
    )
    assert projected["verification"][0]["finding_id"] == finding_aliases["F-001"]
    for original, projected_item in zip(
        source["mitigation_options"], projected["mitigation_options"]
    ):
        assert projected_item["addresses"] == [
            finding_aliases[finding_id] for finding_id in original["addresses"]
        ]
    assert projected["findings"][0]["producer"] == projected["mitigation_options"][0]["producers"][0]
    assert projected["dissent"][0]["producer"] == projected["findings"][0]["producer"]

    assert len(questions) == 6 + 3 * mitigation_count
    original_questions = OrchestraJevQuestionBuilder().build(state)
    unchanged_question_ids = {
        "material_unresolved_uncertainty",
        "material_specialist_dissent",
        "unsupported_assumption_dependency",
        "primary_decision_factor",
        "strongest_residual_risk",
    }
    for question_id in unchanged_question_ids:
        assert questions[question_id] == original_questions[question_id]

    recommendation = questions["recommended_mitigation"]
    reviewed_summaries = _reviewed_text(state).mitigation_summaries
    expected_criteria = {
        mitigation_aliases[item["id"]]: reviewed_summaries[item["id"]]
        for item in source["mitigation_options"]
    }
    assert set(recommendation["criteria"]) == set(expected_criteria) | {
        "NO_CLEAR_PREFERENCE"
    }
    for alias, summary in expected_criteria.items():
        assert recommendation["criteria"][alias] == summary
        assert f"evidence_supports_{alias}" in questions
        assert f"{alias}_introduces_scope_risk" in questions
        assert f"{alias}_preserves_architecture" in questions
    assert recommendation["criteria"]["NO_CLEAR_PREFERENCE"] == original_questions[
        "recommended_mitigation"
    ]["criteria"]["NO_CLEAR_PREFERENCE"]


@pytest.mark.parametrize("mitigation_count", [1, 3])
def test_projection_context_restores_questions_and_mitigation_answers(
    mitigation_count: int,
) -> None:
    state = _state(mitigation_count=mitigation_count)
    source_before = state.to_payload()
    request_bytes, context = _build_with_context(state)
    request = _request(request_bytes)
    source_options = source_before["mitigation_options"]
    projected_options = request["state"]["mitigation_options"]
    alias_by_source = {
        source["id"]: projected["id"]
        for source, projected in zip(source_options, projected_options)
    }
    selected_source = source_options[-1]["id"]
    provider_candidate = _state(
        candidate={
            "repository": "Synthetic/ProviderCandidate",
            "commit": "c" * 40,
            "tree": "d" * 40,
        }
    ).candidate_binding
    projected_response = _typed_response(
        request_bytes,
        provider_candidate,
        recommendation=alias_by_source[selected_source],
    )

    restored = reverse_map_offline_jev_provider_response(
        state,
        request_bytes,
        context,
        projected_response,
    )
    restored_answers = restored.answer_map()
    source_questions = OrchestraJevQuestionBuilder().build(state)
    dynamic_question_ids = {
        question_id
        for mitigation_id in state.mitigation_ids
        for question_id in (
            f"evidence_supports_{mitigation_id}",
            f"{mitigation_id}_introduces_scope_risk",
            f"{mitigation_id}_preserves_architecture",
        )
    }

    assert restored.candidate_binding == state.candidate_binding
    assert restored.candidate_binding != projected_response.candidate_binding
    assert set(restored_answers) == set(source_questions)
    assert dynamic_question_ids <= set(restored_answers)
    recommendation = restored_answers["recommended_mitigation"]
    assert isinstance(recommendation, JevChoiceAnswer)
    assert recommendation.selected == selected_source
    assert set(dict(recommendation.probabilities)) == {
        *state.mitigation_ids,
        "NO_CLEAR_PREFERENCE",
    }
    assert dict(recommendation.probabilities)[selected_source] == 0.8
    assert state.to_payload() == source_before


def test_projection_context_preserves_no_clear_preference_and_advisory_authority() -> None:
    state = _state()
    request_bytes, context = _build_with_context(state)
    projected_response = _typed_response(
        request_bytes,
        state.candidate_binding,
        recommendation="NO_CLEAR_PREFERENCE",
    )

    restored = reverse_map_offline_jev_provider_response(
        state,
        request_bytes,
        context,
        projected_response,
    )
    result = OrchestraJevInterpreter().interpret(state, restored, state.candidate_binding)
    serialized = result.to_dict()

    assert result.advisory_state == JEV_ADVISORY_INCONCLUSIVE
    assert result.recommendation == "NO_CLEAR_PREFERENCE"
    assert dict(dict(result.answers)["recommended_mitigation"].probabilities)[
        "NO_CLEAR_PREFERENCE"
    ] == 0.8
    assert serialized["advisory_only"] is True
    assert serialized["may_authorize"] is False
    assert serialized["authority_effect"] == "NONE"


def test_projection_context_is_transient_and_never_enters_request_bytes() -> None:
    state = _state()
    request_bytes, context = _build_with_context(state)

    assert repr(context) == "JevProjectionMappingContext(<transient>)"
    assert not hasattr(context, "__dict__")
    assert b"mapping_context" not in request_bytes
    assert b"request_digest" not in request_bytes
    assert b"source_scope_hash" not in request_bytes
    with pytest.raises(TypeError):
        json.dumps(context)
    with pytest.raises(TypeError):
        pickle.dumps(context)
    with pytest.raises(TypeError):
        JevProjectionMappingContext()


def test_reverse_mapping_rejects_wrong_request_and_stale_source_bindings() -> None:
    state = _state()
    request_bytes, context = _build_with_context(state, nonce="synthetic-context-nonce-one")
    other_request, _ = _build_with_context(state, nonce="synthetic-context-nonce-two")
    response = _typed_response(request_bytes, state.candidate_binding)

    _assert_error(
        "REQUEST_MISMATCH",
        lambda: reverse_map_offline_jev_provider_response(
            state, other_request, context, response
        ),
    )
    _assert_error(
        "REQUEST_MISMATCH",
        lambda: reverse_map_offline_jev_provider_response(
            state, request_bytes + b" ", context, response
        ),
    )
    stale_state = _state(
        overseer={
            "evidence_sufficiency": "Changed synthetic evidence assessment.",
            "impact": "MEDIUM",
            "residual_risk_context": "The synthetic residual risk remains bounded.",
        }
    )
    _assert_error(
        "SOURCE_STATE_MISMATCH",
        lambda: reverse_map_offline_jev_provider_response(
            stale_state, request_bytes, context, response
        ),
    )
    _assert_error(
        "INVALID_MAPPING_CONTEXT",
        lambda: reverse_map_offline_jev_provider_response(
            state, request_bytes, object(), response
        ),
    )


def test_reverse_mapping_rejects_invalid_boundary_argument_types() -> None:
    state = _state()
    request_bytes, context = _build_with_context(state)
    response = _typed_response(request_bytes, state.candidate_binding)

    _assert_error(
        "INVALID_SOURCE_STATE",
        lambda: reverse_map_offline_jev_provider_response(
            object(), request_bytes, context, response
        ),
    )
    _assert_error(
        "INVALID_INPUT",
        lambda: reverse_map_offline_jev_provider_response(
            state, bytearray(request_bytes), context, response
        ),
    )
    _assert_error(
        "RESPONSE_CONTRACT_INCOMPATIBLE",
        lambda: reverse_map_offline_jev_provider_response(
            state, request_bytes, context, object()
        ),
    )


def test_reverse_mapping_rejects_unknown_duplicate_missing_and_extra_answers() -> None:
    state = _state()
    request_bytes, context = _build_with_context(state)
    response = _typed_response(request_bytes, state.candidate_binding)
    unknown_question = list(response.answers)
    unknown_index = next(
        index
        for index, (question_id, _) in enumerate(unknown_question)
        if question_id.startswith("evidence_supports_")
    )
    unknown_question[unknown_index] = ("unknown_dynamic_question", unknown_question[unknown_index][1])
    missing = replace(response, answers=response.answers[:-1])
    extra = replace(
        response,
        answers=(*response.answers, ("unknown_question", JevNoulAnswer(0.5))),
    )

    _assert_error(
        "RESPONSE_CONTRACT_INCOMPATIBLE",
        lambda: reverse_map_offline_jev_provider_response(
            state, request_bytes, context, replace(response, answers=unknown_question)
        ),
    )
    _assert_error(
        "RESPONSE_CONTRACT_INCOMPATIBLE",
        lambda: reverse_map_offline_jev_provider_response(state, request_bytes, context, missing),
    )
    _assert_error(
        "RESPONSE_CONTRACT_INCOMPATIBLE",
        lambda: reverse_map_offline_jev_provider_response(state, request_bytes, context, extra),
    )
    with pytest.raises(ValueError):
        JevProviderResponse(
            response.model,
            response.candidate_binding,
            (response.answers[0], response.answers[0]),
        )


def test_reverse_mapping_rejects_wrong_types_aliases_and_probabilities() -> None:
    state = _state()
    request_bytes, context = _build_with_context(state)
    response = _typed_response(request_bytes, state.candidate_binding)
    answer_map = response.answer_map()
    questions = _request(request_bytes)["questions"]
    recommendation = answer_map["recommended_mitigation"]
    assert isinstance(recommendation, JevChoiceAnswer)
    selected = recommendation.selected
    probabilities = dict(recommendation.probabilities)
    non_selected = next(key for key in probabilities if key != selected)

    wrong_type_answers = tuple(
        (
            question_id,
            JevChoiceAnswer("true", 0.75, (("true", 0.8), ("false", 0.2)))
            if question_id == "material_unresolved_uncertainty"
            else answer,
        )
        for question_id, answer in response.answers
    )
    unknown_alias_probabilities = tuple(
        ("M-unknown" if key == selected else key, value)
        for key, value in recommendation.probabilities
    )
    unknown_alias = JevChoiceAnswer("M-unknown", 0.75, unknown_alias_probabilities)
    non_maximal = JevChoiceAnswer(
        selected,
        0.75,
        tuple(
            (key, 0.1 if key == selected else 0.8 if key == non_selected else 0.1)
            for key in probabilities
        ),
    )
    missing_confidence = JevChoiceAnswer(
        recommendation.selected,
        None,
        recommendation.probabilities,
    )

    _assert_error(
        "RESPONSE_CONTRACT_INCOMPATIBLE",
        lambda: reverse_map_offline_jev_provider_response(
            state, request_bytes, context, replace(response, answers=wrong_type_answers)
        ),
    )
    for invalid_recommendation in (unknown_alias, non_maximal, missing_confidence):
        invalid_answers = tuple(
            (question_id, invalid_recommendation if question_id == "recommended_mitigation" else answer)
            for question_id, answer in response.answers
        )
        _assert_error(
            "RESPONSE_CONTRACT_INCOMPATIBLE",
            lambda invalid_answers=invalid_answers: reverse_map_offline_jev_provider_response(
                state,
                request_bytes,
                context,
                replace(response, answers=invalid_answers),
            ),
        )

    with pytest.raises(ValueError):
        JevChoiceAnswer(selected, 0.75, ((selected, True),))
    with pytest.raises(ValueError):
        JevChoiceAnswer(selected, 0.75, ((selected, 0.5), (selected, 0.5)))
    assert questions["recommended_mitigation"]["type"] == "choice"


@pytest.mark.parametrize(
    "unsafe_text",
    [
        "Synthetic finding includes api" + "_key=synthetic-secret-value.",
        "Synthetic finding came from C:" + r"\Users" + r"\Example" + r"\private.txt.",
        "Synthetic finding points to docs/private/report.json.",
        "Synthetic finding references https://example.invalid/private.",
        "Synthetic finding includes reviewer@example.invalid.",
    ],
)
def test_unsafe_reviewed_text_rejects_entire_projection_without_disclosure(
    unsafe_text: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    state = _state()
    bundle = _reviewed_text(state)
    summaries = dict(bundle.finding_summaries)
    summaries["F-001"] = unsafe_text
    bundle = replace(bundle, finding_summaries=summaries)

    with pytest.raises(JevProjectionError) as error:
        _build(state, bundle)

    assert error.value.code == "UNSAFE_REVIEWED_TEXT"
    assert unsafe_text not in str(error.value)
    assert caplog.records == []


def test_projection_requires_scope_bound_reviewed_text_and_rejects_review_flags() -> None:
    state = _state()
    bundle = _reviewed_text(state)
    _assert_error(
        "REVIEWED_TEXT_REQUIRED",
        lambda: build_offline_jev_provider_projection(
            state, None, nonce="synthetic-request-nonce-20261012"
        ),
    )
    _assert_error(
        "REVIEWED_TEXT_UNBOUND",
        lambda: _build(state, replace(bundle, source_scope_hash="sha256:" + "0" * 64)),
    )
    untrusted_flag = SimpleNamespace(
        reviewed=True,
        source_scope_hash=bundle.source_scope_hash,
        task_domain=bundle.task_domain,
        finding_summaries=bundle.finding_summaries,
        overseer_assessment=bundle.overseer_assessment,
        mitigation_summaries=bundle.mitigation_summaries,
        mitigation_tradeoffs=bundle.mitigation_tradeoffs,
        dissent_summaries=bundle.dissent_summaries,
    )
    _assert_error("REVIEWED_TEXT_REQUIRED", lambda: _build(state, untrusted_flag))


@pytest.mark.parametrize(
    ("changes", "expected_code"),
    [
        ({"task_domain": None}, "REVIEWED_TEXT_INCOMPLETE"),
        ({"task_domain": "   "}, "REVIEWED_TEXT_INCOMPLETE"),
        ({"task_domain": "Contains source identifier F-001."}, "UNSAFE_REVIEWED_TEXT"),
        ({"overseer_assessment": None}, "REVIEWED_TEXT_INCOMPLETE"),
        ({"mitigation_tradeoffs": None}, "REVIEWED_TEXT_INCOMPLETE"),
    ],
)
def test_projection_rejects_invalid_reviewed_text_values_and_shapes(
    changes: dict[str, object],
    expected_code: str,
) -> None:
    state = _state()
    reviewed = replace(_reviewed_text(state), **changes)

    _assert_error(
        expected_code,
        lambda: build_offline_jev_provider_projection(
            state,
            reviewed,
            nonce="synthetic-invalid-reviewed-text-nonce",
        ),
    )


@pytest.mark.parametrize("nonce", ["", None, 17])
def test_projection_rejects_invalid_nonce_values(nonce: object) -> None:
    state = _state()

    _assert_error(
        "INVALID_NONCE",
        lambda: build_offline_jev_provider_projection(
            state,
            _reviewed_text(state),
            nonce=nonce,  # type: ignore[arg-type]
        ),
    )


def test_projection_rejects_incomplete_or_ambiguous_reviewed_content() -> None:
    state = _state()
    bundle = _reviewed_text(state)
    missing_finding = dict(bundle.finding_summaries)
    missing_finding.pop("F-002")
    _assert_error(
        "REVIEWED_TEXT_INCOMPLETE",
        lambda: _build(state, replace(bundle, finding_summaries=missing_finding)),
    )
    extra_mitigation = dict(bundle.mitigation_summaries)
    extra_mitigation["M-999"] = "Unknown synthetic alternative."
    _assert_error(
        "REVIEWED_TEXT_INCOMPLETE",
        lambda: _build(state, replace(bundle, mitigation_summaries=extra_mitigation)),
    )
    shortened_tradeoffs = dict(bundle.mitigation_tradeoffs)
    shortened_tradeoffs["M-001"] = ["Only one reviewed tradeoff."]
    _assert_error(
        "REVIEWED_TEXT_INCOMPLETE",
        lambda: _build(state, replace(bundle, mitigation_tradeoffs=shortened_tradeoffs)),
    )


def test_projection_rejects_unknown_source_producers_and_values() -> None:
    unknown_producer = _state(first_producer="unregistered-source")
    _assert_error(
        "UNKNOWN_PRODUCER",
        lambda: _build(unknown_producer),
    )
    unknown_status = _state(first_status="PRIVATE_NOTE")
    _assert_error("INVALID_SOURCE_VALUE", lambda: _build(unknown_status))
    unknown_result = _state(first_result="PRIVATE_RESULT")
    _assert_error("INVALID_SOURCE_VALUE", lambda: _build(unknown_result))


def test_projection_rejects_unknown_state_fields_and_empty_mitigation_context() -> None:
    state = _state()
    raw = state.to_payload()
    raw["unexpected"] = "synthetic unknown value"
    with pytest.raises(ValueError):
        OrchestraJevAdjudicationState(raw)
    _assert_error(
        "INVALID_SOURCE_STATE",
        lambda: build_offline_jev_provider_projection(
            raw, _reviewed_text(state), nonce="synthetic-request-nonce-20261012"
        ),
    )
    no_mitigations = _state(mitigation_count=0)
    _assert_error(
        "SOURCE_STATE_INELIGIBLE",
        lambda: _build(no_mitigations),
    )


def test_projection_preserves_long_reviewed_text_without_truncation() -> None:
    state = _state(mitigation_count=1)
    bundle = _reviewed_text(state)
    long_summary = "Reviewed synthetic context remains complete. " * 256
    summaries = dict(bundle.finding_summaries)
    summaries["F-001"] = long_summary
    body = _build(state, replace(bundle, finding_summaries=summaries))

    assert _request(body)["state"]["findings"][0]["summary"] == long_summary


def test_projection_makes_no_network_or_environment_credential_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _state()
    calls: list[str] = []

    def forbidden(*args: object, **kwargs: object) -> None:
        calls.append("called")
        raise AssertionError("offline projection attempted external I/O")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(urllib.request, "build_opener", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(os, "getenv", forbidden)
    body, context = _build_with_context(state)
    response = _typed_response(body, state.candidate_binding)
    reverse_map_offline_jev_provider_response(state, body, context, response)
    semantic_body, semantic_context = _build_semantic_with_context(state)
    semantic_response = _typed_response(semantic_body, state.candidate_binding)
    reverse_map_offline_jev_provider_response(
        state, semantic_body, semantic_context, semantic_response
    )

    assert calls == []


def test_projection_cannot_issue_authority_and_uses_registry_producers() -> None:
    state = _state()
    request = _request(_build(state))
    body = json.dumps(request, sort_keys=True)
    registry_path = Path(__file__).resolve().parents[2] / "machine" / "specialists" / "registry.v1.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry_producers = {item["name"].casefold() for item in registry["specialists"]}

    assert _KNOWN_PRODUCERS == registry_producers
    assert set(_PRODUCER_EXPERTISE) == registry_producers
    assert set(_PRODUCER_EXPERTISE.values()) == {
        "SCOPE_COORDINATION_TRACEABILITY",
        "RISK_SECURITY_VALIDATION",
        "SYSTEM_DESIGN_AND_DELIVERY",
    }
    assert all("AUTHORITY" not in category for category in _PRODUCER_EXPERTISE.values())
    assert set(request) == {"state", "model", "questions"}
    assert not any(key in body for key in ("authorization", "execute", "consent", "authority_effect"))
    assert request["state"]["constraints"] == _CONSTRAINTS
    assert "advisory only" in request["questions"]["recommended_mitigation"]["instructions"]
