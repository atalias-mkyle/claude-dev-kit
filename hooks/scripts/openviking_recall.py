#!/usr/bin/env python3
"""Auto-recall relevant memories from OpenViking before each prompt.

UserPromptSubmit hook — searches OpenViking across user memories, agent
memories, and agent skills for context relevant to the current prompt.
Injects results as hookSpecificOutput.additionalContext. Always approves.

Silently no-ops if OpenViking is unreachable, unconfigured, the prompt is
too short, or DEVKIT_DISABLE_OPENVIKING=1.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


MIN_QUERY_LENGTH = 3
RESULTS_PER_SCOPE = 3
NETWORK_TIMEOUT = 2  # seconds per call; 3 scopes × 2s fits within the 8s hook timeout
SCOPES = [
    "viking://user/memories",
    "viking://agent/memories",
    "viking://agent/skills",
]


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


def search(base_url: str, api_key: str, query: str, scope: str) -> list:
    payload = json.dumps({
        "q": query,
        "target_uri": scope,
        "top_k": RESULTS_PER_SCOPE,
    }).encode()
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


def main() -> None:
    if os.environ.get("DEVKIT_DISABLE_OPENVIKING") == "1":
        return

    try:
        stdin_data = json.loads(sys.stdin.read())
        prompt = stdin_data.get("prompt", "")
    except Exception:
        return

    if len(prompt.strip()) < MIN_QUERY_LENGTH:
        return

    base_url, api_key = load_config()
    if not base_url:
        return

    all_items: list = []
    for scope in SCOPES:
        all_items.extend(search(base_url, api_key, prompt, scope))

    if not all_items:
        return

    seen: set = set()
    deduped = []
    for item in all_items:
        key = item.get("id") or item.get("uri") or id(item)
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    lines = ["<relevant-memories>"]
    for item in deduped[:9]:
        content = item.get("content") or item.get("text") or item.get("summary", "")
        if content:
            lines.append(f"- {content.strip()}")
    lines.append("</relevant-memories>")

    if len(lines) > 2:
        sys.stdout.write(json.dumps({"hookSpecificOutput": {"additionalContext": "\n".join(lines)}}) + "\n")


if __name__ == "__main__":
    main()
