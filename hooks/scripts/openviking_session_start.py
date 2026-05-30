#!/usr/bin/env python3
"""Inject OpenViking user profile and memories at session start.

SessionStart hook — fetches recent user memories and preferences from
OpenViking and prints them as <openviking-context> so Claude begins each
session with persistent memory context. Silently no-ops if OpenViking is
unreachable, unconfigured, or DEVKIT_DISABLE_OPENVIKING=1.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


MAX_ITEMS = 8
NETWORK_TIMEOUT = 2  # seconds per call; fail fast when server is down
PROFILE_QUERY = "user preferences workflow habits context decisions"


def load_config() -> tuple[str, str]:
    base_url = os.environ.get("OPENVIKING_BASE_URL", "")
    api_key = os.environ.get("OPENVIKING_API_KEY", "")
    conf_path = Path.home() / ".openviking" / "ovcli.conf"
    if conf_path.exists():
        try:
            conf = json.loads(conf_path.read_text(encoding="utf-8"))
            base_url = base_url or conf.get("url", "")
            api_key = api_key or conf.get("api_key", "")
        except Exception:
            pass
    return base_url.rstrip("/"), api_key


def search(base_url: str, api_key: str, query: str, scope: str, top_k: int) -> list:
    payload = json.dumps({"q": query, "target_uri": scope, "top_k": top_k}).encode()
    req = urllib.request.Request(
        f"{base_url}/api/v1/search/find",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=NETWORK_TIMEOUT) as resp:
            data = json.loads(resp.read())
            return data.get("items", data.get("results", []))
    except (urllib.error.URLError, Exception):
        return []


def main() -> int:
    if os.environ.get("DEVKIT_DISABLE_OPENVIKING") == "1":
        return 0

    base_url, api_key = load_config()
    if not base_url:
        return 0

    items: list = []
    for scope in ("viking://user/memories", "viking://agent/memories"):
        items.extend(search(base_url, api_key, PROFILE_QUERY, scope, top_k=5))

    if not items:
        return 0

    seen: set = set()
    deduped = []
    for item in items:
        key = item.get("id") or item.get("uri") or id(item)
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    lines = ["<openviking-context>"]
    for item in deduped[:MAX_ITEMS]:
        content = item.get("content") or item.get("text") or item.get("summary", "")
        if content:
            lines.append(f"- {content.strip()}")
    lines.append("</openviking-context>")

    if len(lines) > 2:
        print("\n".join(lines))

    return 0


if __name__ == "__main__":
    sys.exit(main())
