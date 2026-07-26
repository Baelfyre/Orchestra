import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPORTER = ROOT / "adapters" / "codex" / "export-codex-skills.ps1"
VALIDATOR = ROOT / "adapters" / "codex" / "validate_codex_export.py"


def assert_true(name, condition, details=""):
    if not condition:
        suffix = f"\n{details}" if details else ""
        raise AssertionError(f"{name}{suffix}")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_codex_export",
        VALIDATOR,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load validator module: {VALIDATOR}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_exporter_portable_references():
    text = EXPORTER.read_text(encoding="utf-8")
    result = {}
    in_map = False
    current_skill = None

    object_pattern = re.compile(
        r'^\s*\[pscustomobject\]@\{\s*'
        r'Source\s*=\s*"([^"]+)";\s*'
        r'Canonical\s*=\s*"([^"]+)";\s*'
        r'Export\s*=\s*"([^"]+)";\s*'
        r'Anchor\s*=\s*"([^"]+)"\s*'
        r'\},?\s*$'
    )

    for line in text.splitlines():
        stripped = line.strip()

        if stripped == "$portableReferences = @{":
            in_map = True
            continue

        if not in_map:
            continue

        if current_skill is None and stripped == "}":
            break

        skill_match = re.match(
            r'^\s*"([^"]+)"\s*=\s*@\(\s*$',
            line,
        )
        if skill_match:
            current_skill = skill_match.group(1)
            result[current_skill] = []
            continue

        if current_skill is not None and stripped == ")":
            current_skill = None
            continue

        if current_skill is not None:
            object_match = object_pattern.match(line)
            if object_match:
                result[current_skill].append(tuple(object_match.groups()))

    return {
        skill: tuple(items)
        for skill, items in result.items()
    }


def test_exporter_and_validator_reference_maps_match():
    validator = load_validator()
    exporter_map = parse_exporter_portable_references()
    expected = validator.PORTABLE_REFERENCES

    assert_true(
        "PowerShell exporter and Python validator portable-reference skill sets match",
        set(exporter_map) == set(expected),
        (
            f"Exporter skills: {sorted(exporter_map)}\n"
            f"Validator skills: {sorted(expected)}"
        ),
    )

    for skill in sorted(expected):
        assert_true(
            f"Portable-reference entries match for {skill}",
            exporter_map[skill] == expected[skill],
            (
                f"Exporter: {exporter_map[skill]!r}\n"
                f"Validator: {expected[skill]!r}"
            ),
        )


def resolve_powershell():
    return (
        shutil.which("pwsh")
        or shutil.which("powershell")
        or shutil.which("powershell.exe")
    )


def test_fresh_export_validates_when_powershell_is_available():
    host = resolve_powershell()
    if host is None:
        print(
            "SKIP: PowerShell is unavailable; "
            "map-parity regression still executed."
        )
        return

    with tempfile.TemporaryDirectory(
        prefix="codex-fresh-export-",
    ) as temp_name:
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

        export_result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert_true(
            "Fresh PowerShell Codex export succeeds",
            export_result.returncode == 0,
            (
                f"stdout:\n{export_result.stdout}\n"
                f"stderr:\n{export_result.stderr}"
            ),
        )

        tuner_dir = export_root / "skills" / "the-tuner"
        tuner_skill = tuner_dir / "SKILL.md"
        tuner_bundle = tuner_dir / "REFERENCE_CONTEXT.md"

        assert_true(
            "Fresh export contains The Tuner skill",
            tuner_skill.is_file(),
        )
        assert_true(
            "Fresh export contains The Tuner portable reference bundle",
            tuner_bundle.is_file(),
        )

        skill_text = tuner_skill.read_text(encoding="utf-8")
        assert_true(
            "Fresh export rewrites The Tuner protocol link",
            (
                "REFERENCE_CONTEXT.md"
                "#cross-specialist-coordination-protocol"
            )
            in skill_text,
        )
        assert_true(
            "Fresh export removes the repository-relative protocol target",
            (
                "../../docs/routing/"
                "CROSS_SPECIALIST_COORDINATION_PROTOCOL.md"
            )
            not in skill_text,
        )

        validation_result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--export-root",
                str(export_root),
                "--skip-tracked-export-parity",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert_true(
            "Fresh staged export passes canonical Codex export validation",
            validation_result.returncode == 0,
            (
                f"stdout:\n{validation_result.stdout}\n"
                f"stderr:\n{validation_result.stderr}"
            ),
        )


def main():
    test_exporter_and_validator_reference_maps_match()
    test_fresh_export_validates_when_powershell_is_available()
    print("Codex portable-reference export tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
