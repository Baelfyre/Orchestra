from pathlib import Path

import pytest

from scripts.check_for_updates import (
    DEFAULT_UPDATE_CONFIG,
    UpdateCheckError,
    build_update_status,
    parse_version,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")


def create_repo(tmp_path: Path, version: str = "1.0.0", enabled: bool = True) -> Path:
    repo_root = tmp_path / "repo"
    update_check = {
        **DEFAULT_UPDATE_CONFIG,
        "update_check_enabled": enabled,
    }
    write_json(
        repo_root / "plugin.json",
        {
            "name": "conductor",
            "display_name": "Orchestra",
            "version": version,
            "commands": [],
            "skills": [],
            "update_check": update_check,
        },
    )
    write_json(
        repo_root / ".claude-plugin" / "plugin.json",
        {
            "name": "orchestra",
            "description": "test",
            "version": version,
            "update_check": update_check,
        },
    )
    write_json(
        repo_root / ".codex-plugin" / "plugin.json",
        {
            "name": "conductor",
            "version": version,
            "update_check": update_check,
        },
    )
    write_json(
        repo_root / "adapters" / "vscode" / "package.json",
        {
            "name": "orchestra-vscode-scaffold",
            "version": version,
            "orchestra": {
                "runtime_adapter": "vscode",
                "host": "vscode",
                "update_check": update_check,
            },
        },
    )
    return repo_root


def test_current_version_is_latest(tmp_path: Path):
    repo_root = create_repo(tmp_path)

    status = build_update_status(
        repo_root,
        fetcher=lambda _: {"tag_name": "v1.0.0", "html_url": "https://example.test/v1.0.0"},
    )

    assert status.update_available is False
    assert status.current_version == "1.0.0"
    assert status.latest_version == "1.0.0"
    assert "up to date" in status.message.lower()


def test_newer_version_exists(tmp_path: Path):
    repo_root = create_repo(tmp_path)

    status = build_update_status(
        repo_root,
        fetcher=lambda _: {"tag_name": "v1.0.1", "html_url": "https://example.test/v1.0.1"},
    )

    assert status.update_available is True
    assert status.latest_version == "1.0.1"
    assert status.release_url == "https://example.test/v1.0.1"
    assert "Run your host-specific refresh or reinstall command to update." in status.message


def test_invalid_version_fails(tmp_path: Path):
    repo_root = create_repo(tmp_path, version="one.two.three")

    with pytest.raises(UpdateCheckError, match="Invalid version"):
        build_update_status(
            repo_root,
            fetcher=lambda _: {"tag_name": "v1.0.1", "html_url": "https://example.test/v1.0.1"},
        )


def test_github_unavailable_fails(tmp_path: Path):
    repo_root = create_repo(tmp_path)

    with pytest.raises(UpdateCheckError, match="unavailable"):
        build_update_status(repo_root, fetcher=lambda _: (_ for _ in ()).throw(UpdateCheckError("GitHub unavailable")))


def test_update_check_disabled(tmp_path: Path):
    repo_root = create_repo(tmp_path, enabled=False)

    status = build_update_status(
        repo_root,
        fetcher=lambda _: {"tag_name": "v1.0.1", "html_url": "https://example.test/v1.0.1"},
    )

    assert status.disabled is True
    assert status.update_available is False
    assert status.latest_version is None


def test_parse_version_accepts_v_prefix():
    assert parse_version("v1.0.1") == (1, 0, 1)
