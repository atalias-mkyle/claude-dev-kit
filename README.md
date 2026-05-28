# dev-kit — a Claude Code workflow plugin

An opinionated, cross-machine Claude Code setup that you install once and get everywhere.

It bundles:

- **MCPs:** Context7 (live library docs), Serena (LSP-powered code retrieval), Sequential Thinking (structured reasoning)
- **Subagents:** `researcher`, `planner`, `implementer`, `reviewer`, `test-runner` — each in its own context window
- **Hooks:** dangerous-bash guard, auto-format on edit, project-snapshot on session start
- **Skills:** `project-bootstrap`, `debug-playbook`, `pr-checklist`
- **Slash commands:** `/bootstrap` (drop a CLAUDE.md into the current repo), `/pr-check`

Designed so installing it on a new machine is two commands.

---

## One-time setup per machine

### 1. Prerequisites

You need these on each machine. Anything missing means a piece of the kit silently no-ops, never breaks.

| Tool | Why | Install |
|---|---|---|
| `python3` (3.10+) | Hook scripts | macOS: `brew install python` · Ubuntu: `apt install python3` · Windows: [python.org](https://python.org) |
| `node` + `npx` | Context7 + Sequential Thinking MCPs | [nodejs.org](https://nodejs.org) or `nvm` |
| `uv` (`uvx`) | Serena MCP | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (Mac/Linux) · `winget install astral-sh.uv` (Windows) |
| `git` | SessionStart hook reads git state | already on most systems |

Optional but recommended formatters (auto-format hook detects what's installed): `prettier`, `ruff` or `black`, `gofmt`, `rustfmt`, `shfmt`, `rubocop`.

### 2. Install the plugin

From inside Claude Code (any project, anywhere):

```bash
/plugin marketplace add <your-github>/claude-dev-kit
/plugin install dev-kit@dev-kit-marketplace
```

You'll be prompted for the userConfig values (Context7 API key — optional, leave blank for free tier; the three boolean toggles).

That's it. On the next session start in any project, the hooks fire, the MCPs come up, and the subagents are available.

### 3. Bootstrap a project

In any project, run:

```
/bootstrap
```

It drops a small `CLAUDE.md` and `.claude/memory/decisions.md` tailored to whatever stack it detects. Review the file, fix the bits it got wrong, commit.

---

## Cross-machine memory (the "what did I do here vs there" piece)

The kit deliberately leaves persistent cross-session memory to a separate plugin so you can pick the flavor you want. Three options, ranked by setup cost:

### Option A — synced CLAUDE.md + decisions.md (zero infra)

Put your projects on a synced drive (iCloud, Dropbox, Syncthing, OneDrive). The `CLAUDE.md` and `.claude/memory/decisions.md` files travel with the project. This is the simplest "what I decided here vs there" path and the one you should start with.

### Option B — OpenViking auto-recall (recommended for full memory)

[OpenViking](https://github.com/volcengine/OpenViking) is ByteDance's open-source context database for AI agents. Its Claude Code plugin auto-captures memories at session end and auto-recalls relevant ones when you submit a prompt — so when you sit down at your Mac after working on your Linux box yesterday, the relevant context is already in scope.

```bash
# Add OpenViking's marketplace and install its Claude Code plugin
/plugin marketplace add Castor6/openviking-plugins
/plugin install claude-code-memory-plugin@openviking-plugin
```

For cross-machine sharing, point OpenViking's data dir at a synced folder. On each machine, edit `~/.openviking/ov.conf` so the storage path is something like `~/Dropbox/openviking` (or whatever sync tool you use). All machines reading the same path get the same memory.

### Option C — local knowledge graph (lightweight)

If OpenViking feels heavy, use [`mcp-knowledge-graph`](https://github.com/shaneholloman/mcp-knowledge-graph), which stores memory as JSONL. Point it at a synced folder the same way.

Add to your user-scope MCP config (`~/.claude/settings.json` or `claude mcp add`):

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-knowledge-graph",
        "--memory-path",
        "~/Dropbox/claude-memory"
      ]
    }
  }
}
```

---

## What's in the kit, in one page

```
claude-dev-kit/
├── .claude-plugin/
│   ├── plugin.json              # manifest + userConfig prompts
│   └── marketplace.json         # single-plugin marketplace, so the repo is installable directly
├── .mcp.json                    # Context7, Serena, Sequential Thinking
├── hooks/
│   ├── hooks.json               # wires the three baseline hooks
│   └── scripts/
│       ├── pre_bash_guard.py    # blocks rm -rf, force-push to main, etc.
│       ├── post_edit_format.py  # auto-formats by extension; silent if formatter missing
│       └── session_context.py   # prints branch / dirty files / recent commits / TODOs at session start
├── agents/
│   ├── researcher.md            # read-only exploration, returns compressed summary (haiku)
│   ├── planner.md               # produces reviewable plan, no code (sonnet)
│   ├── implementer.md           # executes approved plan in isolation (sonnet)
│   ├── reviewer.md              # read-only diff review against intent (sonnet)
│   └── test-runner.md           # runs tests, returns failure diagnosis only (haiku)
├── skills/
│   ├── project-bootstrap/SKILL.md
│   ├── debug-playbook/SKILL.md
│   └── pr-checklist/SKILL.md
├── commands/
│   ├── bootstrap.md             # /bootstrap
│   └── pr-check.md              # /pr-check
├── templates/
│   └── CLAUDE.md                # reference template the bootstrap skill copies from
└── README.md
```

---

## Daily workflow this is designed for

1. Open a new project. Run `/bootstrap` once.
2. Start a session. The SessionStart hook injects current branch, dirty files, recent commits, and open TODOs — Claude knows where you left off.
3. For any non-trivial task, hand off to the `planner` first. Review the plan, make changes, then say "go".
4. The `implementer` makes the changes. The auto-format hook tidies up after each edit. The bash guard prevents the obvious mistakes.
5. Before pushing, run `/pr-check`. The `test-runner` runs tests and the `reviewer` reads the diff. Both report back compactly.
6. Push.

---

## Tuning levers

Every hook honors an env var if you want to disable it for one session without uninstalling:

- `DEVKIT_DISABLE_BASH_GUARD=1`
- `DEVKIT_DISABLE_AUTOFORMAT=1`
- `DEVKIT_DISABLE_SESSION_CONTEXT=1`

If you find a subagent isn't pulling its weight on a project, delete or rename its `.md` and Claude Code stops routing to it. If you want to add a project-specific subagent, drop a new `.md` in the project's `.claude/agents/` — project-scope agents win over plugin-scope.

If a skill is firing when you don't want it, tighten the `description:` line in its frontmatter. Skill activation is description-driven.

---

## What this kit is *not*

- It's not a memory system. Memory is Option A/B/C above. Pick one.
- It's not a project-specific MCP layer. Postgres / Redis / Sentry / Linear / Slack / Stripe MCPs belong in the project's `.mcp.json`, not here, because they're tied to the stack.
- It's not exhaustive. Five subagents and three skills is intentional — most setups fail by adding more, not less. Add more when you've felt the friction the new piece would remove.
