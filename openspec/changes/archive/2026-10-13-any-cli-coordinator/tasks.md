# Tasks

## 1. Preflight

- [x] 1.1 Update `scripts/test_preflight.py` to remove Claude Code/Codex coordinator expectations and the Codex profile check. Add a regression case where OpenCode is present, Claude Code and Codex are absent, and general requirements pass; verify the focused test passes without coordinator checks.
- [x] 1.2 Remove the required coordinator CLI and optional Codex profile checks from `scripts/preflight.sh`. Keep general requirement and named worker-provider checks; verify `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_preflight.py'` passes and the missing-item count is adjusted.

## 2. Coordinator instructions and routing

- [x] 2.1 Rewrite the skill's Codex profile section as generic coordinator capabilities and point CLI-specific setup to `routing.md`. Search the whole skill: each Claude/Codex mention must be generic or describe a harness feature that may stay.
- [x] 2.2 State in the skill's merge step that the coordinator waits for explicit maintainer approval on every CLI, including CLIs without permission prompts.
- [x] 2.3 Make worker start, wait, read, and end instructions generic. Put harness-specific wait behavior, including Claude Code's background wait behavior, in the matching coordinator note.
- [x] 2.4 In `routing.md`, keep the Coordinator table and add a Coordinator notes list with one entry per CLI: how to start from the main checkout, required writable paths, approval handling, and worker waiting. Move the existing Codex details word for word, including the `--add-dir` instructions from the runner files. Add coordinator setup for preflight and worktree creation outside the sandbox, and waiting behavior for both runners. Rewrite the opencode note from the coordinator proof and reviewer checks.
- [x] 2.5 Move the coordinator capability requirements to `design.md` as a short “What must hold” list, and ensure each item has a verifying task here.

## 3. Runners and documentation

- [x] 3.1 Move Codex `--add-dir` instructions from both runner guides into the Codex coordinator note. State where their worktrees live and that the coordinator must be able to write there; point to coordinator notes in `routing.md`.
- [x] 3.2 Change the `AGENTS.md` coordinator instruction to cover any eligible CLI, name the explicit skill path, and check that `CONTRIBUTING.md`'s provider principle remains true without changing it.
- [x] 3.3 Update README “Who does what”, “Requirements”, “Use it”, and “Make it yours” to use the eligibility rule and routing note. In the intro, change only the approved sentence to “The coordinator runs on any CLI that reads `AGENTS.md` and can run the skill's scripts.” Keep that exact wording in `design.md`.
- [x] 3.4 Add one issue-specific line under Unreleased in `CHANGELOG.md`.

## 4. Real coordinator proof

- [x] 4.1 Coordinator-owned: the coordinator ran one real OpenCode session on its default model against scratch issue #45 in a temporary clone. It read `AGENTS.md` and the skill, ran preflight, created a worktree, wrote a brief, started a real planner turn, and cleaned up. The session could not use `teardown-worktree.sh` on the uncommitted planner draft and removed the disposable worktree, branch, and state entry directly. OpenCode 2.0.20 used `glm-5.3-flash` on the headless runner. See the Coordinator proof line in `.claude/pr-body.md`. The planner and implementer did not start Herdr agents.

## 5. Repository checks

- [x] 5.1 Run `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck`; verify it exits 0.
- [x] 5.2 Run `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile`; verify it exits 0.
- [x] 5.3 Run `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check`; verify it exits 0.
- [x] 5.4 Run `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'`; record the test count and verify all tests pass.
- [x] 5.5 Run `npx --yes @fission-ai/openspec validate --all --strict`; verify all specs and changes pass.
