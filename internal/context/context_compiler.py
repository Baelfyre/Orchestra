#!/usr/bin/env python3
"""Compile bounded AI context from canonical JSON without changing authority.

JSON remains canonical. This module emits either compact JSON or a deterministic,
TOON-compatible projection for large/repetitive context. A JSON manifest binds the
projection to its source digest and output digest so derived context cannot silently
become authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

DEFAULT_MIN_BYTES = 4096
DEFAULT_MIN_SAVINGS_PERCENT = 10.0


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def semantic_digest(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _quote(value: str) -> str:
    if value == "" or value != value.strip() or re.search(r"[,:\[\]{}#\n\r\t]", value):
        return json.dumps(value, ensure_ascii=False)
    low = value.lower()
    if low in {"true", "false", "null"} or re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", value):
        return json.dumps(value, ensure_ascii=False)
    return value


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    if isinstance(value, str):
        return _quote(value)
    raise TypeError(f"unsupported scalar: {type(value)!r}")


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _uniform_scalar_table(values: list[Any]) -> tuple[list[str], list[dict[str, Any]]] | None:
    if not values or not all(isinstance(item, dict) for item in values):
        return None
    keys = list(values[0].keys())
    if not keys:
        return None
    for item in values:
        if list(item.keys()) != keys or not all(_is_scalar(item[key]) for key in keys):
            return None
    return keys, values


def encode_toon(value: Any) -> str:
    """Encode the supported deterministic TOON subset used for AI context projections."""
    lines: list[str] = []

    def emit(node: Any, indent: int, key: str | None = None) -> None:
        pad = " " * indent
        prefix = f"{key}: " if key is not None else ""
        if _is_scalar(node):
            lines.append(f"{pad}{prefix}{_scalar(node)}")
            return
        if isinstance(node, dict):
            if key is not None:
                lines.append(f"{pad}{key}:")
                indent += 2
            for child_key, child in node.items():
                emit(child, indent, str(child_key))
            return
        if isinstance(node, list):
            table = _uniform_scalar_table(node)
            if table:
                fields, rows = table
                header = f"[{len(rows)}]{{{','.join(fields)}}}:"
                if key is not None:
                    header = f"{key}{header}"
                lines.append(f"{pad}{header}")
                for row in rows:
                    lines.append(f"{' ' * (indent + 2)}{','.join(_scalar(row[field]) for field in fields)}")
                return
            if all(_is_scalar(item) for item in node):
                body = ",".join(_scalar(item) for item in node)
                label = f"{key}[{len(node)}]: " if key is not None else f"[{len(node)}]: "
                lines.append(f"{pad}{label}{body}")
                return
            label = f"{key}[{len(node)}]:" if key is not None else f"[{len(node)}]:"
            lines.append(f"{pad}{label}")
            for item in node:
                if _is_scalar(item):
                    lines.append(f"{' ' * (indent + 2)}- {_scalar(item)}")
                elif isinstance(item, dict):
                    first = True
                    for child_key, child in item.items():
                        marker = "- " if first else "  "
                        if _is_scalar(child):
                            lines.append(f"{' ' * (indent + 2)}{marker}{child_key}: {_scalar(child)}")
                        else:
                            lines.append(f"{' ' * (indent + 2)}{marker}{child_key}:")
                            emit(child, indent + 6)
                        first = False
                else:
                    lines.append(f"{' ' * (indent + 2)}-")
                    emit(item, indent + 4)
            return
        raise TypeError(f"unsupported node: {type(node)!r}")

    emit(value, 0)
    return "\n".join(lines) + "\n"


def choose_representation(
    value: Any,
    *,
    min_bytes: int = DEFAULT_MIN_BYTES,
    min_savings_percent: float = DEFAULT_MIN_SAVINGS_PERCENT,
) -> tuple[str, bytes, dict[str, Any]]:
    compact = canonical_json_bytes(value)
    toon = encode_toon(value).encode("utf-8")
    savings = 100.0 * (len(compact) - len(toon)) / max(1, len(compact))
    use_toon = len(compact) >= min_bytes and savings >= min_savings_percent
    selected_format = "TOON" if use_toon else "JSON"
    selected = toon if use_toon else compact + b"\n"
    metrics = {
        "compact_json_bytes": len(compact),
        "toon_bytes": len(toon),
        "toon_savings_percent": round(savings, 2),
        "min_bytes": min_bytes,
        "min_savings_percent": min_savings_percent,
        "selection_reason": "MEASURED_TOON_SAVINGS" if use_toon else "JSON_FALLBACK",
    }
    return selected_format, selected, metrics


def compile_context(
    value: Any,
    *,
    source_identity: str,
    output_path: Path,
    manifest_path: Path,
    min_bytes: int = DEFAULT_MIN_BYTES,
    min_savings_percent: float = DEFAULT_MIN_SAVINGS_PERCENT,
) -> dict[str, Any]:
    selected_format, selected, metrics = choose_representation(
        value, min_bytes=min_bytes, min_savings_percent=min_savings_percent
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(selected)
    manifest = {
        "schema_version": "orchestra.context-projection-manifest.v1",
        "authority": "NONE_DERIVED_CONTEXT_ONLY",
        "canonical_source_format": "JSON",
        "selected_format": selected_format,
        "source_identity": source_identity,
        "source_semantic_sha256": semantic_digest(value),
        "projection_sha256": sha256_bytes(selected),
        "projection_path": output_path.as_posix(),
        "metrics": metrics,
        "promotion_from_projection_forbidden": True,
        "fallback": "COMPACT_JSON",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def verify_projection(value: Any, projection_path: Path, manifest_path: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if manifest.get("authority") != "NONE_DERIVED_CONTEXT_ONLY":
        errors.append("projection authority is not NONE_DERIVED_CONTEXT_ONLY")
    if manifest.get("source_semantic_sha256") != semantic_digest(value):
        errors.append("source semantic digest mismatch")
    if manifest.get("projection_sha256") != sha256_bytes(projection_path.read_bytes()):
        errors.append("projection digest mismatch")
    return errors


def summarize_log(text: str, *, head_lines: int = 20, tail_lines: int = 40, max_matches: int = 80) -> dict[str, Any]:
    lines = text.splitlines()
    signal = re.compile(
        r"(?i)(error|fail(?:ed|ure)?|exception|traceback|warning|passed|success|timeout|killed|survived|coverage|tests?\s+run|collected)"
    )
    matches = [line for line in lines if signal.search(line)][:max_matches]
    return {
        "line_count": len(lines),
        "byte_count": len(text.encode("utf-8")),
        "sha256": sha256_bytes(text.encode("utf-8")),
        "head": lines[:head_lines],
        "signals": matches,
        "tail": lines[-tail_lines:] if len(lines) > head_lines else [],
        "raw_log_required_for_full_evidence": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Orchestra bounded JSON/TOON context compiler")
    sub = parser.add_subparsers(dest="command", required=True)

    compile_p = sub.add_parser("compile")
    compile_p.add_argument("input_json", type=Path)
    compile_p.add_argument("output", type=Path)
    compile_p.add_argument("manifest", type=Path)
    compile_p.add_argument("--source-identity")
    compile_p.add_argument("--min-bytes", type=int, default=DEFAULT_MIN_BYTES)
    compile_p.add_argument("--min-savings-percent", type=float, default=DEFAULT_MIN_SAVINGS_PERCENT)

    verify_p = sub.add_parser("verify")
    verify_p.add_argument("input_json", type=Path)
    verify_p.add_argument("projection", type=Path)
    verify_p.add_argument("manifest", type=Path)

    log_p = sub.add_parser("summarize-log")
    log_p.add_argument("input_log", type=Path)
    log_p.add_argument("output_json", type=Path)

    args = parser.parse_args(argv)
    if args.command == "summarize-log":
        summary = summarize_log(args.input_log.read_text(encoding="utf-8", errors="replace"))
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0

    value = json.loads(args.input_json.read_text(encoding="utf-8"))
    if args.command == "compile":
        manifest = compile_context(
            value,
            source_identity=args.source_identity or args.input_json.as_posix(),
            output_path=args.output,
            manifest_path=args.manifest,
            min_bytes=args.min_bytes,
            min_savings_percent=args.min_savings_percent,
        )
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0

    errors = verify_projection(value, args.projection, args.manifest)
    if errors:
        for error in errors:
            print(f"CONTEXT_PROJECTION_ERROR={error}")
        return 1
    print("CONTEXT_PROJECTION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
