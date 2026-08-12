import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPORTER = ROOT / "adapters" / "codex" / "export-codex-skills.ps1"
SOURCE_JSON = ROOT / "skills" / "clockwork" / "patterns" / "architecture-patterns.json"


def assert_true(name, condition, details=""):
    if not condition:
        suffix = f"\n{details}" if details else ""
        raise AssertionError(f"{name}{suffix}")


def resolve_powershell():
    return (
        shutil.which("pwsh")
        or shutil.which("powershell")
        or shutil.which("powershell.exe")
    )


def test_clockwork_pattern_catalog_is_valid_json():
    data = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    assert_true("Clockwork JSON schema version is present", data.get("schema_version") == "1.0.0")
    assert_true("Clockwork JSON specialist is clockwork", data.get("specialist") == "clockwork")
    assert_true("Clockwork JSON pattern catalog is non-empty", bool(data.get("patterns")))

    pattern_ids = [item.get("id") for item in data["patterns"]]
    assert_true(
        "Clockwork JSON pattern ids are unique",
        len(pattern_ids) == len(set(pattern_ids)),
        f"pattern ids: {pattern_ids}",
    )


def test_exporter_declares_json_support():
    text = EXPORTER.read_text(encoding="utf-8")
    assert_true(
        "Codex exporter includes selective JSON support",
        '".json"' in text and '".md"' in text,
    )


def test_fresh_export_copies_clockwork_json_when_powershell_is_available():
    host = resolve_powershell()
    if host is None:
        print("SKIP: PowerShell is unavailable; JSON parse and exporter declaration checks still executed.")
        return

    with tempfile.TemporaryDirectory(prefix="codex-json-export-") as temp_name:
        export_root = Path(temp_name)
        command = [host, "-NoProfile"]
        if Path(host).name.lower().startswith("powershell"):
            command.extend(["-ExecutionPolicy", "Bypass"])
        command.extend(
            [
                "-File",
                str(EXPORTER),
                "-SourceRoot",
                str(ROOT),
                "-TargetRoot",
                str(export_root),
            ]
        )

        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert_true(
            "Fresh Codex export succeeds with JSON support",
            result.returncode == 0,
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

        exported = export_root / "skills" / "clockwork" / "patterns" / "architecture-patterns.json"
        assert_true("Fresh export contains Clockwork JSON catalog", exported.is_file())

        source_data = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
        exported_data = json.loads(exported.read_text(encoding="utf-8"))
        assert_true("Fresh export preserves Clockwork JSON content", exported_data == source_data)


def main():
    test_clockwork_pattern_catalog_is_valid_json()
    test_exporter_declares_json_support()
    test_fresh_export_copies_clockwork_json_when_powershell_is_available()
    print("Codex JSON support tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
