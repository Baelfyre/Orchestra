#!/usr/bin/env python3
"""Validate Orchestra O7.7 against the immutable Registry v0.4.0 release.

The Registry owns R7 query/index/MCP semantics. This validator binds the Registry
implementation at the integration boundary, verifies the immutable trusted release,
and requires direct JSON, indexed, and MCP consumption to normalize through the
existing Orchestra O7 runtime without authority expansion.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime import registry_adaptive, registry_o7

ORCHESTRA_BASE_COMMIT = "6428a02b9b4a89a467c3fe7443e9478dbef79989"
REGISTRY_CODE_COMMIT = "4926a3b5f48122dd45f3c8e83a12b8d071dd5387"
REGISTRY_CODE_TREE = "01be27bde90f6faa59ab74d60ba13af480c11b1d"
TRUSTED_RELEASE_TAG = "registry-v0.4.0"
TRUSTED_RELEASE_SOURCE_COMMIT = "488c979b37dd84d8645fd8e6c288d297375c4e5b"
TRUSTED_RELEASE_MANIFEST_SHA256 = "040d6576cf10e9f7e3a9a051792869541c1d33b7af3c665fad8eecb939c7baaa"
TRUSTED_RELEASE_BUNDLE_SHA256 = "e0457a75837d169d7bb8a7da14d8f4141d35a691952ff8f8978ef793e3cf92d3"


class JointConformanceError(RuntimeError):
    pass


def _registry_modules(registry_root: Path):
    registry_root = registry_root.resolve()
    if str(registry_root) not in sys.path:
        sys.path.insert(0, str(registry_root))
    from scripts import r7_mcp_server, r7_query_gateway, r7_trusted_release  # type: ignore

    return r7_mcp_server, r7_query_gateway, r7_trusted_release


def _query_spec(module: Any, request: Mapping[str, Any]):
    filters = request.get("filters")
    if not isinstance(filters, Mapping):
        raise JointConformanceError("O7 gateway request filters must be an object")
    fields = request.get("fields", [])
    if not isinstance(fields, list):
        raise JointConformanceError("O7 gateway request fields must be an array")
    return module.QuerySpec(
        record_type=request["record_type"],
        domain=filters.get("domain"),
        jurisdiction=filters.get("jurisdiction"),
        provider=filters.get("provider"),
        source_id=filters.get("source_id"),
        obligation_id=filters.get("obligation_id"),
        projection=request["projection"],
        fields=tuple(fields),
        include_freshness=request["include_freshness"],
        limit=request["limit"],
        cursor=request["cursor"],
        maximum_context_bytes=request["maximum_context_bytes"],
        representation=request["representation"],
    )


def _mcp_arguments(request: Mapping[str, Any]) -> dict[str, Any]:
    filters = request["filters"]
    return {
        "record_type": request["record_type"],
        "domain": filters.get("domain"),
        "jurisdiction": filters.get("jurisdiction"),
        "provider": filters.get("provider"),
        "source_id": filters.get("source_id"),
        "obligation_id": filters.get("obligation_id"),
        "projection": request["projection"],
        "fields": request["fields"],
        "include_freshness": request["include_freshness"],
        "limit": request["limit"],
        "cursor": request["cursor"],
        "maximum_context_bytes": request["maximum_context_bytes"],
        "representation": request["representation"],
    }


def _assert_same_semantics(label: str, left: Mapping[str, Any], right: Mapping[str, Any]) -> None:
    for key in ("records", "source_ids", "obligation_ids", "query_digest", "freshness_evidence"):
        if left.get(key) != right.get(key):
            raise JointConformanceError(f"{label} semantic mismatch for {key}")
    if left.get("authority_expansion") is not False or right.get("authority_expansion") is not False:
        raise JointConformanceError(f"{label} attempted authority expansion")
    if left.get("model_authored_integrity_repair") is not False or right.get("model_authored_integrity_repair") is not False:
        raise JointConformanceError(f"{label} permitted model-authored integrity repair")


def run_conformance(registry_root: Path, release_assets: Path) -> dict[str, Any]:
    r7_mcp_server, r7_query_gateway, r7_trusted_release = _registry_modules(registry_root)
    release_assets = release_assets.resolve()
    verified = r7_trusted_release.verify_release_assets(release_assets)
    if verified.registry_version != "0.4.0" or verified.release_sequence != 4 or verified.release_tag != TRUSTED_RELEASE_TAG:
        raise JointConformanceError("trusted Registry v0.4.0 identity mismatch")
    if verified.release_manifest_sha256 != TRUSTED_RELEASE_MANIFEST_SHA256:
        raise JointConformanceError("trusted Registry release-manifest digest mismatch")
    if verified.bundle_sha256 != TRUSTED_RELEASE_BUNDLE_SHA256:
        raise JointConformanceError("trusted Registry bundle digest mismatch")

    with tempfile.TemporaryDirectory(prefix="orchestra-o7-joint-") as name:
        temp = Path(name)
        installed = temp / "registry-v0.4.0"
        verified, installed_root = r7_trusted_release.install_release(release_assets, installed)
        index_path = temp / "registry-r7.sqlite"
        cache = r7_trusted_release.build_verified_index(
            installed_root,
            index_path,
            TRUSTED_RELEASE_MANIFEST_SHA256,
        )
        if cache.get("authority_expansion") is not False or cache.get("canonical_json_remains_authority") is not True:
            raise JointConformanceError("Registry cache evidence changed authority semantics")

        direct_gateway = r7_query_gateway.RegistryQueryGateway(
            installed_root,
            release_identity=verified.identity,
            contract_root=registry_root,
        )
        indexed_gateway = r7_query_gateway.RegistryQueryGateway(
            installed_root,
            index_path=index_path,
            release_identity=verified.identity,
            contract_root=registry_root,
        )
        mcp_adapter = r7_mcp_server.RegistryMcpAdapter(indexed_gateway)
        status = mcp_adapter.registry_status()
        if status.get("authority_expansion") is not False or status.get("registry_mutation") is not False:
            raise JointConformanceError("Registry MCP status violated read-only boundary")
        if status.get("mcp_capability") != "cap.transport.mcp.v1":
            raise JointConformanceError("Registry MCP capability mismatch")

        capability_surface = registry_adaptive.load_capability_surface(installed_root, verified.registry_version)
        registry_identity = {
            "canonical_repository": registry_o7.CANONICAL_REPOSITORY,
            "registry_version": verified.registry_version,
            "release_sequence": verified.release_sequence,
            "release_tag": verified.release_tag,
            "manifest_sha256": verified.release_manifest_sha256,
        }
        request = registry_o7.O7QueryRequest(
            workflow_stage="steward_requirements_traceability",
            domains=("privacy",),
            projection="EVIDENCE",
            limit=100,
            representation="JSON",
        )

        def legacy_query(_: registry_o7.O7QueryRequest) -> Mapping[str, Any]:
            raise JointConformanceError("O7.7 conformance unexpectedly entered legacy O1-O6 fallback")

        def gateway_call(transport: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
            if transport == registry_o7.DIRECT_JSON:
                return direct_gateway.query(_query_spec(r7_query_gateway, payload))
            if transport == registry_o7.DIRECT_INDEXED:
                return indexed_gateway.query(_query_spec(r7_query_gateway, payload))
            if transport == registry_o7.OPTIONAL_MCP:
                return mcp_adapter.registry_query(**_mcp_arguments(payload))
            raise JointConformanceError(f"unexpected O7 transport: {transport}")

        direct = registry_o7.execute_o7_query(
            request,
            capability_surface=capability_surface,
            registry_identity=registry_identity,
            available_transports=(registry_o7.DIRECT_JSON,),
            r7_gateway=gateway_call,
            legacy_query=legacy_query,
        )
        indexed = registry_o7.execute_o7_query(
            request,
            capability_surface=capability_surface,
            registry_identity=registry_identity,
            available_transports=(registry_o7.DIRECT_INDEXED, registry_o7.DIRECT_JSON),
            r7_gateway=gateway_call,
            legacy_query=legacy_query,
        )
        mcp_request = registry_o7.O7QueryRequest(
            workflow_stage=request.workflow_stage,
            domains=request.domains,
            projection=request.projection,
            limit=request.limit,
            representation=request.representation,
            explicit_mcp=True,
        )
        mcp = registry_o7.execute_o7_query(
            mcp_request,
            capability_surface=capability_surface,
            registry_identity=registry_identity,
            available_transports=(registry_o7.DIRECT_INDEXED, registry_o7.DIRECT_JSON, registry_o7.OPTIONAL_MCP),
            r7_gateway=gateway_call,
            legacy_query=legacy_query,
        )

        expected_transports = {
            "direct": (direct, registry_o7.DIRECT_JSON),
            "indexed": (indexed, registry_o7.DIRECT_INDEXED),
            "mcp": (mcp, registry_o7.OPTIONAL_MCP),
        }
        for label, (result, transport) in expected_transports.items():
            if result.get("mode") != "R7_OPTIMIZED" or result.get("transport") != transport:
                raise JointConformanceError(f"{label} did not use expected R7 optimized transport")
            receipt = result.get("compliance_query_receipt")
            if not isinstance(receipt, Mapping):
                raise JointConformanceError(f"{label} missing normalized ComplianceQueryReceipt")
            if receipt.get("registry_version") != "0.4.0" or receipt.get("release_sequence") != 4:
                raise JointConformanceError(f"{label} normalized receipt Registry identity mismatch")
            if receipt.get("release_tag") != TRUSTED_RELEASE_TAG or receipt.get("manifest_sha256") != TRUSTED_RELEASE_MANIFEST_SHA256:
                raise JointConformanceError(f"{label} normalized receipt release identity mismatch")

        _assert_same_semantics("direct/indexed", direct, indexed)
        _assert_same_semantics("indexed/MCP", indexed, mcp)
        if not direct.get("records"):
            raise JointConformanceError("O7.7 privacy conformance query returned no records")

        evidence = {
            "schema_version": "orchestra.registry-o7-joint-conformance.v1",
            "authority": "EVIDENCE_ONLY_NON_AUTHORIZING",
            "status": "PASS",
            "orchestra": {
                "repository": "Baelfyre/Orchestra",
                "base_commit": ORCHESTRA_BASE_COMMIT,
            },
            "registry_code": {
                "repository": "Baelfyre/Orchestra-Compliance-Registry",
                "commit": REGISTRY_CODE_COMMIT,
                "tree": REGISTRY_CODE_TREE,
            },
            "trusted_release": {
                "tag": TRUSTED_RELEASE_TAG,
                "source_commit": TRUSTED_RELEASE_SOURCE_COMMIT,
                "registry_version": verified.registry_version,
                "release_sequence": verified.release_sequence,
                "release_manifest_sha256": verified.release_manifest_sha256,
                "bundle_sha256": verified.bundle_sha256,
                "immutable_release_required": True,
            },
            "transports": {
                "direct_json": "PASS",
                "indexed": "PASS",
                "mcp_read_only": "PASS",
                "semantic_parity": "PASS",
            },
            "normalized_record_count": len(direct["records"]),
            "source_ids": direct["source_ids"],
            "obligation_ids": direct["obligation_ids"],
            "query_digest": direct["query_digest"],
            "authority_expansion": False,
            "model_authored_integrity_repair": False,
            "canonical_registry_json_remains_authority": True,
        }
        return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Registry R7 and Orchestra O7.7 joint conformance")
    parser.add_argument("--registry-root", type=Path, required=True)
    parser.add_argument("--release-assets", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        evidence = run_conformance(args.registry_root, args.release_assets)
        encoded = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8")
        print(encoded, end="")
        return 0
    except Exception as exc:
        print(f"ORCHESTRA_O7_7_JOINT_CONFORMANCE_FAIL={exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
