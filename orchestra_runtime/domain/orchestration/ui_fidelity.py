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


VALID_SOURCE_KINDS = frozenset(
    (
        "CUIR_NORMALIZED",
        "PROJECT_NATIVE",
        "PUBLIC_PROVIDER_GUIDANCE",
        "OBSERVED_PROVIDER_OUTPUT",
    )
)

UI_FIDELITY_HANDOFF_SCHEMA = "orchestra.ui-fidelity-handoff.v1"


@dataclass(frozen=True)
class UIFidelityHandoff:
    schema_version: str
    contract_id: str
    owned_by: str
    design_contract_ref: str
    ui_implementation_profile_ref: str
    source_revision_or_contract_identity: str
    provenance_refs: tuple[dict[str, Any], ...]
    design_intent: str
    information_hierarchy: tuple[dict[str, Any] | str, ...]
    macro_composition: tuple[dict[str, Any], ...]
    selected_pattern_refs: tuple[dict[str, Any], ...]
    pattern_application_reason: str
    required_regions: tuple[dict[str, Any] | str, ...]
    component_roles: dict[str, Any]
    visual_relationships: dict[str, Any]
    typography_roles: dict[str, Any]
    spacing_relationships: dict[str, Any]
    responsive_transformations: tuple[dict[str, Any] | str, ...]
    interaction_states: tuple[str, ...]
    asset_requirements: tuple[dict[str, Any] | str, ...]
    preserve: tuple[str, ...]
    adapt: tuple[str, ...]
    avoid: tuple[str, ...]
    unresolved: tuple[str, ...]
    authority: dict[str, Any]

    def validate(self) -> None:
        if self.schema_version != UI_FIDELITY_HANDOFF_SCHEMA:
            raise ValueError(f"unsupported UIFidelityHandoff schema_version: {self.schema_version}")
        if self.owned_by != "cloak":
            raise ValueError("UIFidelityHandoff must be owned by cloak")

        # Authority invariant: handoff does NOT authorize implementation or architecture translation
        if not isinstance(self.authority, Mapping):
            raise ValueError("UIFidelityHandoff requires mapping authority")
        if (
            self.authority.get("implementation_authorized") is not False
            or self.authority.get("architecture_translation_authorized") is not False
            or self.authority.get("release_authorized") is not False
        ):
            raise ValueError("UIFidelityHandoff cannot authorize implementation, architecture translation, or release")

        # UIEF-5 Clockwork boundary invariant
        if hasattr(self, "clockwork_translation") or hasattr(self, "engineering_translation_authorized"):
            raise ValueError("UIFidelityHandoff cannot embed or initiate UIEF-5 engineering translation")

        # Non-empty string validations
        for field_name in (
            "contract_id",
            "design_contract_ref",
            "ui_implementation_profile_ref",
            "source_revision_or_contract_identity",
            "design_intent",
            "pattern_application_reason",
        ):
            val = getattr(self, field_name)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"UIFidelityHandoff requires non-empty string {field_name}")

        # Required collections validations
        for field_name in (
            "provenance_refs",
            "information_hierarchy",
            "macro_composition",
            "selected_pattern_refs",
            "required_regions",
            "preserve",
            "avoid",
        ):
            val = getattr(self, field_name)
            if not isinstance(val, (tuple, list)) or not val:
                raise ValueError(f"UIFidelityHandoff requires non-empty collection {field_name}")

        # Check selected_pattern_refs provenance
        for pat in self.selected_pattern_refs:
            if not isinstance(pat, Mapping):
                raise ValueError("selected_pattern_refs items must be mappings")
            pat_id = str(pat.get("pattern_id", "")).strip()
            source_kind = str(pat.get("source_kind", "")).strip()
            prov_id = str(pat.get("provenance_id", "")).strip()
            if not pat_id:
                raise ValueError("selected_pattern_refs items require pattern_id")
            if source_kind not in VALID_SOURCE_KINDS:
                raise ValueError(f"unrecognized source_kind in pattern_ref: {source_kind}")
            if not prov_id:
                raise ValueError("selected_pattern_refs items require provenance_id")

        # Check macro_composition structural roles
        for comp in self.macro_composition:
            if not isinstance(comp, Mapping):
                raise ValueError("macro_composition items must be mappings")
            if not str(comp.get("composition_id", "")).strip():
                raise ValueError("macro_composition items require composition_id")

        # Check unresolved must be a tuple/list (can be empty, but must be present)
        if not isinstance(self.unresolved, (tuple, list)):
            raise ValueError("UIFidelityHandoff requires unresolved list")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "owned_by": self.owned_by,
            "design_contract_ref": self.design_contract_ref,
            "ui_implementation_profile_ref": self.ui_implementation_profile_ref,
            "source_revision_or_contract_identity": self.source_revision_or_contract_identity,
            "provenance_refs": list(self.provenance_refs),
            "design_intent": self.design_intent,
            "information_hierarchy": list(self.information_hierarchy),
            "macro_composition": list(self.macro_composition),
            "selected_pattern_refs": list(self.selected_pattern_refs),
            "pattern_application_reason": self.pattern_application_reason,
            "required_regions": list(self.required_regions),
            "component_roles": dict(self.component_roles),
            "visual_relationships": dict(self.visual_relationships),
            "typography_roles": dict(self.typography_roles),
            "spacing_relationships": dict(self.spacing_relationships),
            "responsive_transformations": list(self.responsive_transformations),
            "interaction_states": list(self.interaction_states),
            "asset_requirements": list(self.asset_requirements),
            "preserve": list(self.preserve),
            "adapt": list(self.adapt),
            "avoid": list(self.avoid),
            "unresolved": list(self.unresolved),
            "authority": dict(self.authority),
        }

    def to_ponytail_context(self) -> dict[str, Any]:
        """Convert handoff into context format required by Ponytail UIEF-3 execution."""
        return {
            "ui_implementation_profile": UI_CONTRACT_FIDELITY,
            "ui_fidelity_context": {
                "design_contract_ref": self.design_contract_ref,
                "cloak_handoff_ref": self.contract_id,
                "clockwork_boundary_ref": "docs/project/UI_EXECUTION_FIDELITY_PLAN.md",
                "pattern_refs": list(self.selected_pattern_refs),
                "composition_refs": list(self.macro_composition),
                "required_fidelity": {
                    "preserve_macro_composition": True,
                    "preserve_visual_hierarchy": True,
                    "preserve_interaction_states": True,
                    "preserve_responsive_transformation": True,
                    "min_accessibility_level": "WCAG_AA",
                },
                "required_regions": list(self.required_regions),
                "preserve": list(self.preserve),
                "adapt": list(self.adapt),
                "avoid": list(self.avoid),
                "unresolved": list(self.unresolved),
            },
        }


def validate_ui_fidelity_handoff(data: Mapping[str, Any]) -> UIFidelityHandoff:
    if not isinstance(data, Mapping):
        raise ValueError("UIFidelityHandoff data must be a mapping")

    # Contamination check
    exec_mode = data.get("execution_mode")
    if isinstance(exec_mode, str) and exec_mode in (MINIMAL_SAFE, UI_CONTRACT_FIDELITY):
        raise ValueError("Generic execution_mode cannot be contaminated with UI fidelity profile values")

    # Prohibited initiation / boundary checks
    if "clockwork_translation" in data or data.get("engineering_translation_authorized") is True:
        raise ValueError("UIFidelityHandoff cannot embed or initiate UIEF-5 engineering translation")

    owned_by = str(data.get("owned_by", "")).strip()
    if owned_by != "cloak":
        raise ValueError("UIFidelityHandoff must be owned by cloak")

    authority = data.get("authority", {})
    if not isinstance(authority, Mapping):
        raise ValueError("UIFidelityHandoff requires mapping authority")

    for seq_field in (
        "provenance_refs",
        "information_hierarchy",
        "macro_composition",
        "selected_pattern_refs",
        "required_regions",
        "responsive_transformations",
        "interaction_states",
        "asset_requirements",
        "preserve",
        "adapt",
        "avoid",
        "unresolved",
    ):
        if seq_field in data and not isinstance(data[seq_field], (list, tuple)):
            raise ValueError(f"UIFidelityHandoff requires list or tuple for {seq_field}")

    for map_field in (
        "component_roles",
        "visual_relationships",
        "typography_roles",
        "spacing_relationships",
    ):
        if map_field in data and not isinstance(data[map_field], Mapping):
            raise ValueError(f"UIFidelityHandoff requires mapping for {map_field}")

    handoff = UIFidelityHandoff(
        schema_version=str(data.get("schema_version", UI_FIDELITY_HANDOFF_SCHEMA)),
        contract_id=str(data.get("contract_id", "")),
        owned_by=owned_by,
        design_contract_ref=str(data.get("design_contract_ref", "")),
        ui_implementation_profile_ref=str(data.get("ui_implementation_profile_ref", "")),
        source_revision_or_contract_identity=str(data.get("source_revision_or_contract_identity", "")),
        provenance_refs=tuple(dict(x) if isinstance(x, Mapping) else x for x in data.get("provenance_refs", ())),
        design_intent=str(data.get("design_intent", "")),
        information_hierarchy=tuple(data.get("information_hierarchy", ())),
        macro_composition=tuple(dict(x) if isinstance(x, Mapping) else x for x in data.get("macro_composition", ())),
        selected_pattern_refs=tuple(dict(x) if isinstance(x, Mapping) else x for x in data.get("selected_pattern_refs", ())),
        pattern_application_reason=str(data.get("pattern_application_reason", "")),
        required_regions=tuple(data.get("required_regions", ())),
        component_roles=dict(data.get("component_roles", {})),
        visual_relationships=dict(data.get("visual_relationships", {})),
        typography_roles=dict(data.get("typography_roles", {})),
        spacing_relationships=dict(data.get("spacing_relationships", {})),
        responsive_transformations=tuple(data.get("responsive_transformations", ())),
        interaction_states=tuple(str(x) for x in data.get("interaction_states", ())),
        asset_requirements=tuple(data.get("asset_requirements", ())),
        preserve=tuple(str(x) for x in data.get("preserve", ())),
        adapt=tuple(str(x) for x in data.get("adapt", ())),
        avoid=tuple(str(x) for x in data.get("avoid", ())),
        unresolved=tuple(str(x) for x in data.get("unresolved", ())),
        authority=dict(authority),
    )
    handoff.validate()
    return handoff


__all__ = [
    "MINIMAL_SAFE",
    "UI_CONTRACT_FIDELITY",
    "UIFidelityRouting",
    "UIDeviationRecord",
    "PonytailFidelityExecution",
    "UIFidelityHandoff",
    "VALID_SOURCE_KINDS",
    "UI_FIDELITY_HANDOFF_SCHEMA",
    "classify_ui_fidelity",
    "enforce_ponytail_fidelity_execution",
    "validate_ui_fidelity_handoff",
]
