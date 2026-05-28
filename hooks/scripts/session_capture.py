#!/usr/bin/env python3
"""Append a session summary to .claude/memory/decisions.md at session end.

Stop hook — reads stdin JSON (may be minimal), gathers git context, and
appends a timestamped entry to the decisions log. All errors are swallowed
so the hook never blocks Claude from stopping.
"""
import json
import os
import subprocess
import sys
from datetime import datetime


MAX_STATUS_LINES = 10
MEMORY_DIR = ".claude/memory"
DECISIONS_FILE = "decisions.md"
DECISIONS_HEADER = """\
# Project Decisions
<!-- Append session summaries and architectural decisions here. -->
<!-- session_capture.py adds entries automatically at session end. -->

"""


def run(cmd: list[str], cwd: str) -> str:
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
    if os.environ.get("DEVKIT_DISABLE_SESSION_CAPTURE") == "1":
        return 0

    # Consume stdin — Stop hook may send JSON; ignore parse errors.
    try:
        raw = sys.stdin.read()
        if raw.strip():
            json.loads(raw)
    except Exception:
        pass

    cwd = os.getcwd()

    branch = run(["git", "branch", "--show-current"], cwd=cwd)
    branch = branch or "unknown"

    status_raw = run(["git", "status", "--short"], cwd=cwd)
    if status_raw:
        status_lines = status_raw.splitlines()
        trimmed = status_lines[:MAX_STATUS_LINES]
        changed_files = ", ".join(line.strip().split()[-1] for line in trimmed if line.strip())
        if len(status_lines) > MAX_STATUS_LINES:
            changed_files += f", ...+{len(status_lines) - MAX_STATUS_LINES} more"
    else:
        changed_files = "none"

    latest_commit = run(["git", "log", "--oneline", "-1"], cwd=cwd)
    if not latest_commit:
        latest_commit = "uncommitted changes"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = (
        f"### [{timestamp}] branch: {branch}\n"
        f"- Files changed: {changed_files}\n"
        f"- Latest commit: {latest_commit}\n"
        f"- Notes: <!-- fill in key decisions made this session -->\n"
        "\n"
    )

    memory_dir = os.path.join(cwd, MEMORY_DIR)
    decisions_path = os.path.join(memory_dir, DECISIONS_FILE)

    try:
        os.makedirs(memory_dir, exist_ok=True)

        if not os.path.exists(decisions_path):
            with open(decisions_path, "w", encoding="utf-8") as fh:
                fh.write(DECISIONS_HEADER)

        with open(decisions_path, "a", encoding="utf-8") as fh:
            fh.write(entry)
    except Exception:
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
