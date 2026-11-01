# Proposal

Delivers GitHub issue #124.

## Why

#79 records each phase from session start to session end. A planner's time includes the coordinator's plan review and the maintainer's answers, and a passing reviewer's time runs until teardown. The report cannot tell worker time from time spent waiting on the coordinator.

## What Changes

- Each phase in the issue record gains a `turns` list. Each turn holds a `started` and an `ended` time, in the same UTC format as phases.
- `state.py phase-start` opens the phase's first turn at the phase's start time.
- New `state.py turn-end <issue>`: closes the open turn of the open phase. The coordinator runs it when a worker's wait returns. No open turn is a no-op, exit 0.
- New `state.py turn-start <issue>`: opens a new turn on the open phase. The coordinator runs it before it prompts or unblocks a worker whose turn has ended. An open turn is a no-op, exit 0. No open phase exits 1.
- Closing a phase (next `phase-start`, `phase-end`, `archive`) also closes its open turn at the same time.
- `state.py timings`:
  - With an issue: each phase line adds `BUSY` (sum of its turns) and `WAIT` (phase time minus busy). The summary line adds `Busy:`.
  - Without an issue: the issue rows add `BUSY`; the provider, model, and role rows add `BUSY`.
  - A phase with no `turns`, such as one archived before this change, shows `-` and adds nothing to busy totals.
- `switchyard/SKILL.md`, Batch state section: say when to run `turn-end` and `turn-start`, and replace the sentence that says times include waits.
- No change to `start-worker.sh`, `end-worker.sh`, `wait-agents.sh`, the runner files, or teardown. `archive` already copies phases, so history lines carry turns.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty in this repo, so the change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- `switchyard/scripts/state.py`: `turn-start`, `turn-end`, `close_phases`, `phase-start`, `timings`, usage line.
- `switchyard/scripts/test_state.py`: new tests.
- `switchyard/SKILL.md`: Batch state section only.
- `CHANGELOG.md`: one line under Unreleased.
- Record and history format: phases gain an optional `turns` list. Older records and history lines still read.
