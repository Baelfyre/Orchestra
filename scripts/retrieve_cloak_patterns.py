from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "machine/knowledge/cloak-ui-pattern-intelligence-cuir4.v1.json"
CATALOG_PATH = ROOT / "machine/knowledge/cloak-ui-reference-cuir3.v1.json"

def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def classify_task(task: str, index: dict[str, Any] | None = None) -> list[str]:
    index = index or _load(INDEX_PATH)
    text = task.casefold()
    scored: list[tuple[int, str]] = []
    for item in index["problem_classes"]:
        score = sum(1 for term in item["trigger_terms"] if term.casefold() in text)
        if score:
            scored.append((score, item["problem_class"]))
    scored.sort(key=lambda item: (-item[0], item[1]))
    limit = index["retrieval_policy"]["maximum_problem_classes"]
    return [name for _, name in scored[:limit]] or [index["fallback"]["problem_class"]]

def retrieve_patterns(task: str) -> dict[str, Any]:
    index = _load(INDEX_PATH)
    catalog = _load(CATALOG_PATH)
    classes = classify_task(task, index)
    class_map = {item["problem_class"]: item for item in index["problem_classes"]}
    category_priority: list[str] = []
    if classes == [index["fallback"]["problem_class"]]:
        category_priority.extend(index["fallback"]["categories"])
    else:
        for name in classes:
            for category in class_map[name]["categories"]:
                if category not in category_priority:
                    category_priority.append(category)
    rank = {category: position for position, category in enumerate(category_priority)}
    candidates = [p for p in catalog["patterns"] if p["category"] in rank]
    candidates.sort(key=lambda p: (rank[p["category"]], -int(p["evidence_count"]), p["pattern_id"]))
    maximum = int(index["retrieval_policy"]["maximum_patterns_per_task"])
    selected = candidates[:maximum]
    return {
        "task": task,
        "problem_classes": classes,
        "categories": category_priority,
        "patterns": selected,
        "implementation_authority": False,
        "handoff": index["handoff"]
    }

def main() -> int:
    parser = argparse.ArgumentParser(description="Retrieve the smallest relevant CUIR-4 Cloak pattern set.")
    parser.add_argument("task")
    args = parser.parse_args()
    print(json.dumps(retrieve_patterns(args.task), indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
