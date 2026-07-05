from pathlib import Path
import shutil

import pytest

from adapters.codex import validate_codex_export


def copy_export_tree(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    export_root = tmp_path / "export"
    shutil.copytree(repo_root / "adapters" / "codex" / "skills", export_root / "skills")
    return export_root


def test_codex_export_validator_accepts_staged_export(tmp_path: Path):
    export_root = copy_export_tree(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        validate_codex_export.main(["--export-root", str(export_root)])

    assert exc_info.value.code == 0


def test_codex_export_validator_rejects_missing_skill_file(tmp_path: Path):
    export_root = copy_export_tree(tmp_path)
    (export_root / "skills" / "conductor" / "SKILL.md").unlink()

    with pytest.raises(SystemExit) as exc_info:
        validate_codex_export.main(["--export-root", str(export_root)])

    assert exc_info.value.code == 1
