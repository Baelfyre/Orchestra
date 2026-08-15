from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validation" / "classify_cosmic_ray_dump.py"
SPEC = importlib.util.spec_from_file_location("orchestra_cosmic_ray_classifier", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
classify_dump = MODULE.classify_dump

SHA = "a" * 40
BITOR = "core/ReplaceBinaryOperator_BitOr_Add"
RUNTIME_OPERATOR = "core/ReplaceComparisonOperator_Eq_NotEq"


def _line(job_id: int, module_path: str, operator: str, outcome: str) -> str:
    return json.dumps(
        [
            {
                "job_id": job_id,
                "mutations": [
                    {
                        "module_path": module_path,
                        "operator_name": operator,
                        "occurrence": 0,
                        "start_pos": [1, 0],
                        "end_pos": [1, 1],
                        "operator_args": {},
                        "definition_name": "fixture",
                    }
                ],
            },
            {"worker_outcome": outcome, "output": "", "test_outcome": 0, "diff": ""},
        ]
    )


def _classify(source: str, lines: list[str]):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        module = root / "fixture.py"
        module.write_text(source, encoding="utf-8")
        dump = root / "dump.jsonl"
        dump.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return classify_dump(dump_path=dump, repository_root=root, source_head_sha=SHA)


def test_postponed_annotation_bitor_is_excluded_for_killed_and_survived_jobs():
    result = _classify(
        "from __future__ import annotations\n\ndef f(value: int | None) -> str | None:\n    return None\n",
        [
            _line(1, "fixture.py", BITOR, "SURVIVED"),
            _line(2, "fixture.py", BITOR, "KILLED"),
            _line(3, "fixture.py", RUNTIME_OPERATOR, "KILLED"),
        ],
    )
    assert result["raw"] == {"total": 3, "killed": 2, "survived": 1, "other": 0}
    assert result["excluded_equivalent"]["count"] == 2
    assert result["runtime_relevant"] == {
        "total": 1,
        "killed": 1,
        "survived": 0,
        "score_percent": 100.0,
    }
    assert result["score_status"] == "VALID_RUNTIME_RELEVANT_SCORE"


def test_runtime_bitor_prevents_annotation_equivalence_exclusion():
    result = _classify(
        "from __future__ import annotations\n\ndef f(value: int | None):\n    return 1 | 2\n",
        [_line(1, "fixture.py", BITOR, "SURVIVED")],
    )
    assert result["excluded_equivalent"]["count"] == 0
    assert result["runtime_relevant"]["survived"] == 1
    assert result["runtime_relevant"]["score_percent"] == 0.0


def test_without_postponed_annotations_bitor_remains_runtime_relevant():
    result = _classify(
        "def f(value: int | None):\n    return None\n",
        [_line(1, "fixture.py", BITOR, "SURVIVED")],
    )
    assert result["excluded_equivalent"]["count"] == 0
    assert result["runtime_relevant"]["survived"] == 1


def test_unknown_outcome_fails_score_closed():
    result = _classify(
        "value = 1\n",
        [_line(1, "fixture.py", RUNTIME_OPERATOR, "INCOMPETENT")],
    )
    assert result["raw"]["other"] == 1
    assert result["score_status"] == "UNSCORED_UNKNOWN_OUTCOME"
    assert result["runtime_relevant"]["score_percent"] is None


def test_empty_dump_is_unscored_empty():
    result = _classify("value = 1\n", [])
    assert result["score_status"] == "UNSCORED_EMPTY"


def test_malformed_dump_and_duplicate_jobs_are_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "fixture.py").write_text("value = 1\n", encoding="utf-8")
        dump = root / "dump.jsonl"
        dump.write_text("{}\n", encoding="utf-8")
        with pytest.raises(ValueError, match="two-object"):
            classify_dump(dump_path=dump, repository_root=root, source_head_sha=SHA)

        duplicate = _line(1, "fixture.py", RUNTIME_OPERATOR, "KILLED")
        dump.write_text(duplicate + "\n" + duplicate + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match="duplicate Cosmic Ray job_id"):
            classify_dump(dump_path=dump, repository_root=root, source_head_sha=SHA)
