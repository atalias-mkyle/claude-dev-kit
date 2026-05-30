#!/usr/bin/env python3
"""Auto-capture conversation turns to OpenViking at session end.

Stop hook — reads the session transcript, strips injected context blocks
from individual content blocks, and sends real user/assistant turns to the
OpenViking sessions API for memory extraction. Always exits 0.

Skipped when DEVKIT_DISABLE_SESSION_CAPTURE=1 or DEVKIT_DISABLE_OPENVIKING=1.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


NETWORK_TIMEOUT = 10

# Content block prefixes injected by hooks — not real user/assistant turns.
INJECTED_PREFIXES = (
    "<openviking-context>",
    "<relevant-memories>",
    "<system-reminder>",
    "[Subagent Context]",
    "## Project snapshot",
    "## Dev-kit tooling",
    "## Recent Decisions",
)


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


def is_injected(text: str) -> bool:
    stripped = text.strip()
    return any(stripped.startswith(p) for p in INJECTED_PREFIXES)


def extract_text(content) -> str:
    """Extract and filter text from a message content field.

    Handles both string content and the content-block array format.
    Filters out individual blocks that are hook-injected context so
    real user text still passes through even if it follows an injected block.
    """
    if isinstance(content, str):
        return "" if is_injected(content) else content
    if isinstance(content, list):
        parts = [
            b.get("text", "")
            for b in content
            if isinstance(b, dict)
            and b.get("type") == "text"
            and not is_injected(b.get("text", ""))
        ]
        return " ".join(p for p in parts if p)
    return ""


def parse_transcript(path: str) -> list[dict]:
    messages = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                role = entry.get("type")
                if role not in ("user", "assistant"):
                    continue
                text = extract_text(entry.get("message", {}).get("content", ""))
                if text.strip():
                    messages.append({"role": role, "content": text})
    except (FileNotFoundError, OSError):
        pass
    return messages


def send(base_url: str, api_key: str, session_id: str, messages: list) -> None:
    payload = json.dumps({"messages": messages}).encode()
    req = urllib.request.Request(
        f"{base_url}/api/v1/sessions/{session_id}/messages",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=NETWORK_TIMEOUT) as _:
            pass
    except (urllib.error.URLError, Exception):
        pass


def main() -> int:
    if os.environ.get("DEVKIT_DISABLE_SESSION_CAPTURE") == "1":
        return 0
    if os.environ.get("DEVKIT_DISABLE_OPENVIKING") == "1":
        return 0

    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0

    transcript_path = data.get("transcript_path", "")
    if not transcript_path:
        return 0

    # Prefer session_id from Claude Code; fall back to transcript filename.
    session_id = data.get("session_id") or os.path.splitext(
        os.path.basename(transcript_path)
    )[0]
    if not session_id:
        return 0

    base_url, api_key = load_config()
    if not base_url:
        return 0

    messages = parse_transcript(transcript_path)
    if messages:
        send(base_url, api_key, session_id, messages)

    return 0


if __name__ == "__main__":
    sys.exit(main())
