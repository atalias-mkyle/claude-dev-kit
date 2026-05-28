#!/usr/bin/env python3
"""Set up OpenViking MCP server from plugin userConfig.

Writes ~/.openviking/ovcli.conf and injects the openviking HTTP MCP
server entry directly into ~/.claude/settings.json.
"""
import json
import os
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
    existing_conf = {}
    if CONF_PATH.exists():
        try:
            existing_conf = json.loads(CONF_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    if existing_conf.get("url") != conf["url"] or existing_conf.get("api_key") != conf["api_key"]:
        CONF_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONF_PATH.write_text(json.dumps(conf, indent=2), encoding="utf-8")

    # Inject HTTP MCP server entry into ~/.claude/settings.json.
    mcp_entry = {
        "type": "http",
        "url": f"{base_url}/mcp",
        "headers": {
            "Authorization": f"Bearer {api_key}",
        },
    }

    settings = {}
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    servers = settings.setdefault("mcpServers", {})
    existing_entry = servers.get("openviking", {})
    if existing_entry.get("url") == mcp_entry["url"] and existing_entry.get("headers") == mcp_entry["headers"]:
        return 0  # already up to date

    servers["openviking"] = mcp_entry
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
