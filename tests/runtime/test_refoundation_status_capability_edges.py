import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestra_runtime.authority import AuthorityProvenance, Constraint, ProvenanceSource
from orchestra_runtime.capabilities import (
    CapabilityResolver,
    RuntimeCapability,
    RuntimeCapabilityGrant,
    load_trusted_capability_manifest,
)
from orchestra_runtime.errors import InvalidCapabilityConfigurationError
from orchestra_runtime.status import (
    ContractStatus,
    DiagnosticsStatus,
    GitStatus,
    OrchestraStatusProjection,
    ProjectStatus,
    StatusDiagnostic,
    ValidationStatus,
    _normalize_string_tuple,
    _parse_porcelain_v1_z,
    _validate_sha,
    build_status_projection,
    collect_contract_status,
    collect_git_status,
    collect_project_status,
    main as status_main,
    reconcile_validation_status,
    render_status_projection,
    serialize_status_projection,
    serialize_status_projection_to_str,
)


SHA = "a" * 40


def _prov(source=ProvenanceSource.TRUSTED_REPOSITORY_POLICY):
    return AuthorityProvenance(source, "policy", "1", "runtime")


def _grant(provenance=None, constraints=(Constraint.exact("mode", "safe"),)):
    capability = RuntimeCapability("filesystem.read", "clockwork", ("read",), "fixture")
    return RuntimeCapabilityGrant(capability, ("read",), provenance or _prov(), constraints)


# Capability integration-boundary gaps

def test_capability_rejects_noncanonical_identifier_and_malformed_from_dict():
    with pytest.raises(InvalidCapabilityConfigurationError, match="canonical identifier"):
        RuntimeCapability("BAD SPACE", "clockwork", ("read",), "fixture")
    with pytest.raises(InvalidCapabilityConfigurationError):
        RuntimeCapability.from_dict({"capability_id": "x", "owner": "clockwork", "operations": "read", "description": "fixture"})
    with pytest.raises(InvalidCapabilityConfigurationError, match="malformed capability grant"):
        RuntimeCapabilityGrant.from_dict({"capability": [], "provenance": {}})


def test_capability_manifest_rejects_corrupted_provenance_and_constraint_intersection():
    resolver = CapabilityResolver()
    corrupted = _prov()
    object.__setattr__(corrupted, "source_type", "UNTRUSTED")
    with pytest.raises(InvalidCapabilityConfigurationError, match="not trusted"):
        resolver.build_manifest("run", (_grant(),), corrupted, manifest_id="manifest", policy_version="1")

    parent = resolver.build_manifest("root", (_grant(),), _prov(), manifest_id="root", policy_version="1")
    delegated = AuthorityProvenance(
        ProvenanceSource.ACCEPTED_DELEGATION,
        "delegation",
        "1",
        "runtime",
        "root",
        "decision",
    )
    requested = _grant(provenance=delegated, constraints=(Constraint.exact("mode", "unsafe"),))
    with pytest.raises(InvalidCapabilityConfigurationError, match="constraints do not intersect"):
        resolver.intersect(parent, (requested,), "child", delegated, manifest_id="child")


def test_capability_loader_rejects_malformed_manifest_shapes(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"capability_manifest":{"provenance":[],"grants":[]}}', encoding="utf-8")
    with pytest.raises(InvalidCapabilityConfigurationError, match="malformed"):
        load_trusted_capability_manifest(tmp_path, Path("bad.json"))


# Status validation and collector gaps

def test_status_scalar_tuple_and_diagnostic_guards():
    with pytest.raises(TypeError, match="must be a str"):
        _validate_sha("sha", 1)
    with pytest.raises(ValueError, match="valid hex SHA"):
        _validate_sha("sha", "not-sha")
    with pytest.raises(TypeError, match="sequence of str"):
        _normalize_string_tuple("values", "abc")
    with pytest.raises(TypeError, match="tuple or list"):
        _normalize_string_tuple("values", {"x"})
    with pytest.raises(ValueError, match="non-empty strings"):
        _normalize_string_tuple("values", [""])
    assert _normalize_string_tuple("values", ["b", "a", "a"]) == ("a", "b")
    with pytest.raises(ValueError, match="severity"):
        StatusDiagnostic("INFO", "message")


def test_git_status_cross_field_invariants():
    with pytest.raises(ValueError, match="must be in remote_names"):
        GitStatus(is_git_repo=True, selected_remote="origin", remote_names=("upstream",))
    with pytest.raises(ValueError, match="without selected_remote"):
        GitStatus(is_git_repo=True, selected_main_ref="origin/main")
    with pytest.raises(ValueError, match="does not match count sums"):
        GitStatus(is_git_repo=True, is_clean=True, staged_count=1, modified_count=0, untracked_count=0)


def test_validation_status_and_projection_guards():
    with pytest.raises(ValueError, match="valid percentage"):
        ValidationStatus(runtime_coverage="ninety")
    with pytest.raises(ValueError, match="between 0 and 100"):
        ValidationStatus(runtime_coverage="101%")
    base = (GitStatus(False), ProjectStatus(), ContractStatus(), ValidationStatus(), DiagnosticsStatus())
    with pytest.raises(ValueError, match="projection_version"):
        OrchestraStatusProjection("bad", "2026-08-15T12:00:00Z", *base)
    with pytest.raises(ValueError, match="UTC"):
        OrchestraStatusProjection("1.0", "2026-08-15T12:00:00", *base)
    with pytest.raises(TypeError, match="git must be"):
        OrchestraStatusProjection("1.0", "2026-08-15T12:00:00Z", "bad", ProjectStatus(), ContractStatus(), ValidationStatus(), DiagnosticsStatus())  # type: ignore[arg-type]


def test_porcelain_parser_malformed_rename_and_normal_counts():
    assert _parse_porcelain_v1_z(b"\xff\xff\x00") == (0, 0, 0, False)
    staged, modified, untracked, clean = _parse_porcelain_v1_z(
        b"M  file\x00 M file2\x00?? file3\x00R  old\x00new\x00"
    )
    assert (staged, modified, untracked, clean) == (2, 1, 1, False)


class _Runner:
    def __init__(self, mapping):
        self.mapping = mapping

    def __call__(self, args, cwd):
        value = self.mapping.get(tuple(args), (1, ""))
        if isinstance(value, BaseException):
            raise value
        code, stdout = value
        return subprocess.CompletedProcess(args, code, stdout=stdout, stderr="")


def test_collect_git_status_fail_closed_environment_edges(tmp_path):
    missing = collect_git_status(
        tmp_path,
        command_runner=_Runner({("git", "rev-parse", "--is-inside-work-tree"): FileNotFoundError()}),
    )
    assert missing[0].is_git_repo is False and missing[2]

    timeout = collect_git_status(
        tmp_path,
        command_runner=_Runner({("git", "rev-parse", "--is-inside-work-tree"): subprocess.TimeoutExpired("git", 1)}),
    )
    assert timeout[0].is_git_repo is False and "timed out" in timeout[2][0]

    nonrepo = collect_git_status(
        tmp_path,
        command_runner=_Runner({("git", "rev-parse", "--is-inside-work-tree"): (1, "false")}),
    )
    assert nonrepo[0].is_git_repo is False


def test_collect_git_status_detached_worktree_shallow_nonorigin_and_missing_main(tmp_path):
    mapping = {
        ("git", "rev-parse", "--is-inside-work-tree"): (0, "true\n"),
        ("git", "rev-parse", "HEAD"): (0, SHA + "\n"),
        ("git", "symbolic-ref", "--quiet", "--short", "HEAD"): (1, ""),
        ("git", "rev-parse", "--git-common-dir"): (0, str(tmp_path / ".git") + "\n"),
        ("git", "rev-parse", "--git-dir"): (0, str(tmp_path / ".git/worktrees/x") + "\n"),
        ("git", "rev-parse", "--is-shallow-repository"): (0, "true\n"),
        ("git", "status", "--porcelain=v1", "-z", "--untracked-files=all"): (0, "?? new.txt\x00"),
        ("git", "remote"): (0, "upstream\n"),
        ("git", "rev-parse", "--verify", "upstream/main"): (1, ""),
    }
    status, unknown, warnings = collect_git_status(tmp_path, command_runner=_Runner(mapping))
    assert status.current_branch == f"(HEAD detached at {SHA[:7]})"
    assert status.is_worktree is True
    assert status.is_shallow is True
    assert status.selected_remote == "upstream"
    assert "git.selected_main_sha" in unknown
    assert warnings == []


def test_collect_git_status_unborn_and_no_remote(tmp_path):
    mapping = {
        ("git", "rev-parse", "--is-inside-work-tree"): (0, "true\n"),
        ("git", "rev-parse", "HEAD"): (1, ""),
        ("git", "rev-parse", "--git-common-dir"): (1, ""),
        ("git", "rev-parse", "--git-dir"): (1, ""),
        ("git", "rev-parse", "--is-shallow-repository"): (1, ""),
        ("git", "status", "--porcelain=v1", "-z", "--untracked-files=all"): (1, ""),
        ("git", "remote"): (0, ""),
    }
    status, unknown, _ = collect_git_status(tmp_path, command_runner=_Runner(mapping))
    assert status.current_branch == "unborn"
    assert status.head_sha is None
    assert "git.selected_remote" in unknown
    assert "git.ahead_count" in unknown


def test_project_and_contract_collectors_fail_closed_on_unreadable_utf8(tmp_path):
    (tmp_path / "PROJECT_STATE.md").write_bytes(b"\xff")
    (tmp_path / "PROJECT_CONTEXT.md").write_bytes(b"\xff")
    project, unknown, _ = collect_project_status(tmp_path)
    assert project.current_release is None
    assert "project.current_release" in unknown
    assert "project.policy_integrated" in unknown

    contract = tmp_path / "docs/project/SPEC_KITTY_DERIVED_CONTRACT_OWNERSHIP.md"
    contract.parent.mkdir(parents=True)
    contract.write_bytes(b"\xff")
    _, contract_unknown = collect_contract_status(tmp_path)
    assert len(contract_unknown) == 6


def test_validation_reconciliation_none_match_and_mismatch():
    empty, unknown, warnings = reconcile_validation_status(SHA, None)
    assert empty.evidence_revision is None and len(unknown) == 6 and warnings == []
    evidence = SimpleNamespace(
        revision=SHA,
        governance_check="PASS",
        preflight_sync="PASS",
        runtime_test_count=1,
        runtime_coverage="100%",
    )
    matched, _, warnings = reconcile_validation_status(SHA, evidence)
    assert matched.revision_match is True and warnings == []
    mismatch, _, warnings = reconcile_validation_status("b" * 40, evidence)
    assert mismatch.revision_match is False and warnings


def test_projection_serialization_render_and_cli_error_paths(tmp_path, monkeypatch, capsys):
    projection = build_status_projection(
        tmp_path,
        command_runner=_Runner({("git", "rev-parse", "--is-inside-work-tree"): (1, "false")}),
    )
    assert serialize_status_projection(projection)["git"]["is_git_repo"] is False
    assert '"projection_version": "1.0"' in serialize_status_projection_to_str(projection)
    assert "Unknown Fields" in render_status_projection(projection)

    assert status_main(["--repo", str(tmp_path / "missing")]) == 1
    capsys.readouterr()
    monkeypatch.setattr(
        "orchestra_runtime.status.build_status_projection",
        lambda path: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert status_main(["--repo", str(tmp_path)]) == 1
    assert "Error building" in capsys.readouterr().err
