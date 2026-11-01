# Design

## Context

- The record at `.switchyard/state/<issue>.json` holds string fields. `start-worker.sh` overwrites `role`, `backend`, `worker`, and `session` at each phase. Teardown deletes the record.
- The coordinator records `planner_row`, `implementer_row`, and `reviewer_row` (`<provider> <flags>`) before it starts each worker (SKILL.md, Per issue, steps 3, 5, 7).
- `end-worker.sh` runs on Herdr only. Headless's End verb is "Nothing to do".
- The SKILL ends each session just before the next phase starts. The planner ends at step 5, after plan review. A passing reviewer ends just before teardown.
- The reviewer writes `.switchyard/reviews/<n>.md`, first line `Verdict: pass` or `Verdict: changes requested`.
- Herdr's agent list has no timestamps. Neither runner exposes token counts to a script without changing the worker command.

## Goals / Non-Goals

**Goals:**
- Time per phase, per role, provider, and model, for live and finished issues.
- Review rounds and the final verdict per issue.
- No provider-specific code, no change to the runner files or `routing.md`.

**Non-Goals:**
- Tokens and cost.
- Time a worker spent busy, as opposed to the time its session was open. See Risks.
- Changes to `state.py status`.

## Decisions

### Phases live in the record as a list

`phases` is a JSON list of `{"role", "provider", "row", "started", "ended"}`. `ended` is absent while the phase is open. `row` is the record's `<role>_row` at start, or `""`. Keeping it in the per-issue record follows the existing pattern and needs no new file per issue. `set` and `init` reject `phases` so a string cannot overwrite the list.

### Two new state.py commands keep the shell scripts thin

- `state.py phase-start <issue>`: reads `role` and `backend` from the record, closes an open phase at now, appends the new one. Fails when `role` or `backend` is empty.
- `state.py phase-end <issue>`: sets `ended` on the open phase. No open phase is a no-op, exit 0.

Reading role and provider from the record, rather than passing them again, keeps one source for them. `start-worker.sh` calls `phase-start` right after its `state.py set`, so a blocked start (exit 3) still opens a phase. `end-worker.sh` calls `phase-end` on its two success paths: `ended=<worker>` and "there is no agent to end".

### Headless closes a phase at the next start or at teardown

The headless runner has no end step, and the SKILL ends sessions just before the next phase anyway. On Herdr, `end-worker.sh` runs at that same point. Closing at the next start therefore gives the same numbers on both runners, with no edit to `runners/headless.md` and no change to `end-worker.sh`'s headless refusal. Alternatives: let `end-worker.sh` record on headless and add it to the headless End verb (a shared-file edit for no gain in accuracy); use the newest turn log's mtime (headless only, depends on log names the coordinator picks).

### Model comes from the recorded row

The report reads the model from the phase's `row`: the value after `--model`, `--model=`, or `-m`. Those cover every provider note in `routing.md`. A row with none shows `default`. No row shows `-`. Alternative: a `model=` field the coordinator sets. Rejected for now: it adds a step to SKILL sections this issue does not own.

### Rounds and verdict come from the review files

Rounds is the count of `<n>.md` files in `<path>/.switchyard/reviews/`. The verdict is the first line of the highest-numbered file, with `Verdict: ` removed. A missing folder shows `-` for both. The review files are the reviewer's handoff on every provider and runner, so this needs no new step. Counting reviewer phases instead would count a restarted reviewer twice.

### Teardown archives before it removes anything

`state.py archive <issue> [--abandon]`:
1. closes an open phase at now,
2. reads rounds and verdict from the worktree,
3. appends one JSON line to `<main checkout>/.switchyard/history.jsonl`: `issue`, `branch`, `plan_size`, `size`, `phases`, `rounds`, `verdict`, `abandoned`, `archived` (time),
4. sets `archived` in the record.

A record that already has `archived` is skipped, so a teardown that fails later and is run again does not append twice. Teardown calls it once it has decided to proceed: after the dirty-worktree refusal and the `--abandon` report, before the down hook, and only when a record exists. It must run before the worktree is removed, because the review files live there. This is one inserted block, not an append at the end of the file.

Abandoned issues are archived with `abandoned: true`, because their time was still spent. The report shows `abandoned` as their verdict.

### The report

`state.py timings <issue>` reads the live record, or the issue's newest history line when there is no record. Output:

```
ROLE         PROVIDER  MODEL    STARTED               TIME
planner      claude    opus     2026-10-31T10:00:00Z  42m
implementer  codex     default  2026-10-31T11:05:00Z  1h10m
reviewer     claude    opus     2026-10-31T12:20:00Z  running 5m
Rounds: 1  Verdict: pass  Total: 2h25m
```

`state.py timings` with no issue: one row per issue (`ISSUE SIZE ROUNDS VERDICT TOTAL`) from history lines and live records without `archived`, then one row per provider, model, and role (`PROVIDER MODEL ROLE PHASES TIME`) summing closed phases. Total is first `started` to last `ended`, or to now while a phase is open. Durations print as `Ns` under a minute, `Nm` under an hour, else `NhMMm`. A history line that is not valid JSON prints `Cannot read history line <n>: <error>` on stderr and is skipped, as `status` does for records. No records and no history prints `No timings recorded.`

### Tokens and cost are left out

No CLI in `routing.md` reports them cheaply in the runs Switchyard makes. Interactive Herdr agents print usage only to the screen. Headless `claude -p` and `codex exec` report usage only with JSON output, which changes the report the coordinator reads, and each needs its own parser. Provider-specific parsing in the scripts goes against CONTRIBUTING.md's "No provider is special". A later issue can add a project-owned hook if a provider exposes usage in a file.

## Risks / Trade-offs

- [Session time, not busy time] The planner's time includes plan review and the maintainer's answers. A passing reviewer's time runs until teardown. Implementer times and changes-requested reviewer times are close to work time, since the SKILL ends those sessions when they report. → The report labels the column TIME, and the design states what it measures. Approved: keep session time. The coordinator will open a follow-up issue for busy time.
- [Clock] Times come from the coordinator machine's clock. All writes run there, so durations are consistent.
- [History grows without bound] One short line per issue. Accepted.
- [Record written twice per start] `set` then `phase-start`. Only the coordinator writes records, so there is no race.
