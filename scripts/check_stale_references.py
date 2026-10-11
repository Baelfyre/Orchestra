import os
import re
import subprocess
import sys
from pathlib import PurePosixPath

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import helpers


SENSITIVE_NAMES = {
    ".env",
    "keys.env",
    ".netrc",
    "netrc",
    "credentials",
    "credential",
    "secrets",
    "secret",
    "tokens",
    "token",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_xmss",
}
SENSITIVE_PREFIXES = (
    ".env.",
    "credentials.",
    "credential.",
    "secrets.",
    "secret.",
    "tokens.",
    "token.",
)
SENSITIVE_SUFFIXES = (
    ".credential",
    ".credentials",
    ".secret",
    ".secrets",
    ".token",
    ".tokens",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".ppk",
    ".jks",
    ".keystore",
)
EXCLUDED_DIRECTORIES = {".git", "brain", ".agents", "adapters"}


def _git_paths(root, *arguments):
    try:
        result = subprocess.run(
            ["git", "-C", root, *arguments],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise RuntimeError("Could not enumerate tracked repository files.") from error

    if result.returncode != 0:
        raise RuntimeError("Could not enumerate tracked repository files.")

    return [os.fsdecode(path) for path in result.stdout.split(b"\0") if path]


def _is_sensitive_path(relative_path):
    name = PurePosixPath(relative_path.replace("\\", "/")).name.casefold()
    return (
        name in SENSITIVE_NAMES
        or name.startswith(SENSITIVE_PREFIXES)
        or name.endswith(SENSITIVE_SUFFIXES)
        or name in {"service-account.json", "service_account.json"}
    )


def _tracked_scan_paths(root):
    tracked = _git_paths(root, "ls-files", "--cached", "-z")
    ignored = set(
        _git_paths(
            root,
            "ls-files",
            "--cached",
            "--ignored",
            "--exclude-standard",
            "-z",
        )
    )
    root_real = os.path.realpath(root)

    for relative_path in tracked:
        normalized = relative_path.replace("\\", "/")
        parts = normalized.split("/")
        if relative_path in ignored or _is_sensitive_path(normalized):
            continue
        if any(part in EXCLUDED_DIRECTORIES for part in parts):
            continue
        if normalized.startswith("skills/clockwork/") or normalized.startswith(
            "docs/governance/postmortems/"
        ):
            continue
        if normalized == "scripts/check_stale_references.py":
            continue
        if PurePosixPath(normalized).name == "check-stale-references.ps1":
            continue

        full_path = os.path.join(root, *parts)
        if os.path.islink(full_path) or not os.path.isfile(full_path):
            continue

        real_path = os.path.realpath(full_path)
        try:
            common_path = os.path.commonpath((root_real, real_path))
        except ValueError:
            continue
        if os.path.normcase(common_path) != os.path.normcase(root_real):
            continue

        yield normalized, full_path


def main():
    root = helpers.get_project_root()
    patterns = [
        re.compile(r"ux-diagram-architect", re.IGNORECASE),
        re.compile(r"meister-virtuoso", re.IGNORECASE),
        re.compile(r"Meister Virtuoso", re.IGNORECASE),
        re.compile(r"AOOP", re.IGNORECASE),
        re.compile(r"MotorPH", re.IGNORECASE),
        re.compile(r"HiveMind", re.IGNORECASE),
        re.compile(r"Art Appreciation", re.IGNORECASE),
        re.compile(r"C:[\\/]Users[\\/]", re.IGNORECASE),
        re.compile(r"/home/", re.IGNORECASE),
        re.compile(r"production\s+secrets?", re.IGNORECASE),
        re.compile(r"api[_ -]?keys?\s*[:=]\s*\S+", re.IGNORECASE),
    ]

    findings = []
    unreadable = []
    try:
        scan_paths = _tracked_scan_paths(root)
        for relative_path, full_path in scan_paths:
            try:
                with open(full_path, "r", encoding="utf-8") as source:
                    for line_number, line in enumerate(source, 1):
                        if any(pattern.search(line) for pattern in patterns):
                            findings.append(f"{relative_path}:{line_number}")
            except UnicodeDecodeError:
                continue
            except OSError:
                unreadable.append(relative_path)
    except RuntimeError:
        helpers.write_color_host(
            "ERROR",
            "Could not enumerate tracked files; stale-reference scan aborted.",
        )
        sys.exit(2)

    if unreadable:
        helpers.write_color_host(
            "ERROR",
            "Could not scan tracked files: " + ", ".join(unreadable),
        )
        sys.exit(2)

    if findings:
        helpers.write_color_host("WARNING", "Stale or disallowed references found:")
        for finding in findings:
            helpers.write_color_host("ERROR", finding)
        sys.exit(1)

    helpers.write_color_host("SUCCESS", "No stale or disallowed references found.")
    sys.exit(0)


if __name__ == "__main__":
    main()
