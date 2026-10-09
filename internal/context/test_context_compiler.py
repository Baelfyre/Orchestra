from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from context_compiler import (
    choose_representation,
    compile_context,
    encode_toon,
    semantic_digest,
    summarize_log,
    verify_projection,
)


class ContextCompilerTests(unittest.TestCase):
    def test_uniform_large_context_selects_toon(self) -> None:
        value = {
            "records": [
                {"id": f"R-{i:04d}", "status": "PASS", "count": i, "required": True}
                for i in range(1000)
            ]
        }
        selected, payload, metrics = choose_representation(value, min_bytes=100, min_savings_percent=5)
        self.assertEqual(selected, "TOON")
        self.assertTrue(payload.startswith(b"records[1000]{id,status,count,required}:"))
        self.assertGreater(metrics["toon_savings_percent"], 5)

    def test_small_context_falls_back_to_json(self) -> None:
        value = {"status": "PASS", "tests": 12}
        selected, payload, metrics = choose_representation(value)
        self.assertEqual(selected, "JSON")
        self.assertEqual(json.loads(payload), value)
        self.assertEqual(metrics["selection_reason"], "JSON_FALLBACK")

    def test_nested_command_receipt_remains_valid_projection(self) -> None:
        value = {
            "schema_version": "1.0.0",
            "command_id": "validate",
            "command": ["python", "-m", "pytest", "-q"],
            "exit_code": 0,
            "verdict": "PASS",
        }
        toon = encode_toon(value)
        self.assertIn("command[4]: python,-m,pytest,-q", toon)
        self.assertIn("verdict: PASS", toon)

    def test_projection_tamper_is_detected(self) -> None:
        value = {"records": [{"id": i, "status": "PASS"} for i in range(500)]}
        with tempfile.TemporaryDirectory() as tmp:
            projection = Path(tmp) / "context.compiled"
            manifest = Path(tmp) / "context-manifest.json"
            compile_context(
                value,
                source_identity="fixture",
                output_path=projection,
                manifest_path=manifest,
                min_bytes=100,
                min_savings_percent=1,
            )
            self.assertEqual(verify_projection(value, projection, manifest), [])
            projection.write_text(projection.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
            self.assertIn("projection digest mismatch", verify_projection(value, projection, manifest))

    def test_source_drift_is_detected(self) -> None:
        original = {"records": [{"id": i, "status": "PASS"} for i in range(500)]}
        drifted = {"records": [{"id": i, "status": "PASS"} for i in range(499)]}
        with tempfile.TemporaryDirectory() as tmp:
            projection = Path(tmp) / "context.compiled"
            manifest = Path(tmp) / "context-manifest.json"
            compile_context(
                original,
                source_identity="fixture",
                output_path=projection,
                manifest_path=manifest,
                min_bytes=100,
                min_savings_percent=1,
            )
            self.assertIn("source semantic digest mismatch", verify_projection(drifted, projection, manifest))
            self.assertNotEqual(semantic_digest(original), semantic_digest(drifted))

    def test_long_log_is_bounded_but_raw_digest_is_preserved(self) -> None:
        text = "\n".join([f"line {i}" for i in range(1000)] + ["FAILED tests/test_x.py::test_y", "1 failed, 999 passed"])
        summary = summarize_log(text, head_lines=5, tail_lines=5, max_matches=10)
        self.assertEqual(summary["line_count"], 1002)
        self.assertEqual(len(summary["head"]), 5)
        self.assertEqual(len(summary["tail"]), 5)
        self.assertTrue(any("FAILED" in line for line in summary["signals"]))
        self.assertEqual(len(summary["sha256"]), 64)
        self.assertTrue(summary["raw_log_required_for_full_evidence"])


if __name__ == "__main__":
    unittest.main()
