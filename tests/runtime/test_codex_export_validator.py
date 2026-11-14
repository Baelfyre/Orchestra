from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from adapters.codex import validate_codex_export

LEGACY_MARKED_GUIDE_TEST_IDS = {
    Path("skills/cloak/VISUAL_REFINEMENT_8PT_GUIDE.md"): "cloak-visual",
    Path("skills/cloak/ARTIFACT_VISUAL_ACCESSIBILITY_GUIDE.md"): "cloak-artifact",
    Path("skills/scribe/ARTIFACT_AUTHORING_AND_BACKEND_SELECTION_GUIDE.md"): "scribe-artifact",
}


def copy_export_tree(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    export_root = tmp_path / "export"
    shutil.copytree(repo_root / "adapters" / "codex" / "skills", export_root / "skills")
    shutil.copytree(repo_root / "adapters" / "codex" / "machine", export_root / "machine")
    source_guide = repo_root / "skills" / "cloak" / "VISUAL_REFINEMENT_8PT_GUIDE.md"
    exported_guide = export_root / "skills" / "cloak" / source_guide.name
    exported_guide.write_text(
        validate_codex_export.strip_cloak_visual_guide_markers(source_guide.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    return export_root


def copy_export_sources(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    source_root = tmp_path / "source"
    shutil.copytree(repo_root / "skills", source_root / "skills")
    required_files = {
        Path("plugin.json"),
        Path("ROUTING_MAP.md"),
        Path("machine/knowledge/truesheet-specialist-reference.v1.json"),
        *(
            Path(reference[0])
            for references in validate_codex_export.PORTABLE_REFERENCES.values()
            for reference in references
        ),
    }
    for relative_path in required_files:
        destination = source_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo_root / relative_path, destination)
    return source_root


def write_visual_guide_pair(tmp_path: Path, source: str, exported: str) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    export_root = tmp_path / "export"
    source_path = repo_root / validate_codex_export.CLOAK_VISUAL_GUIDE_SOURCE
    export_path = export_root / "skills" / validate_codex_export.CLOAK_VISUAL_GUIDE_EXPORT
    source_path.parent.mkdir(parents=True)
    export_path.parent.mkdir(parents=True)
    source_path.write_text(source, encoding="utf-8")
    export_path.write_text(exported, encoding="utf-8")
    return repo_root, export_root / "skills"


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


def test_codex_export_validator_rejects_changed_non_marker_guide_content(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / validate_codex_export.CLOAK_VISUAL_GUIDE_SOURCE).read_text(encoding="utf-8")
    exported = validate_codex_export.strip_cloak_visual_guide_markers(source)
    repo, codex_skills_dir = write_visual_guide_pair(tmp_path, source, exported.replace("Optional Orchestra reference", "Changed reference", 1))

    assert validate_codex_export.validate_cloak_visual_guide_parity(repo, codex_skills_dir) == 1


@pytest.mark.parametrize(
    "mutate_source",
    [
        pytest.param(lambda text: text.replace("<!-- @codebase_provenance_JEO -->\n", "", 1), id="missing"),
        pytest.param(
            lambda text: text.replace(
                "<!-- @codebase_provenance_JEO -->\n<!-- @codebase_rights_JEO -->",
                "<!-- @codebase_rights_JEO -->\n<!-- @codebase_provenance_JEO -->",
                1,
            ),
            id="misordered",
        ),
        pytest.param(lambda text: text.replace("<!-- @codebase_provenance_JEO -->", "<!-- @codebase_provenance_JEO-->", 1), id="malformed"),
        pytest.param(lambda text: text + "\n<!-- @codebase_collaboration_JEO -->\n", id="unexpected"),
        pytest.param(
            lambda text: text.replace(
                "\n\n# Cloak:",
                "\n\n<!-- @Codebase_collaboration_JEO -->\n\n# Cloak:",
                1,
            ),
            id="case-variant-unexpected",
        ),
        pytest.param(lambda text: text.replace("# Cloak:", "<!-- @codebase_verified_JEO -->\n# Cloak:", 1), id="misplaced"),
    ],
)
def test_codex_export_validator_rejects_invalid_source_markers(tmp_path: Path, mutate_source):
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / validate_codex_export.CLOAK_VISUAL_GUIDE_SOURCE).read_text(encoding="utf-8")
    exported = validate_codex_export.strip_cloak_visual_guide_markers(source)
    repo, codex_skills_dir = write_visual_guide_pair(tmp_path, mutate_source(source), exported)

    assert validate_codex_export.validate_cloak_visual_guide_parity(repo, codex_skills_dir) == 1


def test_codex_export_validator_rejects_markers_in_generated_guide(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / validate_codex_export.CLOAK_VISUAL_GUIDE_SOURCE).read_text(encoding="utf-8")
    exported = validate_codex_export.strip_cloak_visual_guide_markers(source)
    repo, codex_skills_dir = write_visual_guide_pair(tmp_path, source, "<!-- @codebase_rights_JEO -->\n" + exported)

    assert validate_codex_export.validate_cloak_visual_guide_parity(repo, codex_skills_dir) == 1

    interior_export = exported.replace(
        "## Activation and precedence",
        "<!-- @codebase_rights_JEO -->\n\n## Activation and precedence",
        1,
    )
    interior_repo, interior_skills_dir = write_visual_guide_pair(tmp_path / "interior", source, interior_export)
    assert validate_codex_export.validate_cloak_visual_guide_parity(interior_repo, interior_skills_dir) == 1


def test_fresh_export_strips_source_markers_from_guides_and_validates(tmp_path: Path):
    host = shutil.which("pwsh") or shutil.which("powershell") or shutil.which("powershell.exe")
    if host is None:
        pytest.skip("PowerShell is unavailable")

    repo_root = Path(__file__).resolve().parents[2]
    export_root = tmp_path / "fresh-codex-export"
    command = [host, "-NoProfile"]
    if Path(host).name.lower().startswith("powershell"):
        command.extend(["-ExecutionPolicy", "Bypass"])
    command.extend(
        [
            "-File",
            str(repo_root / "adapters" / "codex" / "export-codex-skills.ps1"),
            "-SourceRoot",
            str(repo_root),
            "-TargetRoot",
            str(export_root),
        ]
    )
    export_result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=False)
    assert export_result.returncode == 0, f"{export_result.stdout}\n{export_result.stderr}"

    source_guide = repo_root / "skills" / "cloak" / "VISUAL_REFINEMENT_8PT_GUIDE.md"
    exported_guide = export_root / "skills" / "cloak" / source_guide.name
    source_text = source_guide.read_text(encoding="utf-8")
    exported_text = exported_guide.read_text(encoding="utf-8")
    assert source_text.startswith("<!-- @codebase_provenance_JEO -->\n<!-- @codebase_rights_JEO -->\n")
    assert exported_text == validate_codex_export.strip_cloak_visual_guide_markers(source_text)
    assert "@codebase_" not in exported_text
    assert "heydamir/unslop" in exported_text
    assert "mshumer/unslop" in exported_text

    for guide in validate_codex_export.MARKED_SUPPORT_GUIDES[1:]:
        source_relative, export_relative, label = guide[:3]
        expected_markers = guide[3] if len(guide) == 4 else validate_codex_export.CLOAK_VISUAL_GUIDE_MARKERS
        source_path = repo_root / source_relative
        exported_path = export_root / "skills" / export_relative
        source_text = source_path.read_text(encoding="utf-8")
        exported_text = exported_path.read_text(encoding="utf-8")
        assert exported_text == validate_codex_export.strip_jeo_support_markers(source_text, label, expected_markers)
        assert "@codebase_" not in exported_text

    unrelated_source = repo_root / "skills" / "cloak" / "DESIGN_TOKENS_COMPONENT_STATES_GUIDE.md"
    unrelated_export = export_root / "skills" / "cloak" / unrelated_source.name
    assert unrelated_export.read_text(encoding="utf-8") == unrelated_source.read_text(encoding="utf-8")

    validation_result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "adapters" / "codex" / "validate_codex_export.py"),
            "--export-root",
            str(export_root),
            "--skip-tracked-export-parity",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert validation_result.returncode == 0, f"{validation_result.stdout}\n{validation_result.stderr}"


@pytest.mark.parametrize(
    "source_relative",
    tuple(guide[0] for guide in validate_codex_export.MARKED_SUPPORT_GUIDES),
    ids=tuple(
        LEGACY_MARKED_GUIDE_TEST_IDS.get(
            guide[0],
            guide[0].as_posix().lower().replace("/", "-").replace("_", "-").replace(".md", ""),
        )
        for guide in validate_codex_export.MARKED_SUPPORT_GUIDES
    ),
)
def test_exporter_rejects_case_variant_unexpected_guide_marker(
    tmp_path: Path,
    source_relative: Path,
):
    host = shutil.which("pwsh") or shutil.which("powershell") or shutil.which("powershell.exe")
    if host is None:
        pytest.skip("PowerShell is unavailable")

    source_root = copy_export_sources(tmp_path)
    guide_path = source_root / source_relative
    guide_text = guide_path.read_text(encoding="utf-8")
    guide_path.write_text(
        guide_text.replace(
            "<!-- @codebase_provenance_JEO -->",
            "<!-- @Codebase_provenance_JEO -->",
            1,
        ),
        encoding="utf-8",
    )

    command = [host, "-NoProfile"]
    if Path(host).name.lower().startswith("powershell"):
        command.extend(["-ExecutionPolicy", "Bypass"])
    command.extend(
        [
            "-File",
            str(Path(__file__).resolve().parents[2] / "adapters" / "codex" / "export-codex-skills.ps1"),
            "-SourceRoot",
            str(source_root),
            "-TargetRoot",
            str(tmp_path / "rejected-export"),
        ]
    )
    result = subprocess.run(command, cwd=source_root, capture_output=True, text=True, check=False)

    assert result.returncode != 0
    assert "contain no other codebase markers" in " ".join(result.stderr.split())
