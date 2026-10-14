# Tasks

## 1. Preflight and reporting

- [x] 1.1 Add option parsing and dirty-worktree preflight to `teardown-worktree.sh`; verify with tests that ordinary teardown stops before the hook and leaves the worktree, branches, and record intact.
- [x] 1.2 Add `--abandon` reporting for short status and commits absent from remote refs; verify tests include modified and untracked files and a local-only commit, with no prompt.
- [x] 1.3 Extend `test_state.py` for the preflight and report behavior; verify the focused teardown tests pass.

## 2. Cleanup and operator guidance

- [x] 2.1 Herdr's `worktree remove --force` was verified from the main checkout on a dirty disposable worktree: it fails without `--force` (`dirty_worktree_requires_force`) and with `--force` it removes the checkout, keeps the local branch, and exits 0. Use forced removal under `--abandon` on both runners; test the Herdr path with a stub.
- [x] 2.2 Preserve conditional remote deletion and state cleanup; verify tests cover remote branch present and absent.
- [x] 2.3 Add the abandonment use case and command to `SKILL.md` and one `Added` entry under Unreleased in `CHANGELOG.md`; verify the guide command matches the script usage.

## 3. Repository checks

- [x] 3.1 Run `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck` and confirm it exits successfully.
- [x] 3.2 Run `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile` and confirm it exits successfully.
- [x] 3.3 Run `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check` and confirm it exits successfully.
- [x] 3.4 Run `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'` and record the result.
- [x] 3.5 Run `npx --yes @fission-ai/openspec validate --all --strict` and confirm it exits successfully.
