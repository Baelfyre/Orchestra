from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parent.parent
LATEST_RELEASE_URL = "https://api.github.com/repos/Baelfyre/Orchestra/releases/latest"
DEFAULT_UPDATE_CONFIG = {
    "update_check_enabled": True,
    "update_check_channel": "stable",
    "update_check_frequency": "manual",
}
VALID_FREQUENCIES = {"manual", "daily", "startup"}
VALID_CHANNELS = {"stable"}


@dataclass(frozen=True)
class VersionSurface:
    surface: str
    path: Path
    version: str
    update_config: dict[str, object]


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    url: str


@dataclass(frozen=True)
class UpdateStatus:
    current_version: str
    latest_version: str | None
    release_url: str | None
    update_available: bool
    disabled: bool
    message: str
    instruction: str | None = None


class UpdateCheckError(ValueError):
    pass


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_version(value: str) -> tuple[int, int, int]:
    normalized = value.strip()
    if normalized.startswith("v"):
        normalized = normalized[1:]
    parts = normalized.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise UpdateCheckError(f"Invalid version: {value}")
    return tuple(int(part) for part in parts)


def read_update_config(payload: dict, container_key: str | None = None) -> dict[str, object]:
    container = payload if container_key is None else payload.get(container_key, {})
    if container_key is not None and not isinstance(container, dict):
        container = {}
    config = dict(DEFAULT_UPDATE_CONFIG)
    config.update(container.get("update_check", {}))
    return config


def validate_update_config(config: dict[str, object]) -> None:
    frequency = str(config.get("update_check_frequency", "")).lower()
    channel = str(config.get("update_check_channel", "")).lower()
    enabled = config.get("update_check_enabled")

    if not isinstance(enabled, bool):
        raise UpdateCheckError("update_check_enabled must be true or false.")
    if frequency not in VALID_FREQUENCIES:
        raise UpdateCheckError(f"Invalid update check frequency: {frequency}")
    if channel not in VALID_CHANNELS:
        raise UpdateCheckError(f"Invalid update check channel: {channel}")


def load_version_surfaces(repo_root: Path) -> tuple[VersionSurface, ...]:
    surfaces: list[VersionSurface] = []

    plugin_payload = read_json(repo_root / "plugin.json")
    surfaces.append(
        VersionSurface(
            surface="plugin",
            path=repo_root / "plugin.json",
            version=str(plugin_payload.get("version", "")),
            update_config=read_update_config(plugin_payload),
        )
    )

    claude_payload = read_json(repo_root / ".claude-plugin" / "plugin.json")
    surfaces.append(
        VersionSurface(
            surface="claude-code",
            path=repo_root / ".claude-plugin" / "plugin.json",
            version=str(claude_payload.get("version", "")),
            update_config=read_update_config(claude_payload),
        )
    )

    codex_payload = read_json(repo_root / ".codex-plugin" / "plugin.json")
    surfaces.append(
        VersionSurface(
            surface="codex",
            path=repo_root / ".codex-plugin" / "plugin.json",
            version=str(codex_payload.get("version", "")),
            update_config=read_update_config(codex_payload),
        )
    )

    for package_path in sorted((repo_root / "adapters").glob("*/package.json")):
        payload = read_json(package_path)
        adapter_name = package_path.parent.name
        surfaces.append(
            VersionSurface(
                surface=adapter_name,
                path=package_path,
                version=str(payload.get("version", "")),
                update_config=read_update_config(payload, "orchestra"),
            )
        )

    return tuple(surfaces)


def check_surface_consistency(surfaces: tuple[VersionSurface, ...]) -> str:
    versions = {surface.surface: surface.version for surface in surfaces}
    for version in versions.values():
        parse_version(version)

    unique_versions = sorted(set(versions.values()))
    if len(unique_versions) != 1:
        raise UpdateCheckError(
            "Version mismatch across local manifests: "
            + ", ".join(f"{name}={version}" for name, version in sorted(versions.items()))
        )
    return unique_versions[0]


def is_update_check_enabled(surfaces: tuple[VersionSurface, ...]) -> bool:
    return all(bool(surface.update_config.get("update_check_enabled", True)) for surface in surfaces)


def fetch_latest_release(fetcher: Callable[[str], dict] | None = None) -> ReleaseInfo:
    payload_fetcher = fetcher or _fetch_latest_release_payload
    payload = payload_fetcher(LATEST_RELEASE_URL)
    tag_name = str(payload.get("tag_name", ""))
    html_url = str(payload.get("html_url", ""))
    if not tag_name or not html_url:
        raise UpdateCheckError("Latest release payload is missing tag_name or html_url.")
    parse_version(tag_name)
    return ReleaseInfo(version=tag_name.removeprefix("v"), url=html_url)


def _fetch_latest_release_payload(url: str) -> dict:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "orchestra-update-checker",
        },
    )
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise UpdateCheckError(f"GitHub release check failed: HTTP {exc.code}") from exc
    except URLError as exc:
        raise UpdateCheckError(f"GitHub release check failed: {exc.reason}") from exc


def build_update_status(
    repo_root: Path,
    fetcher: Callable[[str], dict] | None = None,
) -> UpdateStatus:
    surfaces = load_version_surfaces(repo_root)
    for surface in surfaces:
        validate_update_config(surface.update_config)
    current_version = check_surface_consistency(surfaces)

    if not is_update_check_enabled(surfaces):
        return UpdateStatus(
            current_version=current_version,
            latest_version=None,
            release_url=None,
            update_available=False,
            disabled=True,
            message="Orchestra update check is disabled.",
        )

    latest = fetch_latest_release(fetcher)
    update_available = parse_version(latest.version) > parse_version(current_version)
    if update_available:
        return UpdateStatus(
            current_version=current_version,
            latest_version=latest.version,
            release_url=latest.url,
            update_available=True,
            disabled=False,
            message=(
                "Orchestra update available.\n\n"
                f"Current version: {current_version}\n"
                f"Latest version: {latest.version}\n\n"
                f"Release:\n{latest.url}\n\n"
                "Run your host-specific refresh or reinstall command to update."
            ),
            instruction="Run your host-specific refresh or reinstall command to update.",
        )

    return UpdateStatus(
        current_version=current_version,
        latest_version=latest.version,
        release_url=latest.url,
        update_available=False,
        disabled=False,
        message=(
            "Orchestra is up to date.\n\n"
            f"Current version: {current_version}\n"
            f"Latest version: {latest.version}\n\n"
            f"Release:\n{latest.url}"
        ),
    )


def main() -> int:
    try:
        status = build_update_status(REPO_ROOT)
    except UpdateCheckError as exc:
        print(f"ERROR: {exc}")
        return 1

    print(status.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
