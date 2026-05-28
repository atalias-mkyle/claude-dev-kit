---
name: debug-playbook
description: Use when debugging a reported bug, an unexpected behavior, a failing test that isn't obvious, or anything that starts with "why is X happening". Walks through a structured isolation approach instead of jumping straight to a guess-and-edit loop, which is the most common failure mode of agentic debugging.
---

# Debug playbook

A disciplined debugging walk. Skip steps only when you can articulate why.

## Step 1 — Reproduce, exactly

Before anything else: get a reproduction you can run repeatedly. If the bug is "the tests fail", run them yourself and capture the failure. If it's "the UI is broken when X happens", produce the exact click sequence or curl command.

If you cannot reproduce, your next action is not "fix" — it's gathering more information. Ask the user for the missing detail (env, input, OS) and stop.

## Step 2 — State what should happen

In one sentence, write down the expected behavior. In a second sentence, write down the actual behavior. The gap between those two sentences is the bug. If you can't write both, you don't understand the bug yet.

## Step 3 — Localize before reading

Before opening files, narrow the search. Use the `researcher` subagent or Serena's symbol search:
- Which function produces the wrong value?
- Which test asserts the wrong thing?
- What's the last line of code that ran before the failure?

If the bug is a stack trace, the stack trace is the localization — read the frames bottom-up.

## Step 4 — Form a hypothesis with a test

Write one sentence: "I think the bug is caused by X, because Y." Then write the smallest experiment that would prove or disprove it (often a one-line print, a focused unit test, a debugger breakpoint).

Run the experiment. If the result surprises you, the hypothesis was wrong — go back to step 3, don't bend the next experiment to match.

## Step 5 — Fix, then prove the fix

When you have a confirmed cause:
1. Add a failing test that captures the bug (red).
2. Make the smallest change that turns it green.
3. Run the broader test suite — fixing a bug often shakes loose another one.

## Step 6 — Note what you learned

If the bug taught you something about the system that wasn't documented, add an entry to `.claude/memory/decisions.md` or update CLAUDE.md so the next debug session starts smarter.

## Anti-patterns to actively avoid

- **Guess-and-edit.** Trying changes without a hypothesis until something works. The "fix" usually masks the real bug.
- **Over-collection.** Reading 20 files when 3 would have told you. Localize first.
- **Premature refactor.** Restructuring the area "while you're in there." Fix the bug, ship the fix, refactor separately.
- **Ignoring the warning.** That deprecation notice or "this never happens" comment is often the bug.
