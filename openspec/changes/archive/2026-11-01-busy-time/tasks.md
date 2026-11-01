# Tasks

## 1. Record turns

- [x] 1.1 In `state.py`, make `phase-start` write `turns: [{"started": <phase started>}]` on the new phase. Verify with the tests in 3.1.
- [x] 1.2 Make `close_phases` also set `ended` on an open turn of each phase it closes, with the same time. Verify with the tests in 3.1.
- [x] 1.3 Add `state.py turn-end <issue>` and `state.py turn-start <issue>` with the behaviour in design.md, Command behaviour. Write the record only when something changed. Add both to the usage line in `command()`. Verify with the tests in 3.1.

## 2. Report busy and wait

- [x] 2.1 In `timings <issue>`, add `BUSY` and `WAIT` columns after `TIME`, and `Busy: <d>` before `Total:` in the summary line, as design.md shows. A phase with no `turns` prints `-` in both columns. Verify with the tests in 3.2.
- [x] 2.2 In `timings` with no issue, add `BUSY` after `TOTAL` on issue rows and after `TIME` on provider, model, and role rows, with the sums in design.md. Verify with the tests in 3.2.

## 3. Tests in `test_state.py`

- [x] 3.1 Turns:
  - `start-worker.sh` on headless opens a phase with one open turn whose `started` equals the phase's.
  - `turn-end` closes it. A second `turn-end` exits 0 and leaves the record unchanged.
  - `turn-start` opens a second turn. `turn-start` with a turn open exits 0 and adds none.
  - A second `start-worker.sh`, and `phase-end`, close an open turn at the phase's `ended`.
  - `turn-start` with no open phase exits 1 with one stderr line. `turn-end` with no open phase exits 0.
- [x] 3.2 Report, using records and history written with fixed times:
  - A phase of 42m with turns of 10m and 8m prints `18m` busy and `24m` wait. The summary prints `Busy:`.
  - An open turn counts to now and the phase prints `running`.
  - A phase with no `turns` prints `-` for BUSY and WAIT.
  - The no-issue report prints issue BUSY and per provider, model, and role BUSY, and `-` where no phase has turns.
  - Existing assertions in `test_timings_fixed_times_models_and_totals` still pass.
  Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`.

## 4. Docs

- [x] 4.1 In `switchyard/SKILL.md`, Batch state section only, replace "These times measure open sessions, including waits." with short sentences: run `python3 switchyard/scripts/state.py turn-end <issue>` as soon as a worker's wait returns, before you read it; run `python3 switchyard/scripts/state.py turn-start <issue>` before you prompt or unblock the same session again. Name the report's BUSY and WAIT columns in the timings sentence. No em-dashes.
- [x] 4.2 Add `- #124: \`state.py timings\` splits each phase into busy and wait time. The coordinator marks turns with \`state.py turn-end\` and \`turn-start\`.` under Unreleased, `### Added`, in `CHANGELOG.md`. Append only.

## 5. Repository checks

- [x] 5.1 `switchyard/hooks/checks.sh` passes from the worktree root (py_compile, unittest, shellcheck, node --check).
- [x] 5.2 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
