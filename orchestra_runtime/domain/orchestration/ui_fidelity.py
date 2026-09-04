"""Pure UI execution-fidelity routing and context-gate semantics."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


MINIMAL_SAFE = "MINIMAL_SAFE"
UI_CONTRACT_FIDELITY = "UI_CONTRACT_FIDELITY"


@dataclass(frozen=True)
class UIFidelityRouting:
    selected_profile: str
    trigger_ids: tuple[str, ...]
    fast_mode_prohibited: bool
    fidelity_context: dict[str, Any] | None

    def to_metadata(self, contract: Mapping[str, Any]) -> dict[str, Any]:
        keys = contract["metadata_keys"]
        result: dict[str, Any] = {
            keys["profile"]: self.selected_profile,
            keys["trigger_ids"]: self.trigger_ids,
            keys["fast_mode_prohibited"]: self.fast_mode_prohibited,
        }
        if self.fidelity_context is not None:
            result[keys["fidelity_context"]] = deepcopy(self.fidelity_context)
        else:
            result.pop(keys["fidelity_context"], None)
        return result


def _has_value(value: object) -> bool:
    if value is None or value is False or value == "":
        return False
    if isinstance(value, (list, tuple, dict, set, frozenset)):
        return bool(value)
    return True


def _evidence_values(metadata: Mapping[str, Any], profile: Mapping[str, Any] | None) -> tuple[Mapping[str, Any], ...]:
    evidence = metadata.get("ui_fidelity_evidence")
    values: list[Mapping[str, Any]] = []
    if isinstance(evidence, Mapping):
        values.append(evidence)
    if profile is not None:
        values.append(profile)
    values.append(metadata)
    return tuple(values)


def _evidence_present(
    metadata: Mapping[str, Any],
    profile: Mapping[str, Any] | None,
    keys: object,
) -> bool:
    if not isinstance(keys, list):
        raise ValueError("UI fidelity trigger evidence_keys must be a list")
    sources = _evidence_values(metadata, profile)
    for key in keys:
        for source in sources:
            if _has_value(source.get(str(key))):
                return True
    return False


def _profile_payload(metadata: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any] | None:
    raw = metadata.get(contract["metadata_keys"]["profile"])
    context = metadata.get(contract["metadata_keys"]["fidelity_context"])
    if isinstance(raw, Mapping):
        return deepcopy(dict(raw))
    if isinstance(raw, str) and raw == UI_CONTRACT_FIDELITY and isinstance(context, Mapping):
        payload = deepcopy(dict(context))
        payload.setdefault("profile", raw)
        return payload
    if raw is not None and not isinstance(raw, str):
        raise ValueError("UI fidelity profile must be an object or a canonical profile name")
    return None


def _profile_name(metadata: Mapping[str, Any], contract: Mapping[str, Any]) -> str | None:
    raw = metadata.get(contract["metadata_keys"]["profile"])
    if isinstance(raw, Mapping):
        value = raw.get("profile")
    else:
        value = raw
    if value is None:
        return None
    if not isinstance(value, str) or value not in tuple(contract["profiles"]):
        raise ValueError("UI fidelity profile must be MINIMAL_SAFE or UI_CONTRACT_FIDELITY")
    return value


def _validate_profile(profile: Mapping[str, Any], contract: Mapping[str, Any]) -> None:
    required = tuple(str(item) for item in contract["fidelity_profile_required_fields"])
    missing = [field for field in required if field not in profile]
    if missing:
        raise ValueError("UI_CONTRACT_FIDELITY missing required evidence: " + ", ".join(missing))
    if profile.get("selected_by") != contract["selected_by"]:
        raise ValueError("UI implementation profile can only be selected by conductor")
    if not isinstance(profile.get("selection_reason"), str) or not profile["selection_reason"].strip():
        raise ValueError("UI implementation profile requires a selection reason")
    for field in ("design_contract_ref", "cloak_handoff_ref", "clockwork_boundary_ref"):
        if not isinstance(profile.get(field), str) or not profile[field].strip():
            raise ValueError(f"UI_CONTRACT_FIDELITY requires {field}")
    for field in ("pattern_refs", "composition_refs"):
        if not isinstance(profile.get(field), list) or not profile[field]:
            raise ValueError(f"UI_CONTRACT_FIDELITY requires non-empty {field}")
    required_fidelity = profile.get("required_fidelity")
    if not isinstance(required_fidelity, Mapping):
        raise ValueError("UI_CONTRACT_FIDELITY requires required_fidelity evidence")
    for field in contract["fidelity_required_true_fields"]:
        if required_fidelity.get(field) is not True:
            raise ValueError(f"UI_CONTRACT_FIDELITY requires {field}=true")
    authority = profile.get("authority")
    if not isinstance(authority, Mapping):
        raise ValueError("UI implementation profile requires authority boundaries")
    for field in contract["authority_false_fields"]:
        if authority.get(field) is not False:
            raise ValueError(f"UI implementation profile authority boundary {field} must be false")


def classify_ui_fidelity(
    prompt: str,
    metadata: Mapping[str, Any] | None,
    contract: Mapping[str, Any],
) -> UIFidelityRouting:
    values = dict(metadata or {})
    profile = _profile_payload(values, contract)
    profile_name = _profile_name(values, contract)
    normalized_prompt = str(prompt).casefold()
    trigger_ids: list[str] = []
    for trigger in contract["triggers"]:
        terms = trigger.get("prompt_terms")
        if not isinstance(terms, list):
            raise ValueError("UI fidelity trigger prompt_terms must be a list")
        prompt_match = any(str(term).casefold() in normalized_prompt for term in terms)
        if prompt_match or _evidence_present(values, profile, trigger.get("evidence_keys", [])):
            trigger_ids.append(str(trigger["id"]))

    if profile_name == UI_CONTRACT_FIDELITY and "explicit_ui_contract_fidelity_profile" not in trigger_ids:
        trigger_ids.append("explicit_ui_contract_fidelity_profile")
    if profile_name == MINIMAL_SAFE and trigger_ids:
        raise ValueError("MINIMAL_SAFE conflicts with a material DESIGN_FIDELITY_TRIGGER")

    selected_profile = UI_CONTRACT_FIDELITY if trigger_ids else MINIMAL_SAFE
    if selected_profile == UI_CONTRACT_FIDELITY:
        if profile is None:
            raise ValueError("UI_CONTRACT_FIDELITY requires conductor-selected profile evidence")
        profile["profile"] = UI_CONTRACT_FIDELITY
        _validate_profile(profile, contract)
        risk_mode = values.get(contract["metadata_keys"]["risk_mode"])
        if isinstance(risk_mode, str) and risk_mode.casefold() == contract["fast_mode"]["value"].casefold():
            raise ValueError("DESIGN_FIDELITY_TRIGGER makes FAST_MODE_PROHIBITED")
        context = {
            field: deepcopy(profile[field])
            for field in contract["context_forward_fields"]
            if field in profile
        }
        context["profile"] = UI_CONTRACT_FIDELITY
        context["selected_by"] = contract["selected_by"]
        return UIFidelityRouting(UI_CONTRACT_FIDELITY, tuple(trigger_ids), True, context)

    if profile is not None:
        minimal_profile = dict(profile)
        if minimal_profile.get("profile") not in (None, MINIMAL_SAFE):
            raise ValueError("MINIMAL_SAFE routing received a conflicting UI profile")
        if "selected_by" in minimal_profile and minimal_profile["selected_by"] != contract["selected_by"]:
            raise ValueError("UI implementation profile can only be selected by conductor")
        authority = minimal_profile.get("authority")
        if authority is not None:
            for field in contract["authority_false_fields"]:
                if authority.get(field) is not False:
                    raise ValueError(f"UI implementation profile authority boundary {field} must be false")
    return UIFidelityRouting(MINIMAL_SAFE, (), False, None)


@dataclass(frozen=True)
class UIDeviationRecord:
    requirement_or_reference: str
    deviation: str
    reason: str
    impact: str
    evidence: str
    requires_upstream_reentry: bool

    def validate(self) -> None:
        for field in ("requirement_or_reference", "deviation", "reason", "impact", "evidence"):
            val = getattr(self, field)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"UIDeviationRecord requires non-empty {field}")
        if not isinstance(self.requires_upstream_reentry, bool):
            raise ValueError("UIDeviationRecord requires boolean requires_upstream_reentry")

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_or_reference": self.requirement_or_reference,
            "deviation": self.deviation,
            "reason": self.reason,
            "impact": self.impact,
            "evidence": self.evidence,
            "requires_upstream_reentry": self.requires_upstream_reentry,
        }


@dataclass(frozen=True)
class PonytailFidelityExecution:
    profile: str
    preserved_compositions: tuple[str, ...]
    preserved_hierarchies: tuple[str, ...]
    preserved_states: tuple[str, ...]
    preserved_responsive: tuple[str, ...]
    project_native_reuse: tuple[str, ...]
    deviations: tuple[UIDeviationRecord, ...]
    motion_implemented: bool
    requires_upstream_reentry: bool
    static_review_ready: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "preserved_compositions": list(self.preserved_compositions),
            "preserved_hierarchies": list(self.preserved_hierarchies),
            "preserved_states": list(self.preserved_states),
            "preserved_responsive": list(self.preserved_responsive),
            "project_native_reuse": list(self.project_native_reuse),
            "deviations": [d.to_dict() for d in self.deviations],
            "motion_implemented": self.motion_implemented,
            "requires_upstream_reentry": self.requires_upstream_reentry,
            "static_review_ready": self.static_review_ready,
        }


def enforce_ponytail_fidelity_execution(
    context: Mapping[str, Any] | Any,
    execution_payload: Mapping[str, Any] | None = None,
) -> PonytailFidelityExecution:
    meta = getattr(context, "metadata", context)
    if not isinstance(meta, Mapping):
        raise ValueError("Context must provide mapping metadata")

    payload = dict(execution_payload or {})

    # Check generic execution_mode contamination
    for source in (meta, payload):
        exec_mode = source.get("execution_mode")
        if isinstance(exec_mode, str) and exec_mode in (MINIMAL_SAFE, UI_CONTRACT_FIDELITY):
            raise ValueError("Generic execution_mode cannot be contaminated with UI fidelity profile values")

    raw_profile = meta.get("ui_implementation_profile")
    if isinstance(raw_profile, str) and raw_profile in ("HOST_NATIVE", "DETERMINISTIC_TEST_ENGINE"):
        raise ValueError("Generic execution_mode cannot be contaminated with UI fidelity profile values")
    if isinstance(payload.get("profile"), str) and payload["profile"] in ("HOST_NATIVE", "DETERMINISTIC_TEST_ENGINE"):
        raise ValueError("Generic execution_mode cannot be contaminated with UI fidelity profile values")

    # Check UIEF-4 initiation boundary
    if (
        payload.get("creates_uifidelity_handoff")
        or payload.get("ui_fidelity_handoff") is not None
        or payload.get("starts_uief4") is True
    ):
        raise ValueError("Ponytail cannot create UIFidelityHandoff or initiate UIEF-4")

    # Determine upstream profile
    if isinstance(raw_profile, Mapping):
        upstream_profile = raw_profile.get("profile", MINIMAL_SAFE)
        profile_dict = dict(raw_profile)
    elif isinstance(raw_profile, str):
        upstream_profile = raw_profile
        profile_dict = meta.get("ui_fidelity_context") if isinstance(meta.get("ui_fidelity_context"), Mapping) else None
    else:
        upstream_profile = MINIMAL_SAFE
        profile_dict = None

    if upstream_profile not in (MINIMAL_SAFE, UI_CONTRACT_FIDELITY):
        raise ValueError(f"Invalid UI implementation profile: {upstream_profile}")

    # Check Ponytail self-selection / downgrade
    if payload.get("selected_by") == "ponytail" or (isinstance(raw_profile, Mapping) and raw_profile.get("selected_by") == "ponytail"):
        raise ValueError("Ponytail cannot select or self-assign UI implementation profile")

    if upstream_profile == UI_CONTRACT_FIDELITY and payload.get("profile") == MINIMAL_SAFE:
        raise ValueError("Ponytail cannot downgrade UI_CONTRACT_FIDELITY to MINIMAL_SAFE")

    if upstream_profile == MINIMAL_SAFE and payload.get("profile") == UI_CONTRACT_FIDELITY:
        raise ValueError("Ponytail cannot self-select UI_CONTRACT_FIDELITY")

    # MINIMAL_SAFE path
    if upstream_profile == MINIMAL_SAFE:
        native_reuse = tuple(str(x) for x in payload.get("project_native_reuse", ()))
        return PonytailFidelityExecution(
            profile=MINIMAL_SAFE,
            preserved_compositions=(),
            preserved_hierarchies=(),
            preserved_states=(),
            preserved_responsive=(),
            project_native_reuse=native_reuse,
            deviations=(),
            motion_implemented=False,
            requires_upstream_reentry=False,
            static_review_ready=True,
        )

    # UI_CONTRACT_FIDELITY path
    fidelity_ctx = profile_dict or meta.get("ui_fidelity_context")
    if not isinstance(fidelity_ctx, Mapping):
        raise ValueError("UI_CONTRACT_FIDELITY missing required fidelity evidence")

    # Validate required fidelity evidence
    for field in ("design_contract_ref", "cloak_handoff_ref", "clockwork_boundary_ref"):
        val = fidelity_ctx.get(field)
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"UI_CONTRACT_FIDELITY missing required fidelity evidence: {field}")

    for field in ("pattern_refs", "composition_refs"):
        val = fidelity_ctx.get(field)
        if not isinstance(val, list) or not val:
            raise ValueError(f"UI_CONTRACT_FIDELITY missing required fidelity evidence: {field}")

    req_fidelity = fidelity_ctx.get("required_fidelity")
    if not isinstance(req_fidelity, Mapping):
        raise ValueError("UI_CONTRACT_FIDELITY missing required fidelity evidence: required_fidelity")

    # Check for invented design requirements / unresolved facts
    if payload.get("invented_design_requirements") or payload.get("unresolved_design_facts"):
        raise ValueError("Ponytail cannot invent unresolved design requirements; upstream re-entry required")

    # Check complexity reduction prohibition
    if (
        payload.get("simplified_composition_for_code_size") is True
        or payload.get("complexity_reduction_for_diff") is True
    ):
        raise ValueError("Complex required composition cannot be replaced with a simpler composition solely for code-size reduction")

    # Parse deviations first so they can account for unpreserved compositions
    raw_deviations = payload.get("deviations", ())
    validated_deviations: list[UIDeviationRecord] = []
    reentry_required = False
    for item in raw_deviations:
        if isinstance(item, UIDeviationRecord):
            rec = item
        elif isinstance(item, Mapping):
            rec = UIDeviationRecord(
                requirement_or_reference=str(item.get("requirement_or_reference", "")),
                deviation=str(item.get("deviation", "")),
                reason=str(item.get("reason", "")),
                impact=str(item.get("impact", "")),
                evidence=str(item.get("evidence", "")),
                requires_upstream_reentry=bool(item.get("requires_upstream_reentry", False)),
            )
        else:
            raise ValueError("Deviations must be UIDeviationRecord or Mapping")
        rec.validate()
        validated_deviations.append(rec)
        if rec.requires_upstream_reentry:
            reentry_required = True

    # Check required composition preservation
    preserved_comps = set(str(c) for c in payload.get("preserved_compositions", ()))
    for comp_ref in fidelity_ctx.get("composition_refs", []):
        if isinstance(comp_ref, Mapping):
            comp_id = str(comp_ref.get("composition_id", "")).strip()
            if comp_id and comp_id not in preserved_comps:
                # Must be covered by an explicit deviation
                matching = [d for d in validated_deviations if comp_id in d.requirement_or_reference]
                if not matching:
                    raise ValueError(
                        f"Required composition '{comp_id}' must be preserved or recorded as an authorized deviation"
                    )

    # Check motion
    motion_implemented = bool(payload.get("motion_implemented", False))
    if motion_implemented and not payload.get("motion_required", False):
        raise ValueError("Motion implemented without explicit design contract requirement")

    native_reuse = tuple(str(x) for x in payload.get("project_native_reuse", ()))
    preserved_hierarchies = tuple(str(x) for x in payload.get("preserved_hierarchies", ()))
    preserved_states = tuple(str(x) for x in payload.get("preserved_states", ()))
    preserved_responsive = tuple(str(x) for x in payload.get("preserved_responsive", ()))

    return PonytailFidelityExecution(
        profile=UI_CONTRACT_FIDELITY,
        preserved_compositions=tuple(sorted(preserved_comps)),
        preserved_hierarchies=preserved_hierarchies,
        preserved_states=preserved_states,
        preserved_responsive=preserved_responsive,
        project_native_reuse=native_reuse,
        deviations=tuple(validated_deviations),
        motion_implemented=motion_implemented,
        requires_upstream_reentry=reentry_required,
        static_review_ready=not reentry_required,
    )


__all__ = [
    "MINIMAL_SAFE",
    "UI_CONTRACT_FIDELITY",
    "UIFidelityRouting",
    "UIDeviationRecord",
    "PonytailFidelityExecution",
    "classify_ui_fidelity",
    "enforce_ponytail_fidelity_execution",
]
