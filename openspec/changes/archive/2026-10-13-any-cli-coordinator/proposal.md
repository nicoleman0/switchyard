# Proposal

## Why

Issue #41 addresses the coordinator setup being tied to Claude Code and Codex even though the workflow's workers are configurable. Projects should be able to use any CLI that can read `AGENTS.md`, run the skill scripts, write to its worktrees, push from the main checkout, and request maintainer approval.

## What Changes

- Make the coordinator instructions and preflight independent of Claude Code and Codex.
- Keep coordinator CLI setup notes in the project-owned `routing.md`, alongside worker CLI notes.
- State in the skill that only the maintainer approves a merge, regardless of whether the coordinator CLI has permission prompts.
- Update the runners, `AGENTS.md`, and README to describe the CLI-neutral coordinator path.
- Prove the path with one real OpenCode coordinator session and name which coordinator CLIs have been tried.

## Impact

- `.claude/skills/work-issues/SKILL.md`, `routing.md`, both runner guides, and `scripts/preflight.sh`.
- `README.md`, `AGENTS.md`, and one Unreleased line in `CHANGELOG.md`.
- Focused preflight test updates.
- A real OpenCode coordinator smoke run on a temporary issue, with no merge or pull request required.
