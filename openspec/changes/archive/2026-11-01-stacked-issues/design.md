# Design

## Context

- `setup-worktree.sh <issue> <branch>` branches from the main checkout's current branch (`git symbolic-ref --short HEAD`), with `herdr worktree create --base` or `git worktree add`. It writes the record with `state.py init`, which accepts any `key=value`, so new fields need no `state.py` change.
- `teardown-worktree.sh` deletes the worktree, the local branch, and the remote branch. It makes no `gh` calls.
- `check-scope.sh` and `roles/reviewer.md` diff `origin/main...HEAD`. On a child branch that range includes the parent's commits.
- PRs are squash-merged (`CONTRIBUTING.md`), so the parent's commits never reach `main` as they are.
- I could not confirm from GitHub's docs whether deleting a merged PR's head branch with `git push --delete` retargets PRs based on it. The page on changing a PR's base does not say. The design does not rely on it.

## Goals / Non-Goals

**Goals:**
- A dependent issue starts before the issue it builds on merges, when the maintainer names it.
- The child's history is correct after the parent squash-merges.
- No path silently closes the child's PR.

**Non-Goals:**
- Stacks deeper than one level.
- Following the parent's later commits into the child before the parent merges. The child stays on `parent_head` until restack.
- Changing `state.py status` output to show the parent.
- Teaching `merge-queue.py` (#121) about stacks. See decision 6.

## Decisions

1. **`--parent <issue>`, not a raw base branch.** The coordinator note says setup takes a base branch. Taking the parent's issue number instead lets setup read the parent's branch from its record, refuse a missing or stacked parent, and record `parent`. Alternative: `--base <branch>`. It cannot check one level and records less.
   Usage: `setup-worktree.sh [--parent <issue>] <issue> <branch>`, the leading-option style `teardown-worktree.sh` already uses.

2. **Record `parent_head` at branch time and rebase with `--onto`.** `parent_head=$(git rev-parse refs/heads/<parent_branch>)`. Pass that captured commit as the base ref to both runners so the worktree and record agree if the parent branch moves during setup. After the squash merge, `git rebase --onto origin/main <parent_head>` replays only the commits after `parent_head`. This holds even when the parent gained fix-round commits or was rebased onto `main` after the child branched. Alternative: `git merge-base child parent_branch` at restack time. It goes wrong once the parent branch is rebased, and the parent's branch is gone after teardown.

3. **Restack in a script.** `restack.sh <issue>` runs from the main checkout:
   - reads `path`, `branch`, `parent_branch`, `parent_head` from the record, and exits 2 when `parent_head` is empty;
   - require a clean child worktree on its recorded branch, with no rebase in progress and `parent_head` still an ancestor; a retry after a completed rebase stops and names the remaining manual steps;
   - `git fetch origin`, then in the child worktree `git rebase --onto origin/main <parent_head>`;
   - on conflict, aborts the rebase, prints the conflicted files, and exits 1, so the coordinator resolves them by hand (with `union-resolve.py` for append-only files) and runs the script's remaining steps;
   - when the remote branch exists, `git push --force-with-lease origin <branch>`;
   - when an open PR exists for the branch, `gh pr edit <branch> --base main`;
   - clears `parent`, `parent_branch`, `parent_head` with `state.py set`.
   It runs no checks. The coordinator runs `pre-review.sh` or the Merge and clean up checks after, as for any rebase. Alternative: the same steps as SKILL text. That leaves five hand steps per stack and gives #121 nothing to call.

4. **Teardown refuses while a child names the issue.** Before any removal, teardown scans `.switchyard/state/*.json` for a non-empty `parent` equal to the issue, and exits 1 naming each child. This covers `--abandon` too: a child of an abandoned parent needs a decision (abandon it, or restack it on `main` and drop the parent's work). Alternative: teardown retargets the child's PR to `main` itself before deleting the remote branch. That adds `gh` calls to teardown and is wrong for an abandoned parent.

5. **Scope diffs from `parent_head`.** `check-scope.sh` reads `parent_head` from the record and diffs `<parent_head>...HEAD` when it is set, `origin/main...HEAD` otherwise. `state.py get` exits non-zero on an empty field, so the script falls back on that status. The reviewer role keeps `origin/main...HEAD`; the brief for a child tells the reviewer to use `<parent_head>...HEAD`, through the coordinator notes.

6. **Where this meets #121.** `merge-queue.py` processes issues in order: rebase onto `origin/main`, gate, push, CI, merge, teardown. For a stacked pair it would merge the parent, then stop on decision 4's refusal at teardown. That stop is loud and safe. The Stacked issues section says: do not queue a child with its parent; after the parent merges, run `restack.sh` on the child, then rerun the queue for the parent (it sees `MERGED` and tears down) and the child. A follow-up can make the queue call `restack.sh` between merge and teardown. #114, #118, #124 do not touch these scripts' base logic; #114's per-role fields and #124's turn times are separate keys in the same record.

7. **One level.** Setup refuses `--parent X` when X's record has a non-empty `parent`. Several children on one parent fall out for free.

## Risks / Trade-offs

- [The parent changes after the child branches] → The child keeps the old `parent_head`. Restack replays only the child's commits onto the merged parent, so conflicts show up there, where the coordinator resolves them. The Stacked issues section says to stack only once the parent's review has passed, to keep this rare.
- [The child's PR on GitHub shows parent commits while the parent is rebased or after a retarget] → Cosmetic until restack, which runs right after the parent merges.
- [A stale record names a torn-down parent] → Teardown removes the parent's record, and `restack.sh` needs only `parent_head`, which is a commit, not a branch. Restack still works after the parent's branch is gone.
- [Conflicts during restack] → The script aborts and stops with the files, leaving the branch as it was.

## Approved plan review

- Add `restack.sh` and change `check-scope.sh` within the approved scope.
- Stack only after the parent review passes.
- Refuse parent teardown in both modes until children are restacked or abandoned.
- Keep merge-queue integration in a coordinator-owned follow-up.
