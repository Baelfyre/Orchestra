from __future__ import annotations

import io
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any, Mapping
import urllib.error

import pytest

from orchestra_runtime.application.use_cases.jev_adjudication import (
    JevAdjudicationEligibilityError,
    OrchestraJevAdjudicationUseCase,
)
from orchestra_runtime.application.services.jev_provider_projection import (
    JEV_PROVIDER_PROJECTION_CONTRACT,
    JevProjectionMappingContext,
    ReviewedJevTextBundle,
    build_offline_jev_provider_projection_with_context,
)
from orchestra_runtime.application.ports.jev_adjudication import (
    JevProviderRequestProjectionContext,
)
from orchestra_runtime.domain.adaptive.jev_adjudication import (
    JEV_ADVISORY_INCONCLUSIVE,
    JEV_ADVISORY_RECOMMENDATION_AVAILABLE,
    JEV_ADVISORY_STALE,
    JEV_ADVISORY_UNBOUND,
    JEV_NOT_REQUIRED,
    JEV_UNAVAILABLE,
    JevCandidateBinding,
    JevAdvisoryResult,
    JevChoiceAnswer,
    JevNoulAnswer,
    JevProviderFailure,
    JevProviderResponse,
    OrchestraJevAdjudicationState,
    OrchestraJevInterpreter,
    OrchestraJevQuestionBuilder,
)
from orchestra_runtime.infrastructure.providers.typesafe_jev import TypeSafeJevAdapter
from orchestra_runtime.shared.canonicalization import canonical_json_bytes


_CANDIDATE = {
    "repository": "Baelfyre/Orchestra",
    "commit": "a" * 40,
    "tree": "b" * 40,
}
_FINDING = {
    "id": "F-001",
    "producer": "Cipher",
    "status": "VERIFIED",
    "summary": "A bounded synthetic finding for adapter contract tests.",
    "evidence_refs": ["E-001"],
}
_VERIFICATION = {
    "id": "V-001",
    "producer": "Dagger",
    "finding_id": "F-001",
    "result": "CONFIRMED",
    "evidence_refs": ["E-002"],
}
_OVERSEER = {
    "evidence_sufficiency": "SUFFICIENT",
    "impact": "MEDIUM",
    "residual_risk_context": "Keep the mitigation narrow and reversible.",
}
_MITIGATIONS = [
    {
        "id": "M1",
        "producers": ["Cipher", "Clockwork"],
        "summary": "Add a narrow boundary check.",
        "addresses": ["F-001"],
        "tradeoffs": ["Small targeted change.", "Preserves architecture."],
    },
    {
        "id": "M2",
        "producers": ["Cipher", "Clockwork"],
        "summary": "Replace the boundary with a generalized subsystem.",
        "addresses": ["F-001"],
        "tradeoffs": ["Larger scope.", "Greater architectural change."],
    },
]
_CONSTRAINTS = {
    "protected_policy_change_allowed": False,
    "authority_change_allowed": False,
    "scope_expansion_allowed": False,
}


def _state(**overrides: object) -> OrchestraJevAdjudicationState:
    sections: dict[str, Any] = {
        "candidate": _CANDIDATE,
        "task": {"domain": "security", "risk_level": "MEDIUM", "assurance_depth": "STANDARD"},
        "findings": [_FINDING],
        "verification": [_VERIFICATION],
        "overseer_assessment": _OVERSEER,
        "mitigation_options": _MITIGATIONS,
        "dissent": [],
        "constraints": _CONSTRAINTS,
    }
    sections.update(overrides)
    return OrchestraJevAdjudicationState.create(**sections)


def _request_projection(
    state: OrchestraJevAdjudicationState,
) -> tuple[bytes, JevProviderRequestProjectionContext]:
    source = state.to_payload()
    reviewed_text = ReviewedJevTextBundle(
        source_scope_hash=source["candidate"]["scope_hash"],
        task_domain="synthetic review task",
        finding_summaries={
            item["id"]: f"Reviewed synthetic finding {index}."
            for index, item in enumerate(source["findings"], start=1)
        },
        overseer_assessment={
            "evidence_sufficiency": "Reviewed synthetic evidence supports comparison.",
            "impact": "The synthetic impact is moderate.",
            "residual_risk_context": "A bounded residual risk remains in the synthetic scenario.",
        },
        mitigation_summaries={
            item["id"]: f"Reviewed synthetic mitigation {index}."
            for index, item in enumerate(source["mitigation_options"], start=1)
        },
        mitigation_tradeoffs={
            item["id"]: [
                f"Reviewed synthetic tradeoff {index}-{tradeoff}."
                for tradeoff, _ in enumerate(item["tradeoffs"], start=1)
            ]
            for index, item in enumerate(source["mitigation_options"], start=1)
        },
        dissent_summaries={
            item["id"]: f"Reviewed synthetic dissent {index}."
            for index, item in enumerate(source["dissent"], start=1)
        },
    )
    return build_offline_jev_provider_projection_with_context(
        state, reviewed_text, nonce="synthetic-typesafe-adapter-test"
    )


def _projected_questions(state: OrchestraJevAdjudicationState) -> Mapping[str, Mapping[str, object]]:
    return json.loads(_request_projection(state)[0])["questions"]


def _adjudicate_with_projection(adapter, state, questions):
    return adapter.adjudicate(
        state,
        questions,
        request_projection=_request_projection(state),
    )


def _projected_mitigation_ids(payload: Mapping[str, Any]) -> list[str]:
    return [
        key
        for key in payload["answers"]["recommended_mitigation"]["probabilities"]
        if key != "NO_CLEAR_PREFERENCE"
    ]


def _typed_response(
    questions: Mapping[str, Mapping[str, object]],
    candidate_binding: JevCandidateBinding,
    *,
    recommendation: str = "M1",
) -> JevProviderResponse:
    answers = []
    for question_id, question in questions.items():
        if question["type"] == "noul":
            value = {
                "material_unresolved_uncertainty": 0.55,
                "material_specialist_dissent": 0.05,
                "unsupported_assumption_dependency": 0.42,
                "evidence_supports_M1": 0.88,
                "M1_introduces_scope_risk": 0.06,
                "M1_preserves_architecture": 0.98,
                "evidence_supports_M2": 0.07,
                "M2_introduces_scope_risk": 0.95,
                "M2_preserves_architecture": 0.04,
            }.get(question_id, 0.25)
            answers.append((question_id, JevNoulAnswer(value)))
            continue
        criteria = list(question["criteria"])
        if question_id == "recommended_mitigation":
            selected = recommendation
        elif question_id == "primary_decision_factor":
            selected = "SCOPE_CONTROL"
        else:
            selected = "SECURITY_RISK"
        answers.append(
            (
                question_id,
                JevChoiceAnswer(
                    selected,
                    0.81,
                    tuple((key, 1.0 if key == selected else 0.0) for key in criteria),
                ),
            )
        )
    return JevProviderResponse("jev-1.13.0", candidate_binding, tuple(answers))


class _CurrentBinding:
    def __init__(self, *bindings: JevCandidateBinding | None) -> None:
        self.bindings = list(bindings)

    def current_binding(self) -> JevCandidateBinding | None:
        if len(self.bindings) > 1:
            return self.bindings.pop(0)
        return self.bindings[0] if self.bindings else None


class _Provider:
    def __init__(self, response: JevProviderResponse | Exception | None = None) -> None:
        self.response = response
        self.calls: list[tuple[OrchestraJevAdjudicationState, dict[str, object]]] = []

    def adjudicate(self, state, questions):
        self.calls.append((state, dict(questions)))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response or _typed_response(questions, state.candidate_binding)


def _use_case(
    state: OrchestraJevAdjudicationState,
    provider: _Provider | None = None,
    *bindings: JevCandidateBinding | None,
) -> tuple[OrchestraJevAdjudicationUseCase, _Provider]:
    actual_provider = provider or _Provider()
    actual_bindings = bindings or (state.candidate_binding,)
    return (
        OrchestraJevAdjudicationUseCase(actual_provider, _CurrentBinding(*actual_bindings)),
        actual_provider,
    )


def _answer_payload(questions: Mapping[str, Mapping[str, object]]) -> dict[str, Any]:
    answers: dict[str, Any] = {}
    for question_id, question in questions.items():
        if question["type"] == "noul":
            answers[question_id] = {"type": "noul", "noul": 0.65}
        else:
            criteria = list(question["criteria"])
            selected = criteria[0]
            answers[question_id] = {
                "type": "choice",
                "choice": selected,
                "confidence": 0.81,
                "probabilities": {
                    key: 1.0 if key == selected else 0.0 for key in criteria
                },
            }
    return {
        "model": "jev-1.13.0",
        "answers": answers,
        "usage": {"input_tokens": 120, "output_tokens": 24},
    }


class _Response:
    status = 200

    def __init__(self, value: object) -> None:
        self.payload = value if isinstance(value, bytes) else json.dumps(value).encode("utf-8")
        self.read_limit: int | None = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, size: int = -1) -> bytes:
        self.read_limit = size
        return self.payload if size < 0 else self.payload[:size]


class _Opener:
    def __init__(self, response: _Response | Exception) -> None:
        self.response = response
        self.requests = []

    def open(self, request, *, timeout):
        self.requests.append((request, timeout))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_state_binds_complete_normalized_scope_deterministically_and_has_no_credential_field() -> None:
    first = _state()
    second = _state(
        task={"assurance_depth": "STANDARD", "risk_level": "MEDIUM", "domain": "security"}
    )
    assert first.candidate_binding.scope_hash == second.candidate_binding.scope_hash
    assert first.candidate_binding.scope_hash.startswith("sha256:")
    payload = first.to_payload()
    assert payload["candidate"]["commit"] == _CANDIDATE["commit"]
    assert "credential" not in json.dumps(payload).casefold()
    payload["credential"] = "test-only-not-a-secret"
    with pytest.raises(ValueError, match="state must match"):
        OrchestraJevAdjudicationState(payload)
    changed = _state(task={"domain": "security", "risk_level": "HIGH", "assurance_depth": "STANDARD"})
    assert changed.candidate_binding.scope_hash != first.candidate_binding.scope_hash
    forged = first.to_payload()
    forged["findings"][0]["summary"] = "Changed scope without rebinding."
    with pytest.raises(ValueError, match="scope_hash"):
        OrchestraJevAdjudicationState(forged)


@pytest.mark.parametrize(
    "candidate",
    [
        {"repository": "", "commit": "a" * 40, "tree": "b" * 40},
        {"repository": "Baelfyre/Orchestra", "commit": "short", "tree": "b" * 40},
        {"repository": "Baelfyre/Orchestra", "commit": "a" * 40, "tree": "bad"},
    ],
)
def test_state_requires_trusted_candidate_identity_shape(candidate: Mapping[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        _state(candidate=candidate)


def test_question_catalog_has_all_nine_nouls_and_three_typed_choices() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    expected_nouls = {
        "material_unresolved_uncertainty",
        "material_specialist_dissent",
        "unsupported_assumption_dependency",
        "evidence_supports_M1",
        "M1_introduces_scope_risk",
        "M1_preserves_architecture",
        "evidence_supports_M2",
        "M2_introduces_scope_risk",
        "M2_preserves_architecture",
    }
    assert set(questions) == expected_nouls | {
        "recommended_mitigation",
        "primary_decision_factor",
        "strongest_residual_risk",
    }
    assert len(questions) == 12
    assert all(questions[key]["type"] == "noul" for key in expected_nouls)
    assert all(set(questions[key]["criteria"]) == {"true", "false"} for key in expected_nouls)
    assert set(questions["recommended_mitigation"]["criteria"]) == {
        "M1",
        "M2",
        "NO_CLEAR_PREFERENCE",
    }
    assert set(questions["primary_decision_factor"]["criteria"]) == {
        "EVIDENCE_FIT",
        "RISK_REDUCTION",
        "ARCHITECTURE_FIT",
        "SCOPE_CONTROL",
        "REVERSIBILITY",
        "COMPATIBILITY",
        "NO_DOMINANT_FACTOR",
    }
    assert set(questions["strongest_residual_risk"]["criteria"]) == {
        "TECHNICAL_RISK",
        "SECURITY_RISK",
        "ARCHITECTURE_RISK",
        "SCOPE_RISK",
        "COMPATIBILITY_RISK",
        "EVIDENCE_GAP",
        "NO_MATERIAL_RESIDUAL_RISK",
    }


def test_question_catalog_is_dynamic_closed_and_serializes_deterministically() -> None:
    options = [*(_MITIGATIONS), {
        "id": "M3",
        "producers": ["Cipher", "Clockwork"],
        "summary": "Use a reversible configuration limit.",
        "addresses": ["F-001"],
        "tradeoffs": ["Small change.", "Requires configuration review."],
    }]
    state = _state(mitigation_options=options)
    builder = OrchestraJevQuestionBuilder()
    questions = builder.build(state)
    assert len(questions) == 15
    assert "evidence_supports_M3" in questions
    assert "M3_introduces_scope_risk" in questions
    assert "M3_preserves_architecture" in questions
    assert set(questions["recommended_mitigation"]["criteria"]) == {"M1", "M2", "M3", "NO_CLEAR_PREFERENCE"}
    assert builder.serialize(state) == builder.serialize(state)
    assert json.loads(builder.serialize(state)) == questions


@pytest.mark.parametrize(
    "mitigation_id",
    ["", "not stable", "NO_CLEAR_PREFERENCE", "x" * 65],
)
def test_state_rejects_unsafe_or_reserved_mitigation_ids(mitigation_id: str) -> None:
    options = [dict(_MITIGATIONS[0], id=mitigation_id), _MITIGATIONS[1]]
    with pytest.raises(ValueError):
        _state(mitigation_options=options)


def test_system_one_adapter_sends_one_exact_request_and_preserves_native_typed_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    request_projection = _request_projection(state)
    projected_request_bytes, _projection_context = request_projection
    projected_questions = json.loads(projected_request_bytes)["questions"]
    fake_secret = "test-only-not-a-secret"
    payload = _answer_payload(projected_questions)
    payload["request_id"] = "synthetic-ignored-metadata"
    payload["provider_metadata"] = {"trace": "synthetic-only"}
    opener = _Opener(_Response(payload))
    adapter = TypeSafeJevAdapter(lambda: fake_secret, opener=opener)
    response = adapter.adjudicate(
        state, questions, request_projection=request_projection
    )

    assert len(opener.requests) == 1
    request, timeout = opener.requests[0]
    request_payload = json.loads(request.data)
    serialized_state = json.dumps(request_payload["state"])
    assert request.full_url == "https://api.typesafe.ai/v1/systemone"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == f"Bearer {fake_secret}"
    assert request.get_header("Content-type") == "application/json"
    assert timeout == 60
    assert request.data == projected_request_bytes
    assert set(request_payload) == {"state", "model", "questions"}
    assert "Authorization" not in request_payload
    assert request_payload["state"]["contract"] == JEV_PROVIDER_PROJECTION_CONTRACT
    assert "candidate" not in request_payload["state"]
    assert "evidence_refs" not in serialized_state
    assert "F-001" not in request.data.decode("utf-8")
    assert request_payload["model"] == "jev-latest"
    assert request_payload["questions"] == projected_questions
    assert response.model == "jev-1.13.0"
    assert len(response.answers) == 12
    assert response.answer_map()["material_unresolved_uncertainty"].probability == 0.65
    assert response.answer_map()["recommended_mitigation"].selected == "M1"
    assert response.answer_map()["recommended_mitigation"].confidence == 0.81
    assert response.answer_map()["recommended_mitigation"].probabilities == (
        ("M1", 1.0),
        ("M2", 0.0),
        ("NO_CLEAR_PREFERENCE", 0.0),
    )
    assert not hasattr(response, "usage")
    assert not hasattr(response, "request_id")
    assert not caplog.records


def test_adapter_rejects_direct_raw_state_serialization_before_credential_or_network() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    credential_calls: list[bool] = []
    opener = _Opener(_Response(_answer_payload(_projected_questions(state))))
    adapter = TypeSafeJevAdapter(
        lambda: credential_calls.append(True) or "test-only-not-a-secret",
        opener=opener,
    )

    with pytest.raises(JevProviderFailure) as caught:
        adapter.adjudicate(state, questions)

    assert caught.value.code == "REQUEST_CONTRACT_REJECTED"
    assert credential_calls == []
    assert opener.requests == []


def test_adapter_rejects_projection_bytes_not_bound_to_local_context() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    request_bytes, context = _request_projection(state)
    credential_calls: list[bool] = []
    opener = _Opener(_Response(_answer_payload(json.loads(request_bytes)["questions"])))
    adapter = TypeSafeJevAdapter(
        lambda: credential_calls.append(True) or "test-only-not-a-secret",
        opener=opener,
    )

    with pytest.raises(JevProviderFailure) as caught:
        adapter.adjudicate(
            state,
            questions,
            request_projection=(request_bytes + b" ", context),
        )

    assert caught.value.code == "REQUEST_CONTRACT_REJECTED"
    assert credential_calls == []
    assert opener.requests == []


def test_adapter_rejects_raw_state_projection_from_caller_context() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    request_body = canonical_json_bytes(
        {"state": state.to_payload(), "model": "jev-latest", "questions": questions}
    )
    credential_calls: list[bool] = []
    opener = _Opener(_Response(_answer_payload(questions)))

    class _MaliciousContext(JevProviderRequestProjectionContext):
        def validate_request(self, supplied_state, supplied_bytes):
            return json.loads(supplied_bytes.decode("utf-8"))

        def restore_response(self, supplied_state, supplied_bytes, response):
            return response

    adapter = TypeSafeJevAdapter(
        lambda: credential_calls.append(True) or "test-only-not-a-secret",
        opener=opener,
    )
    with pytest.raises(JevProviderFailure) as caught:
        adapter.adjudicate(
            state,
            questions,
            request_projection=(request_body, _MaliciousContext()),
        )

    assert caught.value.code == "REQUEST_CONTRACT_REJECTED"
    assert credential_calls == []
    assert opener.requests == []


def test_adapter_rejects_unregistered_projection_context() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    request_body, _ = _request_projection(state)
    forged_context = object.__new__(JevProjectionMappingContext)
    credential_calls: list[bool] = []
    opener = _Opener(_Response(_answer_payload(json.loads(request_body)["questions"])))
    adapter = TypeSafeJevAdapter(
        lambda: credential_calls.append(True) or "test-only-not-a-secret",
        opener=opener,
    )

    with pytest.raises(JevProviderFailure) as caught:
        adapter.adjudicate(
            state,
            questions,
            request_projection=(request_body, forged_context),
        )

    assert caught.value.code == "REQUEST_CONTRACT_REJECTED"
    assert credential_calls == []
    assert opener.requests == []


def test_adapter_uses_trusted_projection_functions_not_context_methods(monkeypatch) -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    request_body, context = _request_projection(state)
    projected_questions = json.loads(request_body)["questions"]
    opener = _Opener(_Response(_answer_payload(projected_questions)))
    adapter = TypeSafeJevAdapter(lambda: "test-only-not-a-secret", opener=opener)
    monkeypatch.setattr(
        JevProjectionMappingContext,
        "validate_request",
        lambda self, supplied_state, supplied_bytes: json.loads(
            canonical_json_bytes(
                {"state": state.to_payload(), "model": "jev-latest", "questions": questions}
            ).decode("utf-8")
        ),
    )
    monkeypatch.setattr(
        JevProjectionMappingContext,
        "restore_response",
        lambda self, supplied_state, supplied_bytes, response: response,
    )

    response = adapter.adjudicate(
        state,
        questions,
        request_projection=(request_body, context),
    )

    sent = opener.requests[0][0].data
    sent_payload = json.loads(sent)
    assert sent == request_body
    assert "candidate" not in sent_payload["state"]
    assert "evidence_refs" not in json.dumps(sent_payload["state"])
    assert "F-001" not in sent.decode("utf-8")
    assert response.candidate_binding == state.candidate_binding


def test_adapter_projection_authorization_rejects_sequential_replay_before_credentials() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    request_projection = _request_projection(state)
    credential_calls: list[bool] = []
    opener = _Opener(
        _Response(_answer_payload(json.loads(request_projection[0])["questions"]))
    )
    adapter = TypeSafeJevAdapter(
        lambda: credential_calls.append(True) or "test-only-not-a-secret",
        opener=opener,
    )

    adapter.adjudicate(state, questions, request_projection=request_projection)
    with pytest.raises(JevProviderFailure) as caught:
        adapter.adjudicate(state, questions, request_projection=request_projection)

    assert caught.value.code == "REQUEST_CONTRACT_REJECTED"
    assert credential_calls == [True]
    assert len(opener.requests) == 1


def test_adapter_projection_authorization_rejects_concurrent_replay() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    request_projection = _request_projection(state)
    credential_calls: list[bool] = []
    opener = _Opener(
        _Response(_answer_payload(json.loads(request_projection[0])["questions"]))
    )
    adapter = TypeSafeJevAdapter(
        lambda: credential_calls.append(True) or "test-only-not-a-secret",
        opener=opener,
    )
    start = Barrier(2)

    def attempt():
        start.wait()
        try:
            return adapter.adjudicate(
                state, questions, request_projection=request_projection
            )
        except JevProviderFailure as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = [executor.submit(attempt) for _ in range(2)]
        results = [future.result() for future in outcomes]

    assert sum(isinstance(result, JevProviderFailure) for result in results) == 1
    failure = next(result for result in results if isinstance(result, JevProviderFailure))
    assert failure.code == "REQUEST_CONTRACT_REJECTED"
    assert sum(not isinstance(result, JevProviderFailure) for result in results) == 1
    assert credential_calls == [True]
    assert len(opener.requests) == 1


def test_adapter_rejects_incomplete_local_catalog_before_network_call() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    questions.pop("material_specialist_dissent")
    opener = _Opener(_Response(_answer_payload(OrchestraJevQuestionBuilder().build(state))))
    adapter = TypeSafeJevAdapter(lambda: "test-only-not-a-secret", opener=opener)
    with pytest.raises(ValueError, match="complete local Orchestra catalog"):
        adapter.adjudicate(state, questions)
    assert opener.requests == []


def test_adapter_rejects_choice_without_required_confidence() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    payload = _answer_payload(_projected_questions(state))
    choice = payload["answers"]["recommended_mitigation"]
    del choice["confidence"]
    adapter = TypeSafeJevAdapter(lambda: "test-only-not-a-secret", opener=_Opener(_Response(payload)))
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "RESPONSE_CONTRACT_INCOMPATIBLE"


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda payload: payload.pop("usage"), id="missing-usage"),
        pytest.param(lambda payload: payload["usage"].pop("input_tokens"), id="missing-input-tokens"),
        pytest.param(lambda payload: payload["usage"].pop("output_tokens"), id="missing-output-tokens"),
        pytest.param(lambda payload: payload["usage"].update(input_tokens=-1), id="negative-input-tokens"),
        pytest.param(lambda payload: payload["usage"].update(output_tokens=-1), id="negative-output-tokens"),
        pytest.param(lambda payload: payload["usage"].update(input_tokens=True), id="boolean-input-tokens"),
        pytest.param(lambda payload: payload["usage"].update(output_tokens=False), id="boolean-output-tokens"),
        pytest.param(lambda payload: payload["usage"].update(input_tokens=1.0), id="fractional-input-tokens"),
    ],
)
def test_adapter_rejects_missing_or_invalid_usage_counts(mutate) -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    payload = _answer_payload(_projected_questions(state))
    mutate(payload)
    adapter = TypeSafeJevAdapter(lambda: "test-only-not-a-secret", opener=_Opener(_Response(payload)))
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "RESPONSE_CONTRACT_INCOMPATIBLE"


@pytest.mark.parametrize(
    "confidence",
    [
        pytest.param(float("nan"), id="nan"),
        pytest.param(float("inf"), id="infinity"),
        pytest.param(-0.01, id="below-zero"),
        pytest.param(1.01, id="above-one"),
        pytest.param(True, id="boolean"),
        pytest.param("0.81", id="string"),
    ],
)
def test_adapter_rejects_invalid_choice_confidence(confidence: object) -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    payload = _answer_payload(_projected_questions(state))
    payload["answers"]["recommended_mitigation"]["confidence"] = confidence
    adapter = TypeSafeJevAdapter(lambda: "test-only-not-a-secret", opener=_Opener(_Response(payload)))
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "RESPONSE_CONTRACT_INCOMPATIBLE"


def test_adapter_rejects_choice_that_is_not_a_maximum_probability_option() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    payload = _answer_payload(_projected_questions(state))
    mitigation_ids = _projected_mitigation_ids(payload)
    choice = payload["answers"]["recommended_mitigation"]
    choice["choice"] = mitigation_ids[1]
    choice["probabilities"] = {
        mitigation_ids[0]: 0.5,
        mitigation_ids[1]: 0.4,
        "NO_CLEAR_PREFERENCE": 0.1,
    }
    adapter = TypeSafeJevAdapter(lambda: "test-only-not-a-secret", opener=_Opener(_Response(payload)))
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "RESPONSE_CONTRACT_INCOMPATIBLE"


def test_adapter_allows_equal_probability_choice_tie() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    payload = _answer_payload(_projected_questions(state))
    mitigation_ids = _projected_mitigation_ids(payload)
    payload["answers"]["recommended_mitigation"].update(
        choice=mitigation_ids[1],
        confidence=0.5,
        probabilities={
            mitigation_ids[0]: 0.5,
            mitigation_ids[1]: 0.5,
            "NO_CLEAR_PREFERENCE": 0.0,
        },
    )
    adapter = TypeSafeJevAdapter(lambda: "test-only-not-a-secret", opener=_Opener(_Response(payload)))
    response = _adjudicate_with_projection(adapter, state, questions)
    answer = response.answer_map()["recommended_mitigation"]
    assert answer.selected == "M2"
    assert answer.probabilities == (("M1", 0.5), ("M2", 0.5), ("NO_CLEAR_PREFERENCE", 0.0))


def test_adapter_rejects_score_answers_for_current_catalog() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    payload = _answer_payload(_projected_questions(state))
    payload["answers"]["material_unresolved_uncertainty"] = {"type": "score", "score": 0.65}
    adapter = TypeSafeJevAdapter(lambda: "test-only-not-a-secret", opener=_Opener(_Response(payload)))
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "RESPONSE_CONTRACT_INCOMPATIBLE"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload["answers"].pop("material_specialist_dissent"),
        lambda payload: payload["answers"]["material_specialist_dissent"].update(type="choice"),
        lambda payload: payload["answers"]["material_unresolved_uncertainty"].update(noul=float("nan")),
        lambda payload: payload["answers"]["recommended_mitigation"].update(choice="UNSUPPLIED"),
        lambda payload: payload["answers"]["recommended_mitigation"]["probabilities"].pop(
            _projected_mitigation_ids(payload)[1]
        ),
        lambda payload: payload["answers"]["recommended_mitigation"]["probabilities"].update(
            {
                _projected_mitigation_ids(payload)[0]: 0.5,
                _projected_mitigation_ids(payload)[1]: 0.25,
                "NO_CLEAR_PREFERENCE": 0.0,
            }
        ),
        lambda payload: payload["answers"].update(
            unknown_question={"type": "noul", "noul": 0.5}
        ),
        lambda payload: payload.update(model="other-model"),
    ],
)
def test_adapter_rejects_incomplete_or_malformed_typed_response(mutate) -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    payload = _answer_payload(_projected_questions(state))
    mutate(payload)
    adapter = TypeSafeJevAdapter(lambda: "test-only-not-a-secret", opener=_Opener(_Response(payload)))
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "RESPONSE_CONTRACT_INCOMPATIBLE"


def test_adapter_bounds_response_body_before_json_parsing() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    response = _Response(b"x" * (4 * 1024 * 1024 + 1))
    adapter = TypeSafeJevAdapter(lambda: "test-only-not-a-secret", opener=_Opener(response))

    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)

    assert caught.value.code == "RESPONSE_CONTRACT_INCOMPATIBLE"
    assert caught.value.http_status == 200
    assert response.read_limit == len(response.payload)


def test_adapter_maps_auth_schema_and_transport_failures_without_retry_or_body_disclosure() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    cases = (
        (urllib.error.HTTPError("https://example.invalid", 401, "unauthorized", None, io.BytesIO(b"private")), "AUTHENTICATION_FAILED"),
        (urllib.error.HTTPError("https://example.invalid", 422, "invalid", None, io.BytesIO(b"private")), "REQUEST_CONTRACT_REJECTED"),
        (TimeoutError("private transport text"), "TRANSPORT_FAILURE"),
    )
    for exception, code in cases:
        opener = _Opener(exception)
        adapter = TypeSafeJevAdapter(lambda: "test-only-not-a-secret", opener=opener)
        with pytest.raises(JevProviderFailure) as caught:
            _adjudicate_with_projection(adapter, state, questions)
        assert caught.value.code == code
        assert caught.value.http_status in (None, 401, 422)
        assert len(opener.requests) == 1
        assert "private" not in str(caught.value)


def test_unavailable_credential_is_not_loaded_from_environment_or_serialized() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    adapter = TypeSafeJevAdapter(lambda: "")
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "CREDENTIAL_UNAVAILABLE"
    assert "TYPESAFE_API_KEY" not in adapter.__dict__


def test_interpreter_preserves_uncertainty_dissent_assumption_and_all_choice_distributions() -> None:
    state = _state(
        dissent=[{
            "id": "D-001",
            "producer": "Clockwork",
            "summary": "The subsystem option may increase future maintenance cost.",
            "evidence_refs": ["E-003"],
        }]
    )
    questions = OrchestraJevQuestionBuilder().build(state)
    response = _typed_response(questions, state.candidate_binding)
    result = OrchestraJevInterpreter().interpret(state, response, state.candidate_binding)
    serialized = result.to_dict()
    assert result.advisory_state == JEV_ADVISORY_RECOMMENDATION_AVAILABLE
    assert result.recommendation == "M1"
    assert serialized["answers"]["material_unresolved_uncertainty"]["noul"] == 0.55
    assert serialized["answers"]["material_specialist_dissent"]["noul"] == 0.05
    assert serialized["answers"]["unsupported_assumption_dependency"]["noul"] == 0.42
    assert serialized["answers"]["recommended_mitigation"]["probabilities"]["M1"] == 1.0
    assert serialized["answers"]["primary_decision_factor"]["confidence"] == 0.81
    assert serialized["answers"]["strongest_residual_risk"]["probabilities"]["SECURITY_RISK"] == 1.0
    assert serialized["model_provenance"]["resolved_model"] == "jev-1.13.0"
    assert serialized["task"] == {"risk_level": "MEDIUM", "assurance_depth": "STANDARD"}


def test_no_clear_preference_is_inconclusive_without_probability_thresholds() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    result = OrchestraJevInterpreter().interpret(
        state,
        _typed_response(questions, state.candidate_binding, recommendation="NO_CLEAR_PREFERENCE"),
        state.candidate_binding,
    )
    assert result.advisory_state == JEV_ADVISORY_INCONCLUSIVE
    assert result.recommendation == "NO_CLEAR_PREFERENCE"
    assert len(result.answers) == 12
    assert result.resolved_model == "jev-1.13.0"
    assert result.to_dict()["answers"]["material_unresolved_uncertainty"]["noul"] == 0.55


@pytest.mark.parametrize("field", ["commit", "tree", "scope_hash"])
def test_interpreter_marks_candidate_binding_mismatch_stale(field: str) -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    candidate = state.candidate_binding.to_dict()
    if field == "scope_hash":
        changed_state = _state(task={"domain": "security", "risk_level": "HIGH", "assurance_depth": "STANDARD"})
        current = changed_state.candidate_binding
    else:
        candidate[field] = "c" * 40
        current = JevCandidateBinding.from_mapping(candidate)
    response = _typed_response(questions, state.candidate_binding)
    result = OrchestraJevInterpreter().interpret(state, response, current)
    assert result.advisory_state == JEV_ADVISORY_STALE
    assert result.recommendation is None
    assert result.answers == ()
    assert result.resolved_model is None
    serialized = result.to_dict()
    assert serialized["answers"] == {}
    assert serialized["model_provenance"]["resolved_model"] is None


def test_interpreter_marks_missing_trusted_binding_unbound() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    response = _typed_response(questions, state.candidate_binding)
    result = OrchestraJevInterpreter().interpret(state, response, None)
    assert result.advisory_state == JEV_ADVISORY_UNBOUND
    assert result.recommendation is None
    assert result.answers == ()
    assert result.resolved_model is None
    serialized = result.to_dict()
    assert serialized["answers"] == {}
    assert serialized["model_provenance"]["resolved_model"] is None


@pytest.mark.parametrize("advisory_state", [JEV_ADVISORY_STALE, JEV_ADVISORY_UNBOUND])
def test_direct_stale_or_unbound_result_construction_redacts_provider_fields(advisory_state: str) -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    response = _typed_response(questions, state.candidate_binding)
    current_binding = (
        _state(task={"domain": "security", "risk_level": "HIGH", "assurance_depth": "STANDARD"}).candidate_binding
        if advisory_state == JEV_ADVISORY_STALE
        else None
    )

    result = JevAdvisoryResult(
        candidate_binding=response.candidate_binding,
        advisory_state=advisory_state,
        risk_level="MEDIUM",
        assurance_depth="STANDARD",
        answers=response.answers,
        resolved_model=response.model,
        recommendation="M1",
        current_candidate_binding=current_binding,
    )

    assert result.candidate_binding == state.candidate_binding
    assert result.current_candidate_binding == current_binding
    assert result.answers == ()
    assert result.resolved_model is None
    assert result.recommendation is None
    serialized = result.to_dict()
    assert serialized["candidate"] == state.candidate_binding.to_dict()
    assert serialized["current_candidate"] == (
        None if current_binding is None else current_binding.to_dict()
    )
    assert serialized["answers"] == {}
    assert serialized["recommendation"] is None
    assert serialized["model_provenance"]["resolved_model"] is None


def test_interpreter_rejects_replayed_typed_answers_bound_to_an_older_scope() -> None:
    original = _state()
    current = _state(task={"domain": "security", "risk_level": "HIGH", "assurance_depth": "STANDARD"})
    old_response = _typed_response(
        OrchestraJevQuestionBuilder().build(original), original.candidate_binding
    )
    result = OrchestraJevInterpreter().interpret(current, old_response, current.candidate_binding)
    assert result.advisory_state == JEV_ADVISORY_STALE
    assert result.recommendation is None
    assert result.candidate_binding == original.candidate_binding
    assert result.current_candidate_binding == current.candidate_binding
    assert result.answers == ()
    assert result.resolved_model is None
    serialized = result.to_dict()
    assert serialized["answers"] == {}
    assert serialized["model_provenance"]["resolved_model"] is None


def test_application_makes_one_call_only_after_upstream_is_ready() -> None:
    state = _state()
    use_case, provider = _use_case(state)
    result = use_case.execute(state)
    assert result.advisory_state == JEV_ADVISORY_RECOMMENDATION_AVAILABLE
    assert len(provider.calls) == 1
    assert provider.calls[0][0] is state
    assert len(provider.calls[0][1]) == 12


@pytest.mark.parametrize(
    ("overrides", "failure_code"),
    [
        ({"findings": [{**_FINDING, "status": "UNVERIFIED"}], "verification": []}, "VERIFIED_FINDINGS_REQUIRED"),
        ({"overseer_assessment": None}, "OVERSEER_ASSESSMENT_REQUIRED"),
        ({"verification": [{**_VERIFICATION, "result": "INCOMPLETE"}]}, "EMPIRICAL_VERIFICATION_INCOMPLETE"),
        ({"verification": [{**_VERIFICATION, "result": "NOT_STARTED"}]}, "EMPIRICAL_VERIFICATION_INCOMPLETE"),
        ({"verification": [{**_VERIFICATION, "result": "PENDING"}]}, "EMPIRICAL_VERIFICATION_INCOMPLETE"),
        ({"verification": [{**_VERIFICATION, "result": "RUNNING"}]}, "EMPIRICAL_VERIFICATION_INCOMPLETE"),
    ],
)
def test_application_blocks_when_upstream_evidence_is_missing_or_incomplete(
    overrides: dict[str, object], failure_code: str
) -> None:
    state = _state(**overrides)
    use_case, provider = _use_case(state)
    with pytest.raises(JevAdjudicationEligibilityError) as caught:
        use_case.execute(state)
    assert caught.value.code == failure_code
    assert provider.calls == []


@pytest.mark.parametrize("field", ["commit", "tree", "scope_hash"])
def test_application_does_not_call_provider_for_stale_candidate(field: str) -> None:
    state = _state()
    candidate = state.candidate_binding.to_dict()
    if field == "scope_hash":
        current = _state(task={"domain": "security", "risk_level": "HIGH", "assurance_depth": "STANDARD"}).candidate_binding
    else:
        candidate[field] = "c" * 40
        current = JevCandidateBinding.from_mapping(candidate)
    use_case, provider = _use_case(state, None, current)
    result = use_case.execute(state)
    assert result.advisory_state == JEV_ADVISORY_STALE
    assert result.answers == ()
    assert result.resolved_model is None
    assert result.to_dict()["answers"] == {}
    assert result.to_dict()["model_provenance"]["resolved_model"] is None
    assert provider.calls == []


def test_application_rechecks_candidate_after_provider_returns_and_stales_replayed_scope() -> None:
    state = _state()
    changed = _state(task={"domain": "security", "risk_level": "HIGH", "assurance_depth": "STANDARD"})
    use_case, provider = _use_case(state, None, state.candidate_binding, changed.candidate_binding)
    result = use_case.execute(state)
    assert result.advisory_state == JEV_ADVISORY_STALE
    assert result.recommendation is None
    assert result.answers == ()
    assert result.resolved_model is None
    assert len(provider.calls) == 1
    serialized = result.to_dict()
    assert serialized["answers"] == {}
    assert serialized["model_provenance"]["resolved_model"] is None


@pytest.mark.parametrize("options", [[], [_MITIGATIONS[0]], [_MITIGATIONS[0], dict(_MITIGATIONS[0], id="M3")]])
def test_application_skips_jev_when_no_material_competing_alternatives(options) -> None:
    state = _state(mitigation_options=options)
    use_case, provider = _use_case(state)
    result = use_case.execute(state)
    assert result.advisory_state == JEV_NOT_REQUIRED
    assert provider.calls == []


def test_provider_failures_are_optional_unavailable_advice() -> None:
    state = _state()
    provider = _Provider(JevProviderFailure("AUTHENTICATION_FAILED", 401))
    use_case, _ = _use_case(state, provider)
    result = use_case.execute(state)
    assert result.advisory_state == JEV_UNAVAILABLE
    assert result.failure_code == "AUTHENTICATION_FAILED"
    assert result.recommendation is None


def test_provider_failure_text_is_not_retained_or_returned() -> None:
    state = _state()
    provider = _Provider(RuntimeError("sensitive provider response text"))
    use_case, _ = _use_case(state, provider)
    result = use_case.execute(state)
    assert result.advisory_state == JEV_UNAVAILABLE
    assert result.failure_code == "PROVIDER_FAILURE"
    assert "sensitive provider response text" not in json.dumps(result.to_dict())


def test_advisory_result_has_no_governance_or_execution_authority_and_cannot_lower_risk() -> None:
    state = _state()
    before = state.to_payload()
    use_case, _ = _use_case(state)
    result = use_case.execute(state)
    serialized = result.to_dict()
    assert serialized["advisory_only"] is True
    assert serialized["may_authorize"] is False
    assert serialized["authority_effect"] == "NONE"
    assert serialized["task"] == {"risk_level": "MEDIUM", "assurance_depth": "STANDARD"}
    assert not {
        "governance_validated",
        "governance_approval",
        "execution_authority",
        "arbiter_transition_decision",
        "execution_envelope",
        "implementation_instruction",
    } & set(serialized)
    assert state.to_payload() == before


def test_type_safe_adapter_does_not_persist_the_authorization_header() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    opener = _Opener(_Response(_answer_payload(_projected_questions(state))))
    adapter = TypeSafeJevAdapter(lambda: "test-only-not-a-secret", opener=opener)
    response = _adjudicate_with_projection(adapter, state, questions)
    assert "Authorization" not in adapter.__dict__
    assert all("Authorization" not in answer.to_dict() for _, answer in response.answers)

# F3_BRANCH_COVERAGE_DEFENSIVE_REGRESSIONS


def test_use_case_defensive_runtime_contracts_and_unbound_lookup() -> None:
    state = _state()

    with pytest.raises(TypeError):
        OrchestraJevAdjudicationUseCase(object(), _CurrentBinding(state.candidate_binding))

    with pytest.raises(TypeError):
        OrchestraJevAdjudicationUseCase(_Provider(), object())

    use_case, _ = _use_case(state)
    with pytest.raises(TypeError):
        use_case.execute(object())

    use_case, provider = _use_case(state, _Provider(object()))
    result = use_case.execute(state)
    assert result.advisory_state == JEV_UNAVAILABLE
    assert result.failure_code == "RESPONSE_CONTRACT_INCOMPATIBLE"
    assert len(provider.calls) == 1

    use_case, provider = _use_case(state, None, None)
    result = use_case.execute(state)
    assert result.advisory_state == JEV_ADVISORY_UNBOUND
    assert provider.calls == []

    class _BrokenBinding:
        def current_binding(self):
            raise RuntimeError("synthetic trusted-binding failure")

    use_case = OrchestraJevAdjudicationUseCase(_Provider(), _BrokenBinding())
    result = use_case.execute(state)
    assert result.advisory_state == JEV_ADVISORY_UNBOUND

    class _RejectingInterpreter(OrchestraJevInterpreter):
        def interpret(self, *args, **kwargs):
            raise ValueError("synthetic typed-response rejection")

    use_case, provider = _use_case(state)
    use_case._interpreter = _RejectingInterpreter()
    result = use_case.execute(state)
    assert result.advisory_state == JEV_UNAVAILABLE
    assert result.failure_code == "RESPONSE_CONTRACT_INCOMPATIBLE"
    assert len(provider.calls) == 1


def test_domain_json_and_candidate_guards_cover_fail_closed_inputs() -> None:
    from orchestra_runtime.domain.adaptive import jev_adjudication as jev

    invalid_calls = (
        lambda: jev._as_json_mapping([], "value"),
        lambda: jev._as_json_mapping({1: "value"}, "value"),
        lambda: jev._as_json_mapping({"value": float("nan")}, "value"),
        lambda: jev._as_json_list({}, "value"),
        lambda: jev._as_json_list([float("nan")], "value"),
        lambda: jev._require_keys({"wrong": True}, {"expected"}, "value"),
        lambda: jev._validate_candidate({}),
        lambda: jev._validate_candidate(
            {
                "repository": "Baelfyre/Orchestra",
                "commit": "a" * 40,
                "tree": "b" * 40,
                "scope_hash": "not-sha256",
            }
        ),
    )

    for call in invalid_calls:
        with pytest.raises(ValueError):
            call()


def test_state_nested_contract_rejections_cover_defensive_branches() -> None:
    def reject(mutator) -> None:
        payload = _state().to_payload()
        mutator(payload)
        with pytest.raises(ValueError):
            OrchestraJevAdjudicationState(payload)

    reject(lambda p: p["task"].update(risk_level="UNKNOWN"))
    reject(lambda p: p.__setitem__("findings", [{}]))
    reject(lambda p: p["findings"].append(dict(p["findings"][0])))
    reject(lambda p: p.__setitem__("verification", [{}]))
    reject(lambda p: p["verification"].append(dict(p["verification"][0])))
    reject(lambda p: p["verification"][0].update(finding_id="F-UNKNOWN"))
    reject(lambda p: p["verification"][0].update(producer=""))
    reject(lambda p: p.__setitem__("mitigation_options", [{}]))
    reject(lambda p: p["mitigation_options"][0].update(addresses=["F-UNKNOWN"]))
    reject(lambda p: p.__setitem__("dissent", ["not-a-record"]))
    reject(
        lambda p: p.__setitem__(
            "dissent",
            [{
                "id": "bad id",
                "producer": "Clockwork",
                "summary": "Synthetic invalid dissent identifier.",
                "evidence_refs": ["E-003"],
            }],
        )
    )
    reject(
        lambda p: p.__setitem__(
            "constraints",
            {
                "protected_policy_change_allowed": False,
                "authority_change_allowed": False,
            },
        )
    )
    reject(
        lambda p: p.__setitem__(
            "constraints",
            {
                "protected_policy_change_allowed": False,
                "authority_change_allowed": False,
                "scope_expansion_allowed": 1,
            },
        )
    )


def test_create_string_list_and_eligibility_guards() -> None:
    from orchestra_runtime.domain.adaptive import jev_adjudication as jev

    with pytest.raises(ValueError, match="candidate input"):
        _state(
            candidate={
                "repository": "Baelfyre/Orchestra",
                "commit": "a" * 40,
                "tree": "b" * 40,
                "extra": "unexpected",
            }
        )

    for value, nonempty in (
        ((), False),
        ([], True),
        ([""], False),
    ):
        with pytest.raises(ValueError):
            jev._validate_string_list(value, "synthetic", nonempty=nonempty)

    state = _state(
        findings=[{**_FINDING, "verification_required": True}],
        verification=[],
    )
    use_case, provider = _use_case(state)
    with pytest.raises(JevAdjudicationEligibilityError) as caught:
        use_case.execute(state)

    assert caught.value.code == "EMPIRICAL_VERIFICATION_REQUIRED"
    assert state.to_payload()["findings"][0]["verification_required"] is True
    assert provider.calls == []

    with pytest.raises(TypeError):
        OrchestraJevQuestionBuilder().build(object())


@pytest.mark.parametrize("flag", [None, False])
def test_verification_requirement_is_optional_when_not_enabled(flag: bool | None) -> None:
    finding = dict(_FINDING)
    if flag is not None:
        finding["verification_required"] = flag
    state = _state(findings=[finding], verification=[])
    use_case, provider = _use_case(state)
    result = use_case.execute(state)
    assert result.advisory_state == JEV_ADVISORY_RECOMMENDATION_AVAILABLE
    assert len(provider.calls) == 1


@pytest.mark.parametrize("value", [1, "true", None])
def test_verification_required_rejects_non_boolean_values(value: object) -> None:
    with pytest.raises(ValueError, match="verification_required"):
        _state(findings=[{**_FINDING, "verification_required": value}])


@pytest.mark.parametrize("result", ["NOT_CONFIRMED", "PRIVATE_RESULT", "confirmed"])
def test_verification_rejects_unsupported_results(result: str) -> None:
    with pytest.raises(ValueError, match="verification.result is unsupported"):
        _state(verification=[{**_VERIFICATION, "result": result}])


def test_confirmed_verification_requires_supporting_evidence() -> None:
    with pytest.raises(ValueError, match="verification.evidence_refs"):
        _state(verification=[{**_VERIFICATION, "evidence_refs": []}])


def test_conflicting_verification_records_fail_closed_before_provider_call() -> None:
    state = _state(
        verification=[
            _VERIFICATION,
            {**_VERIFICATION, "id": "V-002", "result": "PENDING"},
        ]
    )
    use_case, provider = _use_case(state)
    with pytest.raises(JevAdjudicationEligibilityError) as caught:
        use_case.execute(state)
    assert caught.value.code == "EMPIRICAL_VERIFICATION_INCOMPLETE"
    assert provider.calls == []


def test_typed_answer_and_provider_response_guards() -> None:
    from orchestra_runtime.domain.adaptive import jev_adjudication as jev

    state = _state()
    binding = state.candidate_binding

    with pytest.raises(ValueError):
        JevNoulAnswer(True)

    with pytest.raises(ValueError):
        JevNoulAnswer(float("nan"))

    with pytest.raises(ValueError):
        JevChoiceAnswer("M1", None, ())

    with pytest.raises(ValueError):
        JevChoiceAnswer(
            "M1",
            None,
            (("M1", 0.5), ("M1", 0.5)),
        )

    with pytest.raises(ValueError):
        JevChoiceAnswer(
            "M1",
            None,
            (("M1", 0.4), ("M2", 0.4)),
        )

    with pytest.raises(ValueError):
        JevChoiceAnswer(
            "M1",
            None,
            (("M2", 0.5), ("M3", 0.5)),
        )

    with pytest.raises(TypeError):
        JevProviderResponse("jev-1.13.0", object(), ())

    with pytest.raises(ValueError):
        JevProviderResponse(
            "jev-1.13.0",
            binding,
            (
                ("duplicate", JevNoulAnswer(0.5)),
                ("duplicate", JevNoulAnswer(0.5)),
            ),
        )

    with pytest.raises(TypeError):
        JevProviderResponse(
            "jev-1.13.0",
            binding,
            (("question", object()),),
        )

    common = {
        "candidate_binding": binding,
        "risk_level": "MEDIUM",
        "assurance_depth": "STANDARD",
    }

    with pytest.raises(ValueError):
        jev.JevAdvisoryResult(
            advisory_state="UNKNOWN",
            **common,
        )

    with pytest.raises(ValueError):
        jev.JevAdvisoryResult(
            advisory_state=JEV_UNAVAILABLE,
            candidate_binding=binding,
            risk_level="UNKNOWN",
            assurance_depth="STANDARD",
        )

    with pytest.raises(ValueError):
        jev.JevAdvisoryResult(
            advisory_state=JEV_ADVISORY_RECOMMENDATION_AVAILABLE,
            **common,
        )

    with pytest.raises(ValueError):
        jev.JevAdvisoryResult(
            advisory_state=JEV_UNAVAILABLE,
            recommendation="NO_CLEAR_PREFERENCE",
            **common,
        )

    with pytest.raises(ValueError):
        jev.JevAdvisoryResult(
            advisory_state=JEV_UNAVAILABLE,
            resolved_model="not-a-jev-model",
            **common,
        )


def test_interpreter_rejects_structurally_invalid_typed_responses() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    normal = _typed_response(questions, state.candidate_binding)
    interpreter = OrchestraJevInterpreter()

    with pytest.raises(TypeError):
        interpreter.interpret(object(), normal, state.candidate_binding)

    with pytest.raises(TypeError):
        interpreter.interpret(state, object(), state.candidate_binding)

    incomplete = JevProviderResponse(
        "jev-1.13.0",
        state.candidate_binding,
        (),
    )
    with pytest.raises(ValueError, match="complete question catalog"):
        interpreter.interpret(state, incomplete, state.candidate_binding)

    def replace(question_id, replacement):
        return JevProviderResponse(
            normal.model,
            normal.candidate_binding,
            tuple(
                (key, replacement if key == question_id else answer)
                for key, answer in normal.answers
            ),
        )

    wrong_noul = JevChoiceAnswer(
        "true",
        None,
        (("true", 1.0), ("false", 0.0)),
    )
    with pytest.raises(ValueError, match="Noul"):
        interpreter.interpret(
            state,
            replace("material_unresolved_uncertainty", wrong_noul),
            state.candidate_binding,
        )

    wrong_choice_criteria = JevChoiceAnswer(
        "M1",
        None,
        (("M1", 1.0), ("EXTRA", 0.0)),
    )
    with pytest.raises(ValueError, match="criteria"):
        interpreter.interpret(
            state,
            replace("recommended_mitigation", wrong_choice_criteria),
            state.candidate_binding,
        )

    criteria = list(questions["recommended_mitigation"]["criteria"])
    corrupted_choice = JevChoiceAnswer(
        criteria[0],
        None,
        tuple(
            (criterion, 1.0 if criterion == criteria[0] else 0.0)
            for criterion in criteria
        ),
    )
    object.__setattr__(corrupted_choice, "selected", "OUTSIDE_LOCAL_CRITERIA")

    with pytest.raises(ValueError, match="outside its criteria"):
        interpreter.interpret(
            state,
            replace("recommended_mitigation", corrupted_choice),
            state.candidate_binding,
        )

    with pytest.raises(TypeError):
        interpreter.unavailable(object(), "TRANSPORT_FAILURE")


def test_typesafe_adapter_constructor_and_local_input_guards() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)

    with pytest.raises(TypeError):
        TypeSafeJevAdapter(None)

    for invalid_timeout in (True, 0, -1, 1.5):
        with pytest.raises(ValueError):
            TypeSafeJevAdapter(lambda: "test-only-not-a-secret", timeout_seconds=invalid_timeout)

    adapter = TypeSafeJevAdapter(
        lambda: "test-only-not-a-secret",
        opener=_Opener(_Response(_answer_payload(_projected_questions(state)))),
    )

    with pytest.raises(TypeError):
        adapter.adjudicate(object(), questions)

    def broken_credential():
        raise RuntimeError("synthetic credential lookup failure")

    adapter = TypeSafeJevAdapter(
        broken_credential,
        opener=_Opener(_Response(_answer_payload(_projected_questions(state)))),
    )
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "CREDENTIAL_UNAVAILABLE"


def test_typesafe_adapter_rejects_non_http_success_contract_failures() -> None:
    state = _state()
    questions = OrchestraJevQuestionBuilder().build(state)
    projected_questions = _projected_questions(state)

    response = _Response(_answer_payload(projected_questions))
    response.status = 500
    adapter = TypeSafeJevAdapter(
        lambda: "test-only-not-a-secret",
        opener=_Opener(response),
    )
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "TRANSPORT_FAILURE"

    adapter = TypeSafeJevAdapter(
        lambda: "test-only-not-a-secret",
        opener=_Opener(_Response(b"{not-json")),
    )
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "RESPONSE_CONTRACT_INCOMPATIBLE"

    for payload in (
        [],
        {"error": "synthetic"},
        {"model": None, "answers": {}},
    ):
        adapter = TypeSafeJevAdapter(
            lambda: "test-only-not-a-secret",
            opener=_Opener(_Response(payload)),
        )
        with pytest.raises(JevProviderFailure) as caught:
            _adjudicate_with_projection(adapter, state, questions)
        assert caught.value.code == "RESPONSE_CONTRACT_INCOMPATIBLE"

    payload = _answer_payload(projected_questions)
    first_question = next(iter(payload["answers"]))
    payload["answers"][first_question] = None
    adapter = TypeSafeJevAdapter(
        lambda: "test-only-not-a-secret",
        opener=_Opener(_Response(payload)),
    )
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "RESPONSE_CONTRACT_INCOMPATIBLE"

    payload = _answer_payload(projected_questions)
    payload["answers"]["material_unresolved_uncertainty"]["noul"] = True
    adapter = TypeSafeJevAdapter(
        lambda: "test-only-not-a-secret",
        opener=_Opener(_Response(payload)),
    )
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "RESPONSE_CONTRACT_INCOMPATIBLE"

    failed_opener = _Opener(RuntimeError("synthetic opener failure"))
    adapter = TypeSafeJevAdapter(
        lambda: "test-only-not-a-secret",
        opener=failed_opener,
    )
    with pytest.raises(JevProviderFailure) as caught:
        _adjudicate_with_projection(adapter, state, questions)
    assert caught.value.code == "TRANSPORT_FAILURE"
    assert len(failed_opener.requests) == 1


def test_typesafe_adapter_unknown_local_question_type_fails_closed(monkeypatch) -> None:
    state = _state()
    original_questions = OrchestraJevQuestionBuilder().build(state)
    request_projection = _request_projection(state)

    questions = {
        key: dict(value)
        for key, value in original_questions.items()
    }

    first_question = next(iter(questions))
    questions[first_question]["type"] = "synthetic-unknown"

    payload = _answer_payload(json.loads(request_projection[0])["questions"])
    payload["answers"][first_question] = {
        "type": "synthetic-unknown",
    }

    monkeypatch.setattr(
        OrchestraJevQuestionBuilder,
        "build",
        lambda self, supplied_state: questions,
    )

    opener = _Opener(_Response(payload))
    adapter = TypeSafeJevAdapter(
        lambda: "test-only-not-a-secret",
        opener=opener,
    )

    with pytest.raises(JevProviderFailure) as caught:
        adapter.adjudicate(
            state,
            questions,
            request_projection=request_projection,
        )

    assert caught.value.code == "RESPONSE_CONTRACT_INCOMPATIBLE"
    assert len(opener.requests) == 1
