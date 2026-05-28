#!/usr/bin/env python3
"""Block writes to sensitive paths before they execute.

Reads PreToolUse JSON from stdin. Exit code 2 blocks the tool call;
the stderr message is fed back to Claude so it can adjust and retry.
Exit code 0 allows the write through.

Applies to tools: Write, Edit, MultiEdit.

Toggle via DEVKIT_DISABLE_WRITE_GUARD=1 env var, or the plugin's
`enable_bash_guard` userConfig (pass "false" as argv[1]).
"""
import fnmatch
import json
import os
import sys


WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}


def _build_rules():
    def ends_with(suffix):
        return lambda p: p.endswith(suffix)

    def contains(fragment):
        return lambda p: fragment in p

    def starts_with(prefix):
        return lambda p: p.startswith(prefix)

    def filename_matches(pattern):
        return lambda p: fnmatch.fnmatch(os.path.basename(p), pattern)

    return [
        # .env and .env.<anything>  (e.g. .env.production, .env.local)
        ("dotenv file", lambda p: (
            os.path.basename(p) == ".env"
            or os.path.basename(p).startswith(".env.")
        )),
        # ~/.ssh/ directory
        ("SSH directory", contains("/.ssh/")),
        # /etc/ system files
        ("system /etc/ file", starts_with("/etc/")),
        # Git global config
        ("git config", ends_with("/.gitconfig")),
        # AWS credentials
        ("AWS credentials", lambda p: (
            p.endswith("/.aws/credentials") or p.endswith("/.aws/config")
        )),
        # Generic secret filenames
        ("credentials file", filename_matches("*credentials*")),
        ("secrets file", filename_matches("*secrets*")),
        ("private key file", filename_matches("*private_key*")),
        ("id_rsa key file", filename_matches("*id_rsa*")),
        ("id_ed25519 key file", filename_matches("*id_ed25519*")),
    ]


RULES = _build_rules()


def main() -> int:
    if os.environ.get("DEVKIT_DISABLE_WRITE_GUARD") == "1":
        return 0
    if len(sys.argv) > 1 and sys.argv[1].lower() == "false":
        return 0

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name not in WRITE_TOOLS:
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        return 0

    cwd = os.getcwd()
    resolved = os.path.normpath(os.path.abspath(os.path.join(cwd, file_path)))
    resolved_fwd = resolved.replace(os.sep, "/")
    cwd_norm = os.path.normpath(cwd)

    # Path-traversal check: block writes outside the project root.
    if not resolved.startswith(cwd_norm + os.sep) and resolved != cwd_norm:
        sys.stderr.write(
            f"[dev-kit write-guard] Blocked: path traversal outside project root\n"
            f"Resolved path : {resolved}\n"
            f"Project root  : {cwd_norm}\n"
            "To override for this session, set DEVKIT_DISABLE_WRITE_GUARD=1 in your shell.\n"
        )
        return 2

    for label, matcher in RULES:
        if matcher(resolved_fwd):
            sys.stderr.write(
                f"[dev-kit write-guard] Blocked: {label}\n"
                f"Resolved path : {resolved}\n"
                f"Rule          : {label}\n"
                "To override for this session, set DEVKIT_DISABLE_WRITE_GUARD=1 in your shell.\n"
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
