"""Regression tests for tracked-only stale-reference scanning."""

import builtins
import importlib.util
import io
import os
from contextlib import redirect_stdout
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCANNER_PATH = ROOT / "scripts" / "check_stale_references.py"


def _load_scanner():
    spec = importlib.util.spec_from_file_location(
        "orchestra_stale_reference_scanner",
        SCANNER_PATH,
    )
    if spec is None or spec.loader is None:
        raise AssertionError("Could not load stale-reference scanner.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ignored_and_untracked_secret_files_are_never_read_or_printed():
    root = os.path.join(os.getcwd(), "synthetic-stale-reference-repository")
    sentinel = "SYNTHETIC_SENTINEL_ONLY"
    credential_line = "api" + "_key=" + sentinel
    marker = "AO" + "OP"
    synthetic_files = {
        "README.md": "clean tracked fixture\n",
        "Keys.env": credential_line + "\n",
        ".env": credential_line + "\n",
        ".env.local": credential_line + "\n",
        "ignored.txt": credential_line + "\n",
        "untracked.txt": credential_line + "\n",
        "private.pem": credential_line + "\n",
        "match.txt": marker + " " + sentinel + "\n",
    }

    scanner = _load_scanner()
    scanner.helpers.get_project_root = lambda: root
    git_calls = []

    def synthetic_git_paths(project_root, *arguments):
        git_calls.append(arguments)
        if arguments == ("ls-files", "--cached", "-z"):
            return [
                "README.md",
                "Keys.env",
                ".env",
                ".env.local",
                "ignored.txt",
                "private.pem",
                "match.txt",
            ]
        if arguments == (
            "ls-files",
            "--cached",
            "--ignored",
            "--exclude-standard",
            "-z",
        ):
            return ["Keys.env", ".env", ".env.local", "ignored.txt"]
        raise AssertionError("Unexpected tracked-file enumeration command.")

    opened = []
    blocked = {
        "Keys.env",
        ".env",
        ".env.local",
        "ignored.txt",
        "untracked.txt",
        "private.pem",
    }

    def synthetic_open(file, *args, **kwargs):
        relative = os.path.relpath(os.fspath(file), root).replace("\\", "/")
        if relative in blocked:
            raise AssertionError("Excluded synthetic file was opened.")
        opened.append(relative)
        return io.StringIO(synthetic_files[relative])

    def synthetic_realpath(file):
        return os.path.normcase(os.path.abspath(os.fspath(file)))

    output = io.StringIO()
    with (
        mock.patch.object(scanner, "_git_paths", side_effect=synthetic_git_paths),
        mock.patch.object(scanner.os.path, "islink", return_value=False),
        mock.patch.object(scanner.os.path, "isfile", return_value=True),
        mock.patch.object(scanner.os.path, "realpath", side_effect=synthetic_realpath),
        mock.patch.object(builtins, "open", side_effect=synthetic_open),
        mock.patch.object(scanner.helpers, "get_project_root", return_value=root),
        redirect_stdout(output),
    ):
        try:
            scanner.main()
        except SystemExit as error:
            assert error.code == 1
        else:
            raise AssertionError("Scanner did not return its success status.")

    result = output.getvalue()
    assert git_calls == [
        ("ls-files", "--cached", "-z"),
        ("ls-files", "--cached", "--ignored", "--exclude-standard", "-z"),
    ]
    assert opened == ["README.md", "match.txt"]
    assert "match.txt:1" in result
    assert marker not in result
    assert sentinel not in result
    assert "Keys.env" not in result


def main():
    test_ignored_and_untracked_secret_files_are_never_read_or_printed()
    print("Stale-reference scanner regression tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
