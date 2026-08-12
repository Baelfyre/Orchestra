import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VERSION = "1.3.0"

JSON_VERSION_SURFACES = (
    "plugin.json",
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    "adapters/cursor/package.json",
    "adapters/jetbrains/package.json",
    "adapters/neovim/package.json",
    "adapters/vscode/package.json",
    "adapters/windsurf/package.json",
    "adapters/zed/package.json",
)


def _load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_release_package_versions_are_consistent() -> None:
    observed = {
        path: _load_json(path).get("version")
        for path in JSON_VERSION_SURFACES
    }
    observed[".claude-plugin/marketplace.json"] = _load_json(
        ".claude-plugin/marketplace.json"
    )["plugins"][0].get("version")

    plugin_xml = ET.parse(ROOT / "adapters/jetbrains/plugin.xml").getroot()
    observed["adapters/jetbrains/plugin.xml"] = plugin_xml.findtext("version")

    assert set(observed.values()) == {EXPECTED_VERSION}, observed
    assert len(observed) == 11
