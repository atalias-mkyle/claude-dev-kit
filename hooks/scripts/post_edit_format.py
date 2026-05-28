#!/usr/bin/env python3
"""Auto-format files after Claude writes or edits them.

Reads PostToolUse JSON from stdin, looks up the appropriate formatter
for the file's extension, and runs it if available. Silently no-ops if
the formatter isn't installed — never breaks the workflow.

Stdout is suppressed (PostToolUse stdout doesn't reach Claude); we use
exit 0 always so a missing formatter doesn't look like a failure.
"""
import json
import os
import shutil
import subprocess
import sys


# extension -> list of (command, args-template) candidates to try in order.
# {file} is substituted with the absolute file path.
FORMATTERS = {
    ".py": [
        ("ruff", ["format", "{file}"]),
        ("black", ["{file}"]),
    ],
    ".js": [("prettier", ["--write", "{file}"])],
    ".jsx": [("prettier", ["--write", "{file}"])],
    ".ts": [("prettier", ["--write", "{file}"])],
    ".tsx": [("prettier", ["--write", "{file}"])],
    ".mjs": [("prettier", ["--write", "{file}"])],
    ".cjs": [("prettier", ["--write", "{file}"])],
    ".json": [("prettier", ["--write", "{file}"])],
    ".jsonc": [("prettier", ["--write", "{file}"])],
    ".yaml": [("prettier", ["--write", "{file}"])],
    ".yml": [("prettier", ["--write", "{file}"])],
    ".md": [("prettier", ["--write", "{file}"])],
    ".css": [("prettier", ["--write", "{file}"])],
    ".scss": [("prettier", ["--write", "{file}"])],
    ".html": [("prettier", ["--write", "{file}"])],
    ".go": [("gofmt", ["-w", "{file}"])],
    ".rs": [("rustfmt", ["{file}"])],
    ".rb": [("rubocop", ["-A", "{file}"])],
    ".sh": [("shfmt", ["-w", "{file}"])],
    ".bash": [("shfmt", ["-w", "{file}"])],
    ".sql": [("sqlfluff", ["fix", "--disable-progress-bar", "{file}"])],
    ".tf": [("terraform", ["fmt", "{file}"])],
}


def main() -> int:
    if os.environ.get("DEVKIT_DISABLE_AUTOFORMAT") == "1":
        return 0
    if len(sys.argv) > 1 and sys.argv[1].lower() == "false":
        return 0

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path")
    if not file_path or not os.path.isfile(file_path):
        return 0

    ext = os.path.splitext(file_path)[1].lower()
    candidates = FORMATTERS.get(ext)
    if not candidates:
        return 0

    for cmd, args_template in candidates:
        if not shutil.which(cmd):
            continue
        args = [a.replace("{file}", file_path) for a in args_template]
        try:
            subprocess.run(
                [cmd, *args],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError):
            pass
        # Only run the first available formatter for this extension.
        break

    return 0


if __name__ == "__main__":
    sys.exit(main())
