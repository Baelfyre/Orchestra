from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "machine/knowledge/cloak-ui-pattern-intelligence-cuir4.v1.json"
CATALOG = ROOT / "machine/knowledge/cloak-ui-reference-cuir3.v1.json"
GUIDE = ROOT / "skills/cloak/CUIR_PATTERN_INTELLIGENCE_GUIDE.md"
CODEX_GUIDE = ROOT / "adapters/codex/skills/cloak/CUIR_PATTERN_INTELLIGENCE_GUIDE.md"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _module():
    path = ROOT / "scripts/retrieve_cloak_patterns.py"
    spec = importlib.util.spec_from_file_location("cuir4_retrieval", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cuir4_binds_exact_canonical_cuir3_and_keeps_cuir5_closed():
    index = _json(INDEX)
    assert index["canonical_cuir3_input"]["lifecycle_closeout_commit"] == "36f8d262f64efd91f0961f780f1cd54272eeadb3"
    assert index["canonical_cuir3_input"]["normalized_pattern_count"] == 16
    assert index["protected_boundaries"]["cuir5_started"] is False
    assert index["retrieval_policy"]["default_catalog_injection"] is False
    assert index["retrieval_policy"]["automatic_host_injection"] is False


def test_all_normalized_categories_and_patterns_are_reachable_without_full_injection():
    index = _json(INDEX)
    catalog = _json(CATALOG)
    categories = {c["category_id"] for c in catalog["categories"]}
    referenced = {category for item in index["problem_classes"] for category in item["categories"]}
    referenced.update(index["fallback"]["categories"])
    assert categories <= referenced
    reachable = {p["pattern_id"] for p in catalog["patterns"] if p["category"] in referenced}
    assert reachable == {p["pattern_id"] for p in catalog["patterns"]}
    assert index["retrieval_policy"]["maximum_patterns_per_task"] < len(catalog["patterns"])


def test_representative_retrieval_is_bounded_and_semantically_relevant():
    module = _module()
    cases = {
        "Design a multi-step signup form with password validation": "cuir3.semantic_field_and_control_state",
        "Show upload progress, pause, resume, and completion": "cuir3.operation_progress_lifecycle",
        "Separate delete account from normal settings actions": "cuir3.action_priority_and_destructive_separation",
        "Create a collapsed sidebar with a clear selected destination": "cuir3.destination_state_navigation",
        "Choose general UI icons and a brand logo": "cuir3.general_ui_icon_system",
    }
    for task, expected in cases.items():
        result = module.retrieve_patterns(task)
        ids = {p["pattern_id"] for p in result["patterns"]}
        assert expected in ids
        assert len(result["patterns"]) <= 5
        assert result["implementation_authority"] is False


def test_brand_and_general_icon_rights_remain_separate():
    module = _module()
    result = module.retrieve_patterns("Use UI icons and a brand logo")
    patterns = {p["pattern_id"]: p for p in result["patterns"]}
    assert "cuir3.general_ui_icon_system" in patterns
    assert "cuir3.brand_icon_traceability_and_rights" in patterns
    assert "REUSE_WITH_NOTICE" in patterns["cuir3.general_ui_icon_system"]["reuse_classifications"]
    assert "REUSE_WITH_RIGHTS_REVIEW" in patterns["cuir3.brand_icon_traceability_and_rights"]["reuse_classifications"]


def test_adjacent_progressive_disclosure_guide_preserves_frozen_core_skill():
    assert GUIDE.read_text(encoding="utf-8") == CODEX_GUIDE.read_text(encoding="utf-8")
    guide = GUIDE.read_text(encoding="utf-8")
    assert "Ponytail" in guide
    assert "do not copy source expression or assets" in guide
    index = _json(INDEX)
    assert index["retrieval_policy"]["mode"] == "PROGRESSIVE_DISCLOSURE"
    assert index["retrieval_policy"]["default_catalog_injection"] is False


def test_readme_machine_projection_tracks_separately_started_cuir5_without_authority_widening():
    readme = _json(ROOT / "README.json")
    cuir3 = readme["capabilities"]["cloak_ui_reference_corpus_cuir3"]
    cuir4 = readme["capabilities"]["cloak_ui_reference_corpus_cuir4"]
    cuir5 = readme["capabilities"]["cloak_ui_reference_corpus_cuir5"]
    assert cuir3["cuir4_started"] is True
    assert cuir4["status"] == "CUIR_4_CANONICAL_MERGED_VERIFIED"
    assert cuir4["progressive_retrieval"] is True
    assert cuir4["cuir5_started"] is True
    assert cuir4["implementation_authority"] is False
    assert cuir5["status"] == "CUIR_5_CONTROLLED_EVALUATION_CANDIDATE"
    assert cuir5["runtime_integration"] is False
    assert "cannot grant implementation" in cuir5["authority_note"]
