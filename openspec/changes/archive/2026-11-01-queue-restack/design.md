# Design

## Context

- `merge-queue.py` processes each issue in order: check the PR, fetch, compare local `HEAD` with the PR's `headRefOid`, rebase, gate, push, wait for CI, merge or print the merge command, tear down. A PR already `MERGED` goes straight to teardown.
- `restack.sh <child>` (#119) runs from the main checkout. It fetches, rebases the child with `--onto origin/main <parent_head>`, pushes with a lease when the remote branch exists, retargets an open PR to `main`, and clears `parent`, `parent_branch`, `parent_head`. On conflict it aborts the rebase, lists the files on stderr, and exits 1. It exits 2 when the record has no `parent_head`. It refuses an untracked file in the worktree, while the queue ignores untracked files.
- `teardown-worktree.sh` exits 1 while any record names the issue as `parent`.
- `wait_ci` already polls `gh pr view --json headRefOid` until it matches the pushed head, inside the CI timeout.
- The test `gh` stub supports `pr list`, `pr view`, `pr checks`, and `pr merge`. `restack.sh` also calls `gh pr list ... --jq` and `gh pr edit`.

## Goals / Non-Goals

**Goals:**
- One queue run merges a parent, restacks its children, tears the parent down, and goes on to the next issue.
- A rerun after any stop picks up where it stopped.
- The head check tolerates GitHub's lag after a push without hiding a real divergence.

**Non-Goals:**
- Changing `restack.sh` or `teardown-worktree.sh`.
- Resolving restack conflicts in the queue. `restack.sh` has no union resolve, and its conflicts are the coordinator's to fix.
- Running checks on a restacked child that is not in the batch.

## Decisions

1. **Restack in one place, before teardown.** A helper `restack_children(main, issue)` runs before both `teardown` calls in `process` (the `MERGED` path and the post-merge path). It scans `<main>/.switchyard/state/*.json` for records whose `parent` equals the issue, as `teardown-worktree.sh` does, sorts them with `key_order`, and runs `bash scripts/restack.sh <child>` from the main checkout for each. It prints restack's stdout and a progress line per child. A nonzero exit raises `Stop` with the child's key and restack's stderr, for example `restack of #12 failed (1): ...`. The issue then stops with exit 1, the parent stays, and a rerun finds only the children not yet restacked. Alternative: restack inside `teardown`. That mixes two scripts' jobs in one helper and would also fire for callers that only want teardown.

2. **Restack every child, queued or not.** The coordinator's note settles this. A child left stacked would block the parent's teardown anyway. A child not in the batch gets no checks from the queue; the Stacked issues section keeps "run every check after the rebase" for it.

3. **Refuse a bad order up front.** During batch validation in `main`, read each queued record's `parent`. When it is set and that parent is not earlier in the argument list, exit 2: `#<child> is stacked on #<parent>; queue #<parent> before it`. Without this, the queue would plain-rebase a child onto `origin/main` while the parent is unmerged, and replay the parent's commits. A child whose parent is earlier is safe: by the time the queue reaches it, the restack has cleared its `parent`. Alternative: stop when processing reaches the child. That fails after earlier PRs already merged, which the up-front check avoids.

4. **Wait for head lag only when the push landed.** When local `HEAD` differs from the PR's `headRefOid`, read the remote branch with `git ls-remote --heads origin refs/heads/<branch>`.
   - Remote differs from local `HEAD`: stop at once with today's "local head differs" message. The divergence is real.
   - Remote equals local `HEAD`: the push landed and GitHub has not caught up. Poll `gh pr view <pr> --json headRefOid` every `SWITCHYARD_POLL_SECONDS` until it matches, for up to the bound below. On timeout stop with `PR head did not reach <sha> within <bound>s`.
   The bound is `min(60, --timeout)`: a 60-second module constant, capped by `--timeout` so `--timeout 0` stops at once, which also lets tests reach the stop without waiting. No new flag. GitHub usually catches up in seconds. Alternative: `--timeout` alone (default 1800). A stuck head would hold the queue for half an hour.
   Leave `wait_ci` as it is. Sharing its head poll would be a refactor in the same commit as a behaviour change.

5. **Test with the real scripts.** Extend the stub: `pr list` with `--jq` prints the first open PR's number or nothing; `pr edit <branch> --base main` records the base on the row. `pr list` also honours a per-row `list_heads` sequence, like `heads` for `pr view`, so a test can make the list lag. A `stacked(child, parent)` helper branches the child's worktree from the parent's branch and writes `parent`, `parent_branch`, `parent_head` into its record.

## Risks / Trade-offs

- [`restack.sh` refuses untracked files that the queue would ignore] → The stop names the child and the file. The coordinator cleans the worktree and reruns.
- [A child's restack pushes, then the next queued issue is that child and GitHub lags] → Decision 4 covers it: the remote equals local `HEAD`, so the queue waits.
- [Several children, one conflicts] → Earlier children are restacked and cleared, so a rerun skips them. The parent stays until every child is restacked or abandoned.
- [A child restacked but not in the batch has no checks yet] → Its PR CI runs on the push. The SKILL text tells the coordinator to run checks before queueing it.
