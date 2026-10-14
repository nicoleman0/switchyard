# Proposal

## Why

When an issue is stopped before its worktree is clean, normal teardown can run the down hook and then fail to remove the checkout. The coordinator has to finish cleanup by hand, and the skill does not explain how to discard abandoned work safely.

## What Changes

- Add an explicit `--abandon` mode to worktree teardown that reports uncommitted files and local-only commits before discarding them.
- Make ordinary teardown reject dirty worktrees before running hooks or changing branches, records, or worktrees.
- Document when and how to abandon an issue.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`. Switchyard is a template, and `openspec/specs/` ships empty to every project made from it, so teardown rules live in the skill and its scripts. The scripts' tests are the acceptance check.

## Impact

Changes are limited to `teardown-worktree.sh`, its tests in `test_state.py`, the work-issues skill, the changelog, and this OpenSpec change. The Herdr runner's dirty-worktree removal behavior was checked on a scratch worktree from the main checkout; the result is recorded in the design.
