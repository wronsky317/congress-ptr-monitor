#!/usr/bin/env python3
"""Commit and push a generated pending long-term update.

The script intentionally stages only the pending update path passed on the
command line. Runtime outputs such as reports, data, PDFs, and state remain
ignored and untouched.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("/Users/wronsky/Documents/codes/congress-ptr-monitor")


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_key_values(stdout: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def resolve_pending_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def relative_to_project(path: Path) -> Path:
    try:
        return path.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise SystemExit(f"Pending update is outside project: {path}") from exc


def branch_name() -> str:
    completed = run(["git", "branch", "--show-current"])
    if completed.returncode != 0:
        raise SystemExit((completed.stderr or completed.stdout).strip())
    branch = completed.stdout.strip()
    if not branch:
        raise SystemExit("Cannot push from a detached HEAD.")
    return branch


def commit_pending(path: Path) -> str:
    relative = relative_to_project(path)
    if not path.exists():
        raise SystemExit(f"Pending update not found: {path}")

    add = run(["git", "add", "--", str(relative)])
    if add.returncode != 0:
        raise SystemExit((add.stderr or add.stdout).strip())

    staged = run(["git", "diff", "--cached", "--quiet", "--", str(relative)])
    if staged.returncode == 0:
        return "commit=skipped no staged change"
    if staged.returncode not in (0, 1):
        raise SystemExit((staged.stderr or staged.stdout).strip())

    commit = run(["git", "commit", "-m", f"Add PTR pending long-term update {path.stem}", "--", str(relative)])
    if commit.returncode != 0:
        raise SystemExit((commit.stderr or commit.stdout).strip())
    first_line = commit.stdout.splitlines()[0] if commit.stdout.splitlines() else "committed"
    return f"commit={first_line}"


def push_current_branch() -> str:
    branch = branch_name()
    push = run(["git", "push", "origin", branch])
    if push.returncode != 0:
        raise SystemExit((push.stderr or push.stdout).strip())
    first_line = push.stderr.splitlines()[0] if push.stderr.splitlines() else f"pushed origin/{branch}"
    return f"push={first_line}"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Commit and push one pending long-term update file.")
    parser.add_argument("--pending-update", help="Path to long_term_views/pending_updates/YYYY-MM-DD.md.")
    parser.add_argument(
        "--from-generator-output",
        help="A line-oriented file/stdout capture containing pending_update=<path>.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    path_text = args.pending_update
    if args.from_generator_output:
        output_path = Path(args.from_generator_output).expanduser()
        values = parse_key_values(output_path.read_text(encoding="utf-8", errors="replace"))
        path_text = values.get("pending_update", path_text)
    if not path_text:
        raise SystemExit("Provide --pending-update or --from-generator-output with pending_update=<path>.")

    pending_path = resolve_pending_path(path_text)
    commit_status = commit_pending(pending_path)
    print(commit_status)
    if not commit_status.startswith("commit=skipped"):
        print(push_current_branch())
    else:
        print("push=skipped no new commit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
