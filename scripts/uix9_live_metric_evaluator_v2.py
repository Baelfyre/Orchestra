"""Frozen, treatment-blind UIX-9B V2 metric evaluator.

The evaluator reads only a frozen fixture bundle, a completed candidate tree,
and an independently produced deterministic validator record.  It performs no
model, provider, network, subprocess, or repository mutation operation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "ui" / "uix9-live-project"
DEFAULT_IDENTITY = ROOT / "machine" / "ui" / "uix9b-live-proof-v2-identity.json"
DEFAULT_RESULT_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-metric-result.v2.schema.json"
DEFAULT_VALIDATOR_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-validator-result.v2.schema.json"

EVALUATOR_VERSION = "uix9b-live-metric-evaluator-v2.0.0"
FROZEN_VALIDATOR_DIGEST = "285494688ef105c813ef5f449f1e13b75529c8cddbf8a42ea76d283a9d5eecf3"

PRIMARY_METRICS = (
    "COMPONENT_REUSE",
    "DUPLICATE_COMPONENT_COUNT",
    "TOKEN_VIOLATIONS",
    "ARBITRARY_STYLE_DRIFT",
    "STATE_COVERAGE",
    "ASSET_PROVENANCE",
    "ASSET_SUBSTITUTION",
    "RESPONSIVE_CONTAINMENT",
    "ACCESSIBILITY_INVARIANTS",
    "UNRESOLVED_MAPPINGS",
    "REVISION_MISMATCH",
    "VISUAL_BASELINE_REPLACEMENT",
    "DETERMINISTIC_ACCEPTANCE",
)

CONTRACT_FILES = (
    "requirements.json",
    "task.md",
    "component-map.json",
    "design-tokens.json",
    "asset-manifest.json",
    "state-contract.json",
    "accessibility-contract.json",
    "validation-contract.json",
    "fixture-manifest.json",
    "project/package.json",
    "project/package-lock.json",
)

TOKEN_GOVERNED_PROPERTIES = {
    "background",
    "background-color",
    "border",
    "border-color",
    "border-radius",
    "box-shadow",
    "color",
    "font-family",
    "font-size",
    "font-weight",
    "gap",
    "line-height",
    "margin",
    "margin-block",
    "margin-inline",
    "outline",
    "outline-color",
    "padding",
    "padding-block",
    "padding-inline",
    "transition-duration",
}

RAW_STYLE_LITERAL = re.compile(r"(?:#[0-9a-f]{3,8}\b|(?:rgb|rgba|hsl|hsla)\s*\(|\b\d+(?:\.\d+)?(?:px|rem|em|vh|vw|ms|s)\b)", re.I)
DECLARATION = re.compile(r"(?P<property>[-a-z]+)\s*:\s*(?P<value>[^;{}]+)", re.I)
ASSET_REFERENCE = re.compile(r"(?P<reference>(?:https?://|(?:\.?/)?[^\"'`\s)]+\.(?:svg|png|jpe?g|webp|gif)))", re.I)


class EvaluationError(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def canonical_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except (OSError, UnicodeError) as exc:
        raise EvaluationError("UNREADABLE_ARTIFACT", f"{path}: {exc}") from exc


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(canonical_text(path).encode("utf-8"))


def digest_records(records: Iterable[tuple[str, str]]) -> str:
    return digest_bytes("\n".join(f"{path}\t{digest}" for path, digest in sorted(records)).encode("utf-8"))


def tree_records(root: Path, *, exclude_fixture_manifest: bool = True) -> list[tuple[str, str]]:
    if not root.is_dir():
        raise EvaluationError("MISSING_CANDIDATE_ROOT", str(root))
    records: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise EvaluationError("SYMLINK_INPUT", path.as_posix())
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if exclude_fixture_manifest and relative == "fixture-manifest.json":
            continue
        if relative.startswith("project/dist/") or relative.startswith("project/node_modules/"):
            continue
        records.append((relative, digest_file(path)))
    return records


def tree_digest(root: Path) -> str:
    return digest_records(tree_records(root))


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(canonical_text(path))
    except (json.JSONDecodeError, EvaluationError) as exc:
        detail = str(exc)
        raise EvaluationError("MALFORMED_JSON_ARTIFACT", f"{path}: {detail}") from exc
    if not isinstance(value, dict):
        raise EvaluationError("MALFORMED_JSON_ARTIFACT", f"{path} must contain an object")
    return value


def validate_schema(value: dict[str, Any], schema_path: Path, code: str) -> None:
    try:
        schema = load_json(schema_path)
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(value)
    except (EvaluationError, jsonschema.exceptions.SchemaError, jsonschema.exceptions.ValidationError) as exc:
        raise EvaluationError(code, f"{schema_path}: {exc}") from exc


def require_file(path: Path, code: str = "MISSING_REQUIRED_ARTIFACT") -> Path:
    if not path.is_file():
        raise EvaluationError(code, str(path))
    return path


def source_files(candidate_root: Path) -> dict[str, str]:
    project = require_file(candidate_root / "project" / "package.json", "MISSING_PROJECT_MANIFEST").parent
    files: dict[str, str] = {}
    for path in sorted(project.rglob("*")):
        if path.is_symlink():
            raise EvaluationError("SYMLINK_INPUT", path.as_posix())
        if not path.is_file() or "node_modules" in path.parts or "dist" in path.parts:
            continue
        relative = path.relative_to(candidate_root).as_posix()
        if path.suffix.lower() not in {".css", ".html", ".js", ".jsx", ".mjs", ".ts", ".tsx", ".vue"} or relative.startswith("project/tests/"):
            continue
        files[relative] = canonical_text(path)
    if not files:
        raise EvaluationError("MISSING_CANDIDATE_SOURCE", str(project))
    return files


def guidance_digest_from_frozen_manifest() -> str:
    manifest = load_json(require_file(ROOT / "machine" / "ui" / "uix9-live-guidance-manifest.v1.json"))
    records: list[tuple[str, str]] = []
    for material in manifest.get("materials", []):
        path = material.get("path")
        if not isinstance(path, str):
            raise EvaluationError("MALFORMED_GUIDANCE_MANIFEST", "material path")
        actual = digest_file(require_file(ROOT / path, "MISSING_GUIDANCE_MATERIAL"))
        if actual != material.get("canonical_blob_digest"):
            raise EvaluationError("GUIDANCE_DIGEST_MISMATCH", path)
        records.append((path, f"{actual}\t{material.get('role')}\t{material.get('revision_identity')}"))
    actual_digest = digest_records(records)
    if actual_digest != manifest.get("guidance_digest"):
        raise EvaluationError("GUIDANCE_MANIFEST_DIGEST_MISMATCH", str(ROOT / "machine" / "ui" / "uix9-live-guidance-manifest.v1.json"))
    return actual_digest


def verify_identity(identity_path: Path, fixture_root: Path) -> dict[str, Any]:
    identity = load_json(require_file(identity_path))
    if identity.get("evaluator_version") != EVALUATOR_VERSION:
        raise EvaluationError("EVALUATOR_VERSION_MISMATCH", str(identity_path))
    source_path = ROOT / identity.get("evaluator_source", "")
    require_file(source_path, "MISSING_EVALUATOR_SOURCE")
    if digest_file(source_path) != identity.get("evaluator_digest"):
        raise EvaluationError("EVALUATOR_DIGEST_MISMATCH", str(source_path))
    if identity.get("validator_digest") != FROZEN_VALIDATOR_DIGEST:
        raise EvaluationError("VALIDATOR_DIGEST_MISMATCH", "identity validator digest is not the frozen V1 validator")
    if identity.get("fixture_digest") != digest_records(tree_records(fixture_root)):
        raise EvaluationError("FIXTURE_DIGEST_MISMATCH", str(fixture_root))
    if identity.get("task_digest") != digest_file(require_file(fixture_root / "task.md")):
        raise EvaluationError("TASK_DIGEST_MISMATCH", str(fixture_root / "task.md"))
    if identity.get("uix_guidance_digest") != guidance_digest_from_frozen_manifest():
        raise EvaluationError("GUIDANCE_DIGEST_MISMATCH", "identity guidance digest")
    return identity


def load_fixture_contracts(fixture_root: Path, candidate_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], str]:
    require_file(fixture_root / "fixture-manifest.json")
    require_file(candidate_root / "fixture-manifest.json")
    for relative in CONTRACT_FILES:
        canonical = fixture_root / relative
        candidate = candidate_root / relative
        require_file(canonical)
        require_file(candidate)
        if digest_file(canonical) != digest_file(candidate):
            continue
        if relative.endswith(".json"):
            load_json(candidate)
    try:
        requirements = load_json(require_file(candidate_root / "requirements.json"))
        component_map = load_json(require_file(candidate_root / "component-map.json"))
        tokens = load_json(require_file(candidate_root / "design-tokens.json"))
        state_contract = load_json(require_file(candidate_root / "state-contract.json"))
        accessibility = load_json(require_file(candidate_root / "accessibility-contract.json"))
        asset_manifest = load_json(require_file(candidate_root / "asset-manifest.json"))
        validation_contract = load_json(require_file(candidate_root / "validation-contract.json"))
        fixture_manifest = load_json(require_file(candidate_root / "fixture-manifest.json"))
    except EvaluationError:
        raise
    return requirements, component_map, tokens, state_contract, digest_file(fixture_root / "fixture-manifest.json")


def revision_mismatch(fixture_root: Path, candidate_root: Path) -> bool:
    return any(digest_file(fixture_root / relative) != digest_file(candidate_root / relative) for relative in CONTRACT_FILES)


def component_metrics(requirements: dict[str, Any], component_map: dict[str, Any], files: dict[str, str]) -> tuple[bool, int]:
    source_truth = component_map.get("source_of_truth")
    if not isinstance(source_truth, str) or source_truth not in files:
        raise EvaluationError("AMBIGUOUS_COMPONENT_SOURCE", str(source_truth))
    required = requirements.get("required_components")
    if not isinstance(required, list) or not required or not all(isinstance(name, str) for name in required):
        raise EvaluationError("MALFORMED_COMPONENT_REQUIREMENTS", "required_components")
    all_source = "\n".join(files.values())
    truth_source = files[source_truth]
    duplicate_count = 0
    reused = True
    for name in required:
        declaration = re.compile(rf"(?:export\s+)?(?:async\s+)?function\s+{re.escape(name)}\b|(?:export\s+)?class\s+{re.escape(name)}\b|(?:export\s+)?(?:const|let|var)\s+{re.escape(name)}\s*=")
        total = len(declaration.findall(all_source))
        in_truth = len(declaration.findall(truth_source))
        duplicate_count += max(total - 1, 0)
        reused = reused and total == 1 and in_truth == 1
    return reused, duplicate_count


def canonical_css_variables(fixture_root: Path) -> set[str]:
    text = canonical_text(fixture_root / "project" / "src" / "styles" / "tokens.css")
    return set(re.findall(r"(--[-a-z0-9]+)\s*:", text, re.I))


def css_metrics(files: dict[str, str], allowed_variables: set[str]) -> tuple[int, int]:
    token_violations = 0
    arbitrary_style_drift = 0
    for relative, text in files.items():
        if not relative.endswith(".css") or relative.endswith("/tokens.css"):
            continue
        stripped = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        stripped = re.sub(r"@media\s*\([^)]*\)", "@media", stripped, flags=re.I)
        for match in DECLARATION.finditer(stripped):
            property_name = match.group("property").lower()
            value = " ".join(match.group("value").split())
            variables = set(re.findall(r"var\(\s*(--[-a-z0-9]+)", value, re.I))
            has_unknown_variable = bool(variables - allowed_variables)
            structural_tokens = {"0", "auto", "none", "normal", "inherit", "initial", "unset", "transparent", "currentcolor", "solid", "buttontext", "!important"}
            is_structural = all(token.lower() in structural_tokens for token in value.split())
            if property_name in TOKEN_GOVERNED_PROPERTIES and (has_unknown_variable or not variables) and not is_structural:
                token_violations += 1
            if RAW_STYLE_LITERAL.search(value) and not variables:
                arbitrary_style_drift += 1
    return token_violations, arbitrary_style_drift


def state_coverage(requirements: dict[str, Any], state_contract: dict[str, Any], files: dict[str, str]) -> float:
    required = requirements.get("required_states")
    contract_states = [item.get("id") for item in state_contract.get("states", []) if isinstance(item, dict) and item.get("required")]
    if not isinstance(required, list) or required != contract_states or not required:
        raise EvaluationError("STATE_CONTRACT_MISMATCH", "requirements and state contract differ")
    source = "\n".join(files.values())
    present = sum(bool(re.search(rf"\b{re.escape(state)}\b", source)) for state in required)
    return present / len(required)


def asset_metrics(fixture_root: Path, candidate_root: Path, asset_manifest: dict[str, Any], files: dict[str, str]) -> tuple[bool, bool]:
    approved = asset_manifest.get("approved_assets")
    if not isinstance(approved, list) or not approved:
        raise EvaluationError("MALFORMED_ASSET_MANIFEST", "approved_assets")
    approved_paths = {item.get("path") for item in approved if isinstance(item, dict)}
    references: set[str] = set()
    for text in files.values():
        for match in ASSET_REFERENCE.finditer(text):
            reference = match.group("reference")
            if reference.startswith("http://") or reference.startswith("https://"):
                references.add(reference)
            else:
                normalized = reference.replace("\\", "/").lstrip("./")
                references.add(normalized if normalized.startswith("project/") else f"project/{normalized}")
    substitution = False
    provenance = True
    for item in approved:
        path = item.get("path")
        if not isinstance(path, str) or path not in approved_paths:
            raise EvaluationError("MALFORMED_ASSET_MANIFEST", "asset path")
        candidate_asset = candidate_root / path
        canonical_asset = fixture_root / path
        if not candidate_asset.is_file() or digest_file(candidate_asset) != digest_file(canonical_asset):
            provenance = False
            substitution = True
        if path not in references:
            provenance = False
    if any(reference not in approved_paths for reference in references):
        substitution = True
    if asset_manifest.get("external_assets_allowed") is not False:
        raise EvaluationError("ASSET_POLICY_NOT_FROZEN", "external assets must be disallowed")
    return provenance, substitution


def responsive_containment(tokens: dict[str, Any], files: dict[str, str]) -> bool:
    breakpoints = tokens.get("responsive_breakpoints")
    if not isinstance(breakpoints, dict):
        raise EvaluationError("MALFORMED_RESPONSIVE_CONTRACT", "responsive_breakpoints")
    css = "\n".join(text for relative, text in files.items() if relative.endswith(".css"))
    required = [str(value) for name, value in breakpoints.items() if name in {"tablet", "desktop"}]
    media_present = all(re.search(rf"@media\s*\([^)]*\b{re.escape(value)}\b", css) for value in required)
    containment = bool(re.search(r"overflow-x\s*:\s*(?:auto|hidden)", css)) and bool(re.search(r"min-width\s*:\s*0", css)) and bool(re.search(r"max-width\s*:\s*100%", css))
    return media_present and containment


def accessibility_invariants(accessibility: dict[str, Any], files: dict[str, str]) -> bool:
    invariants = accessibility.get("invariants")
    expected = {
        "one_main_landmark": r"(?:<main\b|createElement\(\s*['\"]main['\"])",
        "navigation_has_accessible_name": r"(?:<nav\b[^>]*(?:aria-label|aria-labelledby)|createElement\(\s*['\"]nav['\"][\s\S]{0,260}aria-label)",
        "headings_follow_logical_order": r"(?:<h1\b|createElement\(\s*['\"]h1['\"]).*(?:<h[23]\b|createElement\(\s*['\"]h[23]['\"])",
        "every_interactive_control_has_accessible_name": r"(?:aria-label|<label\b|createElement\(\s*['\"]label['\"])",
        "keyboard_operation_has_no_pointer_only_action": r"(?:keydown|keyup|Escape|type\s*[:=]\s*['\"]button['\"])",
        "visible_focus_indicator_is_preserved": r"(?::focus-visible|focus-visible|focus-ring)",
        "table_has_header_cells_and_scope": r"(?:<th\b[^>]*scope\s*=|createElement\(\s*['\"]th['\"][\s\S]{0,160}scope)",
        "loading_and_error_status_is_programmatically_exposed": r"(?:aria-live|role\s*[:=]\s*['\"](?:alert|status)['\"]|aria-busy)",
        "error_text_is_not_color_only": r"(?:error|failed|unable)[\s\S]{0,180}role\s*[:=]\s*['\"]alert['\"]|role\s*[:=]\s*['\"]alert['\"][\s\S]{0,180}(?:error|failed|unable)",
        "drawer_uses_dialog_semantics_when_open": r"(?:<dialog\b|createElement\(\s*['\"]dialog['\"]|role\s*[:=]\s*['\"]dialog['\"])",
        "drawer_close_is_keyboard_operable": r"(?:Close|close)[\s\S]{0,220}(?:keydown|Escape|cancel)",
        "reduced_motion_is_respected": r"prefers-reduced-motion",
        "forced_colors_remain_usable": r"forced-colors",
    }
    if not isinstance(invariants, list) or set(invariants) != set(expected):
        raise EvaluationError("ACCESSIBILITY_CONTRACT_MISMATCH", "invariant set differs from frozen evaluator")
    source = "\n".join(files.values())
    return all(re.search(expected[invariant], source, re.I | re.S) for invariant in invariants)


def unresolved_mapping_count(files: dict[str, str]) -> int:
    source = "\n".join(files.values())
    return len(re.findall(r"UNRESOLVED_MAPPING|TODO_MAPPING|MAPPING_REQUIRED|UNKNOWN_MAPPING", source, re.I))


def visual_baseline_replacement(fixture_root: Path, candidate_root: Path, files: dict[str, str], asset_substitution: bool) -> bool:
    if asset_substitution:
        return True
    source = "\n".join(files.values())
    if re.search(r"BASELINE[_ -]REPLACED|VISUAL[_ -]BASELINE[_ -]REPLACED", source, re.I):
        return True
    canonical_manifest = load_json(fixture_root / "fixture-manifest.json")
    candidate_manifest = load_json(candidate_root / "fixture-manifest.json")
    return candidate_manifest.get("reference_identity") != canonical_manifest.get("reference_identity")


def deterministic_acceptance(fixture_root: Path, candidate_root: Path, validator_result_path: Path, identity: dict[str, Any]) -> bool:
    validator_result = load_json(require_file(validator_result_path, "MISSING_VALIDATOR_RESULT"))
    validate_schema(validator_result, DEFAULT_VALIDATOR_SCHEMA, "MALFORMED_VALIDATOR_RESULT")
    required_digests = {
        "fixture_digest": digest_records(tree_records(fixture_root)),
        "validator_digest": identity["validator_digest"],
        "dependency_manifest_digest": digest_file(fixture_root / "project" / "package-lock.json"),
        "asset_manifest_digest": digest_file(fixture_root / "asset-manifest.json"),
        "component_map_digest": digest_file(fixture_root / "component-map.json"),
        "design_token_digest": digest_file(fixture_root / "design-tokens.json"),
    }
    if any(validator_result.get(key) != value for key, value in required_digests.items()):
        return False
    if validator_result.get("candidate_tree_digest") != tree_digest(candidate_root):
        return False
    if any(validator_result.get(key) != 0 for key in ("model_calls", "provider_calls", "network_access", "external_repo_mutations")):
        return False
    checks = validator_result.get("checks", {})
    return all(isinstance(value, dict) and value.get("status") == "PASS" for value in checks.values())


def metric_payload_digest(status: str, candidate_digest: str | None, metrics: dict[str, Any] | None, failures: list[str]) -> str:
    return digest_bytes(canonical_json({"status": status, "candidate_tree_digest": candidate_digest, "metrics": metrics, "failure_codes": failures}))


def evaluate(fixture_root: Path, candidate_root: Path, validator_result_path: Path, identity_path: Path) -> dict[str, Any]:
    candidate_digest: str | None = None
    try:
        identity = verify_identity(identity_path, fixture_root)
        fixture_manifest = load_json(require_file(fixture_root / "fixture-manifest.json"))
        expected_fixture = digest_records(tree_records(fixture_root))
        if fixture_manifest.get("fixture_digest") != expected_fixture:
            raise EvaluationError("FROZEN_FIXTURE_DIGEST_MISMATCH", str(fixture_root))
        candidate_digest = tree_digest(candidate_root)
        requirements, component_map, tokens, state_contract, _ = load_fixture_contracts(fixture_root, candidate_root)
        accessibility = load_json(candidate_root / "accessibility-contract.json")
        asset_manifest = load_json(candidate_root / "asset-manifest.json")
        files = source_files(candidate_root)
        component_reuse, duplicate_count = component_metrics(requirements, component_map, files)
        token_violations, style_drift = css_metrics(files, canonical_css_variables(fixture_root))
        metrics: dict[str, Any] = {
            "COMPONENT_REUSE": component_reuse,
            "DUPLICATE_COMPONENT_COUNT": duplicate_count,
            "TOKEN_VIOLATIONS": token_violations,
            "ARBITRARY_STYLE_DRIFT": style_drift,
            "STATE_COVERAGE": state_coverage(requirements, state_contract, files),
        }
        metrics["ASSET_PROVENANCE"], metrics["ASSET_SUBSTITUTION"] = asset_metrics(fixture_root, candidate_root, asset_manifest, files)
        metrics["RESPONSIVE_CONTAINMENT"] = responsive_containment(tokens, files)
        metrics["ACCESSIBILITY_INVARIANTS"] = accessibility_invariants(accessibility, files)
        metrics["UNRESOLVED_MAPPINGS"] = unresolved_mapping_count(files)
        metrics["REVISION_MISMATCH"] = revision_mismatch(fixture_root, candidate_root)
        metrics["VISUAL_BASELINE_REPLACEMENT"] = visual_baseline_replacement(fixture_root, candidate_root, files, metrics["ASSET_SUBSTITUTION"])
        metrics["DETERMINISTIC_ACCEPTANCE"] = deterministic_acceptance(fixture_root, candidate_root, validator_result_path, identity)
        if set(metrics) != set(PRIMARY_METRICS):
            raise EvaluationError("INCOMPLETE_PRIMARY_METRICS", "evaluator did not emit exactly thirteen metrics")
        result = {
            "$schema": "../../../machine/schemas/uix9b-live-metric-result.v2.schema.json",
            "schema_version": "orchestra.uix9b-live-metric-result.v2",
            "role": "UIX_9B_LIVE_METRIC_RESULT",
            "evaluator_version": identity["evaluator_version"],
            "evaluator_digest": identity["evaluator_digest"],
            "fixture_digest": identity["fixture_digest"],
            "task_digest": identity["task_digest"],
            "validator_digest": identity["validator_digest"],
            "uix_guidance_digest": identity["uix_guidance_digest"],
            "candidate_tree_digest": candidate_digest,
            "metric_result_digest": None,
            "status": "PASS",
            "failure_codes": [],
            "metrics": metrics,
            "deterministic": True,
        }
        result["metric_result_digest"] = metric_payload_digest(result["status"], candidate_digest, metrics, [])
    except EvaluationError as exc:
        failures = [exc.code]
        result = {
            "$schema": "../../../machine/schemas/uix9b-live-metric-result.v2.schema.json",
            "schema_version": "orchestra.uix9b-live-metric-result.v2",
            "role": "UIX_9B_LIVE_METRIC_RESULT",
            "evaluator_version": EVALUATOR_VERSION,
            "evaluator_digest": None,
            "fixture_digest": None,
            "task_digest": None,
            "validator_digest": None,
            "uix_guidance_digest": None,
            "candidate_tree_digest": candidate_digest,
            "metric_result_digest": None,
            "status": "FAIL_CLOSED",
            "failure_codes": failures,
            "metrics": None,
            "deterministic": True,
        }
        result["metric_result_digest"] = metric_payload_digest(result["status"], candidate_digest, None, failures)
    validate_schema(result, DEFAULT_RESULT_SCHEMA, "EVALUATOR_RESULT_SCHEMA_FAILURE")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-root", type=Path, default=DEFAULT_FIXTURE_ROOT)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--validator-result", type=Path, required=True)
    parser.add_argument("--identity", type=Path, default=DEFAULT_IDENTITY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(args.fixture_root.resolve(), args.candidate_root.resolve(), args.validator_result.resolve(), args.identity.resolve())
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
