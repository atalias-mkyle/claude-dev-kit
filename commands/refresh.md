---
description: Re-run project-bootstrap in refresh mode — re-detects the stack and updates only the sections of CLAUDE.md that have drifted
---

Check whether `CLAUDE.md` exists in the project root.

If it does NOT exist, stop and tell the user to run `/bootstrap` first to create it.

If it DOES exist, use the `project-bootstrap` skill in **REFRESH MODE**:

1. Re-detect the stack exactly as bootstrap would (language, framework, package manager, test runner, lint/format commands, etc.).
2. Compare each detected value against what is currently written in `CLAUDE.md`.
3. Report only the sections that have changed or drifted — skip anything still current.
4. Before overwriting any section, show the user the old value vs. the new value and ask for confirmation.
5. Apply only the confirmed changes; leave everything else untouched.

Keep the output terse — one line per unchanged section is enough ("stack: unchanged"), a short diff block for anything that changed.
