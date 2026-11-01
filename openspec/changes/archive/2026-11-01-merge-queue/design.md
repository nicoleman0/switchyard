# Design

## Context

- Records in `.switchyard/state/<issue>.json` hold each issue's `branch` and `path`. `state.py` finds the main checkout as the first `git worktree list` entry.
- `setup-worktree.sh` disables the push URL in each worktree. Pushes run from the main checkout, which shares refs with the worktrees.
- `pre-review.sh <issue>` already runs the clean-tree, scope, archived-change, OpenSpec, and project checks on the worktree, and exits 0, 1, or 2.
- `teardown-worktree.sh <issue> <branch>` runs the down hook, removes the worktree and both branches, and removes the record. It refuses a dirty worktree.
- `union-resolve.py` keeps both sides of each two-sided hunk, upstream first. It fails on any other conflict shape, including the `|||||||` section that `merge.conflictStyle=diff3` or `zdiff3` adds.
- Every Switchyard project ships `.github/workflows/switchyard.yml`, which runs on `pull_request`, so every PR gets at least one check.
- Lessons from the last batch's manual queue:
  - The CHANGELOG conflicted on every merge, and a plain union duplicated `### Added`.
  - A one-line Python set literal (`PROJECT_OWNED`) conflicted and needed a hand merge.
  - `gh pr checks --watch` right after a push exited 1 before the check registered.
  - Claude Code's auto-mode classifier refused a background command that chained CI waits and merges, and allowed a standalone `gh pr merge`.

## Goals / Non-Goals

**Goals:**
- One command that takes passing PRs in merge order and runs the loop up to the merge.
- A stop that names the file or step, and leaves the branch as it was.
- Safe to run again with the same arguments after any stop.

**Non-Goals:**
- Deciding which PRs pass review or their order. The coordinator passes them.
- Pre-approval of merges. #113 owns the approval rule; this change adds only the `--merge` switch it can point at.
- Auto-merge (`gh pr merge --auto`). The queue already waits for CI.
- Resolving conflicts in code. Any file outside the append-only set stops the queue.
- Ending worker sessions. Ending is runner-specific; the coordinator ends them before the queue starts.

## Decisions

### Python, not shell

The loop parses `gh` JSON, polls with a deadline, and reports structured stops. Python does that without `jq` and is easier to test with a stub `gh` that returns JSON. It calls `pre-review.sh`, `union-resolve.py`, and `teardown-worktree.sh` as subprocesses, so each rule keeps one home. Python 3.10 syntax, like the other scripts.

### Input is issue numbers

`merge-queue.py <issue>...`, as every other script takes issues. The branch and worktree come from the record. The PR comes from `gh pr list --head <branch> --state all --json number,state,headRefOid,url`, newest first. An issue with no record exits 2 before any work. An issue with no PR, or a closed unmerged PR, stops the queue.

### Stop before merging by default; `--merge` merges

Without `--merge`, the first PR that is ready ends the run: the script prints `gh pr merge <pr> --squash --match-head-commit <sha>` and exits 3. The coordinator gets approval, runs that command on its own, and runs the queue again. The next run sees the merged PR, tears it down, and goes on.

Why:
- The Coordinator section requires explicit maintainer approval for each merge. A merge buried in a long script hides that approval point.
- The auto-mode classifier allowed a standalone `gh pr merge` and refused a chained one. Printing the command fits what it allows.
- A queue cannot rebase PR 2 until PR 1 has merged, so stopping at PR 1 is the natural break.

With `--merge`, the script merges, checks the PR now reads `MERGED`, tears down, fetches, and goes on. The coordinator passes it only when the maintainer pre-approved merges for the batch. A classifier may still refuse a background run with `--merge`; the default mode is the fallback.

`--match-head-commit` makes GitHub refuse the merge if the head moved after the checks passed.

### Which conflicts resolve

During a rebase, `CHANGELOG.md` at the repository root and `openspec/specs/*/spec.md` resolve with `union-resolve.py`. Any other conflicted file stops the queue. The list is fixed in the script: these are the files the workflow makes every PR append to. A project-owned list waits until a project needs one.

The rebase runs with `-c merge.conflictStyle=merge` so a user's `diff3` setting does not break `union-resolve.py`, and `-c rerere.enabled=false` so a recorded resolution cannot apply unseen. `rebase --continue` runs with `GIT_EDITOR=true`, in a loop, since each branch commit can conflict.

On a stop, the script runs `git rebase --abort`, so the branch and worktree are as they were. It prints the conflicted files it could not resolve and the reason (outside the append-only set, or not a plain two-sided append). The coordinator rebases by hand, commits, and runs the queue again; the queue's rebase is then a no-op.

### CHANGELOG subsections merge in `union-resolve.py`

After the union, when the text has a `## [Unreleased]` heading, the script merges that section's `### <name>` subsections: one heading per name, items in the order they appeared, upstream first. Known names follow Keep a Changelog order: Added, Changed, Deprecated, Removed, Fixed, Security. Unknown names follow them in first-seen order. Text between `## [Unreleased]` and its first `###` stays. Released sections are not touched.

It lives in `union-resolve.py`, not the queue, so the manual path and the queue share it. It keys on the heading, not the file name, so any Keep a Changelog file gets it. Outside a CHANGELOG, `## [Unreleased]` does not appear, so spec files keep the plain union.

### Branch safety before the rebase

Before rebasing, the script fetches `origin` and checks:
- The worktree has no tracked changes. Otherwise stop.
- The local branch head equals the PR's `headRefOid`. Otherwise stop: the local branch and the PR disagree, and a force-push would drop commits.

The push runs from the main checkout as `git push --force-with-lease=<branch>:<old head> origin <branch>`. The lease names the head the script saw, not the tracking ref the fetch just moved. When the rebase did not change the head, the script skips the push. If the push fails and the remote still has the old head, restore the local head with `git reset --keep` so the queue can retry. If the remote moved, leave the local head intact and stop for reconciliation.

### Checks after the rebase

The script runs `pre-review.sh <issue>`. Exit 0 goes on. Exit 1 or 2 stops and prints the gate's output, which ends with the log path. Every check that gates a review gates a merge, from one script. If the gate fails after a completed rebase, restore the original head with `git reset --keep`, provided HEAD is still the queue's rebased commit. Preserve any hook edits. This lets a clean failed gate be retried without a local/remote head mismatch.

### Waiting for CI

After the push, the script polls every 10 seconds:
1. until `gh pr view <pr> --json headRefOid` equals the pushed head;
2. until `gh pr checks <pr> --json name,bucket` lists at least one check (`gh` exits 1 with no checks reported; treat that as not yet);
3. until no check is `pending`.

Any `fail` or `cancel` bucket stops the queue and names the checks. `pass` and `skipping` count as passed. One `--timeout <seconds>` bound covers all three, default 1800. On timeout the script stops and says which wait ran out. The environment variable `SWITCHYARD_POLL_SECONDS` overrides the 10-second interval for tests.

### Output and exit codes

One line per step on stdout, prefixed with the issue, such as `#121 rebased onto origin/main (resolved CHANGELOG.md)`. A stop prints `STOP #<issue> PR #<pr>: <reason>` on stderr.

- 0: every issue merged and torn down.
- 1: stopped on a conflict or failure.
- 2: cannot run: bad arguments, an issue with no record, or `gh` or `git` failing outside a step.
- 3: a PR is ready and waits for a merge. The merge command is the last stdout line.

### SKILL.md

Several PRs replaces its throwaway-worktree text with the queue: how to run it, what exit 1 and 3 mean, when `--merge` is allowed, and to run it in the background when the CLI limits command time. The numbered rebase list under Merge and clean up becomes one line pointing at the queue. The approval paragraph above it stays as #113 leaves it.

## Risks / Trade-offs

- [The throwaway integration worktree goes away] → It found conflicts before approval. The queue tests each PR on the `main` it lands on, which the throwaway did not. See question 1 in the plan summary.
- [A release PR that renames Unreleased conflicts with feature PRs] → The union keeps both headings and the CHANGELOG step finds no clean Unreleased section to merge. The release-version CI check catches a broken heading. Merge release PRs alone.
- [Long CI waits exceed a CLI's command time limit] → SKILL says to run the queue in the background. `--timeout` bounds the wait.
- [`pre-review.sh` runs the main checkout's `checks.sh`] → After a PR that changes the hook merges, the next PR is gated by the main checkout's copy until the coordinator pulls `main`. CI on the PR still runs the new checks.
- [The reviewer saw the pre-rebase commit] → The rebase changes only what main brought in plus the resolved append-only files. A conflict anywhere else stops the queue for a person.
- [Codex as coordinator] → The queue runs `fetch`, `rebase`, and `push`, which `routing.md` says to request up front.
