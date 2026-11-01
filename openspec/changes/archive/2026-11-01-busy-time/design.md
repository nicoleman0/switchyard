# Design

## Context

- `state.py` keeps `phases` in `.switchyard/state/<issue>.json`: `{"role", "provider", "row", "started", "ended"}`. `start-worker.sh` calls `phase-start`. `end-worker.sh` calls `phase-end` on Herdr. Headless phases close at the next start or at teardown. `archive` copies `phases` into `.switchyard/history.jsonl`.
- A worker session can run several turns. The fast-path implementer stops with questions and is prompted again after the coordinator writes `answers/plan.md` (SKILL.md, Per issue, step 3). Any worker can stop blocked or with a report the coordinator answers (step 6).
- The coordinator learns a turn is over in a different way per runner:
  - Herdr agents: `wait-agents.sh` returns when the agent is `idle`, `done`, `blocked`, or `unknown`. It polls every 15 seconds.
  - Herdr turns providers (opencode): the `TURN-DONE` marker in the pane.
  - Headless: the turn command exits.
- Herdr's agent list has no timestamps (design of #79).

## Goals / Non-Goals

**Goals:**
- Busy and wait time per phase, per issue, and per provider, model, and role.
- One mechanism that works on both runners and every provider, with no per-provider parsing.

**Non-Goals:**
- Exact busy time. The recorded end of a turn is when the coordinator notices it, not when the worker stopped.
- Edits to `start-worker.sh` and `end-worker.sh` (#114 changes them in parallel), the runner files, or `routing.md`.
- Wait time split by cause (coordinator vs maintainer).

## Decisions

### The coordinator marks turn ends with `state.py`

The coordinator runs `state.py turn-end <issue>` as soon as a worker's wait returns, before it reads the report. It runs `state.py turn-start <issue>` before it prompts or unblocks a worker in the same session.

This is the only signal that every runner and provider share: the coordinator always learns that a turn ended, since it must read the report. It needs no parsing and no file conventions.

Alternatives:
- (b) Each role's handoff file mtime: the change folder, `pr-body.md`, the newest review. Rejected:
  - A question turn writes no handoff file, so multi-turn phases are lost.
  - The files move or change after the phase. The implementer archives the change, and the coordinator fills the Review section of `pr-body.md` before the PR.
  - It spreads knowledge of each role's handoff files into `state.py`.
- (c) `wait-agents.sh` records the end on Herdr. Rejected as the only mechanism: it misses headless and Herdr turns providers, so the coordinator would still need (a) there. Two mechanisms for one fact. It would be more precise on Herdr (within 15 seconds). See question 3 in the plan summary.

### Turns live inside each phase

`phase["turns"]` is a list of `{"started", "ended"}`, with `ended` absent while open. `phase-start` writes the first turn with the phase's own `started` time. Nesting keeps one record per phase, so `archive` and history need no change, and `set` cannot overwrite it (`phases` is already reserved).

Alternative: a flat `done` time per phase. Rejected: it counts the wait between a question and its answer as busy.

### Command behaviour

- `turn-end <issue>`: sets `ended` on the open turn of the open phase. No open phase or no open turn: no-op, exit 0. Reading a report twice must not fail.
- `turn-start <issue>`: appends `{"started": now}` to the open phase's turns. An open turn already: no-op, exit 0, because the worker is still busy. No open phase: exit 1 with `Issue <n>: no open phase. Start the worker with start-worker.sh`. A prompt into a session with no phase is a coordinator mistake worth surfacing.
- `close_phases`: also sets `ended` on an open turn of a phase it closes, at the same time. A forgotten `turn-end` then yields busy equal to session time, which is today's number, never more.

### Busy and wait in the report

- Phase busy: sum of its turns, with an open turn counted to now. Phase wait: phase time minus busy.
- A phase with no `turns` key shows `-` for BUSY and WAIT and adds nothing to any busy sum. Only phases recorded before this change lack it.
- Issue busy: sum of phase busy, open turns to now, as TOTAL counts open phases to now. `-` when no phase has turns.
- Provider, model, and role rows: busy over closed phases, as TIME already uses. `-` when none of them has turns.

```
ROLE         PROVIDER  MODEL    STARTED               TIME        BUSY   WAIT
planner      claude    opus     2026-10-31T10:00:00Z  42m         18m    24m
implementer  codex     default  2026-10-31T11:05:00Z  1h10m       1h02m  8m
reviewer     claude    opus     2026-10-31T12:20:00Z  running 5m  5m     0s
Rounds: 1  Verdict: pass  Busy: 1h25m  Total: 2h25m
```

The no-issue report adds `BUSY` after `TOTAL` on issue rows and after `TIME` on provider rows. Durations use the existing `duration()` format. Columns go at the end so existing column positions stay.

### Docs live in the Batch state section

The brief limits SKILL.md edits to Batch state. That section gets the two commands and when to run them, and the sentence "These times measure open sessions, including waits." is replaced, since it becomes wrong. Step 6 (Watch) and the runner files' Prompt and Read verbs are where a coordinator acts. Adding one clause there is question 1.

## Risks / Trade-offs

- [Coordinator latency counts as busy] Up to 15 seconds of polling on Herdr plus the coordinator's own reaction. → Run `turn-end` first, before reading. Minutes-scale phases make this small.
- [Coordinator forgets `turn-end`] Busy falls back to session time for that turn. → Safe upper bound; `close_phases` closes it.
- [Coordinator forgets `turn-start`] The later turn's busy time is lost and counts as wait. → Documented next to `turn-end`. Question 1 puts it where prompts happen.
- [Mixed history] Aggregates over a mix of old and new phases show BUSY over fewer phases than TIME. → Only history from before this change. Accepted.
