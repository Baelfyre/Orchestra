from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

CAPABILITY_MANIFEST_SCHEMA = "orchestra.compliance-registry.capability-manifest.v1"
CAPABILITY_NEGOTIATION_SCHEMA = "orchestra.registry-capability-negotiation.v1"
ADAPTIVE_RECEIPT_SCHEMA = "orchestra.registry-adaptive-consumption-receipt.v1"
RELEASE_DELTA_SCHEMA = "orchestra.compliance-registry.release-delta.v1"
CANONICAL_REPOSITORY = "Baelfyre/Orchestra-Compliance-Registry"

REQUIRED_CAPABILITIES: dict[str, str] = {
    "cap.query.v1": "1.0.0",
}
OPTIONAL_CAPABILITIES: dict[str, str] = {
    "cap.query.multi-jurisdiction.v1": "1.0.0",
    "cap.query.scoped-freshness.v1": "1.0.0",
    "cap.release-delta.v1": "1.0.0",
    "cap.source-monitor.v1": "1.0.0",
    "cap.schema-negotiation.v1": "1.0.0",
}
STALE_SOURCE_STATES = {"SOURCE_UNAVAILABLE", "SOURCE_MOVED", "REVIEW_OVERDUE"}
ATTENTION_SOURCE_STATES = {
    "CURRENT_WITH_PENDING_CHANGE",
    "NOT_EFFECTIVE_YET",
    "SUPERSEDED",
    "REPEALED",
    "APPLICABILITY_UNRESOLVED",
    "HUMAN_INTERPRETATION_REQUIRED",
}

SPECIALIST_PRIORITY = (
    "the-governor",
    "the-steward",
    "cipher",
    "chronicler",
    "clockwork",
    "cloak",
    "overseer",
    "arbiter",
)
DOMAIN_SPECIALISTS: dict[str, tuple[str, ...]] = {
    "privacy": ("the-governor",),
    "data-protection": ("the-governor",),
    "personal-data-processing": ("the-governor",),
    "governance": ("the-governor",),
    "accountability": ("the-governor",),
    "transparency": ("the-governor",),
    "training": ("the-governor", "the-steward"),
    "privacy-engineering": ("the-governor", "cipher"),
    "security": ("cipher",),
    "access-control": ("cipher",),
    "resilience": ("cipher",),
    "business-continuity": ("the-steward",),
    "systems-lifecycle": ("the-steward", "clockwork"),
    "risk-management": ("the-steward",),
    "data-lifecycle": ("the-governor", "chronicler"),
    "retention": ("the-governor", "chronicler"),
    "data-minimization": ("the-governor", "chronicler"),
    "software-development": ("clockwork",),
    "secure-software-development": ("cipher", "clockwork"),
    "cybersecurity": ("cipher",),
    "database-security": ("cipher", "chronicler"),
    "data-governance": ("the-governor", "chronicler"),
    "data-residency": ("the-governor", "chronicler"),
    "ai-usage": ("the-governor", "the-steward"),
    "ai-systems": ("the-governor", "clockwork"),
    "ai-risk-management": ("the-governor", "the-steward"),
    "accessibility": ("cloak",),
    "provider-platform-policy": ("the-governor", "the-steward"),
    "cloud-shared-responsibility": ("cipher", "clockwork"),
    "developer-distribution-requirements": ("the-governor", "the-steward"),
}


class RegistryAdaptiveError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def stable_digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _ids(values: Iterable[object] | None, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    normalized: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            raise RegistryAdaptiveError(f"{field_name} contains an empty value")
        normalized.append(text)
    return tuple(sorted(set(normalized)))


def _version(value: object, field_name: str) -> tuple[int, int, int]:
    text = str(value or "").strip()
    parts = text.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise RegistryAdaptiveError(f"{field_name} must be semantic version MAJOR.MINOR.PATCH")
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def _version_compatible(actual: object, minimum: object) -> bool:
    actual_version = _version(actual, "capability contract_version")
    minimum_version = _version(minimum, "consumer minimum contract_version")
    return actual_version[0] == minimum_version[0] and actual_version >= minimum_version


def legacy_v0_2_capability_profile(registry_version: str) -> dict[str, Any]:
    if registry_version != "0.2.0":
        raise RegistryAdaptiveError(
            "missing capability manifest is only supported by the explicit trusted Registry v0.2.0 compatibility profile"
        )
    return {
        "schema_version": "orchestra.registry-legacy-capability-profile.v1",
        "canonical_repository": CANONICAL_REPOSITORY,
        "authority": "ORCHESTRA_EXPLICIT_COMPATIBILITY_PROFILE_NON_AUTHORIZING",
        "capability_source": "LEGACY_V0_2_COMPATIBILITY_PROFILE",
        "capabilities": [
            {
                "capability_id": "cap.query.v1",
                "contract_version": "1.0.0",
                "status": "SUPPORTED",
                "required_records": ["sources", "obligations"],
                "optional": False,
                "fallback": "NONE",
            }
        ],
        "authority_boundaries": {
            "legal_interpretation": False,
            "project_applicability": False,
            "orchestra_execution": False,
            "automatic_merge": False,
            "trusted_release_publication": False,
        },
    }


def load_capability_surface(bundle_root: Path, registry_version: str) -> dict[str, Any]:
    capability_path = bundle_root / "registry" / "capabilities.json"
    if not capability_path.is_file():
        return legacy_v0_2_capability_profile(registry_version)
    try:
        value = json.loads(capability_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryAdaptiveError(f"cannot read Registry capability manifest: {exc}") from exc
    if not isinstance(value, dict):
        raise RegistryAdaptiveError("Registry capability manifest must be an object")
    if value.get("schema_version") != CAPABILITY_MANIFEST_SCHEMA:
        raise RegistryAdaptiveError("unsupported Registry capability manifest schema")
    if value.get("canonical_repository") != CANONICAL_REPOSITORY:
        raise RegistryAdaptiveError("Registry capability manifest canonical repository mismatch")
    if value.get("authority") != "DESCRIPTIVE_NON_AUTHORIZING":
        raise RegistryAdaptiveError("Registry capability manifest attempted to change authority semantics")
    boundaries = value.get("authority_boundaries")
    if not isinstance(boundaries, Mapping) or any(boundaries.values()):
        raise RegistryAdaptiveError("Registry capability manifest contains authority expansion")
    return value


def negotiate_capabilities(
    surface: Mapping[str, Any],
    *,
    required: Mapping[str, str] | None = None,
    optional: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    required = dict(required or REQUIRED_CAPABILITIES)
    optional = dict(optional or OPTIONAL_CAPABILITIES)
    capabilities = surface.get("capabilities")
    if not isinstance(capabilities, Sequence) or isinstance(capabilities, (str, bytes)):
        raise RegistryAdaptiveError("capability surface must contain a capability array")
    indexed: dict[str, Mapping[str, Any]] = {}
    for item in capabilities:
        if not isinstance(item, Mapping):
            raise RegistryAdaptiveError("capability entry must be an object")
        capability_id = str(item.get("capability_id") or "").strip()
        if not capability_id:
            raise RegistryAdaptiveError("capability entry is missing capability_id")
        if capability_id in indexed:
            raise RegistryAdaptiveError(f"duplicate capability ID: {capability_id}")
        indexed[capability_id] = item

    def match(requirements: Mapping[str, str]) -> tuple[list[str], list[str], list[str]]:
        matched: list[str] = []
        missing: list[str] = []
        incompatible: list[str] = []
        for capability_id, minimum_version in sorted(requirements.items()):
            candidate = indexed.get(capability_id)
            if candidate is None or candidate.get("status") != "SUPPORTED":
                missing.append(capability_id)
                continue
            try:
                compatible = _version_compatible(candidate.get("contract_version"), minimum_version)
            except RegistryAdaptiveError:
                compatible = False
            if compatible:
                matched.append(capability_id)
            else:
                incompatible.append(capability_id)
        return matched, missing, incompatible

    matched_required, missing_required, incompatible_required = match(required)
    matched_optional, missing_optional, incompatible_optional = match(optional)
    disposition = "COMPATIBLE" if not missing_required and not incompatible_required else "INCOMPATIBLE_REQUIRED_CAPABILITY"
    result: dict[str, Any] = {
        "schema_version": CAPABILITY_NEGOTIATION_SCHEMA,
        "capability_source": str(surface.get("capability_source") or "DECLARED_R5_CAPABILITY_MANIFEST"),
        "required_capabilities": dict(sorted(required.items())),
        "optional_capabilities": dict(sorted(optional.items())),
        "matched_required_capability_ids": matched_required,
        "matched_optional_capability_ids": matched_optional,
        "missing_required_capability_ids": missing_required,
        "missing_optional_capability_ids": missing_optional,
        "incompatible_required_capability_ids": incompatible_required,
        "incompatible_optional_capability_ids": incompatible_optional,
        "disposition": disposition,
        "authority_expansion": False,
    }
    result["digest"] = stable_digest(result)
    return result


def select_query_records(
    sources: Sequence[Mapping[str, Any]],
    obligations: Sequence[Mapping[str, Any]],
    *,
    jurisdictions: Iterable[object] | None = None,
    providers: Iterable[object] | None = None,
    domains: Iterable[object] | None = None,
    source_id: str | None = None,
    obligation_id: str | None = None,
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    jurisdiction_ids = set(_ids(jurisdictions, "jurisdictions"))
    provider_ids = set(_ids(providers, "providers"))
    domain_ids = set(_ids(domains, "domains"))
    source_filter = str(source_id or "").strip() or None
    obligation_filter = str(obligation_id or "").strip() or None

    def intersects(item: Mapping[str, Any], field: str, requested: set[str]) -> bool:
        if not requested:
            return True
        values = item.get(field, [])
        return isinstance(values, list) and bool(requested & {str(value) for value in values})

    selected_obligations: list[Mapping[str, Any]] = []
    for item in obligations:
        if obligation_filter and item.get("obligation_id") != obligation_filter:
            continue
        if source_filter:
            source_refs = item.get("source_ids", [])
            if not isinstance(source_refs, list) or source_filter not in source_refs:
                continue
        if not intersects(item, "jurisdiction_ids", jurisdiction_ids):
            continue
        if not intersects(item, "provider_ids", provider_ids):
            continue
        if not intersects(item, "domains", domain_ids):
            continue
        selected_obligations.append(item)

    referenced_source_ids: set[str] = set()
    for item in selected_obligations:
        refs = item.get("source_ids", [])
        if isinstance(refs, list):
            referenced_source_ids.update(str(ref) for ref in refs if str(ref))
    if source_filter:
        referenced_source_ids.add(source_filter)

    selected_sources = [item for item in sources if str(item.get("source_id") or "") in referenced_source_ids]
    return selected_sources, selected_obligations


def evaluate_query_scoped_freshness(
    source_ids: Iterable[object],
    source_status_entries: Sequence[Mapping[str, Any]],
    review_due_entries: Sequence[Mapping[str, Any]],
    *,
    today: date | None = None,
) -> dict[str, Any]:
    selected = set(_ids(source_ids, "source_ids"))
    today = today or date.today()
    if not selected:
        result = {
            "state": "NO_REQUIRED_SOURCES",
            "source_ids": [],
            "stale_source_ids": [],
            "attention_source_ids": [],
            "untracked_source_ids": [],
        }
        result["digest"] = stable_digest(result)
        return result

    status_map = {
        str(item.get("source_id")): str(item.get("status"))
        for item in source_status_entries
        if item.get("source_id") is not None
    }
    due_map = {
        str(item.get("source_id")): str(item.get("next_review_due"))
        for item in review_due_entries
        if item.get("source_id") is not None
    }
    untracked = sorted(source_id for source_id in selected if source_id not in status_map or source_id not in due_map)
    stale: set[str] = set()
    attention: set[str] = set()
    for source_id in selected - set(untracked):
        status = status_map[source_id]
        if status in STALE_SOURCE_STATES:
            stale.add(source_id)
        elif status != "VERIFIED_CURRENT":
            attention.add(source_id)
        due_value = due_map[source_id]
        try:
            if date.fromisoformat(due_value) < today:
                stale.add(source_id)
        except ValueError as exc:
            raise RegistryAdaptiveError(f"invalid review-due date for {source_id}: {due_value}") from exc

    if untracked:
        state = "INCOMPLETE"
    elif stale:
        state = "STALE"
    elif attention:
        state = "REVIEW_REQUIRED"
    else:
        state = "CURRENT"
    result = {
        "state": state,
        "source_ids": sorted(selected),
        "stale_source_ids": sorted(stale),
        "attention_source_ids": sorted(attention - stale),
        "untracked_source_ids": untracked,
    }
    result["digest"] = stable_digest(result)
    return result


def assess_release_delta(delta: Mapping[str, Any]) -> dict[str, Any]:
    expected_keys = {
        "schema_version",
        "authority",
        "base",
        "target",
        "disposition",
        "changed_record_types",
        "affected",
        "structural_changes",
        "requires_human_review",
        "digest",
    }
    if set(delta) != expected_keys:
        raise RegistryAdaptiveError("release delta field set does not match the closed R6 contract")
    if delta.get("schema_version") != RELEASE_DELTA_SCHEMA:
        raise RegistryAdaptiveError("unsupported Registry release delta schema")
    if delta.get("authority") != "EVIDENCE_ONLY_NON_AUTHORIZING":
        raise RegistryAdaptiveError("Registry release delta attempted authority expansion")
    expected_digest = str(delta.get("digest") or "")
    unsigned = {key: value for key, value in delta.items() if key != "digest"}
    if stable_digest(unsigned) != expected_digest:
        raise RegistryAdaptiveError("Registry release delta digest mismatch")
    disposition = delta.get("disposition")
    actions = {
        "UNCHANGED": "NO_REVALIDATION",
        "COMPATIBLE_SCOPED_CHANGE": "SCOPED_REVALIDATION",
        "REVALIDATION_REQUIRED": "SCOPED_REVALIDATION",
        "UNSUPPORTED_CAPABILITY_CHANGE": "FULL_REVALIDATION_FAIL_CLOSED",
        "HUMAN_REVIEW_REQUIRED": "HUMAN_REVIEW_REQUIRED",
    }
    if disposition not in actions:
        raise RegistryAdaptiveError(f"unsupported Registry release delta disposition: {disposition!r}")
    affected = delta.get("affected")
    if not isinstance(affected, Mapping):
        raise RegistryAdaptiveError("Registry release delta affected scope is malformed")
    domains = _ids(affected.get("domains", []), "release delta domains")
    routing = resolve_specialists(domains)
    result: dict[str, Any] = {
        "delta_digest": expected_digest,
        "disposition": disposition,
        "recommended_action": actions[str(disposition)],
        "affected": {key: list(_ids(value if isinstance(value, list) else [], f"affected {key}")) for key, value in sorted(affected.items())},
        "routing": routing,
        "authority_expansion": False,
    }
    result["digest"] = stable_digest(result)
    return result


def resolve_specialists(domains: Iterable[object]) -> dict[str, Any]:
    normalized_domains = _ids(domains, "domains")
    selected: set[str] = set()
    unresolved: list[str] = []
    for domain in normalized_domains:
        specialists = DOMAIN_SPECIALISTS.get(domain)
        if specialists is None:
            unresolved.append(domain)
            continue
        selected.update(specialists)
    priority = {name: index for index, name in enumerate(SPECIALIST_PRIORITY)}
    ordered = sorted(selected, key=lambda name: (priority.get(name, len(priority)), name))
    disposition = "ROUTED" if not unresolved else "HUMAN_ROUTING_REQUIRED"
    result: dict[str, Any] = {
        "domains": list(normalized_domains),
        "specialist_ids": ordered,
        "unresolved_domains": sorted(unresolved),
        "disposition": disposition,
        "router": "conductor",
        "authority_expansion": False,
    }
    result["digest"] = stable_digest(result)
    return result


def build_adaptive_receipt(
    *,
    registry_identity: Mapping[str, Any],
    filters: Mapping[str, Any],
    source_ids: Iterable[object],
    obligation_ids: Iterable[object],
    negotiation: Mapping[str, Any],
    freshness: Mapping[str, Any],
    routing: Mapping[str, Any],
    release_impact: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    identity = {
        "canonical_repository": str(registry_identity.get("canonical_repository") or ""),
        "registry_version": str(registry_identity.get("registry_version") or ""),
        "release_sequence": registry_identity.get("release_sequence"),
        "release_tag": str(registry_identity.get("release_tag") or ""),
        "manifest_sha256": str(registry_identity.get("manifest_sha256") or ""),
    }
    if identity["canonical_repository"] != CANONICAL_REPOSITORY:
        raise RegistryAdaptiveError("adaptive receipt Registry identity mismatch")
    receipt: dict[str, Any] = {
        "schema_version": ADAPTIVE_RECEIPT_SCHEMA,
        "authority": "EVIDENCE_ONLY_NON_AUTHORIZING",
        "registry_identity": identity,
        "filters": {str(key): value for key, value in sorted(filters.items())},
        "source_ids": list(_ids(source_ids, "source_ids")),
        "obligation_ids": list(_ids(obligation_ids, "obligation_ids")),
        "capability_negotiation_digest": str(negotiation.get("digest") or ""),
        "freshness_digest": str(freshness.get("digest") or ""),
        "routing_digest": str(routing.get("digest") or ""),
        "release_impact_digest": str(release_impact.get("digest") or "") if release_impact else None,
        "authority_expansion": False,
    }
    receipt["digest"] = stable_digest(receipt)
    return receipt
