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


__all__ = ["MINIMAL_SAFE", "UI_CONTRACT_FIDELITY", "UIFidelityRouting", "classify_ui_fidelity"]
