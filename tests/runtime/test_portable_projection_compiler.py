from __future__ import annotations

import json
from pathlib import Path
import shutil

from jsonschema import Draft202012Validator

from scripts.compile_portable_projections import (
    CONTRACT_PATH,
    CONTRACT_SCHEMA_PATH,
    INDEX_SCHEMA_PATH,
    compile_projections,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "machine" / "projections" / "portable-projection-index.v1.json"


def test_canonical_projection_contract_and_generated_index_are_current() -> None:
    errors, index = compile_projections(ROOT)
    assert errors == []
    assert index is not None
    current = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    contract = json.loads((ROOT / CONTRACT_PATH).read_text(encoding="utf-8"))
    Draft202012Validator(json.loads((ROOT / CONTRACT_SCHEMA_PATH).read_text(encoding="utf-8"))).validate(contract)
    Draft202012Validator(json.loads((ROOT / INDEX_SCHEMA_PATH).read_text(encoding="utf-8"))).validate(current)
    assert current == index
    assert current["parity_status"] == "PASS"
    assert all(item["parity"] == "PASS" for item in current["projections"])


def test_projection_marker_drift_fails_closed(tmp_path: Path) -> None:
    contract = json.loads((ROOT / CONTRACT_PATH).read_text(encoding="utf-8"))
    paths = {CONTRACT_PATH, CONTRACT_SCHEMA_PATH}
    paths.update(
        source["path"]
        for source in contract["canonical_sources"]
    )
    paths.update(projection["output_path"] for projection in contract["projections"])
    for relative_path in paths:
        source_path = ROOT / relative_path
        target_path = tmp_path / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)

    target = tmp_path / contract["projections"][0]["output_path"]
    content = target.read_text(encoding="utf-8")
    content = content.replace("CONDUCTOR_IS_SOLE_INTERNAL_SPECIALIST_ROUTER", "CONDUCTOR_ROUTER_MARKER_REMOVED", 1)
    target.write_text(content, encoding="utf-8")
    errors, _ = validate_contract(tmp_path)
    assert "PARITY_MISSING:github-copilot-repository-instructions-template:conductor-sole-router" in errors
