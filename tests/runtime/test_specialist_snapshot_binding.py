from __future__ import annotations

# @codebase_provenance_JEO
# @codebase_rights_JEO

from dataclasses import replace
from pathlib import Path
import shutil
import subprocess
from typing import Callable

import pytest

from orchestra_runtime.application.ports.specialist_execution import (
    ReviewChangeStatus,
    SpecialistReviewChange,
)
from orchestra_runtime.domain.execution.operation_contracts import (
    DEFENSIVE_SECURITY_REVIEW,
    ReadOnlySpecialistExecutionRequest,
    SpecialistReviewResult,
    SpecialistReviewStatus,
)
import orchestra_runtime.specialist_execution as specialist_execution
from orchestra_runtime.specialist_execution import (
    SpecialistExecutionContractError,
    _create_host_read_only_snapshot,
    _repository_review_inventory,
    _repository_snapshot_identity,
    _review_snapshot_digest,
)


class FilesystemWorkspace:
    def __init__(
        self,
        root: Path,
        paths: tuple[str, ...],
        *,
        root_override: Path | None = None,
        text_override: dict[str, str] | None = None,
        after_read: Callable[[str], None] | None = None,
    ) -> None:
        self.repository_root = root_override or root
        self.paths = paths
        self.text_override = text_override or {}
        self.after_read = after_read

    def list_paths(self, relative_path: str = "") -> tuple[str, ...]:
        return self.paths

    def read_bytes(self, relative_path: str, *, max_bytes: int) -> bytes:
        if relative_path in self.text_override:
            content = self.text_override[relative_path].encode("utf-8")
        else:
            content = (Path(self.repository_root) / relative_path).read_bytes()
        if self.after_read is not None:
            self.after_read(relative_path)
        return content


class FilesystemWorkspaceProvider:
    def __init__(
        self,
        *,
        root_override: Path | None = None,
        omit: tuple[str, ...] = (),
        extra_paths: tuple[str, ...] = (),
        text_override: dict[str, str] | None = None,
        reverse_paths: bool = False,
        after_read: Callable[[str], None] | None = None,
    ) -> None:
        self.root_override = root_override
        self.omit = set(omit)
        self.extra_paths = extra_paths
        self.text_override = text_override or {}
        self.reverse_paths = reverse_paths
        self.after_read = after_read
        self.snapshot_digest = "e" * 64
        self.workspace: FilesystemWorkspace | None = None
        self.expected_paths: tuple[str, ...] = ()

    def for_review(self, repository_root: Path, expected_paths: tuple[str, ...]) -> FilesystemWorkspace:
        self.expected_paths = tuple(path for path in expected_paths if path not in self.omit)
        paths = self.expected_paths + self.extra_paths
        if self.reverse_paths:
            paths = paths[::-1]
        self.workspace = FilesystemWorkspace(
            repository_root,
            paths,
            root_override=self.root_override,
            text_override=self.text_override,
            after_read=self.after_read,
        )
        return self.workspace


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def create_candidate_repo(
    parent: Path,
    *,
    remote_url: str = "https://github.com/example/repo.git",
    baseline_text: str = "def authorize(user): return False\n",
    candidate_text: str = "def authorize(user): return user.is_active\n",
) -> Path:
    root = parent / "repo"
    root.mkdir(parents=True)
    source = root / "src" / "auth.py"
    source.parent.mkdir(parents=True)
    source.write_text(baseline_text, encoding="utf-8")
    git(root, "init")
    git(root, "config", "user.name", "Snapshot Test")
    git(root, "config", "user.email", "snapshot@example.invalid")
    git(root, "remote", "add", "origin", remote_url)
    git(root, "add", "src/auth.py")
    git(root, "commit", "-m", "baseline")
    base = git(root, "rev-parse", "HEAD")
    git(root, "update-ref", "refs/remotes/origin/main", base)
    git(root, "switch", "-c", "candidate")
    source.write_text(candidate_text, encoding="utf-8")
    return root


def snapshot(root: Path, provider: FilesystemWorkspaceProvider | None = None) -> tuple[object, str]:
    return _create_host_read_only_snapshot(provider or FilesystemWorkspaceProvider(), root)


def test_non_git_root_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "not-a-repository"
    root.mkdir()

    with pytest.raises(SpecialistExecutionContractError) as error:
        snapshot(root)

    assert error.value.reason_code == "SNAPSHOT_IDENTITY_UNAVAILABLE"


def test_missing_repository_identity_fails_closed(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    git(root, "remote", "remove", "origin")

    with pytest.raises(SpecialistExecutionContractError) as error:
        snapshot(root)

    assert error.value.reason_code == "SNAPSHOT_IDENTITY_UNAVAILABLE"


def test_local_remote_without_portable_repository_identity_fails_closed(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    git(root, "remote", "set-url", "origin", str(tmp_path / "remote" / "repo.git"))

    with pytest.raises(SpecialistExecutionContractError) as error:
        snapshot(root)

    assert error.value.reason_code == "SNAPSHOT_IDENTITY_UNAVAILABLE"


@pytest.mark.parametrize("missing_field", ("base_sha", "head_sha", "tree_sha"))
def test_missing_required_git_identity_fails_closed(tmp_path: Path, monkeypatch, missing_field: str) -> None:
    root = create_candidate_repo(tmp_path)
    identity = _repository_snapshot_identity(root)
    identity[missing_field] = None
    monkeypatch.setattr(specialist_execution, "_repository_snapshot_identity", lambda _root: identity)

    with pytest.raises(SpecialistExecutionContractError) as error:
        snapshot(root)

    assert error.value.reason_code == "SNAPSHOT_IDENTITY_UNAVAILABLE"


def test_provider_root_must_match_identity_root(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    other = create_candidate_repo(tmp_path / "other", remote_url="https://github.com/example/other.git")

    with pytest.raises(SpecialistExecutionContractError, match="provider root") as error:
        snapshot(root, FilesystemWorkspaceProvider(root_override=other))

    assert error.value.reason_code == "SNAPSHOT_BINDING_FAILED"


def test_provider_cannot_omit_expected_candidate_inventory(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    (root / "src" / "extra.py").write_text("candidate change\n", encoding="utf-8")
    inventory = _repository_review_inventory(root, _repository_snapshot_identity(root)["base_sha"] or "")
    omitted = next(change.path for change in inventory if change.status is not ReviewChangeStatus.DELETED)

    with pytest.raises(SpecialistExecutionContractError, match="complete host review scope") as error:
        snapshot(root, FilesystemWorkspaceProvider(omit=(omitted,)))

    assert error.value.reason_code == "SNAPSHOT_BINDING_FAILED"


def test_provider_cannot_add_paths_outside_host_candidate_inventory(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)

    with pytest.raises(SpecialistExecutionContractError, match="complete host review scope") as error:
        snapshot(root, FilesystemWorkspaceProvider(extra_paths=("src/provider-only.py",)))

    assert error.value.reason_code == "SNAPSHOT_BINDING_FAILED"


@pytest.mark.parametrize("changed_field", ("head_sha", "tree_sha"))
def test_expected_candidate_identity_change_during_snapshot_fails_closed(
    tmp_path: Path,
    monkeypatch,
    changed_field: str,
) -> None:
    root = create_candidate_repo(tmp_path)
    original = _repository_snapshot_identity(root)
    calls = 0

    def drifting_identity(_root: Path) -> dict[str, str | None]:
        nonlocal calls
        calls += 1
        current = dict(original)
        if calls > 1:
            current[changed_field] = "f" * 40
        return current

    monkeypatch.setattr(specialist_execution, "_repository_snapshot_identity", drifting_identity)

    with pytest.raises(SpecialistExecutionContractError, match="changed while") as error:
        snapshot(root)

    assert error.value.reason_code == "SNAPSHOT_DRIFT_DETECTED"


def test_same_repository_candidate_and_content_have_deterministic_digest(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    (root / "src" / "extra.py").write_text("extra candidate content\n", encoding="utf-8")

    first, first_digest = snapshot(root)
    second, second_digest = snapshot(root, FilesystemWorkspaceProvider(reverse_paths=True))

    assert first_digest == second_digest
    expected = tuple(change.path for change in _repository_review_inventory(
        root,
        _repository_snapshot_identity(root)["base_sha"] or "",
    ) if change.status is not ReviewChangeStatus.DELETED)
    assert first.list_paths() == expected
    assert second.list_paths() == expected
    assert {change.status for change in first.list_changes()} == {
        ReviewChangeStatus.ADDED,
        ReviewChangeStatus.MODIFIED,
    }


def test_dirty_modification_changes_digest_without_changing_head(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    head = git(root, "rev-parse", "HEAD")
    _, first_digest = snapshot(root)
    (root / "src" / "auth.py").write_text("def authorize(user): return user.is_admin\n", encoding="utf-8")
    _, second_digest = snapshot(root)

    assert git(root, "rev-parse", "HEAD") == head
    assert first_digest != second_digest


def test_candidate_addition_deletion_and_rename_change_snapshot_identity(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    _, baseline_digest = snapshot(root)

    added = root / "src" / "new.py"
    added.write_text("new content\n", encoding="utf-8")
    _, added_digest = snapshot(root)

    (root / "src" / "auth.py").unlink()
    _, deleted_digest = snapshot(root)

    (root / "src" / "renamed.py").write_text(added.read_text(encoding="utf-8"), encoding="utf-8")
    added.unlink()
    _, renamed_digest = snapshot(root)

    assert len({baseline_digest, added_digest, deleted_digest, renamed_digest}) == 4


def test_deleted_path_is_visible_with_frozen_base_text_and_provider_cannot_hide_it(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    expected_base = git(root, "show", "origin/main:src/auth.py")
    (root / "src" / "auth.py").unlink()
    provider = FilesystemWorkspaceProvider()
    provider.claimed_changes = (("src/auth.py", "MODIFIED"),)

    workspace, _digest = snapshot(root, provider)
    changes = workspace.list_changes()

    assert len(changes) == 1
    assert changes[0].status is ReviewChangeStatus.DELETED
    assert changes[0].path == "src/auth.py"
    assert changes[0].base_content == f"{expected_base}\n"
    assert changes[0].current_content is None
    assert "src/auth.py" not in workspace.list_paths()


def test_rename_manifest_exposes_before_and_after_content(tmp_path: Path) -> None:
    baseline = "".join(f"def check_{index}(): return {index}\n" for index in range(20))
    candidate = baseline.replace("check_10(): return 10", "check_10(): return -10")
    root = create_candidate_repo(tmp_path, baseline_text=baseline, candidate_text=candidate)
    git(root, "mv", "src/auth.py", "src/renamed.py")
    renamed = root / "src" / "renamed.py"
    renamed.write_text(renamed.read_text(encoding="utf-8").replace("return -10", "return 100"), encoding="utf-8")
    git(root, "add", "-A")

    workspace, _digest = snapshot(root)
    changes = workspace.list_changes()

    assert len(changes) == 1
    assert changes[0].status is ReviewChangeStatus.RENAMED
    assert changes[0].previous_path == "src/auth.py"
    assert changes[0].path == "src/renamed.py"
    assert changes[0].base_content == baseline
    assert changes[0].current_content == renamed.read_bytes().decode("utf-8")
    assert workspace.list_paths() == ("src/renamed.py",)


def test_removal_and_rename_evidence_are_bound_into_snapshot_digest(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    identity = _repository_snapshot_identity(root)
    assert all(identity.values())
    deleted = SpecialistReviewChange(
        "src/auth.py", ReviewChangeStatus.DELETED, base_content="old authorization logic\n"
    )
    changed_deletion = replace(deleted, base_content="different removed logic\n")
    renamed = SpecialistReviewChange(
        "src/new.py",
        ReviewChangeStatus.RENAMED,
        previous_path="src/old.py",
        base_content="before\n",
        current_content="after\n",
    )
    other_rename = replace(renamed, previous_path="src/other.py")

    assert _review_snapshot_digest((deleted,), identity) != _review_snapshot_digest((changed_deletion,), identity)
    assert _review_snapshot_digest((renamed,), identity) != _review_snapshot_digest((other_rename,), identity)


def test_mutating_an_already_captured_file_during_materialization_fails_closed(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    extra = root / "src" / "extra.py"
    extra.write_text("extra\n", encoding="utf-8")

    def mutate_after_extra(path: str) -> None:
        if path == "src/extra.py":
            (root / "src" / "auth.py").write_text("changed after capture\n", encoding="utf-8")

    with pytest.raises(SpecialistExecutionContractError) as error:
        snapshot(root, FilesystemWorkspaceProvider(after_read=mutate_after_extra))

    assert error.value.reason_code == "SNAPSHOT_DRIFT_DETECTED"


def test_mutating_a_different_captured_file_during_materialization_fails_closed(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    (root / "src" / "first.py").write_text("first\n", encoding="utf-8")
    (root / "src" / "last.py").write_text("last\n", encoding="utf-8")

    def mutate_first_after_last(path: str) -> None:
        if path == "src/last.py":
            (root / "src" / "first.py").write_text("changed after capture\n", encoding="utf-8")

    with pytest.raises(SpecialistExecutionContractError) as error:
        snapshot(root, FilesystemWorkspaceProvider(after_read=mutate_first_after_last))

    assert error.value.reason_code == "SNAPSHOT_DRIFT_DETECTED"


def test_deleting_a_present_file_during_materialization_fails_closed(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    (root / "src" / "extra.py").write_text("extra\n", encoding="utf-8")

    def delete_auth_after_extra(path: str) -> None:
        if path == "src/extra.py":
            (root / "src" / "auth.py").unlink()

    with pytest.raises(SpecialistExecutionContractError) as error:
        snapshot(root, FilesystemWorkspaceProvider(after_read=delete_auth_after_extra))

    assert error.value.reason_code == "SNAPSHOT_DRIFT_DETECTED"


def test_recreating_a_deleted_file_during_materialization_fails_closed(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    (root / "src" / "auth.py").unlink()
    (root / "src" / "extra.py").write_text("extra\n", encoding="utf-8")

    def recreate_auth_after_extra(path: str) -> None:
        if path == "src/extra.py":
            (root / "src" / "auth.py").write_text("recreated\n", encoding="utf-8")

    with pytest.raises(SpecialistExecutionContractError) as error:
        snapshot(root, FilesystemWorkspaceProvider(after_read=recreate_auth_after_extra))

    assert error.value.reason_code == "SNAPSHOT_DRIFT_DETECTED"


@pytest.mark.parametrize("drift", ("recreate_source", "delete_target"))
def test_rename_source_or_target_drift_fails_closed(tmp_path: Path, drift: str) -> None:
    root = create_candidate_repo(tmp_path)
    git(root, "mv", "src/auth.py", "src/renamed.py")
    git(root, "add", "-A")

    def mutate_rename_after_read(path: str) -> None:
        if path != "src/renamed.py":
            return
        if drift == "recreate_source":
            (root / "src" / "auth.py").write_text("recreated source\n", encoding="utf-8")
        else:
            (root / "src" / "renamed.py").unlink()

    with pytest.raises(SpecialistExecutionContractError) as error:
        snapshot(root, FilesystemWorkspaceProvider(after_read=mutate_rename_after_read))

    assert error.value.reason_code == "SNAPSHOT_DRIFT_DETECTED"


def test_different_repository_identity_cannot_reuse_same_content_snapshot(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    second_root = tmp_path / "same-candidate-other-location"
    shutil.copytree(root, second_root)
    _, same_repository_digest = snapshot(second_root)
    _, first_digest = snapshot(root)
    assert same_repository_digest == first_digest

    git(second_root, "remote", "set-url", "origin", "https://github.com/other/repo.git")

    _, second_digest = snapshot(second_root)

    assert _repository_snapshot_identity(root)["head_sha"] == _repository_snapshot_identity(second_root)["head_sha"]
    assert first_digest != second_digest


def test_scope_identity_changes_even_when_overlapping_content_matches(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    identity = _repository_snapshot_identity(root)
    assert all(identity.values())
    content = (
        SpecialistReviewChange(
            "src/auth.py",
            ReviewChangeStatus.MODIFIED,
            base_content="def authorize(user): return False\n",
            current_content="def authorize(user): return user.is_active\n",
        ),
    )
    narrow_scope = content
    broad_scope = content + (
        SpecialistReviewChange(
            "src/deleted.py", ReviewChangeStatus.DELETED, base_content="removed\n"
        ),
    )

    assert _review_snapshot_digest(narrow_scope, identity) != _review_snapshot_digest(broad_scope, identity)


def test_facade_is_an_immutable_copy_with_only_read_capabilities(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    facade, _digest = snapshot(root)
    snapshot_paths = facade.list_paths()
    first_path = snapshot_paths[0]
    original = facade.read_text(first_path, max_bytes=1024 * 1024)
    original_changes = facade.list_changes()
    (root / first_path).write_text("changed after snapshot\n", encoding="utf-8")

    assert facade.read_text(first_path, max_bytes=1024 * 1024) == original
    assert facade.list_changes() == original_changes
    assert not hasattr(facade, "__dict__")
    for capability in ("source", "workspace", "write_text", "delete", "rename", "run_command", "authorize"):
        assert not hasattr(facade, capability)
    with pytest.raises(SpecialistExecutionContractError, match="outside the immutable review snapshot"):
        facade.read_text("missing.py", max_bytes=1024)


def test_provider_content_and_provider_digest_are_not_authoritative(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    provider = FilesystemWorkspaceProvider(text_override={"src/auth.py": "forged provider text\n"})

    with pytest.raises(SpecialistExecutionContractError, match="does not match the verified repository") as error:
        snapshot(root, provider)

    assert error.value.reason_code == "SNAPSHOT_BINDING_FAILED"
    assert provider.snapshot_digest == "e" * 64


def test_review_result_from_one_snapshot_cannot_match_another(tmp_path: Path) -> None:
    root = create_candidate_repo(tmp_path)
    _workspace_a, digest_a = snapshot(root)
    (root / "src" / "auth.py").write_text("def authorize(user): return user.is_admin\n", encoding="utf-8")
    _workspace_b, digest_b = snapshot(root)
    request_a = ReadOnlySpecialistExecutionRequest(
        "review-a",
        "a" * 64,
        digest_a,
        "run-a",
        "codex",
        "security-check",
        "cipher",
        DEFENSIVE_SECURITY_REVIEW.operation_id,
        "review candidate A",
    )
    request_b = ReadOnlySpecialistExecutionRequest(
        request_a.request_id,
        request_a.request_digest,
        digest_b,
        request_a.run_id,
        request_a.adapter_name,
        request_a.command_name,
        request_a.specialist,
        request_a.operation_id,
        request_a.task_input,
    )
    review_a = SpecialistReviewResult.create(
        request_a,
        SpecialistReviewStatus.FINDINGS,
        "A finding was reported.",
        ("evidence:src/auth.py",),
    )

    review_a.assert_matches(request_a)
    with pytest.raises(ValueError, match="does not match"):
        review_a.assert_matches(request_b)
