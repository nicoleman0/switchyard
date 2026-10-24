# Design

## Context

`teardown-worktree.sh` finds the worktree path by matching `branch refs/heads/<branch>` in `git worktree list --porcelain`, and exits 1 when nothing matches. After that, `set -e` aborts on the first failing step, so a missing local branch (`git branch -D`) also stops it before the record is removed. A missing remote branch is already tolerated, silently.

Checked on git 2.54 with a scratch repo: when a worktree folder is deleted by hand, `git worktree list --porcelain` still lists it with a `prunable` line, `git -C <path> status` fails with exit 128, and `git worktree remove <path>` removes the stale entry and exits 0.

The record (`.switchyard/state/<issue>.json`) holds `branch` and `path`. Teardown already succeeds without a record (`test_teardown_without_record_succeeds`), so the record cannot be required.

## Goals / Non-Goals

**Goals:**
- Teardown finishes and removes the record whatever subset of worktree, local branch, and remote branch is already gone.
- Each skipped step is named on stdout.

**Non-Goals:**
- Changes to merge, setup, or `--abandon` beyond skipping missing steps.
- Finding out what removed the worktrees in #53 and #54.

## Decisions

### Detect each step's state before acting

- Worktree: present when the git entry exists and its folder is a directory. Gone when there is no entry, or when the folder is missing (stale entry).
- Local branch: `git show-ref --verify --quiet refs/heads/<branch>`.
- Remote branch: the existing `ls-remote --exit-code` check, with a skip message added.

Each skip prints one line, for example `Skipped: worktree for topic is already gone.` The final line lists what was removed instead of the fixed `Removed worktree ... (local and remote).`

Alternative: drop `set -e` around each step and ignore failures. Rejected: it would also hide real failures, such as a branch checked out elsewhere.

### Dirty check only on a worktree that exists

The `git status` preflight runs only when the folder exists. Under `--abandon`, the uncommitted-files report is replaced by a line saying the folder is gone, and the local-only commits report runs only when the local branch exists.

### Down hook still runs when the worktree is gone

Per-issue state such as a database or container outlives the folder, and the hook is the only thing that removes it. Skipping it would leak that state. `WORKTREE` is set to the git entry's path, else the record's `path`, else empty. The hook already runs from the main checkout, so it does not need the folder. A hook failure still stops teardown with the record kept, as today.

Alternative: skip the hook when the folder is gone. Rejected for the leak above.

### Stale git entry removed with `git worktree remove <path>`

It removes only that entry. `git worktree prune` would also prune other issues' stale entries, which this script does not own.

### Pending coordinator answers

The tasks follow the recommended answer to each question below. A different answer changes the named task only.

1. Where the tests go (task 2.1).
2. Whether a record whose `branch` differs from the argument stops teardown (task 1.1).
3. What happens on the Herdr runner when the folder is gone (task 1.3).
4. Whether `SKILL.md` and the `worktree-down.sh` header are updated (task 3.2).

## Risks / Trade-offs

- [A typo in `<branch>` now looks like "everything already gone" and would remove the record of a live issue] → Refuse before any change when the record's `branch` differs from the argument (question 2).
- [Hooks that `cd "$WORKTREE"` will fail when the folder is gone] → The hook failure keeps the record, so nothing is half torn down. The hook header says the folder may be gone (question 4).
- [Herdr may still list an open workspace for a branch whose folder is gone; its behaviour on `worktree remove` in that state is unverified] → Do not call Herdr when the folder is gone (question 3).
