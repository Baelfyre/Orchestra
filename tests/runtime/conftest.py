from pathlib import Path
import subprocess

import pytest


@pytest.fixture(scope="module")
def read_only_review_candidate_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Use a real nonempty Git candidate, independent of the CI checkout ref.

    The detached worktree shares the canonical Git objects but not its files;
    only the temporary copy is modified. This verifies snapshot binding on
    PR checkouts and on main, where HEAD may equal origin/main.
    """
    repository_root = Path(__file__).resolve().parents[2]
    candidate_root = tmp_path_factory.mktemp("read-only-review") / "candidate"
    subprocess.run(
        ["git", "-C", str(repository_root), "worktree", "add", "--detach",
         str(candidate_root), "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    try:
        review_path = candidate_root / "docs/setup/VALIDATION.md"
        review_path.write_bytes(
            review_path.read_bytes()
            + b"\n<!-- read-only review test candidate: changed content -->\n"
        )
        changed = subprocess.run(
            ["git", "-C", str(candidate_root), "diff", "--name-only", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert changed.stdout.splitlines() == ["docs/setup/VALIDATION.md"]
        yield candidate_root
    finally:
        subprocess.run(
            ["git", "-C", str(repository_root), "worktree", "remove", "--force",
             str(candidate_root)],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )


def pytest_pycollect_makeitem(collector, name, obj):
    """Do not collect imported runtime helpers that merely happen to start with test_."""
    if (
        name == "test_evidence_main"
        and getattr(obj, "__module__", None) == "orchestra_runtime.test_evidence"
    ):
        return []
    return None
