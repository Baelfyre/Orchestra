from pathlib import Path

from scripts.validate_ide_packaging import validate_packaging_scaffold


def test_ide_packaging_scaffolds_validate():
    repo_root = Path(__file__).resolve().parents[2]
    assert validate_packaging_scaffold(repo_root) == []
