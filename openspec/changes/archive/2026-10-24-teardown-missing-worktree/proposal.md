# Proposal

## Why

Issue #56: `teardown-worktree.sh <issue> <branch>` exits 1 with `No worktree has branch <branch> checked out.` when the worktree is already gone. It stops before `state.py rm`, so the record in `.switchyard/state/<issue>.json` stays and the coordinator has to clear it by hand.

## What Changes

- Teardown checks each step before it runs it: worktree, local branch, remote branch. A step that is already done is skipped and reported on stdout. The record is still removed.
- A worktree whose folder is gone but whose git entry remains is treated as gone: no dirty check, and only the stale git entry is removed.
- The down hook still runs when the worktree is gone, because per-issue state such as a database can outlive the folder. `WORKTREE` is the last known path, which may not exist.
- A dirty worktree that exists still stops ordinary teardown before anything changes. `--abandon` keeps its current behaviour and skips the same missing steps.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`. Switchyard is a template and `openspec/specs/` ships empty, so teardown rules live in the skill and its scripts. The script's tests are the acceptance check.

## Impact

- `switchyard/scripts/teardown-worktree.sh`
- New tests for the missing-step cases (location is an open question in the design).
- `CHANGELOG.md`, one `Fixed` line under Unreleased.
