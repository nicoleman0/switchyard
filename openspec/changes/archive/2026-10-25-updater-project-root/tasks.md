# Tasks

## 1. Refactor

- [x] 1.1 In `switchyard/scripts/test_update_switchyard.py`, add a test that `--check` run outside a git work tree exits 2 and prints "inside a git work tree" on stderr. Verify it passes before the refactor.
- [x] 1.2 In `switchyard/scripts/update-switchyard.py`, add `find_project_root()` after `git()` and replace both inline copies in `run()` with calls to it. Verify the unittest command passes unchanged.

## 2. Repository checks

- [x] 2.1 Run `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` and confirm it exits 0.
- [x] 2.2 Run `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` and confirm it exits 0.
- [x] 2.3 Run `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` and confirm it exits 0.
- [x] 2.4 Run `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` and record the counts.
- [x] 2.5 Run `npm test --prefix create-switchyard` and record the counts.
- [x] 2.6 Run `npx --yes @fission-ai/openspec validate --all --strict` and confirm it exits 0.

## Workflow follow-up

- Archive the change in the PR that completes it.
