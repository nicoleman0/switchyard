# Proposal

Delivers issue #119, "Issues that share files run one after another".

## Why

Issues that touch the same files run in series: the second starts only after the first merges. With a review and a merge wait per PR, this serialises whole batches. The maintainer wants an opt-in way to start the dependent issue early, on top of the one it builds on.

## What Changes

- Stacking is opt-in. The coordinator stacks two issues only when the maintainer names it in the session. The default stays: issues that share files run one after another.
- `setup-worktree.sh` takes `--parent <issue>`. The new worktree branches from the parent issue's branch, not the checkout's branch. The child's record gets `parent`, `parent_branch`, and `parent_head` (the parent branch's commit at branch time).
- One level only. `setup-worktree.sh --parent` refuses when the parent issue has no record or is itself stacked. Several children on one parent work, since each records its own `parent_head`.
- The child's PR targets the parent's branch (`gh pr create --base <parent_branch>`).
- After the parent squash-merges, the child is restacked: `git rebase --onto origin/main <parent_head>` replays only the child's commits, then the branch is force-pushed with a lease, the PR is retargeted with `gh pr edit --base main`, and the parent fields are cleared from the record. A plain rebase would replay the parent's commits, which the squash rewrote.
- New `switchyard/scripts/restack.sh <issue>` runs those steps. It stops with the conflicted files when the rebase conflicts.
- `teardown-worktree.sh` refuses, with or without `--abandon`, while another record names the issue as its parent. Deleting the parent's remote branch would otherwise close the child's PR. The message names the child and says to restack or abandon it first.
- `check-scope.sh` diffs from `parent_head` when the record has one, so the parent's files do not count against the child's scope.
- `switchyard/SKILL.md`: Before starting step 2 points to a new short Stacked issues section, which gives the order: set up with `--parent`, open the PR on the parent's branch, merge the parent, restack, then tear the parent down.
- `CHANGELOG.md`: one line under Unreleased, Added.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`, as every workflow change in this repo does. `openspec/specs/` ships empty.

## Impact

- `switchyard/scripts/setup-worktree.sh`: `--parent` option, base branch, parent fields in the record.
- `switchyard/scripts/teardown-worktree.sh`: refusal while a child names the issue as parent.
- `switchyard/scripts/restack.sh`: new.
- `switchyard/scripts/check-scope.sh`: diff base from `parent_head`.
- `switchyard/scripts/test_state.py`: tests for the above.
- `switchyard/SKILL.md`: Before starting step 2, and a new Stacked issues section after Several PRs.
- `CHANGELOG.md`: one line.
- `README.md`: no change. No README text describes the series rule.
- Meets in-flight work: #121 `merge-queue.py` rebases with a plain `git rebase origin/main` and tears down after merge. With this change, its teardown of a parent stops on the refusal, and its rebase of a child would be wrong. See design.md, decision 6.
