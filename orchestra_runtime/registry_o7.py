from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Callable, Iterable, Mapping, Sequence

from .compliance_protocol import ComplianceQueryReceipt
from . import registry_adaptive

O7_RUNTIME_SCHEMA = "orchestra.registry-o7-runtime.v1"
R7_RESPONSE_SCHEMA = "orchestra.compliance-registry.r7-query-response.v1"
R7_RECEIPT_SCHEMA = "orchestra.compliance-registry.r7-query-receipt.v1"
CANONICAL_REPOSITORY = registry_adaptive.CANONICAL_REPOSITORY

R7_OPTIONAL_CAPABILITIES: dict[str, str] = {
    "cap.query.projection.v1": "1.0.0",
    "cap.query.relationships.v1": "1.0.0",
    "cap.query.indexed-read.v1": "1.0.0",
    "cap.query.budget.v1": "1.0.0",
    "cap.transport.mcp.v1": "1.0.0",
}
R7_DIRECT_BASE_CAPABILITIES = {
    "cap.query.projection.v1",
    "cap.query.relationships.v1",
}
ALLOWED_PROJECTIONS = ("MINIMAL", "SUMMARY", "EVIDENCE", "FULL")
DIRECT_INDEXED = "DIRECT_LOCAL_INDEXED_GATEWAY"
DIRECT_JSON = "DIRECT_LOCAL_JSON_QUERY"
OPTIONAL_MCP = "OPTIONAL_MCP_TRANSPORT"
LEGACY_O1_O6 = "USE_CURRENT_O1_O6_PATH"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

WORKFLOW_DEFAULT_PROJECTION: dict[str, str] = {
    "conductor_discovery": "MINIMAL",
    "governor_applicability_review": "SUMMARY",
    "steward_requirements_traceability": "EVIDENCE",
    "explicit_audit_escalation": "FULL",
}


class O7RegistryError(ValueError):
    """Base fail-closed O7 consumer error."""


class O7SemanticMismatch(O7RegistryError):
    """Registry response does not match the exact consumer request."""


class O7IndexIntegrityError(O7RegistryError):
    """Verified-index identity or digest validation failed."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def stable_digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise O7RegistryError(f"{field_name} must be non-empty")
    return text


def _sha(value: object, field_name: str) -> str:
    text = _text(value, field_name).lower()
    if SHA256_RE.fullmatch(text) is None:
        raise O7RegistryError(f"{field_name} must be a lowercase SHA-256 digest")
    return text


def _values(values: Iterable[object] | None, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    normalized = tuple(sorted({_text(value, field_name) for value in values}))
    return normalized


@dataclass(frozen=True, slots=True)
class O7QueryRequest:
    workflow_stage: str
    jurisdictions: tuple[str, ...] = ()
    providers: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    source_id: str | None = None
    obligation_id: str | None = None
    projection: str | None = None
    maximum_context_bytes: int | None = None
    limit: int = 50
    cursor: str | None = None
    representation: str = "AUTO"
    explicit_mcp: bool = False

    def __post_init__(self) -> None:
        stage = _text(self.workflow_stage, "workflow_stage")
        if stage not in WORKFLOW_DEFAULT_PROJECTION:
            raise O7RegistryError(f"unsupported O7 workflow stage: {stage}")
        object.__setattr__(self, "workflow_stage", stage)
        object.__setattr__(self, "jurisdictions", _values(self.jurisdictions, "jurisdiction"))
        object.__setattr__(self, "providers", _values(self.providers, "provider"))
        object.__setattr__(self, "domains", _values(self.domains, "domain"))
        if self.source_id is not None:
            object.__setattr__(self, "source_id", _text(self.source_id, "source_id"))
        if self.obligation_id is not None:
            object.__setattr__(self, "obligation_id", _text(self.obligation_id, "obligation_id"))
        if self.projection is not None:
            projection = _text(self.projection, "projection").upper()
            if projection not in ALLOWED_PROJECTIONS:
                raise O7RegistryError(f"unsupported O7 projection: {projection}")
            object.__setattr__(self, "projection", projection)
        if isinstance(self.limit, bool) or not isinstance(self.limit, int) or not 1 <= self.limit <= 1000:
            raise O7RegistryError("limit must be an integer between 1 and 1000")
        if self.maximum_context_bytes is not None:
            if isinstance(self.maximum_context_bytes, bool) or not isinstance(self.maximum_context_bytes, int) or self.maximum_context_bytes <= 0:
                raise O7RegistryError("maximum_context_bytes must be a positive integer")
        representation = _text(self.representation, "representation").upper()
        if representation not in {"AUTO", "JSON", "TOON"}:
            raise O7RegistryError("representation must be AUTO, JSON, or TOON")
        object.__setattr__(self, "representation", representation)
        if not isinstance(self.explicit_mcp, bool):
            raise O7RegistryError("explicit_mcp must be bool")

    @property
    def effective_projection(self) -> str:
        return self.projection or WORKFLOW_DEFAULT_PROJECTION[self.workflow_stage]

    @property
    def r7_single_filter_compatible(self) -> bool:
        return all(len(values) <= 1 for values in (self.jurisdictions, self.providers, self.domains))

    def receipt_filters(self) -> dict[str, str]:
        return {
            "jurisdictions": ",".join(self.jurisdictions),
            "providers": ",".join(self.providers),
            "domains": ",".join(self.domains),
            "source_id": self.source_id or "",
            "obligation_id": self.obligation_id or "",
        }

    def gateway_request(self) -> dict[str, Any]:
        if not self.r7_single_filter_compatible:
            raise O7RegistryError("R7 direct gateway currently accepts at most one jurisdiction/provider/domain filter")
        return {
            "record_type": "obligations",
            "filters": {
                "domain": self.domains[0] if self.domains else None,
                "jurisdiction": self.jurisdictions[0] if self.jurisdictions else None,
                "provider": self.providers[0] if self.providers else None,
                "source_id": self.source_id,
                "obligation_id": self.obligation_id,
            },
            "projection": self.effective_projection,
            "fields": [],
            "include_freshness": True,
            "limit": self.limit,
            "cursor": self.cursor,
            "maximum_context_bytes": self.maximum_context_bytes,
            "representation": self.representation,
        }


@dataclass(frozen=True, slots=True)
class O7TransportPlan:
    disposition: str
    transport: str
    projection: str
    reason: str
    authority_expansion: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": O7_RUNTIME_SCHEMA,
            "disposition": self.disposition,
            "transport": self.transport,
            "projection": self.projection,
            "reason": self.reason,
            "authority_expansion": self.authority_expansion,
        }


GatewayCall = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]
LegacyCall = Callable[[O7QueryRequest], Mapping[str, Any]]


def negotiate_o7_capabilities(surface: Mapping[str, Any]) -> dict[str, Any]:
    optional = {**registry_adaptive.OPTIONAL_CAPABILITIES, **R7_OPTIONAL_CAPABILITIES}
    return registry_adaptive.negotiate_capabilities(
        surface,
        required=registry_adaptive.REQUIRED_CAPABILITIES,
        optional=optional,
    )


def _matched_optional(negotiation: Mapping[str, Any]) -> set[str]:
    values = negotiation.get("matched_optional_capability_ids", [])
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise O7RegistryError("capability negotiation matched_optional_capability_ids must be an array")
    return {_text(value, "matched optional capability") for value in values}


def select_o7_transport(
    request: O7QueryRequest,
    negotiation: Mapping[str, Any],
    *,
    available_transports: Iterable[str],
) -> O7TransportPlan:
    if negotiation.get("disposition") != "COMPATIBLE":
        raise O7RegistryError("required Registry capability incompatibility: FAIL_CLOSED")
    matched = _matched_optional(negotiation)
    available = set(_values(available_transports, "available transport"))
    projection = request.effective_projection

    if not request.r7_single_filter_compatible:
        return O7TransportPlan(LEGACY_O1_O6, LEGACY_O1_O6, projection, "R7_SINGLE_FILTER_CONTRACT_NOT_SUFFICIENT")
    if not R7_DIRECT_BASE_CAPABILITIES <= matched:
        return O7TransportPlan(LEGACY_O1_O6, LEGACY_O1_O6, projection, "R7_DIRECT_BASE_CAPABILITY_ABSENT")
    if request.maximum_context_bytes is not None and "cap.query.budget.v1" not in matched:
        return O7TransportPlan(LEGACY_O1_O6, LEGACY_O1_O6, projection, "R7_BUDGET_CAPABILITY_ABSENT")
    if request.explicit_mcp:
        if OPTIONAL_MCP in available and "cap.transport.mcp.v1" in matched:
            return O7TransportPlan("R7_OPTIMIZED", OPTIONAL_MCP, projection, "EXPLICIT_MCP_SELECTED")
        if DIRECT_JSON in available:
            return O7TransportPlan("R7_OPTIMIZED", DIRECT_JSON, projection, "MCP_UNAVAILABLE_DIRECT_FALLBACK")
        return O7TransportPlan(LEGACY_O1_O6, LEGACY_O1_O6, projection, "MCP_AND_R7_DIRECT_UNAVAILABLE")
    if DIRECT_INDEXED in available and "cap.query.indexed-read.v1" in matched:
        return O7TransportPlan("R7_OPTIMIZED", DIRECT_INDEXED, projection, "VERIFIED_INDEXED_GATEWAY_AVAILABLE")
    if DIRECT_JSON in available:
        return O7TransportPlan("R7_OPTIMIZED", DIRECT_JSON, projection, "DIRECT_JSON_FALLBACK")
    return O7TransportPlan(LEGACY_O1_O6, LEGACY_O1_O6, projection, "R7_TRANSPORT_UNAVAILABLE")


def _verify_registry_identity(registry_identity: Mapping[str, Any], receipt: Mapping[str, Any]) -> None:
    if receipt.get("canonical_repository") != CANONICAL_REPOSITORY:
        raise O7SemanticMismatch("R7 canonical repository mismatch")
    if registry_identity.get("canonical_repository") != CANONICAL_REPOSITORY:
        raise O7SemanticMismatch("active Registry canonical repository mismatch")
    pairs = (
        ("registry_version", "registry_version"),
        ("release_sequence", "release_sequence"),
        ("release_tag", "release_tag"),
        ("manifest_sha256", "release_manifest_sha256"),
    )
    for active_key, receipt_key in pairs:
        if registry_identity.get(active_key) != receipt.get(receipt_key):
            raise O7SemanticMismatch(f"R7 receipt identity mismatch for {receipt_key}")


def _verify_request_echo(request: O7QueryRequest, response: Mapping[str, Any]) -> None:
    query = response.get("query")
    if not isinstance(query, Mapping):
        raise O7SemanticMismatch("R7 response is missing query echo")
    expected = request.gateway_request()
    for key in ("record_type", "projection", "include_freshness", "limit", "cursor", "maximum_context_bytes"):
        if query.get(key) != expected[key]:
            raise O7SemanticMismatch(f"R7 semantic query mismatch for {key}")
    filters = query.get("filters")
    if not isinstance(filters, Mapping) or dict(filters) != expected["filters"]:
        raise O7SemanticMismatch("R7 semantic query mismatch for filters")


def normalize_r7_query(
    request: O7QueryRequest,
    response: Mapping[str, Any],
    *,
    registry_identity: Mapping[str, Any],
    negotiation: Mapping[str, Any],
    transport: str,
) -> dict[str, Any]:
    if response.get("schema_version") != R7_RESPONSE_SCHEMA:
        raise O7SemanticMismatch("unsupported R7 query response schema")
    if response.get("authority") != "DERIVED_NON_AUTHORITATIVE":
        raise O7SemanticMismatch("R7 response attempted authority expansion")
    if response.get("projection") != request.effective_projection:
        raise O7SemanticMismatch("R7 response projection mismatch")
    backend = response.get("backend")
    if transport in {DIRECT_INDEXED, DIRECT_JSON} and backend != transport:
        raise O7SemanticMismatch("R7 response backend mismatch")
    _verify_request_echo(request, response)

    receipt = response.get("receipt")
    if not isinstance(receipt, Mapping) or receipt.get("schema_version") != R7_RECEIPT_SCHEMA:
        raise O7SemanticMismatch("R7 response is missing a supported receipt")
    if receipt.get("authority") != "NONE_EVIDENCE_ONLY" or receipt.get("authority_expansion") is not False:
        raise O7SemanticMismatch("R7 receipt attempted authority expansion")
    if receipt.get("model_authored_integrity_repair") is not False:
        raise O7SemanticMismatch("model-authored R7 integrity repair is prohibited")
    if receipt.get("external_reverification_required_before_trust_or_mutation") is not True:
        raise O7SemanticMismatch("R7 receipt removed external reverification boundary")
    if receipt.get("promotion_from_receipt_forbidden") is not True:
        raise O7SemanticMismatch("R7 receipt attempted promotion authority")
    if receipt.get("publication_trust") != "TRUSTED_RELEASE_IDENTITY_VERIFIED":
        raise O7SemanticMismatch("O7 optimized consumption requires trusted Registry release identity")
    if receipt.get("registry_authority_realm") != "TRUSTED_RELEASE_READ_MODEL":
        raise O7SemanticMismatch("O7 optimized consumption requires trusted release read model")
    _verify_registry_identity(registry_identity, receipt)

    query_digest = _sha(receipt.get("query_semantic_sha256"), "R7 query digest")
    result_digest = _sha(receipt.get("result_semantic_sha256"), "R7 result digest")
    records = response.get("records")
    if not isinstance(records, list) or not all(isinstance(item, Mapping) for item in records):
        raise O7SemanticMismatch("R7 response records must be an array of objects")
    if stable_digest(records) != result_digest:
        raise O7SemanticMismatch("R7 result semantic digest mismatch")

    source_ids = _values(receipt.get("exact_source_ids", []), "R7 exact source ID")
    obligation_ids = _values(receipt.get("exact_obligation_ids", []), "R7 exact obligation ID")
    record_obligation_ids = _values((item.get("obligation_id") for item in records), "R7 record obligation ID")
    if obligation_ids != record_obligation_ids:
        raise O7SemanticMismatch("R7 exact obligation identity differs from returned records")
    if response.get("count") != len(records):
        raise O7SemanticMismatch("R7 response count mismatch")

    freshness = receipt.get("freshness_evidence")
    if not isinstance(freshness, list) or not all(isinstance(item, Mapping) for item in freshness):
        raise O7SemanticMismatch("R7 freshness evidence must be an array of objects")
    freshness_ids = _values((item.get("source_id") for item in freshness), "R7 freshness source ID")
    if freshness_ids != source_ids:
        raise O7SemanticMismatch("R7 freshness evidence does not cover the exact source set")

    capability_evidence = receipt.get("capability_negotiation_evidence")
    if not isinstance(capability_evidence, list) or not all(isinstance(item, Mapping) for item in capability_evidence):
        raise O7SemanticMismatch("R7 capability evidence must be an array of objects")
    domain_evidence = receipt.get("domain_routing_evidence")
    if not isinstance(domain_evidence, Mapping):
        raise O7SemanticMismatch("R7 domain-routing evidence must be an object")

    compliance_receipt = ComplianceQueryReceipt(
        canonical_repository=CANONICAL_REPOSITORY,
        registry_version=_text(receipt.get("registry_version"), "registry_version"),
        release_sequence=receipt.get("release_sequence"),
        release_tag=_text(receipt.get("release_tag"), "release_tag"),
        manifest_sha256=_sha(receipt.get("release_manifest_sha256"), "release manifest digest"),
        filters=tuple(sorted((key, value) for key, value in request.receipt_filters().items() if value)),
        source_ids=source_ids,
        obligation_ids=obligation_ids,
    )
    routing_domains = request.domains or _values(domain_evidence.get("returned_domains", []), "returned domain")
    routing = registry_adaptive.resolve_specialists(routing_domains)
    normalized = {
        "schema_version": O7_RUNTIME_SCHEMA,
        "mode": "R7_OPTIMIZED",
        "transport": transport,
        "projection": request.effective_projection,
        "registry_identity": dict(registry_identity),
        "query_digest": query_digest,
        "source_ids": list(source_ids),
        "obligation_ids": list(obligation_ids),
        "freshness_evidence": [dict(item) for item in freshness],
        "capability_negotiation": dict(negotiation),
        "registry_capability_evidence": [dict(item) for item in capability_evidence],
        "domain_routing_evidence": dict(domain_evidence),
        "routing": routing,
        "compliance_query_receipt": compliance_receipt.to_dict(),
        "compliance_query_receipt_digest": compliance_receipt.digest,
        "records": [dict(item) for item in records],
        "next_cursor": response.get("next_cursor"),
        "encoded_bytes": response.get("encoded_bytes"),
        "authority_expansion": False,
        "model_authored_integrity_repair": False,
    }
    normalized["digest"] = stable_digest(normalized)
    return normalized


def execute_o7_query(
    request: O7QueryRequest,
    *,
    capability_surface: Mapping[str, Any],
    registry_identity: Mapping[str, Any],
    available_transports: Iterable[str],
    r7_gateway: GatewayCall | None,
    legacy_query: LegacyCall,
) -> dict[str, Any]:
    negotiation = negotiate_o7_capabilities(capability_surface)
    plan = select_o7_transport(request, negotiation, available_transports=available_transports)
    if plan.disposition == LEGACY_O1_O6:
        legacy = dict(legacy_query(request))
        return {
            "schema_version": O7_RUNTIME_SCHEMA,
            "mode": LEGACY_O1_O6,
            "transport_plan": plan.to_dict(),
            "capability_negotiation": negotiation,
            "legacy_result": legacy,
            "authority_expansion": False,
        }
    if r7_gateway is None:
        legacy = dict(legacy_query(request))
        return {
            "schema_version": O7_RUNTIME_SCHEMA,
            "mode": LEGACY_O1_O6,
            "transport_plan": O7TransportPlan(LEGACY_O1_O6, LEGACY_O1_O6, plan.projection, "R7_GATEWAY_NOT_BOUND").to_dict(),
            "capability_negotiation": negotiation,
            "legacy_result": legacy,
            "authority_expansion": False,
        }

    gateway_request = request.gateway_request()
    transport = plan.transport
    try:
        response = r7_gateway(transport, gateway_request)
    except O7IndexIntegrityError:
        available = set(available_transports)
        if transport == DIRECT_INDEXED and DIRECT_JSON in available:
            transport = DIRECT_JSON
            response = r7_gateway(transport, gateway_request)
        else:
            legacy = dict(legacy_query(request))
            return {
                "schema_version": O7_RUNTIME_SCHEMA,
                "mode": LEGACY_O1_O6,
                "transport_plan": O7TransportPlan(LEGACY_O1_O6, LEGACY_O1_O6, plan.projection, "INDEX_INTEGRITY_REJECTED_FALLBACK").to_dict(),
                "capability_negotiation": negotiation,
                "legacy_result": legacy,
                "authority_expansion": False,
            }
    normalized = normalize_r7_query(
        request,
        response,
        registry_identity=registry_identity,
        negotiation=negotiation,
        transport=transport,
    )
    normalized["transport_plan"] = O7TransportPlan("R7_OPTIMIZED", transport, plan.projection, "NORMALIZED_R7_RESULT").to_dict()
    return normalized
