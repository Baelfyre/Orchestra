"""Single-request TypeSafe System One adapter for Orchestra JEV advice."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

import json
import math
from typing import Any, Callable, Mapping
import urllib.error
import urllib.request

from ...application.ports.jev_adjudication import (
    JevAdjudicationProvider,
    JevProviderRequestProjectionContext,
)
from ...domain.adaptive.jev_adjudication import (
    JevChoiceAnswer,
    JevNoulAnswer,
    JevProviderFailure,
    JevProviderResponse,
    OrchestraJevAdjudicationState,
    OrchestraJevQuestionBuilder,
    TYPESAFE_JEV_MODEL,
    TYPESAFE_SYSTEM_ONE_ENDPOINT,
)
from ...shared.canonicalization import canonical_json_bytes


_MAX_RESPONSE_BYTES = 4 * 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


class TypeSafeJevAdapter(JevAdjudicationProvider):
    """Use an injected secret source; never read environment or retain request headers."""

    def __init__(
        self,
        credential_provider: Callable[[], str],
        *,
        timeout_seconds: int = 60,
        opener: Any | None = None,
    ) -> None:
        if not callable(credential_provider):
            raise TypeError("credential_provider must be callable")
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive integer")
        self._credential_provider = credential_provider
        self._timeout_seconds = timeout_seconds
        self._opener = opener or urllib.request.build_opener(_NoRedirect)

    def adjudicate(
        self,
        state: OrchestraJevAdjudicationState,
        questions: Mapping[str, Mapping[str, object]],
        *,
        request_projection: tuple[bytes, JevProviderRequestProjectionContext] | None = None,
    ) -> JevProviderResponse:
        if not isinstance(state, OrchestraJevAdjudicationState):
            raise TypeError("state must be a normalized Orchestra adjudication state")
        expected_questions = OrchestraJevQuestionBuilder().build(state)
        if not isinstance(questions, Mapping) or canonical_json_bytes(dict(questions)) != canonical_json_bytes(
            expected_questions
        ):
            raise ValueError("questions must be the complete local Orchestra catalog")
        if (
            not isinstance(request_projection, tuple)
            or len(request_projection) != 2
            or not isinstance(request_projection[0], bytes)
            or not isinstance(request_projection[1], JevProviderRequestProjectionContext)
        ):
            raise JevProviderFailure("REQUEST_CONTRACT_REJECTED")
        request_body, projection_context = request_projection
        try:
            projected_request = projection_context.validate_request(state, request_body)
        except Exception:
            raise JevProviderFailure("REQUEST_CONTRACT_REJECTED") from None
        if not isinstance(projected_request, Mapping):
            raise JevProviderFailure("REQUEST_CONTRACT_REJECTED")
        projected_questions = projected_request.get("questions")
        if (
            set(projected_request) != {"state", "model", "questions"}
            or projected_request.get("model") != TYPESAFE_JEV_MODEL
            or not isinstance(projected_questions, dict)
        ):
            raise JevProviderFailure("REQUEST_CONTRACT_REJECTED")
        try:
            credential = self._credential_provider()
        except Exception:
            raise JevProviderFailure("CREDENTIAL_UNAVAILABLE") from None
        if not isinstance(credential, str) or not credential:
            raise JevProviderFailure("CREDENTIAL_UNAVAILABLE")

        request = urllib.request.Request(
            TYPESAFE_SYSTEM_ONE_ENDPOINT,
            data=request_body,
            headers={
                "Authorization": f"Bearer {credential}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self._opener.open(request, timeout=self._timeout_seconds) as response:
                status = response.status
                response_bytes = response.read(_MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
            code = (
                "AUTHENTICATION_FAILED"
                if status in (401, 403)
                else "REQUEST_CONTRACT_REJECTED"
                if status in (400, 422)
                else "TRANSPORT_FAILURE"
            )
            raise JevProviderFailure(code, status) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise JevProviderFailure("TRANSPORT_FAILURE") from None
        except Exception:
            raise JevProviderFailure("TRANSPORT_FAILURE") from None
        if not isinstance(status, int) or not 200 <= status < 300:
            raise JevProviderFailure("TRANSPORT_FAILURE", status if isinstance(status, int) else None)
        if not isinstance(response_bytes, bytes) or len(response_bytes) > _MAX_RESPONSE_BYTES:
            raise JevProviderFailure("RESPONSE_CONTRACT_INCOMPATIBLE", status)
        try:
            data = json.loads(response_bytes)
        except Exception:
            raise JevProviderFailure("RESPONSE_CONTRACT_INCOMPATIBLE", status) from None
        if not isinstance(data, dict) or "error" in data:
            raise JevProviderFailure("RESPONSE_CONTRACT_INCOMPATIBLE", status)
        usage = data.get("usage")
        if not isinstance(usage, dict) or any(
            type(usage.get(field)) is not int or usage[field] < 0
            for field in ("input_tokens", "output_tokens")
        ):
            raise JevProviderFailure("RESPONSE_CONTRACT_INCOMPATIBLE", status)
        model = data.get("model")
        answers = data.get("answers")
        if not isinstance(model, str) or not isinstance(answers, dict):
            raise JevProviderFailure("RESPONSE_CONTRACT_INCOMPATIBLE", status)
        if set(answers) != set(projected_questions):
            raise JevProviderFailure("RESPONSE_CONTRACT_INCOMPATIBLE", status)

        typed_answers: list[tuple[str, JevNoulAnswer | JevChoiceAnswer]] = []
        try:
            for question_id, question in projected_questions.items():
                answer = answers[question_id]
                if not isinstance(question, Mapping) or not isinstance(answer, dict):
                    raise ValueError
                answer_type = question.get("type")
                if answer.get("type") != answer_type:
                    raise ValueError
                if answer_type == "noul":
                    typed_answers.append((question_id, JevNoulAnswer(_finite_probability(answer.get("noul")))))
                elif answer_type == "choice":
                    criteria = question.get("criteria")
                    choice = answer.get("choice")
                    if not isinstance(criteria, Mapping) or not isinstance(choice, str) or choice not in criteria:
                        raise ValueError
                    confidence = _finite_probability(answer["confidence"])
                    probabilities = answer.get("probabilities")
                    if not isinstance(probabilities, dict) or set(probabilities) != set(criteria):
                        raise ValueError
                    typed_probabilities = {
                        key: _finite_probability(value) for key, value in probabilities.items()
                    }
                    if typed_probabilities[choice] != max(typed_probabilities.values()):
                        raise ValueError
                    typed_answers.append(
                        (
                            question_id,
                            JevChoiceAnswer(
                                choice,
                                confidence,
                                tuple(typed_probabilities.items()),
                            ),
                        )
                    )
                else:
                    raise ValueError
        except (KeyError, TypeError, ValueError):
            raise JevProviderFailure("RESPONSE_CONTRACT_INCOMPATIBLE", status) from None
        try:
            projected_response = JevProviderResponse(
                model, state.candidate_binding, tuple(typed_answers)
            )
            return projection_context.restore_response(
                state, request_body, projected_response
            )
        except (TypeError, ValueError):
            raise JevProviderFailure("RESPONSE_CONTRACT_INCOMPATIBLE", status) from None


def _finite_probability(value: object) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("probability must be numeric")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("probability must be finite and between zero and one")
    return value


__all__ = ["TypeSafeJevAdapter"]
