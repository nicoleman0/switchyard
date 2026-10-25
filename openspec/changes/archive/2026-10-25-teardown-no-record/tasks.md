# Tasks

## 1. Teardown

- [x] 1.1 In `teardown-worktree.sh`, capture `state.py get`'s stderr. On status 3 drop it and note there is no record. On any other nonzero status print it and exit with that status. Verify with the test in 1.3.
- [x] 1.2 Move `remote_branch_state` above the hook. When there is no record, no `entry_path`, no local branch, and no remote branch, print `Issue <n>: no record, and nothing to remove for branch <branch>.` to stderr and exit 1 before the hook, the abandon report, and `state.py rm`. Verify the hook does not run.
- [x] 1.3 Add tests in `test_state.py`:
  - no record, no worktree, no branch: exit 1, the new message on stderr, no setup hint, no `Removed`, down hook not run.
  - the same with `--abandon`: exit 1.
  - no record with only a local branch: exit 0 and the branch is gone.
  - no record with only a remote branch: exit 0 and the branch is gone.
  - a record file that is unreadable JSON: exit 1 with `cannot read record` shown.
  - existing `test_teardown_missing_entry_removes_record_and_reports_skips` still passes (record, nothing else).
  Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`.

## 2. Docs

- [x] 2.1 Add `- #86: Teardown exits 1 when the issue has no record and nothing to remove, instead of reporting success.` under Unreleased, in a `### Fixed` section in `CHANGELOG.md`. Append only.

## 3. Repository checks

- [x] 3.1 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` passes.
- [x] 3.2 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 3.3 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 3.4 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 3.5 `npm test --prefix create-switchyard` passes.
- [x] 3.6 `npx @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
