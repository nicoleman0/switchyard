# Proposal

## Why

Delivers GitHub issue #59. The provider-neutral workflow lives in `.claude/skills/work-issues/`, and its git-ignored runtime files live under `.claude/`. A Codex, opencode, or pi user sees a Claude folder and assumes the workflow is not for them, and every worker prompt names that folder.

## What Changes

- Move the tracked workflow from `.claude/skills/work-issues/` to a top-level `switchyard/` folder. File names inside it stay the same.
- Move the git-ignored runtime files (brief, answers, reviews, turns, state, sessions, PR body, shots) from `.claude/` to one git-ignored folder, `.switchyard/`.
- `.claude/` keeps only Claude-specific files: the `.claude/agents/*.md` wrappers, now pointing at `switchyard/roles/`, OpenSpec's generated files, and a short `.claude/skills/work-issues/SKILL.md` stub that sends Claude Code to `switchyard/SKILL.md`.
- Update every reference: scripts, roles, runners, the brief template, `routing.md`, `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, the CI workflow, `.gitignore`, and the tests.
- `update-switchyard.py` moves an install made from 0.6.0 or older to the new layout. Local edits merge as in any update. `routing.md` and files the project added move unchanged. **BREAKING** for adopters: the 0.6.0 updater cannot take the next release, so a one-time run of the new updater from a Switchyard checkout is required.
- A compat `update-paths.txt` stays at the old path so a 0.6.0 or older updater stops before writing anything and prints that one-time step.
- `init-project.py` deletes the compat file in a new project.
- CHANGELOG entry under Unreleased.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty and this change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- All files under `.claude/skills/work-issues/` move to `switchyard/`.
- `scripts/state.py`, `setup-worktree.sh`, `teardown-worktree.sh`, `compare.py`, `shots.mjs`, `update-switchyard.py`, and all four test files change paths.
- `.github/workflows/switchyard.yml` checks `switchyard/` instead.
- Adopters on 0.6.0 or older follow a one-time update step. Adopters whose `routing.md` names `.claude/sessions/` for pi update that row themselves, because the updater never changes `routing.md`.
- Out of scope: version bump and release.
