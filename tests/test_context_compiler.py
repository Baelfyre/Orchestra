from __future__ import annotations

import json
from pathlib import Path

from scripts.context_compiler import (
    choose_representation,
    compile_context,
    encode_toon,
    semantic_digest,
    summarize_log,
    verify_projection,
)


def test_uniform_large_context_selects_toon() -> None:
    value = {
        "records": [
            {"id": f"R-{i:04d}", "status": "PASS", "count": i, "required": True}
            for i in range(1000)
        ]
    }
    selected, payload, metrics = choose_representation(value, min_bytes=100, min_savings_percent=5)
    assert selected == "TOON"
    assert payload.startswith(b"records[1000]{id,status,count,required}:")
    assert metrics["toon_savings_percent"] > 5


def test_small_context_falls_back_to_json() -> None:
    value = {"status": "PASS", "tests": 12}
    selected, payload, metrics = choose_representation(value)
    assert selected == "JSON"
    assert json.loads(payload) == value
    assert metrics["selection_reason"] == "JSON_FALLBACK"


def test_nested_command_receipt_remains_valid_projection() -> None:
    value = {
        "schema_version": "1.0.0",
        "command_id": "validate",
        "command": ["python", "-m", "pytest", "-q"],
        "exit_code": 0,
        "verdict": "PASS",
    }
    toon = encode_toon(value)
    assert "command[4]: python,-m,pytest,-q" in toon
    assert "verdict: PASS" in toon


def test_compile_and_verify_detects_projection_tamper(tmp_path: Path) -> None:
    value = {"records": [{"id": i, "status": "PASS"} for i in range(500)]}
    projection = tmp_path / "context.compiled"
    manifest = tmp_path / "context-manifest.json"
    compile_context(
        value,
        source_identity="fixture",
        output_path=projection,
        manifest_path=manifest,
        min_bytes=100,
        min_savings_percent=1,
    )
    assert verify_projection(value, projection, manifest) == []
    projection.write_text(projection.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
    assert "projection digest mismatch" in verify_projection(value, projection, manifest)


def test_compile_and_verify_detects_source_drift(tmp_path: Path) -> None:
    original = {"records": [{"id": i, "status": "PASS"} for i in range(500)]}
    drifted = {"records": [{"id": i, "status": "PASS"} for i in range(499)]}
    projection = tmp_path / "context.compiled"
    manifest = tmp_path / "context-manifest.json"
    compile_context(
        original,
        source_identity="fixture",
        output_path=projection,
        manifest_path=manifest,
        min_bytes=100,
        min_savings_percent=1,
    )
    assert "source semantic digest mismatch" in verify_projection(drifted, projection, manifest)
    assert semantic_digest(original) != semantic_digest(drifted)


def test_long_log_is_bounded_but_raw_digest_is_preserved() -> None:
    text = "\n".join([f"line {i}" for i in range(1000)] + ["FAILED tests/test_x.py::test_y", "1 failed, 999 passed"])
    summary = summarize_log(text, head_lines=5, tail_lines=5, max_matches=10)
    assert summary["line_count"] == 1002
    assert len(summary["head"]) == 5
    assert len(summary["tail"]) == 5
    assert any("FAILED" in line for line in summary["signals"])
    assert len(summary["sha256"]) == 64
    assert summary["raw_log_required_for_full_evidence"] is True
