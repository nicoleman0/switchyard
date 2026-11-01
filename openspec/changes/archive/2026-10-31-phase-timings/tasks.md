# Tasks

## 1. Record phases

- [x] 1.1 In `state.py`, add `phases` and `archived` to the reserved field names in `fields()`. Verify `state.py set 8 phases=x` exits 1 with one stderr line.
- [x] 1.2 Add `state.py phase-start <issue>` and `state.py phase-end <issue>` as design.md describes, with UTC `YYYY-MM-DDTHH:MM:SSZ` times. Verify with the tests in 4.1.
- [x] 1.3 In `start-worker.sh`, call `python3 "$state" phase-start "$issue"` right after the existing `state.py set` line, before the blocked exit. Verify with the tests in 4.1.
- [x] 1.4 In `end-worker.sh`, call `python3 "$state" phase-end "$issue"` before the `exit 0` on the "no agent to end" path and before `printf 'ended=%s\n'`. Leave the headless refusal unchanged. Verify with the tests in 4.1.

## 2. Archive at teardown

- [x] 2.1 Add `state.py archive <issue> [--abandon]` as design.md describes: close an open phase, read rounds and verdict from `<path>/.switchyard/reviews/`, append one line to `.switchyard/history.jsonl` in the main checkout, set `archived`. Skip when `archived` is already set. Verify with the tests in 4.2.
- [x] 2.2 In `teardown-worktree.sh`, when `has_record` is set, run `python3 switchyard/scripts/state.py archive "$issue"` (with `--abandon` when abandoning) after the `--abandon` report and before the down hook. Change nothing else in the file. Verify with the tests in 4.2.

## 3. Report

- [x] 3.1 Add `state.py timings [issue]` with the output in design.md: per-phase lines, rounds, verdict, and total for one issue; per-issue rows and per provider, model, and role totals with no issue. Read the model from the row as design.md describes. Update the usage line in `command()`. Verify with the tests in 4.3.

## 4. Tests in `test_state.py`

- [x] 4.1 Phases:
  - `start-worker.sh` on headless with `planner_row` set records one open phase with role, provider, row, and `started`.
  - A second `start-worker.sh` closes the first phase and opens another.
  - `start-worker.sh` exiting 3 at a blocked Herdr start still opens a phase.
  - `end-worker.sh` sets `ended` on the `ended=` path and the no-agent path, and leaves the phase open when it refuses a working agent or times out.
  - `phase-end` with no open phase exits 0 and changes nothing. `phase-start` with no `role` exits 1.
- [x] 4.2 Archive:
  - Teardown of an issue with phases and two review files appends one history line with the phases, `rounds: 2`, the second file's verdict, and every phase closed. The record is gone.
  - A record that already has `archived` adds no line.
  - `--abandon` writes `abandoned: true`.
  - Teardown with no record writes no history.
- [x] 4.3 Report, using records and history written with fixed times:
  - `timings <issue>` prints each phase's role, provider, model (`--model`, `-m`, `default`, `-`), and duration, then rounds, verdict, and total.
  - An open phase prints `running`.
  - `timings` with no issue lists a history issue and a live issue once each, and sums time per provider, model, and role.
  - A bad history line prints `Cannot read history line` on stderr and the rest still prints.
  - No records and no history prints `No timings recorded.`
  - Durations format as `45s`, `42m`, `1h10m`.
  Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`.

## 5. Docs

- [x] 5.1 In `switchyard/SKILL.md`, append to the Batch state section only: `start-worker.sh` and `end-worker.sh` record when each phase starts and ends. `python3 switchyard/scripts/state.py timings [issue]` prints time per phase, review rounds, and the verdict. Teardown appends each issue's summary to `.switchyard/history.jsonl`, so the report covers finished issues. Short sentences, no em-dashes.
- [x] 5.2 As approved in `.switchyard/answers/plan.md`, add `- #79: \`state.py timings\` reports time per phase, provider, and model, with review rounds and the verdict. Teardown keeps a summary in \`.switchyard/history.jsonl\`.` under Unreleased, in an `### Added` section of `CHANGELOG.md`. Append only.

## 6. Repository checks

- [x] 6.1 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 6.2 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 6.3 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` passes.
- [x] 6.4 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 6.5 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
