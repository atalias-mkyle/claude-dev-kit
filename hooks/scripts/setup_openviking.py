#!/usr/bin/env python3
"""Write OpenViking remote-server config from plugin userConfig values.

Called at SessionStart with base_url as argv[1] (or OPENVIKING_BASE_URL env var).
API key is read from the OPENVIKING_API_KEY environment variable.
Skips silently if base_url is empty or the literal string 'undefined'.
Idempotent: only writes if the file content would change.
"""
import json
import os
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".openviking" / "claude-code-memory-plugin" / "config.json"


def main() -> int:
    base_url = os.environ.get('OPENVIKING_BASE_URL', '') or (sys.argv[1] if len(sys.argv) > 1 else "")
    api_key = os.environ.get('OPENVIKING_API_KEY', '')

    if not api_key:
        return 0

    if not base_url or base_url in ("undefined", "null", ""):
        return 0

    config = {
        "mode": "remote",
        "baseUrl": base_url,
        "autoRecall": True,
        "autoCapture": True,
    }
    if api_key and api_key not in ("undefined", "null", ""):
        config["apiKey"] = api_key

    new_content = json.dumps(config, indent=2)

    if CONFIG_PATH.exists():
        try:
            existing = CONFIG_PATH.read_text(encoding="utf-8")
            # Only rewrite if the managed keys differ (preserve any extra user keys).
            existing_data = json.loads(existing)
            if all(existing_data.get(k) == v for k, v in config.items()):
                return 0
        except (json.JSONDecodeError, OSError):
            pass

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(new_content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
