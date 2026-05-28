---
description: Set up Claude Code in the current project — drops a small CLAUDE.md and .claude/memory/decisions.md tailored to the stack
---

Use the `project-bootstrap` skill to set up Claude Code for the current project.

If a `CLAUDE.md` already exists in the project root, ask the user before overwriting it. Otherwise, follow the skill's steps end-to-end and report what was created.

After the setup completes, suggest the user spend two minutes reviewing `CLAUDE.md` and adjusting anything that's wrong — auto-detected commands are a starting point, not the truth.
