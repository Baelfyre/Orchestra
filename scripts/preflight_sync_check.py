import os
import subprocess
import sys


def run_git(repo_root, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def read_stdout(result):
    return result.stdout.strip()


def classify_sync_state(ahead_count, behind_count):
    if ahead_count == 0 and behind_count == 0:
        return "aligned"
    if ahead_count > 0 and behind_count == 0:
        return "ahead-only"
    if ahead_count == 0 and behind_count > 0:
        return "behind"
    return "diverged"


def print_report(branch, head, origin_main, worktree, sync_state, decision, action, dirty_files=None):
    print("PREFLIGHT_SYNC_CHECK")
    print("")
    print(f"Current branch: {branch}")
    print(f"Local HEAD: {head}")
    print(f"origin/main: {origin_main}")
    print(f"Worktree: {worktree}")
    print(f"Sync state: {sync_state}")
    print(f"Decision: {decision}")
    print(f"Recommended action: {action}")
    if dirty_files:
        print("Dirty files:")
        for path in dirty_files:
            print(f"- {path}")


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    branch_result = run_git(repo_root, "branch", "--show-current")
    head_result = run_git(repo_root, "rev-parse", "HEAD")
    status_result = run_git(repo_root, "status", "--short")

    branch = read_stdout(branch_result) if branch_result.returncode == 0 else "(unavailable)"
    head = read_stdout(head_result) if head_result.returncode == 0 else "(unavailable)"
    dirty_files = [line for line in status_result.stdout.splitlines() if line.strip()] if status_result.returncode == 0 else []
    worktree = "dirty" if dirty_files else "clean"

    fetch_result = run_git(repo_root, "fetch", "origin")
    if fetch_result.returncode != 0:
        print_report(
            branch,
            head,
            "(unavailable)",
            worktree,
            "unverifiable",
            "BLOCKED",
            "Remote sync state could not be verified. Resolve git remote access before starting edits.",
            dirty_files=dirty_files or None,
        )
        sys.exit(1)

    origin_result = run_git(repo_root, "rev-parse", "origin/main")
    if origin_result.returncode != 0:
        print_report(
            branch,
            head,
            "(unavailable)",
            worktree,
            "unverifiable",
            "BLOCKED",
            "origin/main is unavailable. Verify remote refs before starting edits.",
            dirty_files=dirty_files or None,
        )
        sys.exit(1)

    origin_main = read_stdout(origin_result)

    if not branch:
        print_report(
            "(detached HEAD)",
            head,
            origin_main,
            worktree,
            "unverifiable",
            "BLOCKED",
            "Check out a working branch before starting edits.",
            dirty_files=dirty_files or None,
        )
        sys.exit(1)

    compare_result = run_git(repo_root, "rev-list", "--left-right", "--count", "HEAD...origin/main")
    if compare_result.returncode != 0:
        print_report(
            branch,
            head,
            origin_main,
            worktree,
            "unverifiable",
            "BLOCKED",
            "Commit graph comparison failed. Verify repository history before starting edits.",
            dirty_files=dirty_files or None,
        )
        sys.exit(1)

    counts = read_stdout(compare_result).split()
    ahead_count = int(counts[0]) if len(counts) >= 1 else 0
    behind_count = int(counts[1]) if len(counts) >= 2 else 0
    sync_state = f"{classify_sync_state(ahead_count, behind_count)} (ahead {ahead_count}, behind {behind_count})"

    if dirty_files:
        print_report(
            branch,
            head,
            origin_main,
            worktree,
            sync_state,
            "BLOCKED",
            "Do not begin edits or pull automatically. Review dirty files and decide whether to commit, stash, or discard them first.",
            dirty_files=dirty_files,
        )
        sys.exit(1)

    if ahead_count == 0 and behind_count == 0:
        print_report(
            branch,
            head,
            origin_main,
            worktree,
            sync_state,
            "PROCEED",
            "Local branch is aligned with origin/main. Safe to start a new local work session.",
        )
        sys.exit(0)

    if ahead_count > 0 and behind_count == 0:
        print_report(
            branch,
            head,
            origin_main,
            worktree,
            sync_state,
            "PROCEED_WITH_CAUTION",
            "Local branch has unpublished commits. Report the ahead-only state, then continue with caution.",
        )
        sys.exit(0)

    if ahead_count == 0 and behind_count > 0:
        print_report(
            branch,
            head,
            origin_main,
            worktree,
            sync_state,
            "BLOCKED",
            "Local branch is behind origin/main. Stop before editing and run `git pull --rebase origin main` manually.",
        )
        sys.exit(1)

    print_report(
        branch,
        head,
        origin_main,
        worktree,
        sync_state,
        "BLOCKED",
        "Local branch has diverged from origin/main. Stop before editing and reconcile the branch manually.",
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
