#!/usr/bin/env python3
"""Block destructive bash commands before they execute.

Reads PreToolUse JSON from stdin. Exit code 2 blocks the tool call;
the stderr message is fed back to Claude so it can adjust and retry.
Exit code 0 allows the command through.

Toggle via the plugin's `enable_bash_guard` userConfig.
"""
import json
import os
import re
import sys


# Patterns that should never run unattended. Each is matched
# case-insensitively against the *full* command string.
DANGEROUS_PATTERNS = [
    # Recursive force-delete in any form (rm -rf, rm -fr, rm -Rf, etc.)
    (r"\brm\s+(-[a-zA-Z]*[rRf][a-zA-Z]*\s+|--recursive\s+|--force\s+)", "recursive/force rm"),
    # Anything sudo + rm
    (r"\bsudo\s+rm\b", "sudo rm"),
    # Wide-open permissions
    (r"\bchmod\s+(-R\s+)?777\b", "chmod 777"),
    # Force-push in any form (bare -f or --force/--force-with-lease, any branch)
    (r"\bgit\s+push\b.*?\s(-f|--force(?:-with-lease)?)(?:\s|$)", "force-push"),
    # Reset --hard on protected branches
    (r"\bgit\s+reset\s+--hard\b.*\b(origin/main|origin/master|origin/release|origin/prod)\b", "hard reset of protected branch"),
    # Pipe-to-shell installs from the network
    (r"curl\s+[^|]*\|\s*(sudo\s+)?(bash|sh|zsh)\b", "curl | shell"),
    (r"wget\s+[^|]*\|\s*(sudo\s+)?(bash|sh|zsh)\b", "wget | shell"),
    # Disk-erasing commands
    (r"\bmkfs(\.[a-z0-9]+)?\b", "mkfs (filesystem wipe)"),
    (r"\bdd\s+if=.*\s+of=/dev/[sh]d", "dd to raw disk device"),
    # Fork bomb
    (r":\(\)\s*\{\s*:\|:&\s*\};:", "fork bomb"),
    # rm of obviously critical paths
    (r"\brm\s+(-[a-zA-Z]*\s+)*/(\s|$|\*)", "rm targeting filesystem root"),
    (r"\brm\s+(?:-[a-zA-Z]*\s+)*~/", "rm targeting entire home dir"),
]


def main() -> int:
    # argv[1] is the install-time userConfig value ("true"/"false").
    # The env var is a per-session override that always wins.
    if os.environ.get("DEVKIT_DISABLE_BASH_GUARD") == "1":
        return 0
    if len(sys.argv) > 1 and sys.argv[1].lower() == "false":
        return 0

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # If we can't parse the hook payload, fail open rather than
        # breaking every bash call.
        return 0

    command = (payload.get("tool_input") or {}).get("command", "")
    if not command:
        return 0

    for pattern, label in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            sys.stderr.write(
                f"[dev-kit guard] Blocked: {label}\n"
                f"Command: {command}\n"
                "If you really need to run this, ask the user to run it manually, "
                "or set DEVKIT_DISABLE_BASH_GUARD=1 in your shell for one session.\n"
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
