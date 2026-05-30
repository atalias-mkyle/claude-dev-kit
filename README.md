# dev-kit — a Claude Code workflow plugin

An opinionated, cross-machine Claude Code setup that you install once and get everywhere.

It bundles:

- **MCPs:** OpenViking (persistent memory, auto-recall on every prompt), Context7 (live library docs), Serena (LSP-powered code retrieval), Sequential Thinking (structured reasoning), plus optional Brave Search and local memory graph
- **Subagents:** `orchestrator`, `researcher`, `planner`, `reverse-reasoner`, `implementer`, `reviewer`, `security-reviewer`, `test-runner`, `debugger`, `ci-triager`, `memory-curator` — each in its own context window
- **Hooks:** bash guard, write guard, auto-format on edit, project-snapshot on session start, session capture on stop
- **Skills:** `project-bootstrap`, `debug-playbook`, `pr-checklist`, `security-review`, `dependency-audit`, `incident-response`, `deploy-check`, `onboard`
- **Slash commands:** `/bootstrap`, `/pr-check`, `/security-check`, `/refresh`
- **Workflow guides:** feature-workflow, hotfix-workflow, recovery-playbook

Designed so installing it on a new machine is two commands.

---

## One-time setup per machine

### 1. Prerequisites

You need these on each machine. Anything missing means a piece of the kit silently no-ops, never breaks.

| Tool | Why | Install |
|---|---|---|
| `python3` (**3.10+ required**) | Hook scripts. **3.9 will fail silently** on session_context.py. Check: `python3 --version` | macOS: `brew install python` · Ubuntu: `apt install python3` · Windows: [python.org](https://python.org) |
| `node` + `npx` | Context7 + Sequential Thinking MCPs | [nodejs.org](https://nodejs.org) or `nvm` |
| `uv` (`uvx`) | Serena MCP | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (Mac/Linux) · `winget install astral-sh.uv` (Windows) |
| `git` | SessionStart hook reads git state | already on most systems |

Optional but recommended formatters (auto-format hook detects what's installed): `prettier`, `ruff` or `black`, `gofmt`, `rustfmt`, `shfmt`, `rubocop`.

### 2. Install the plugin

From inside Claude Code (any project, anywhere):

```bash
/plugin marketplace add atalias-tech/claude-dev-kit
/plugin install dev-kit@dev-kit-marketplace
```

You'll be prompted for the userConfig values (Context7 API key — optional, leave blank for free tier; OpenViking URL and API key; the boolean toggles).

That's it. On the next session start in any project, the hooks fire, the MCPs come up, and the subagents are available.

### 3. Bootstrap a project

In any project, run:

```
/bootstrap
```

It drops a `CLAUDE.md` and `.claude/memory/decisions.md` tailored to whatever stack it detects. Review the file, fix the bits it got wrong, commit. Run `/refresh` later when the stack changes.

---

## Cross-machine memory (the "what did I do here vs there" piece)

The kit ships three memory layers, active by default:

### Layer 1 — OpenViking (semantic memory, built-in)

[OpenViking](https://github.com/volcengine/OpenViking) is ByteDance's open-source context database for AI agents. The kit wires it directly — no separate plugin needed.

**What the kit does automatically:**
- **SessionStart** — fetches your recent memories and preferences from OpenViking and injects them as `<openviking-context>` so Claude starts every session with persistent context.
- **UserPromptSubmit** — searches OpenViking for memories relevant to each prompt and injects them as `<relevant-memories>` before Claude responds.
- **Stop** — sends the conversation transcript to OpenViking for memory extraction and indexing.
- **MCP** — `openviking` MCP server registered at `http://127.0.0.1:1933` by default, exposing `mcp__openviking__search`, `mcp__openviking__store`, `mcp__openviking__read`, `mcp__openviking__forget`, and others.

**Setup:** Start an OpenViking server locally (`docker run -p 1933:1933 volcengine/openviking`) or point `openviking_base_url` at a remote one. Set `openviking_api_key` if your server requires auth. The kit writes `~/.openviking/ovcli.conf` on first session start.

For cross-machine sharing, point OpenViking's data dir at a synced folder (`~/Dropbox/openviking`).

### Layer 2 — decisions.md (zero infra)

The `session_capture.py` Stop hook appends a timestamped git snapshot to `.claude/memory/decisions.md` at the end of every session. Syncs naturally if the project is on a synced drive.

### Layer 3 — local knowledge graph (optional)

If you prefer a local JSONL graph over OpenViking, set `memory_path` in userConfig and use the `mcp__memory__*` tools. Set `memory_system: local-graph` to have the session-start nudge point Claude at the right tools.

---

## What's in the kit, in one page

```
claude-dev-kit/
├── .claude-plugin/
│   ├── plugin.json              # complete manifest: agents, skills, commands, hooks, MCPs
│   └── marketplace.json         # single-plugin marketplace, so the repo is installable directly
├── .mcp.json                    # Context7, Serena, Sequential Thinking, Brave Search, Memory
├── hooks/
│   ├── hooks.json               # wires all six hooks
│   └── scripts/
│       ├── pre_bash_guard.py    # blocks rm -rf, force-push to main, etc.
│       ├── pre_write_guard.py   # blocks writes to .env, .ssh/, /etc/, and sensitive paths
│       ├── post_edit_format.py  # auto-formats by extension; silent if formatter missing
│       ├── session_context.py        # injects git state + recent decisions + tooling nudges
│       ├── session_capture.py        # appends session summary to decisions.md on stop
│       ├── setup_openviking.py       # writes ~/.openviking/ovcli.conf idempotently
│       ├── openviking_session_start.py  # fetches OpenViking profile and injects as context
│       ├── openviking_recall.py      # searches OpenViking for relevant memories per prompt
│       └── openviking_capture.py     # sends transcript to OpenViking for memory extraction
├── agents/
│   ├── orchestrator.md          # routes tasks to the right agents, owns workflow state (sonnet)
│   ├── researcher.md            # read-only exploration, returns compressed summary (haiku)
│   ├── planner.md               # produces reviewable plan, no code (sonnet)
│   ├── reverse-reasoner.md      # validates plan with forward+backward passes (sonnet)
│   ├── implementer.md           # executes approved plan in isolation (sonnet)
│   ├── reviewer.md              # read-only diff review against intent (sonnet)
│   ├── security-reviewer.md     # OWASP/secrets/dependency security audit (sonnet)
│   ├── test-runner.md           # runs tests, returns failure diagnosis only (haiku)
│   ├── debugger.md              # isolates root cause, describes fix — no writes (sonnet)
│   ├── ci-triager.md            # reads CI logs via gh CLI, classifies failure type (haiku)
│   └── memory-curator.md        # prunes and consolidates .claude/memory/ files (haiku)
├── skills/
│   ├── project-bootstrap/SKILL.md
│   ├── debug-playbook/SKILL.md
│   ├── pr-checklist/SKILL.md
│   ├── security-review/SKILL.md
│   ├── dependency-audit/SKILL.md
│   ├── incident-response/SKILL.md
│   ├── deploy-check/SKILL.md
│   └── onboard/SKILL.md
├── commands/
│   ├── bootstrap.md             # /bootstrap
│   ├── pr-check.md              # /pr-check
│   ├── security-check.md        # /security-check [PR#]
│   └── refresh.md               # /refresh
├── workflows/
│   ├── feature-workflow.md      # full 6-agent pipeline for new features
│   ├── hotfix-workflow.md       # fast-path for production fixes
│   └── recovery-playbook.md     # reference for mid-pipeline failures
├── templates/
│   └── CLAUDE.md                # reference template the bootstrap skill copies from
└── README.md
```

---

## Daily workflow this is designed for

0. Start with the `orchestrator` for any non-trivial task, or invoke agents individually for quick tasks.
1. Open a new project. Run `/bootstrap` once.
2. Start a session. The SessionStart hook injects current branch, dirty files, recent commits, open TODOs, recent decisions, and any in-progress workflow state — Claude knows where you left off.
3. For any non-trivial task, hand off to the `planner` first. The `reverse-reasoner` validates the plan before you say "go".
4. The `implementer` makes the changes. The auto-format hook tidies up after each edit. The bash and write guards prevent the obvious mistakes.
5. The `security-reviewer` checks for vulnerabilities on changes touching auth, inputs, or APIs. The `reviewer` reads the diff.
6. The `test-runner` runs tests and returns failure diagnosis if anything is red.
7. Before pushing, run `/pr-check`. Run `/security-check` for sensitive changes.
8. Push.

---

## Workflows

The `workflows/` directory contains pre-composed multi-agent playbooks:

- **`feature-workflow.md`** — end-to-end pipeline for new features: researcher → planner → reverse-reasoner → implementer → test-runner → reviewer → security-reviewer. Includes parallel work stream patterns.
- **`hotfix-workflow.md`** — fast-path for production fixes: debugger → implementer → test-runner → reviewer → deploy-check. Has escalation rules for when a hotfix turns out to be bigger than expected.
- **`recovery-playbook.md`** — reference for mid-pipeline failures: what to do when implementer returns blocked/partial, tests won't pass, or a session is interrupted.

Tell the orchestrator which workflow to follow, or reference a workflow file directly in your prompt.

---

## Verifying the install

**Are the MCPs running?**

Ask Claude: "what MCP servers are active?" It should list Context7, Serena, and Sequential Thinking. Or run `/mcp` in Claude Code to see server status.

**Is Python the right version?**

```bash
python3 --version
# Must be 3.10 or higher. 3.9 will cause a syntax error in session_context.py.
```

**Are the hooks wired?**

Run `/hooks` in Claude Code, or open `.claude/settings.local.json` and confirm the hook entries from `hooks/hooks.json` appear.

**Common silent failures:**

| Symptom | Likely cause |
|---|---|
| Context7 or Sequential Thinking MCP never starts | `node` / `npx` not on PATH |
| Serena MCP never starts | `uv` not on PATH — re-run the uv install and open a new shell |
| Serena starts but Claude ignores it and uses Read/Grep | Make sure `--context claude-code` is set (not `ide-assistant`). Check with `mcp__serena__get_current_config`. |
| Session context not printed at session start | Python < 3.10, or `DEVKIT_DISABLE_SESSION_CONTEXT=1` is set |
| decisions.md not updated after sessions | `DEVKIT_DISABLE_SESSION_CAPTURE=1` is set, or git not available |
| OpenViking MCP not connecting | Check the server is running; default URL is `http://127.0.0.1:1933`. Set `openviking_base_url` in userConfig for a different host. |
| OpenViking not capturing memories | Check `~/.openviking/ovcli.conf` exists (written by setup_openviking.py on SessionStart). Requires `openviking_base_url` set in userConfig. |

**Note on `.claude/` in `.gitignore`:** The `.claude/` directory is gitignored because `settings.local.json` contains machine-local permission allowlists. This means the first session on a new clone will prompt for permissions that were pre-approved on the original machine — that's expected behavior.

---

## Tuning levers

Every hook honors an env var if you want to disable it for one session without uninstalling:

- `DEVKIT_DISABLE_BASH_GUARD=1`
- `DEVKIT_DISABLE_WRITE_GUARD=1`
- `DEVKIT_DISABLE_AUTOFORMAT=1`
- `DEVKIT_DISABLE_SESSION_CONTEXT=1`
- `DEVKIT_DISABLE_SESSION_CAPTURE=1`
- `DEVKIT_DISABLE_NUDGES=1`
- `DEVKIT_DISABLE_OPENVIKING=1` — skips session-start inject, per-prompt recall, and Stop capture (MCP stays connected)

**Serena tuning:**

The kit ships Serena in `--context claude-code` mode, which gives Claude a built-in instruction manual (injected via the MCP system prompt) telling it to prefer symbolic tools over Read/Grep. The key tool sequence for code editing: `get_symbols_overview` → `find_symbol(include_body=True)` → `replace_symbol_body` (or `replace_content` for small in-method edits). Always read the symbol body first — skipping that step silently drops decorators.

To check what Serena has available in a session: `mcp__serena__get_current_config`.

To tune language servers per-project, edit `.serena/project.yml`. Change the `languages` list to match your project's stack (Python, TypeScript, Go, etc.). Project memories live in `.serena/memories/` and survive across sessions.

**Optional: serena-hooks** — the Serena maintainers ship a CLI companion (`serena-hooks`) that enforces usage: after 3 consecutive Read/Grep calls on code files, it denies the call and injects a reminder. To enable globally, add to `~/.claude/settings.json`:
```json
"hooks": {
  "PreToolUse": [{ "matcher": "Read|Grep", "hooks": [{ "type": "command", "command": "serena-hooks remind --client=claude-code", "timeout": 5 }] }]
}
```
This is not bundled in the kit because it requires `serena-hooks` on PATH (comes with Serena).

If you find a subagent isn't pulling its weight on a project, delete or rename its `.md` and Claude Code stops routing to it. If you want to add a project-specific subagent, drop a new `.md` in the project's `.claude/agents/` — project-scope agents win over plugin-scope.

If a skill is firing when you don't want it, tighten the `description:` line in its frontmatter. Skill activation is description-driven.

---

## What this kit is *not*

- It's not a memory server. It wires OpenViking as the memory layer but doesn't run the server — you run OpenViking separately (local Docker or remote).
- It's not a project-specific MCP layer. Postgres / Redis / Sentry / Linear / Slack / Stripe MCPs belong in the project's `.mcp.json`, not here, because they're tied to the stack.
- It's not exhaustive. The agent and skill roster is intentional — most setups fail by adding more, not less. Add more when you've felt the friction the new piece would remove.
