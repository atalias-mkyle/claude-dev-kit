---
name: conventional-commits
description: Use when writing a commit message, reviewing a branch's commit history before PR, or when the user says "commit this", "stage and commit", "let's commit", or asks whether commits are clean. Formats all commit messages per the Conventional Commits spec and audits existing commit history on request.
---

# Conventional commits

All commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org) spec. This keeps the history machine-readable for changelogs, semver automation, and release tooling.

## Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Types

| Type | When to use |
|---|---|
| `feat` | New feature or behavior visible to users |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `perf` | Performance improvement |
| `build` | Build system, deps, or tooling changes |
| `ci` | CI/CD pipeline changes |
| `chore` | Maintenance tasks that don't affect production code |
| `revert` | Reverts a previous commit |

## Rules for the subject line

- Imperative mood: "add feature" not "added feature" or "adds feature"
- No period at the end
- Max 72 characters
- First word after the colon is lowercase (proper nouns and acronyms keep their casing)

## Breaking changes

Add `!` after the type/scope, or add a `BREAKING CHANGE:` footer:

```
feat!: drop support for Node 16

BREAKING CHANGE: minimum Node version is now 18
```

## Body and footers

- Body explains **why**, not what. The diff shows what.
- Reference issues in footers: `Fixes #123`, `Closes #456`
- Separate body from subject with a blank line

## Examples

```
feat(auth): add OAuth2 PKCE flow

fix: prevent race condition in job queue

refactor(api): extract pagination logic into shared util

feat!: replace REST endpoints with GraphQL

BREAKING CHANGE: all /api/v1/* routes have been removed
```

## When auditing a branch before PR

1. Run `git log <base>..HEAD --oneline` and list every commit subject
2. Check each against the rules above — flag any that:
   - Use past tense ("added", "fixed")
   - Are vague ("update stuff", "wip", "cleanup")
   - Missing a type prefix
   - Exceed 72 characters
3. Suggest a reword for each flagged message
4. If any commits need rewording, surface the `git rebase -i` command with the commit range — don't run it, let the user decide
