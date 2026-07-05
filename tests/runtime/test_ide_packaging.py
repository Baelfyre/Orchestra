from pathlib import Path

from orchestra_runtime.protocol import ProtocolValidator
from scripts.validate_ide_packaging import validate_packaging_scaffold


def test_ide_packaging_scaffolds_validate():
    repo_root = Path(__file__).resolve().parents[2]
    assert validate_packaging_scaffold(repo_root) == []


def test_jetbrains_packaging_files_exist():
    repo_root = Path(__file__).resolve().parents[2]
    jetbrains_dir = repo_root / "adapters" / "jetbrains"

    assert (jetbrains_dir / "README.md").is_file()
    assert (jetbrains_dir / "install-guide.md").is_file()
    assert (jetbrains_dir / "workspace-instructions.template.md").is_file()
    assert (jetbrains_dir / "plugin.xml").is_file()
    assert (jetbrains_dir / "package.json").is_file()


def test_zed_and_neovim_packaging_files_exist():
    repo_root = Path(__file__).resolve().parents[2]

    for adapter_name in ("zed", "neovim"):
        adapter_dir = repo_root / "adapters" / adapter_name
        assert (adapter_dir / "README.md").is_file()
        assert (adapter_dir / "install-guide.md").is_file()
        assert (adapter_dir / "workspace-instructions.template.md").is_file()
        assert (adapter_dir / "package.json").is_file()


def test_vscodium_maps_to_vscode_compatibility_record():
    record = ProtocolValidator.compatibility_for("vscodium")

    assert record.runtime_adapter == "vscode"
    assert record.compatibility_status == "compatible"
