#!/usr/bin/env python3
"""Compile and validate canonical-source-backed portable projection parity."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


CONTRACT_PATH = Path("machine/projections/portable-projection-contract.v1.json")
CONTRACT_SCHEMA_PATH = Path("machine/schemas/portable-projection-contract.v1.schema.json")
INDEX_PATH = Path("machine/projections/portable-projection-index.v1.json")
INDEX_SCHEMA_PATH = Path("machine/schemas/portable-projection-index.v1.schema.json")
SUPPORTED_FORMATS = {"MARKDOWN_TEMPLATE"}
SUPPORTED_STRATEGIES = {
    "AGENT_SKILLS",
    "CUSTOM_AGENT",
    "MCP_TRANSPORT",
    "PLUGIN_OR_EXTENSION",
    "CLI_ADAPTER",
    "REPOSITORY_INSTRUCTIONS",
    "WORKSPACE_INSTRUCTIONS",
    "INSTRUCTION_ONLY_FALLBACK",
}
REQUIRED_INVARIANTS = (
    "CONDUCTOR_IS_SOLE_INTERNAL_SPECIALIST_ROUTER",
    "CLEAR_OWNERSHIP != CONDUCTOR_BYPASS",
    "CLEAR_OWNERSHIP MAY_ENABLE DIRECT_SINGLE_SPECIALIST_FAST_ROUTE",
    "FAST_ROUTE != ROUTER_BYPASS",
    "HOST != PROVIDER",
    "PROVIDER != SPECIALIST",
    "HOST_CAPABILITY != EXECUTION_AUTHORITY",
    "TRANSPORT != WORKFLOW",
    "UAI_TRANSPORT_SELECTION != AWF_SPECIALIST_ROUTING",
    "MODEL_SELECTION != GOVERNANCE",
)
AUTHORITY = {
    "canonical_source_remains_authoritative": True,
    "generated_projection_is_derived_only": True,
    "projection_grants_execution_authority": False,
    "projection_grants_routing_authority": False,
    "projection_grants_specialist_selection_authority": False,
    "projection_grants_workflow_topology_authority": False,
    "projection_grants_provider_selection_authority": False,
    "projection_grants_governance_authority": False,
    "installed_integration_refresh": False,
    "automatic_provider_routing": False,
    "automatic_provider_fallback": False,
    "learned_routing_promotion": False,
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized_bytes(path: Path) -> bytes:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _digest(path: Path, *, json_document: bool = False) -> str:
    if json_document:
        value = _load_json(path)
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    else:
        payload = _normalized_bytes(path)
    return hashlib.sha256(payload).hexdigest()


def _repo_path(root: Path, relative_path: str, label: str, errors: list[str]) -> Path | None:
    if not isinstance(relative_path, str) or not relative_path.strip():
        errors.append(f"MALFORMED:{label}:path")
        return None
    candidate = (root / Path(relative_path)).resolve()
    resolved_root = root.resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        errors.append(f"PROTECTED_PATH:{label}:outside_repository")
        return None
    if ".agents" in candidate.parts:
        errors.append(f"PROTECTED_PATH:{label}:runtime_copy")
        return None
    if not candidate.is_file():
        errors.append(f"MISSING:{label}:{relative_path}")
        return None
    return candidate


def _schema_errors(value: Any, schema: Any, label: str) -> list[str]:
    try:
        import jsonschema

        return [
            f"SCHEMA_VALIDATION:{label}:{'.'.join(str(part) for part in error.absolute_path) or '$'}:{error.message}"
            for error in jsonschema.Draft202012Validator(schema).iter_errors(value)
        ]
    except ImportError:
        return []
    except Exception as exc:  # pragma: no cover - schema tooling failure is environment-specific
        return [f"SCHEMA_VALIDATION:{label}:validator_error:{exc}"]


def validate_contract(root: Path) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    contract_path = _repo_path(root, CONTRACT_PATH.as_posix(), "contract", errors)
    schema_path = _repo_path(root, CONTRACT_SCHEMA_PATH.as_posix(), "contract_schema", errors)
    if contract_path is None:
        return errors, None
    try:
        contract = _load_json(contract_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"MALFORMED:contract:{exc}"], None
    schema = None
    if schema_path is not None:
        try:
            schema = _load_json(schema_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"MALFORMED:contract_schema:{exc}")
    if schema is not None:
        errors.extend(_schema_errors(contract, schema, "contract"))
    if not isinstance(contract, dict):
        return errors + ["MALFORMED:contract:object_required"], None

    if contract.get("required_invariants") != list(REQUIRED_INVARIANTS):
        errors.append("CONTRACT_DRIFT:required_invariants")
    if contract.get("authority") != AUTHORITY:
        errors.append("AUTHORITY_EXPANSION:contract.authority")
    if set(contract.get("supported_projection_formats", ())) != SUPPORTED_FORMATS:
        errors.append("CONTRACT_DRIFT:supported_projection_formats")

    sources = contract.get("canonical_sources")
    source_map: dict[str, tuple[str, Path]] = {}
    if not isinstance(sources, list):
        errors.append("MALFORMED:canonical_sources:list_required")
    else:
        for index, source in enumerate(sources):
            label = f"canonical_sources[{index}]"
            if not isinstance(source, dict):
                errors.append(f"MALFORMED:{label}:object_required")
                continue
            source_id = source.get("source_id")
            source_path = source.get("path")
            if not isinstance(source_id, str) or not source_id:
                errors.append(f"MALFORMED:{label}.source_id")
                continue
            if source_id in source_map:
                errors.append(f"CONTRACT_DRIFT:DUPLICATE_SOURCE:{source_id}")
                continue
            resolved = _repo_path(root, source_path, f"{label}.path", errors)
            if resolved is not None:
                source_map[source_id] = (source_path, resolved)

    projections = contract.get("projections")
    projection_ids: set[str] = set()
    output_paths: set[str] = set()
    if not isinstance(projections, list) or not projections:
        errors.append("MALFORMED:projections:non_empty_list_required")
    else:
        for index, projection in enumerate(projections):
            label = f"projections[{index}]"
            if not isinstance(projection, dict):
                errors.append(f"MALFORMED:{label}:object_required")
                continue
            projection_id = projection.get("projection_id")
            output_path = projection.get("output_path")
            if not isinstance(projection_id, str) or not projection_id:
                errors.append(f"MALFORMED:{label}.projection_id")
            elif projection_id in projection_ids:
                errors.append(f"CONTRACT_DRIFT:DUPLICATE_PROJECTION:{projection_id}")
            else:
                projection_ids.add(projection_id)
            if not isinstance(output_path, str) or not output_path:
                errors.append(f"MALFORMED:{label}.output_path")
            elif output_path in output_paths:
                errors.append(f"CONTRACT_DRIFT:DUPLICATE_OUTPUT:{output_path}")
            else:
                output_paths.add(output_path)
            if projection.get("format") not in SUPPORTED_FORMATS:
                errors.append(f"UNSUPPORTED_FORMAT:{label}.format")
            if projection.get("strategy_id") not in SUPPORTED_STRATEGIES:
                errors.append(f"UNSUPPORTED_STRATEGY:{label}.strategy_id")
            for source_id in projection.get("source_ids", ()):
                if source_id not in source_map:
                    errors.append(f"MISSING_SOURCE_REFERENCE:{label}:{source_id}")
            markers = projection.get("required_markers")
            marker_ids: set[str] = set()
            if not isinstance(markers, list) or not markers:
                errors.append(f"MALFORMED:{label}.required_markers")
            else:
                for marker in markers:
                    if not isinstance(marker, dict):
                        errors.append(f"MALFORMED:{label}.marker:object_required")
                        continue
                    marker_id = marker.get("marker_id")
                    text = marker.get("text")
                    if not isinstance(marker_id, str) or not marker_id or marker_id in marker_ids:
                        errors.append(f"CONTRACT_DRIFT:{label}.marker_id")
                    else:
                        marker_ids.add(marker_id)
                    if not isinstance(text, str) or not text:
                        errors.append(f"MALFORMED:{label}.marker_text")
            output = _repo_path(root, output_path, f"{label}.output_path", errors)
            if output is not None and isinstance(markers, list):
                content = output.read_text(encoding="utf-8")
                for marker in markers:
                    if isinstance(marker, dict) and isinstance(marker.get("text"), str) and marker["text"] not in content:
                        errors.append(f"PARITY_MISSING:{projection_id}:{marker.get('marker_id')}")

    return errors, contract


def build_index(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    source_map = {
        source["source_id"]: (source["path"], (root / source["path"]).resolve())
        for source in contract["canonical_sources"]
    }
    projections: list[dict[str, Any]] = []
    for projection in contract["projections"]:
        output = (root / projection["output_path"]).resolve()
        source_digests = [
            {
                "source_id": source_id,
                "path": source_map[source_id][0],
                "sha256": _digest(source_map[source_id][1], json_document=source_map[source_id][0].endswith(".json")),
            }
            for source_id in projection["source_ids"]
        ]
        projections.append(
            {
                "projection_id": projection["projection_id"],
                "host_id": projection["host_id"],
                "strategy_id": projection["strategy_id"],
                "format": projection["format"],
                "output_path": projection["output_path"],
                "output_sha256": _digest(output),
                "source_digests": source_digests,
                "matched_markers": [marker["marker_id"] for marker in projection["required_markers"]],
                "parity": "PASS",
            }
        )
    return {
        "$schema": "./machine/schemas/portable-projection-index.v1.schema.json",
        "schema_version": "orchestra.portable-projection-index.v1",
        "contract_id": contract["contract_id"],
        "contract_revision": contract["contract_revision"],
        "generated_from": {
            "contract_path": CONTRACT_PATH.as_posix(),
            "contract_sha256": _digest(root / CONTRACT_PATH, json_document=True),
        },
        "authority": AUTHORITY,
        "projections": projections,
        "parity_status": "PASS",
    }


def compile_projections(root: Path) -> tuple[list[str], dict[str, Any] | None]:
    errors, contract = validate_contract(root)
    if errors or contract is None:
        return errors, None
    return [], build_index(root, contract)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write the deterministic generated parity index")
    mode.add_argument("--check", action="store_true", help="verify the committed parity index matches current sources")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    errors, index = compile_projections(root)
    if errors or index is None:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    if args.write:
        with (root / INDEX_PATH).open("w", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(index, indent=2) + "\n")
        print(f"[PASS] Wrote {INDEX_PATH.as_posix()} with parity=PASS.")
        return 0

    index_path = root / INDEX_PATH
    try:
        current = _load_json(index_path)
    except FileNotFoundError:
        print(f"[FAIL] MISSING:{INDEX_PATH.as_posix()}")
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] MALFORMED:{INDEX_PATH.as_posix()}:{exc}")
        return 1
    schema_path = root / INDEX_SCHEMA_PATH
    if schema_path.is_file():
        errors = _schema_errors(current, _load_json(schema_path), "index")
        if errors:
            for error in errors:
                print(f"[FAIL] {error}")
            return 1
    if current != index:
        print(f"[FAIL] STALE_GENERATED_INDEX:{INDEX_PATH.as_posix()}")
        return 1
    print(f"[PASS] {INDEX_PATH.as_posix()} is current and parity=PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
