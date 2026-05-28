#!/usr/bin/env python3
"""Inject project context at session start.

SessionStart hook stdout is added directly to Claude's context, so we
print a compact, useful snapshot: branch, recent commits, uncommitted
changes, and the first few TODO/FIXME markers in the repo.

Keep output short. Anything we print here is paid for on every session.
"""
import os
import subprocess
import sys


MAX_RECENT_COMMITS = 5
MAX_TODOS = 8
MAX_DIRTY_FILES = 15


def run(cmd: list[str], cwd: str | None = None) -> str:
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
            text=True,
            check=False,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def main() -> int:
    if os.environ.get("DEVKIT_DISABLE_SESSION_CONTEXT") == "1":
        return 0

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if not os.path.isdir(os.path.join(project_dir, ".git")):
        # Not a git repo — nothing useful to inject.
        return 0

    lines: list[str] = ["## Project snapshot (dev-kit SessionStart)"]

    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=project_dir)
    if branch:
        lines.append(f"- Branch: `{branch}`")

    upstream = run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd=project_dir,
    )
    if upstream:
        ahead_behind = run(
            ["git", "rev-list", "--left-right", "--count", f"{upstream}...HEAD"],
            cwd=project_dir,
        )
        if ahead_behind:
            try:
                behind, ahead = ahead_behind.split()
                if int(ahead) or int(behind):
                    lines.append(f"- Tracking `{upstream}`: {ahead} ahead, {behind} behind")
            except ValueError:
                pass

    dirty = run(["git", "status", "--porcelain"], cwd=project_dir)
    if dirty:
        files = dirty.splitlines()[:MAX_DIRTY_FILES]
        lines.append(f"- Uncommitted changes ({len(dirty.splitlines())} file(s)):")
        for f in files:
            lines.append(f"  - `{f.strip()}`")
        if len(dirty.splitlines()) > MAX_DIRTY_FILES:
            lines.append(f"  - ...and {len(dirty.splitlines()) - MAX_DIRTY_FILES} more")

    recent = run(
        ["git", "log", "-n", str(MAX_RECENT_COMMITS), "--pretty=format:%h %s"],
        cwd=project_dir,
    )
    if recent:
        lines.append("- Recent commits:")
        for c in recent.splitlines():
            lines.append(f"  - {c}")

    # TODO/FIXME survey, but only via git so we don't traverse node_modules.
    todos = run(
        [
            "git",
            "grep",
            "-n",
            "-E",
            "TODO|FIXME|XXX",
            "--",
            ":(exclude)*.lock",
            ":(exclude)*.lock.json",
            ":(exclude)package-lock.json",
            ":(exclude)yarn.lock",
            ":(exclude)pnpm-lock.yaml",
        ],
        cwd=project_dir,
    )
    if todos:
        todo_lines = todos.splitlines()[:MAX_TODOS]
        lines.append(f"- Open TODO/FIXME markers ({len(todos.splitlines())} total, showing {len(todo_lines)}):")
        for t in todo_lines:
            # Trim very long lines to keep output compact.
            if len(t) > 160:
                t = t[:157] + "..."
            lines.append(f"  - {t}")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
