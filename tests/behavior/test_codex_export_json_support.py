import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPORTER = ROOT / "adapters" / "codex" / "export-codex-skills.ps1"
CATALOGS = {
    "clockwork": ROOT / "skills" / "clockwork" / "patterns" / "architecture-patterns.json",
    "cipher": ROOT / "skills" / "cipher" / "patterns" / "security-control-catalog.json",
}


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


def test_selective_json_catalogs_are_valid():
    for specialist, path in CATALOGS.items():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert_true(f"{specialist} JSON schema version is present", data.get("schema_version") == "1.0.0")
        assert_true(f"{specialist} JSON specialist identity matches", data.get("specialist") == specialist)

        items = data.get("patterns") if specialist == "clockwork" else data.get("control_families")
        assert_true(f"{specialist} JSON catalog is non-empty", bool(items))

        item_ids = [item.get("id") for item in items]
        assert_true(
            f"{specialist} JSON ids are unique",
            len(item_ids) == len(set(item_ids)),
            f"ids: {item_ids}",
        )


def test_exporter_declares_json_support():
    text = EXPORTER.read_text(encoding="utf-8")
    assert_true(
        "Codex exporter includes selective JSON support",
        '".json"' in text and '".md"' in text,
    )


def test_fresh_export_copies_selective_json_when_powershell_is_available():
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
            "Fresh Codex export succeeds with selective JSON support",
            result.returncode == 0,
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

        for specialist, source_path in CATALOGS.items():
            filename = source_path.name
            exported = export_root / "skills" / specialist / "patterns" / filename
            assert_true(f"Fresh export contains {specialist} JSON catalog", exported.is_file())

            source_data = json.loads(source_path.read_text(encoding="utf-8"))
            exported_data = json.loads(exported.read_text(encoding="utf-8"))
            assert_true(
                f"Fresh export preserves {specialist} JSON content",
                exported_data == source_data,
            )


def main():
    test_selective_json_catalogs_are_valid()
    test_exporter_declares_json_support()
    test_fresh_export_copies_selective_json_when_powershell_is_available()
    print("Codex selective JSON support tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())