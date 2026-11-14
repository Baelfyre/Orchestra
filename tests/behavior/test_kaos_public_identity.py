import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BRAND_ASSET = "assets/branding/kontrolled-kaos-dual-k-emblem.png"
BRAND_ASSET_SHA256 = "e8a9deefd3cbb0bf9a9bedec33dd1542d19de1ad044933824e7830de3de0f48b"
SPECIALISTS = {
    "arbiter",
    "chronicler",
    "cipher",
    "cloak",
    "clockwork",
    "conductor",
    "dagger",
    "overseer",
    "ponytail",
    "scribe",
    "the-governor",
    "the-steward",
    "the-tuner",
    "weaver",
}


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_public_brand_aliases_preserve_specialist_contracts_and_asset_bytes():
    root_manifest = load_json("plugin.json")
    registry = load_json("machine/specialists/registry.v1.json")
    manifest_specialists = {item["slug"]: item for item in root_manifest["skills"]}
    registered_specialists = {item["slug"]: item for item in registry["specialists"]}

    assert root_manifest["name"] == "conductor"
    assert root_manifest["display_name"] == "Kontrolled Kaos"
    assert root_manifest["repository"] == "https://github.com/Baelfyre/Kaos"
    assert root_manifest["version"] == "1.12.0"
    assert set(manifest_specialists) == SPECIALISTS
    assert set(registered_specialists) == SPECIALISTS
    assert {
        slug: (item["name"], item["icon_path"])
        for slug, item in manifest_specialists.items()
    } == {
        slug: (item["name"], item["icon_path"])
        for slug, item in registered_specialists.items()
    }

    codex = load_json(".codex-plugin/plugin.json")
    codex_marketplace = load_json(".agents/plugins/marketplace.json")
    assert codex["name"] == "conductor"
    assert codex["interface"]["displayName"] == "Kontrolled Kaos"
    assert "./brand-skills/" in codex["skills"]
    assert codex_marketplace["name"] == "orchestra"
    assert codex_marketplace["interface"]["displayName"] == "Kontrolled Kaos"
    assert codex_marketplace["plugins"][0]["name"] == "conductor"

    antigravity = load_json(".antigravity-plugin/plugin.json")
    assert antigravity["name"] == "kaos"
    assert antigravity["displayName"] == "Kontrolled Kaos"
    assert antigravity["skills"] == "./brand-skills/"

    claude = load_json(".claude-plugin/plugin.json")
    claude_marketplace = load_json(".claude-plugin/marketplace.json")
    assert claude["name"] == "kaos"
    assert claude["displayName"] == "Kontrolled Kaos"
    assert claude_marketplace["name"] == "orchestra"
    assert claude_marketplace["plugins"][0]["name"] == "kaos"

    alias = (ROOT / "brand-skills/kaos/SKILL.md").read_text(encoding="utf-8")
    assert "name: kaos" in alias
    assert "skills/conductor/SKILL.md" in alias
    assert "no dispatcher" in alias

    asset = ROOT / BRAND_ASSET
    assert hashlib.sha256(asset.read_bytes()).hexdigest() == BRAND_ASSET_SHA256
    assert root_manifest["icon_path"] == BRAND_ASSET
    assert root_manifest["logo_path"] == BRAND_ASSET
    assert codex["interface"]["composerIcon"] == f"./{BRAND_ASSET}"
    assert codex["interface"]["logo"] == f"./{BRAND_ASSET}"
    assert antigravity["logo"] == BRAND_ASSET

    scaffold_ids = {
        "cursor": "orchestra-cursor-scaffold",
        "jetbrains": "orchestra-jetbrains-scaffold",
        "neovim": "orchestra-neovim-scaffold",
        "vscode": "orchestra-vscode-scaffold",
        "windsurf": "orchestra-windsurf-scaffold",
        "zed": "orchestra-zed-scaffold",
    }
    for host, plugin_id in scaffold_ids.items():
        manifest = load_json(f"adapters/{host}/package.json")
        assert manifest["name"] == plugin_id
        assert manifest["displayName"].startswith("Kontrolled Kaos ")
        assert manifest["displayName"].endswith(" Scaffold")


def test_installation_docs_use_host_specific_kaos_namespaces():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    installation = (ROOT / "docs/setup/INSTALLATION.md").read_text(encoding="utf-8")
    compatibility = (ROOT / "docs/setup/COMPATIBILITY.md").read_text(encoding="utf-8")
    readiness = (ROOT / "docs/project/PLUGIN_READINESS.md").read_text(encoding="utf-8")
    docs_map = (ROOT / "docs/README.md").read_text(encoding="utf-8")
    reference = (ROOT / "docs/reference/README.md").read_text(encoding="utf-8")
    getting_started = (ROOT / "docs/reference/getting-started/README.md").read_text(encoding="utf-8")
    integrations = (ROOT / "docs/reference/integrations/README.md").read_text(encoding="utf-8")

    assert "Codex: $kaos" in readme
    assert "Antigravity: /kaos" in readme
    assert "Claude Code: /kaos:conductor" in readme
    assert "https://github.com/Baelfyre/Kaos" in readme
    assert "agy plugin install https://github.com/Baelfyre/Kaos" in installation
    assert "codex plugin add conductor@orchestra" in installation
    assert "/plugin install kaos@orchestra" in installation
    assert "kaos@orchestra" in compatibility
    assert "kaos@kaos" not in compatibility
    assert "/kaos:conductor" in installation
    assert "Kontrolled Kaos update checks are notify-only" in installation
    assert "conductor@orchestra" in compatibility
    assert "Kontrolled Kaos is intentionally designed" in readiness
    assert "Orchestra is intentionally designed" not in readiness
    assert "# Kontrolled Kaos Documentation Map" in docs_map
    assert "# Kontrolled Kaos Reference" in reference
    assert "Kontrolled Kaos capability does not grant permission" in getting_started
    assert "Kontrolled Kaos integrates with supported hosts" in integrations
    assert "@Kaos" in compatibility
    assert "https://github.com/Baelfyre/Orchestra" not in readme + installation


def test_selected_kaos_emblem_png_uses_rgba_and_expected_dimensions():
    image = (ROOT / BRAND_ASSET).read_bytes()
    assert image[:8] == b"\x89PNG\r\n\x1a\n"
    assert image[12:16] == b"IHDR"
    assert (
        int.from_bytes(image[16:20], "big"),
        int.from_bytes(image[20:24], "big"),
        image[24],
        image[25],
    ) == (1254, 1254, 8, 6)
