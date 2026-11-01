# Proposal

Delivers issue #134, "The merge queue stops at a stacked parent".

## Why

After #119 and #121, `merge-queue.py` merges a stacked parent and then stops at teardown, which refuses while a child names the parent. The coordinator must run `restack.sh` by hand and rerun the queue. Separately, right after a push GitHub's `headRefOid` can lag, so the queue's head check stops with "local head differs" and a rerun seconds later passes. A restack pushes the child just before the queue reaches it, so the integration would hit that lag every time.

## What Changes

- After a parent merges, and before its teardown, the queue finds every record whose `parent` is that issue and runs `scripts/restack.sh <child>` for each, in issue order. This also runs on the "already merged" path, so a rerun after a manual merge restacks too. Children are restacked whether or not they are in the batch.
- A failed restack stops the queue with exit 1 and names the child. The parent is not torn down. A rerun restacks only the children that still name the parent.
- The queue validates the batch before any action: a queued child whose parent is not queued before it exits 2.
- Before rebasing, when local `HEAD` differs from the PR's `headRefOid` but equals the remote branch head, the queue polls the PR head for up to 60 seconds, capped by `--timeout`, before it stops. When the remote branch differs from local `HEAD`, it stops at once, as now.
- `switchyard/SKILL.md`: Several PRs and Stacked issues say the queue restacks children, and drop "do not queue a child with its parent".
- `CHANGELOG.md`: one line under Unreleased.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`, as every workflow change in this repo does. `openspec/specs/` ships empty.

## Impact

- `switchyard/scripts/merge-queue.py`: restack step before teardown, batch order check, head lag wait.
- `switchyard/scripts/test_merge_queue.py`: `gh` stub learns `pr edit` and `pr list --jq`; new tests.
- `switchyard/SKILL.md`: Several PRs and Stacked issues sections only.
- `CHANGELOG.md`: one line.
- `switchyard/scripts/restack.sh`, `teardown-worktree.sh`: no change. The queue calls them as they are.
- `README.md`: no change. No README text covers the queue and stacks.
