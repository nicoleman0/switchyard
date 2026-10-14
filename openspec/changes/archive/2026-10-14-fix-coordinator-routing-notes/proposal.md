# Proposal

## Why

Issue #47 records four gaps in the coordinator routing notes and the archived design for #41. The gaps leave Claude headless turns vulnerable to the runner's foreground timeout and omit verified setup and configuration details.

## What Changes

- Update the Claude coordinator note to use a background worker turn on headless and read the newest turn log after it exits.
- Add provider-neutral background and log-reading guidance to the headless runner.
- Document Claude's model and effort startup flags from `claude --help`.
- Record the #41 OpenCode `--auto` worktree proof result and point the archived design to PR #48.
- Add one Unreleased changelog line that tells existing projects to update their own Claude note.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This change updates project-owned workflow documentation and examples. No spec-level behavior is changing.

## Impact

`.claude/skills/work-issues/routing.md`, `.claude/skills/work-issues/runners/headless.md`, `openspec/changes/archive/2026-10-13-any-cli-coordinator/design.md`, `CHANGELOG.md`, and the new OpenSpec planning files. The issue body will link to this change.
