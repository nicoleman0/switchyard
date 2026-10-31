# Proposal

Delivers issue #123, "A stuck worker is waited on forever".

## Why

`wait-agents.sh` returns only when a watched agent is `idle`, `done`, `blocked`, or `unknown`. A worker looping on a failing test or hung on a command keeps the coordinator waiting with no limit. The coordinator needs the wait to end on a deadline, with a report naming the agents that ran past it and a different exit status so it can branch without parsing output.

## What Changes

- `wait-agents.sh` takes `--timeout <seconds>`, accepted before or after the agent names, and also as `--timeout=<seconds>`. Without the flag the script behaves exactly as before.
- The script counts the wait from its start. When the wait reaches the timeout, it prints one line per watched agent still working, `name status elapsed` with elapsed in seconds, and exits `4`.
- `4` is new. The script's existing outcomes keep their statuses: `0` on an agent needing the coordinator, `3` meaning still working while it loops, `1` for an unknown name or a failed `herdr agent list`, and `2` for a bad `--timeout` value.
- Elapsed time is bounded: `herdr agent list` has no start timestamp, so the script measures from when the wait began. If the coordinator starts the wait soon after the worker starts, as it does in the Herdr runner flow, the number is close to how long the agent has worked. See design.md, decision 2.
- `switchyard/runners/herdr.md` documents the flag and the `4` status in the Wait row and the paragraph below it.
- `switchyard/SKILL.md` step 6, Watch, tells the coordinator what to do on a timeout: read the pane, then nudge, end, or reassign. Two or three lines, in the existing style.
- `CHANGELOG.md` is not touched: the brief does not list it among the owned paths for this issue. See design.md, decision 5.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`, as every earlier workflow change did. `openspec/specs/` ships empty, so the workflow's own rules live in `SKILL.md` and the runner files.

## Impact

- `switchyard/scripts/wait-agents.sh`: argument handling, timeout check, timed-out report. No change to the polling states or the no-flag loop.
- `switchyard/runners/herdr.md`: Wait row and the `wait-agents.sh` paragraph.
- `switchyard/SKILL.md`: step 6, Watch, only.
- No change elsewhere. `routing.md` names the script but needs no text change for a new optional flag; it is outside this issue's owned paths.
