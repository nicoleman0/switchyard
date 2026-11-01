# Proposal

Delivers GitHub issue #79.

## Why

Switchyard keeps no record of how long each phase of an issue took, on which provider and model, or how many review rounds it needed. A maintainer on several subscriptions cannot tell which provider delivers issues cheaply. The issue record is overwritten at each phase and removed at teardown, so nothing survives to compare.

## What Changes

- Each issue record gains a `phases` list. Each entry holds the role, the provider, the recorded row, a `started` time, and an `ended` time, in UTC ISO 8601 to the second.
- `start-worker.sh` opens a phase after it records the worker. Opening a phase closes any phase still open at the same moment.
- `end-worker.sh` closes the open phase when it ends an agent, or when there is no agent to end. Its failures and timeouts record nothing.
- Headless has no end step. Its phase closes when the next phase starts, or at teardown.
- New `state.py timings [issue]` report:
  - With an issue: one line per phase with role, provider, model, start, and duration, then review rounds, the final verdict, and the issue's total time.
  - Without an issue: one line per issue from live records and history, then time per provider, model, and role across them.
- Review rounds and the verdict come from `<worktree>/.switchyard/reviews/<n>.md`: the number of files, and the first line of the highest-numbered one.
- Teardown appends one summary line per issue to `.switchyard/history.jsonl` in the main checkout before it removes the worktree. The report reads it, so finished issues still count.
- `state.py set` and `init` reject `phases` and `archived` as field names, as they reject `issue`.
- Not included: tokens and cost. See design.md. README numbers stay with #30.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty in this repo, so the change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- `switchyard/scripts/state.py`: `phase-start`, `phase-end`, `archive`, `timings`, reserved fields.
- `switchyard/scripts/start-worker.sh`, `switchyard/scripts/end-worker.sh`: one call each.
- `switchyard/scripts/teardown-worktree.sh`: one `archive` call.
- `switchyard/scripts/test_state.py`: new tests.
- `switchyard/SKILL.md`: Batch state section only.
- `CHANGELOG.md`: one line under Unreleased, if the coordinator approves.
- New ignored file `.switchyard/history.jsonl` in the main checkout.
