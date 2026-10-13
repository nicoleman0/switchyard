# Tasks

## 1. Preflight

- [x] 1.1 Update `scripts/test_preflight.py` to remove Claude Code/Codex coordinator expectations and the Codex profile check. Add a regression case where OpenCode is present, Claude Code and Codex are absent, and general requirements pass; verify the focused test passes without coordinator checks.
- [x] 1.2 Remove the required coordinator CLI and optional Codex profile checks from `scripts/preflight.sh`. Keep general requirement and named worker-provider checks; verify `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_preflight.py'` passes and the missing-item count is adjusted.

## 2. Coordinator instructions and routing

- [x] 2.1 Rewrite the skill's Codex profile section as generic coordinator capabilities and point CLI-specific setup to `routing.md`. Search the whole skill: each Claude/Codex mention must be generic or describe a harness feature that may stay.
- [x] 2.2 State in the skill's merge step that the coordinator waits for explicit maintainer approval on every CLI, including CLIs without permission prompts.
- [x] 2.3 Make worker start, wait, read, and end instructions generic. Put harness-specific wait behavior, including Claude Code's background wait behavior, in the matching coordinator note.
- [x] 2.4 In `routing.md`, keep the Coordinator table and add a Coordinator notes list with one entry per CLI: how to start from the main checkout, required writable paths, approval handling, and worker waiting. Move the existing Codex details word for word. Draft the opencode note from documentation and `opencode --help`; mark unconfirmed details for the coordinator to check during the proof.
- [x] 2.5 Move the coordinator capability requirements to `design.md` as a short “What must hold” list, and ensure each item has a verifying task here.

## 3. Runners and documentation

- [x] 3.1 Remove Codex writable-path instructions from both runner guides. State where their worktrees live and that the coordinator must be able to write there; point to coordinator notes in `routing.md`.
- [x] 3.2 Change the `AGENTS.md` coordinator instruction to cover any eligible CLI, name the explicit skill path, and check that `CONTRIBUTING.md`'s provider principle remains true without changing it.
- [x] 3.3 Update README “Who does what”, “Requirements”, “Use it”, and “Make it yours” to use the eligibility rule and routing note. In the intro, change only the approved sentence to “The coordinator runs on any CLI that reads `AGENTS.md` and can run the skill's scripts.” Keep that exact wording in `design.md`.
- [x] 3.4 Add one issue-specific line under Unreleased in `CHANGELOG.md`.

## 4. Real coordinator proof

- [ ] 4.1 Coordinator-owned: the coordinator of this issue batch runs one real OpenCode session on its default model against a temporary GitHub scratch issue. Verify it reads `AGENTS.md` and the skill, runs preflight, creates a worktree, writes a brief, starts and completes one real worker turn, ends the worker, and tears down the worktree. Record OpenCode version/model, worker provider, and results in the PR body, then close the scratch issue. The planner and implementer do not start Herdr agents.

## 5. Repository checks

- [x] 5.1 Run `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck`; verify it exits 0.
- [x] 5.2 Run `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile`; verify it exits 0.
- [x] 5.3 Run `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check`; verify it exits 0.
- [x] 5.4 Run `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'`; record the test count and verify all tests pass.
- [x] 5.5 Run `npx --yes @fission-ai/openspec validate --all --strict`; verify all specs and changes pass.
