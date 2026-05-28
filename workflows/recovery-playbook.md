# Recovery Playbook

This document is a reference for recovering from mid-pipeline failures in claude-dev-kit v2.0. The pipeline order is:

```
orchestrator → researcher → planner → reverse-reasoner → implementer → reviewer → test-runner
                                                                       ↓ (if security-sensitive)
                                                                       security-reviewer
```

Breakout agents (on-demand): debugger, ci-triager, memory-curator

---

## Quick Reference Table

| Failure | Recovery | Max retries | Escalate when |
|---|---|---|---|
| implementer: blocked | re-plan with blocker as constraint | 2 re-plans | 3rd block |
| implementer: partial | resume from last step in workflow-state.json | 3 resume attempts | Still partial after 3 |
| test-runner: failures | route back to implementer with full output | 3 | Still failing after 3 |
| reviewer: block | re-plan with block reasons as new constraints | 2 re-plans | 2nd block |
| security-reviewer: block | route to implementer with specific findings | 2 | Still blocked after 2 |
| hook script error | disable hook, fix, re-enable | n/a | Always fix root cause |
| session interrupted | read workflow-state.json, resume | n/a | If state is corrupt |

---

## Detailed Recovery Steps

### Implementer returns Status: blocked

1. Read the `Blockers[]` field carefully
2. Route back to planner with the original plan + blocker description as new input
3. Planner produces a revised plan that addresses the blocker
4. Run reverse-reasoner on the revised plan
5. If third block: present to human — the task is not well-defined enough for autonomous execution

**State location:** `.claude/workflow-state.json` — field `blockers`

**Do not** route the blocker directly to the implementer with a workaround. The planner must re-evaluate the full plan so the blocker becomes a constraint, not a patch.

---

### Implementer returns Status: partial

1. Read `.claude/workflow-state.json` — find the last completed `step_index`
2. Verify no half-written state: check that all files in `files_changed[]` are complete (no truncated writes)
3. Route back to implementer with: `"Resume from STEP-N. Steps 1 through N-1 are complete. workflow-state.json has the checkpoint."`
4. Implementer should not redo completed steps

**State location:** `.claude/workflow-state.json` — fields `step_index`, `files_changed`

**Do not** start over from scratch. Completed steps are checkpointed and re-running them risks introducing inconsistency.

---

### Test-runner returns failures

1. Pass the full failure output (exact test names, assertion errors) to the implementer
2. Implementer fixes only the failing tests — no scope expansion
3. Re-run test-runner
4. After 3 failed fix attempts: stop, present test output to human — the fix introduced a regression

**Do not** ask the implementer to fix tests by weakening assertions or skipping them. If tests cannot be fixed without expanding scope, escalate.

---

### Reviewer returns verdict: block

1. Extract the reviewer's specific blocking reasons
2. These become new constraints for the planner (not just the implementer)
3. Re-plan with: original task + reviewer blocking reasons added as "must avoid" constraints
4. Run full validate → implement → test → review cycle again
5. Second block: escalate to human

**Do not** send reviewer feedback directly to the implementer without re-planning. A reviewer block often means the approach is wrong, not just the code.

---

### Security-reviewer returns verdict: block

1. Extract the specific security findings (file, line, description)
2. Route to implementer with: `"Fix these security issues before proceeding: [findings]"`
3. Re-run security-reviewer only (not full review cycle) after fix
4. Second block: escalate to human

**Do not** run the full review cycle after a security fix — only re-run the security reviewer. This avoids re-introducing reviewer feedback loops before the security issue is confirmed resolved.

---

### Hook script error (script exits non-zero unexpectedly)

1. Check which hook failed and its corresponding disable env var:

| Hook script | Disable env var |
|---|---|
| `hooks/scripts/pre_bash_guard.py` | `DEVKIT_DISABLE_BASH_GUARD=1` |
| `hooks/scripts/pre_write_guard.py` | `DEVKIT_DISABLE_WRITE_GUARD=1` |
| `hooks/scripts/post_edit_format.py` | `DEVKIT_DISABLE_AUTOFORMAT=1` |
| `hooks/scripts/session_context.py` | `DEVKIT_DISABLE_SESSION_CONTEXT=1` |
| `hooks/scripts/session_capture.py` | `DEVKIT_DISABLE_SESSION_CAPTURE=1` |

2. Temporarily disable the failing hook via env var
3. Fix the script (syntax error, missing dependency, path issue)
4. Re-enable and verify it passes on a no-op input
5. **Never permanently disable a safety hook** — always fix the root cause

**Hook config location:** `hooks/hooks.json`

---

### Session interrupted mid-pipeline

1. At next session start: `session_context.py` will inject `workflow-state.json` if present
2. Read `.claude/workflow-state.json` to find: `stage`, `step_index`, `files_changed`, `blockers`
3. Re-invoke the orchestrator with: `"Resume the in-progress workflow. State is in .claude/workflow-state.json."`
4. Do **not** start over — start from the last completed step

**If state is corrupt** (malformed JSON, missing required fields): do not attempt to resume. Assess the files_changed from git diff, determine how far the work got, and re-invoke from the last safe checkpoint manually.

---

## State File Reference

`.claude/workflow-state.json` is the authoritative checkpoint. Fields used during recovery:

| Field | Written by | Read by | Purpose |
|---|---|---|---|
| `stage` | implementer | orchestrator, session_context.py | Current pipeline stage |
| `step_index` | implementer | orchestrator | Last completed step number |
| `files_changed` | implementer | recovery procedures | All files touched so far |
| `blockers` | implementer | orchestrator, planner | Blocker descriptions for re-planning |

`.claude/memory/decisions.md` is appended at `Stop` by `session_capture.py` and injected (last 3 entries) at `SessionStart` by `session_context.py`. It is not a recovery target — it is context for the next session.
