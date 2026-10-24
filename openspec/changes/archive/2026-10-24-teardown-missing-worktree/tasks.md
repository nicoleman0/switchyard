# Tasks

## 1. Teardown skips steps that are already done

- [x] 1.1 Replace the `No worktree has branch` exit with step detection for the worktree (entry plus folder) and local branch. Before any change, refuse with exit 1 when a record exists and its `branch` differs from the argument. Verify with tests: worktree entry gone; folder gone with a stale entry; branch mismatch leaves the record and changes nothing.
- [x] 1.2 Run the dirty preflight and the `--abandon` reports only for the parts that exist. Verify with tests: a dirty existing worktree still stops ordinary teardown before the hook; `--abandon` with the folder gone exits 0 and removes the record.
- [x] 1.3 Run the down hook with `WORKTREE` set to the entry path, else the record path, else empty. Skip Herdr removal and remove a stale entry with `git worktree remove <path>`. Skip `git branch -D` when the local branch is gone. Verify with tests: the hook runs and sees the record path when the worktree is gone; with `HERDR_ENV=1` and the folder gone, the herdr stub logs no `worktree remove`.
- [x] 1.4 Print one `Skipped:` line per skipped step, including the remote branch, and a final line naming what was removed. Verify with a test where worktree, local branch, and remote branch are all gone: exit 0, three `Skipped:` lines, record removed. Existing teardown tests still pass.

## 2. Tests

- [x] 2.1 Add the tests above to `switchyard/scripts/test_state.py` next to the other teardown tests, reusing `Harness`. Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`.

## 3. Docs

- [x] 3.1 Add one `Fixed` line for #56 under Unreleased in `CHANGELOG.md`.
- [x] 3.2 In `switchyard/SKILL.md`, add one sentence after the teardown description: teardown skips steps that are already done and still removes the record. In the `switchyard/hooks/worktree-down.sh` header, say the worktree folder may already be gone. Verify the SKILL.md usage still matches the script's usage line.

## 4. Repository checks

- [x] 4.1 Run `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` and confirm it exits 0.
- [x] 4.2 Run `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` and confirm it exits 0.
- [x] 4.3 Run `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` and confirm it exits 0.
- [x] 4.4 Run `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` and record the counts.
- [x] 4.5 Run `npx --yes @fission-ai/openspec validate --all --strict` and confirm it exits 0.

## Workflow follow-up

- Archive the change in the PR that completes it.
