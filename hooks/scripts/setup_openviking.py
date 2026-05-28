#!/usr/bin/env python3
"""Set up OpenViking MCP server from plugin userConfig.

Writes ~/.openviking/ovcli.conf with the correct schema and registers
the openviking HTTP MCP server via `claude mcp add` if not already present.

Called at SessionStart with base_url as argv[1] and api_key via
OPENVIKING_API_KEY env var.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

CONF_PATH = Path.home() / ".openviking" / "ovcli.conf"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def main() -> int:
    base_url = (sys.argv[1] if len(sys.argv) > 1 else "") or os.environ.get("OPENVIKING_BASE_URL", "")
    api_key = os.environ.get("OPENVIKING_API_KEY", "")

    if not base_url or base_url in ("undefined", "null", ""):
        return 0
    if not api_key or api_key in ("undefined", "null", ""):
        return 0

    base_url = base_url.rstrip("/")

    # Write ovcli.conf with the correct upstream schema.
    conf = {"url": base_url, "api_key": api_key}
    existing = {}
    if CONF_PATH.exists():
        try:
            existing = json.loads(CONF_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    if existing.get("url") != conf["url"] or existing.get("api_key") != conf["api_key"]:
        CONF_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONF_PATH.write_text(json.dumps(conf, indent=2), encoding="utf-8")

    # Register the HTTP MCP server if not already in settings.
    already_registered = False
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            already_registered = "openviking" in settings.get("mcpServers", {})
        except (json.JSONDecodeError, OSError):
            pass

    if not already_registered:
        subprocess.run(
            [
                "claude", "mcp", "add",
                "--scope", "user",
                "--transport", "http",
                "openviking", f"{base_url}/mcp",
                "--header", f"Authorization: Bearer {api_key}",
            ],
            check=False,
            capture_output=True,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
