# Tasks

## 1. Head lag wait

- [x] 1.1 In `switchyard/scripts/merge-queue.py`, replace the immediate "local head differs" stop with design.md decision 4: stop at once when `git ls-remote` shows a remote head other than local `HEAD`; otherwise poll `gh pr view --json headRefOid` at the poll interval for up to `min(60, --timeout)` seconds. Do not change `wait_ci`. Verify: tests in 1.2.
- [x] 1.2 In `switchyard/scripts/test_merge_queue.py`, add `list_heads` to the `gh` stub's `pr list`. Test: a lagging list head plus one stale `pr view` head still reaches exit 3; a lagging head with `--timeout 0` stops with "did not reach". `test_local_remote_mismatch_stops_before_rebase` still passes unchanged.

## 2. Restack after a parent merges

- [x] 2.1 Add `restack_children` per design.md decision 1, and call it before both `teardown` calls in `process`. Verify: tests in 2.3.
- [x] 2.2 In `main`, during batch validation, exit 2 when a queued record's `parent` is set and that parent is not earlier in the arguments, per decision 3. Verify: tests in 2.3.
- [x] 2.3 Extend the `gh` stub with `pr list --jq` and `pr edit --base`, and add a `stacked(child, parent)` helper. Tests:
  - `--merge <parent> <child>`: both merge, the child's PR base becomes `main`, the child's merged tree has the parent's and child's changes once, and both are torn down.
  - `--merge <parent>` with the child not queued: the parent merges and is torn down; the child's record has no parent fields and its branch is `origin/main` plus only its own commits.
  - Default mode: exit 3 for the parent, run the merge command, rerun with `<parent> <child>`: the `MERGED` path restacks before teardown.
  - A child whose change conflicts with `main`: the queue exits 1, stderr names the child, the parent's worktree and record remain, and no rebase is left in progress.
  - `<child> <parent>` and `<child>` alone exit 2 before any `gh` call.

## 3. Docs

- [x] 3.1 In `switchyard/SKILL.md` Several PRs, add one sentence: after an issue merges, the queue runs `restack.sh` for each child that names it, then tears it down; a failed restack stops the queue and names the child. Verify: no other section is touched.
- [x] 3.2 In Stacked issues, replace the closing paragraph ("Do not queue a child with its parent ... follow-up.") with: queue the parent before its children, or the queue exits 2; the queue restacks children itself; a child it restacks but does not queue still needs its checks. In step 3, add that `merge-queue.py` runs this step. Verify: steps 1, 2, and 4 are unchanged.
- [x] 3.3 Add one line under Unreleased in `CHANGELOG.md`, in the style of the others. Verify: only that line changes.

## 4. Repository checks

- [x] 4.1 Run `switchyard/hooks/checks.sh` from the worktree root and confirm it exits 0. Record the unittest counts.
- [x] 4.2 Run `npx --yes @fission-ai/openspec validate --all --strict` and confirm it exits 0.

## Workflow follow-up

- `Change: openspec/changes/queue-restack` added as the first line of issue #134 at plan time.
- Archive the change in the PR that completes it.
