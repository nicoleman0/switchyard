# Tasks

## 1. Setup

- [x] 1.1 In `switchyard/scripts/setup-worktree.sh`, accept a leading `--parent <issue>` as design.md decision 1 describes. Read the parent's `branch` and `parent` with `state.py get`; exit 1 with a clear message when the parent has no record or is itself stacked. Use the parent's branch as the base for both the Herdr and the plain-git path. Add `parent`, `parent_branch`, and `parent_head` to the `state.py init` arguments. Update the usage comment. Verify: tests in 4.1.
- [x] 1.2 Without `--parent`, the script behaves as before. Verify: the existing setup tests in `test_state.py` pass unchanged.

## 2. Teardown

- [x] 2.1 In `switchyard/scripts/teardown-worktree.sh`, before the hook and any removal, find records in `.switchyard/state/` whose `parent` equals the issue. When any exist, exit 1, naming each child issue and saying to run `restack.sh` on it or abandon it first. Apply this with and without `--abandon`. Verify: tests in 4.2.

## 3. Restack and scope

- [x] 3.1 Add `switchyard/scripts/restack.sh <issue>` with the steps in design.md decision 3, and a short header comment. Verify: tests in 4.3, and shellcheck exits 0.
- [x] 3.2 In `switchyard/scripts/check-scope.sh`, diff from `parent_head` when the record has one, as design.md decision 5 describes. Verify: test in 4.4.

## 4. Tests in `switchyard/scripts/test_state.py`

- [x] 4.1 Setup with `--parent`: the child worktree's `HEAD` contains the parent's commit, and the record has `parent`, `parent_branch`, `parent_head`. Setup refuses a parent with no record and a parent that is itself stacked, and creates no worktree in either case.
- [x] 4.2 Teardown of a parent refuses, with and without `--abandon`, while a child record names it, and removes nothing. After the child's `parent` is cleared, teardown succeeds.
- [x] 4.3 Restack: with a parent and a child pushed to the test's bare origin, squash the parent onto `main` and push it. `restack.sh` leaves the child as `origin/main` plus only the child's commits, pushes it, calls the `gh` stub with `pr edit <branch> --base main`, and clears the parent fields. A conflicting child exits 1, names the file, and leaves no rebase in progress. A record with no `parent_head` exits 2.
- [x] 4.4 Scope: a child whose only own change is in its owned paths passes `check-scope.sh` though the parent changed other files.

## 5. Docs

- [x] 5.1 In `switchyard/SKILL.md`, Before starting step 2: add one sentence that the maintainer may name issues to stack instead, pointing to Stacked issues. Verify: no other sentence in the step is reworded.
- [x] 5.2 Add a short `## Stacked issues` section after Several PRs: opt-in only; stack once the parent's review passes; `setup-worktree.sh --parent`; tell a child's reviewer to diff from `parent_head` in the brief; open the PR with `--base <parent_branch>`; after the parent merges, run `restack.sh <child>`, then tear the parent down; do not queue a child with its parent in `merge-queue.py`. Verify: no other section is touched.
- [x] 5.3 Add one line under Unreleased, Added, in `CHANGELOG.md`, in the style of the others. Verify: only that line changes.

## 6. Repository checks

- [x] 6.1 Run `switchyard/hooks/checks.sh` from the worktree root and confirm it exits 0. Record the unittest counts.
- [x] 6.2 Run `npx --yes @fission-ai/openspec validate --all --strict` and confirm it exits 0.

## Workflow follow-up

- `Change: openspec/changes/stacked-issues` added as the first line of issue #119 at plan time.
- Archive the change in the PR that completes it.

## Verification

- `switchyard/hooks/checks.sh`: passed; 181 unittest tests, plus Python compilation, ShellCheck, and Node syntax checks.
- Focused restack checks after the retry guard: 5 tests passed.
- `npx --yes @fission-ai/openspec validate --all --strict`: 1 change passed.
