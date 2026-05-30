#!/usr/bin/env python3
"""Inject project context at session start.

SessionStart hook stdout is added directly to Claude's context, so we
print a compact, useful snapshot: branch, recent commits, uncommitted
changes, and the first few TODO/FIXME markers in the repo.

Keep output short. Anything we print here is paid for on every session.
"""
import os
import subprocess
import sys

if sys.version_info < (3, 10):
    print("## Dev Kit Warning\nPython 3.10+ is required for the session context hook.\nDetected:", sys.version, "\nSet DEVKIT_DISABLE_SESSION_CONTEXT=1 to suppress.")
    sys.exit(0)


MAX_RECENT_COMMITS = 5
MAX_TODOS = 8
MAX_DIRTY_FILES = 15


def run(cmd: list[str], cwd: str | None = None) -> str:
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


def read_recent_decisions(cwd: str) -> list[str]:
    decisions_path = os.path.join(cwd, ".claude", "memory", "decisions.md")
    try:
        with open(decisions_path, encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return []
        entries = content.split("### ")
        entries = [e for e in entries if e.strip()]
        last_three = entries[-3:]
        result = []
        for entry in last_three:
            text = ("### " + entry).strip()
            if len(text) > 300:
                text = text[:297] + "..."
            result.append(text)
        return result
    except (FileNotFoundError, OSError):
        return []


def main() -> int:
    if os.environ.get("DEVKIT_DISABLE_SESSION_CONTEXT") == "1":
        return 0
    if len(sys.argv) > 1 and sys.argv[1].lower() == "false":
        return 0

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if not os.path.isdir(os.path.join(project_dir, ".git")):
        # Not a git repo — nothing useful to inject.
        return 0

    lines: list[str] = ["## Project snapshot (dev-kit SessionStart)"]

    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=project_dir)
    if branch:
        lines.append(f"- Branch: `{branch}`")

    upstream = run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd=project_dir,
    )
    if upstream:
        ahead_behind = run(
            ["git", "rev-list", "--left-right", "--count", f"{upstream}...HEAD"],
            cwd=project_dir,
        )
        if ahead_behind:
            try:
                behind, ahead = ahead_behind.split()
                if int(ahead) or int(behind):
                    lines.append(f"- Tracking `{upstream}`: {ahead} ahead, {behind} behind")
            except ValueError:
                pass

    dirty = run(["git", "status", "--porcelain"], cwd=project_dir)
    if dirty:
        files = dirty.splitlines()[:MAX_DIRTY_FILES]
        lines.append(f"- Uncommitted changes ({len(dirty.splitlines())} file(s)):")
        for f in files:
            lines.append(f"  - `{f.strip()}`")
        if len(dirty.splitlines()) > MAX_DIRTY_FILES:
            lines.append(f"  - ...and {len(dirty.splitlines()) - MAX_DIRTY_FILES} more")

    # In-progress workflow state
    workflow_state_path = os.path.join(project_dir, ".claude", "workflow-state.json")
    try:
        if os.path.isfile(workflow_state_path):
            import json
            with open(workflow_state_path, encoding="utf-8") as wf:
                ws = json.load(wf)
            stage = ws.get("stage", "")
            if stage and stage != "complete":
                steps_done = len(ws.get("steps_completed", []))
                steps_total = len(ws.get("step_index", []))
                lines.append(f"- In-progress workflow: stage={stage}, {steps_done}/{steps_total} steps complete")
    except Exception:
        pass

    recent = run(
        ["git", "log", "-n", str(MAX_RECENT_COMMITS), "--pretty=format:%h %s"],
        cwd=project_dir,
    )
    if recent:
        lines.append("- Recent commits:")
        for c in recent.splitlines():
            lines.append(f"  - {c}")

    # TODO/FIXME survey, but only via git so we don't traverse node_modules.
    todos = run(
        [
            "git",
            "grep",
            "-n",
            "-E",
            "TODO|FIXME|XXX",
            "--",
            ":(exclude)*.lock",
            ":(exclude)*.lock.json",
            ":(exclude)package-lock.json",
            ":(exclude)yarn.lock",
            ":(exclude)pnpm-lock.yaml",
        ],
        cwd=project_dir,
    )
    if todos:
        todo_lines = todos.splitlines()[:MAX_TODOS]
        lines.append(f"- Open TODO/FIXME markers ({len(todos.splitlines())} total, showing {len(todo_lines)}):")
        for t in todo_lines:
            # Trim very long lines to keep output compact.
            if len(t) > 160:
                t = t[:157] + "..."
            lines.append(f"  - {t}")

    # Inject recent decisions
    if decisions := read_recent_decisions(project_dir):
        lines.append("\n## Recent Decisions (last 3)")
        lines.extend(decisions)

    # CLAUDE.md staleness signal
    try:
        claude_md = os.path.join(project_dir, "CLAUDE.md")
        if os.path.isfile(claude_md):
            age = run(["git", "log", "-1", "--format=%cr", "--", "CLAUDE.md"], cwd=project_dir)
            last_hash = run(["git", "log", "-1", "--format=%H", "--", "CLAUDE.md"], cwd=project_dir)
            if age and last_hash:
                commit_count_str = run(
                    ["git", "rev-list", "--count", f"{last_hash}..HEAD"],
                    cwd=project_dir,
                )
                commit_count = int(commit_count_str) if commit_count_str.isdigit() else 0
                age_lower = age.lower()
                is_old = (
                    "year" in age_lower
                    or ("month" in age_lower and int(age_lower.split()[0]) >= 2)
                )
                if is_old and commit_count > 10:
                    lines.append(
                        f"- CLAUDE.md last updated {age} — consider /refresh to check for stale content."
                    )
    except Exception:
        pass

    # Tooling nudges
    if os.environ.get("DEVKIT_DISABLE_NUDGES") != "1":
        lines.append("\n## Dev-kit tooling")
        lines.append("- Non-trivial task? → `orchestrator` agent, or `planner` → `reverse-reasoner` → `implementer`")
        lines.append("- Library API question? → Context7 MCP (not training data)")
        lines.append("- Before pushing? → `/pr-check`; auth/API/secrets changes → `/security-check`")
        lines.append("- Code files: use Serena, not Read/Grep. Sequence: `get_symbols_overview` → `find_symbol(include_body=True)` → `replace_symbol_body` (or `replace_content` for small in-body edits). Always read the body before replacing it or decorators will be silently dropped.")

        memory_system = (os.environ.get("MEMORY_SYSTEM") or "openviking").lower().strip()
        if memory_system == "openviking":
            lines.append("- Memory: OpenViking — `mcp__openviking__store` to save, `mcp__openviking__search` to recall, `mcp__openviking__forget` to delete")
        elif memory_system == "local-graph":
            lines.append("- Memory: local knowledge graph — use `mcp__memory__add_observations` / `mcp__memory__search_nodes`")
        elif memory_system == "decisions-md":
            lines.append("- Memory: decisions.md — append decisions to `.claude/memory/decisions.md`")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
