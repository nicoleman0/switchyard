# Tasks

## 1. Update coordinator guidance

- [x] 1.1 Update the Claude coordinator note: one sentence that the startup flags `claude --model <model> --effort <level>` set the values from the `claude` row of the Coordinator table; on headless, run each worker turn in the background with the Bash tool's `run_in_background`, and when Claude Code reports the command exited, read the newest log in `<path>/.claude/turns/`. Verify the flags against `claude --help`; do not add polling instructions.
- [x] 1.2 Add one provider-neutral line to `runners/headless.md`: when the coordinator's harness stops long foreground commands, run the turn in the background and read its log when it exits; verify it applies across providers and matches the existing per-turn log convention.
- [x] 1.3 Update the OpenCode note with the #41 result from PR #48: with `--auto`, the proof session set up the worktree, wrote the brief, and started the planner, so the worktrees needed no extra setup; keep the existing `Not tried` lines. Verify against `gh pr view 48`.

## 2. Correct archived evidence and release notes

- [x] 2.1 Replace the ignored proof-file reference in the archived #41 design with PR #48; verify the link identifies the recorded proof.
- [x] 2.2 Add one Unreleased changelog entry under `### Fixed` (create the subsection if missing, keeping the Added, Changed, Fixed order) that tells existing projects to update their own Claude coordinator note; do not disturb concurrent changelog edits.

## 3. Validate

- [x] 3.1 Review the resulting documentation for both headless guidance and provider-specific coordinator notes; record the runner and providers covered, with no live provider call implied.
- [x] 3.2 Run `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck` and record the real result.
- [x] 3.3 Run `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile` and record the real result.
- [x] 3.4 Run `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check` and record the real result.
- [x] 3.5 Run `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'` and record the real result.
- [x] 3.6 Run `npx --yes @fission-ai/openspec validate --all --strict` and record the real result.
