# Tasks

## 1. Shared issue lookup (refactor only)

- [x] 1.1 In `tracker.py`, move `Linear.set_change`'s `issue(id) { id description }` lookup and its "Linear has no issue" error into one `Linear` method that returns the issue's fields, and call it from `set_change`. No behaviour change. Verify: `python3 -m unittest discover -s switchyard/scripts -p 'test_tracker.py'` passes with the test file unchanged.

## 2. Phases and statuses in tracker.py

- [x] 2.1 Add `PHASES`, the phase-to-default-status dict from design.md. Parse the optional `Phase | Status` table in `load_tracker` as design.md describes, and pass it to `Linear(statuses=...)`; a bad row raises `TrackerError` quoting the row and listing the phases. Verify: `test_tracker.py` tests that a table overrides one phase and keeps the others, that header and separator rows are skipped, and that an unknown phase, a repeated phase, and an empty status each exit 1 on `view` naming the row; a `tracker.md` with no table loads as today.
- [x] 2.2 Add `set-phase <issue> <phase>` with `choices` from `PHASES`. GitHub checks the key and returns. Linear reads the issue's team and states, matches the name exactly, runs `issueUpdate` with `stateId`, and fails on `success: false`, on `hasNextPage`, and on a missing status with the team name and its status names. Update the module docstring. Verify: tests with the recording transport: `building` sends the `In Progress` state id; an override table changes the id sent; a missing status exits 1 listing the team's statuses and sends no update; `done` exits 2 and calls nothing; `149` on Linear exits 2; GitHub `set-phase 150 building` exits 0, prints nothing, and runs no `gh` (use the existing `gh` stub's call log).
- [x] 2.3 Add `comment <issue> <file>`. Read the file first: missing, unreadable, or blank exits 1 before any call. GitHub runs `gh issue comment <n> --body-file <file>`. Linear sends `commentCreate` with the issue's UUID and the body, and fails on `success: false`. Verify: tests that Linear sends the UUID and exact body, that a blank file and a missing file exit 1 without a transport call, that GitHub calls `gh issue comment` with the file, and that a missing `LINEAR_API_KEY` exits 1 with `LINEAR_API_KEY is not set` for both `set-phase` and `comment`.
- [x] 2.4 Key agreement test from design.md: for each key in the fixed list that is not all digits, `state.valid_key` and the Linear key check agree. Verify: the test passes, and fails when one pattern is edited locally (check by hand, then revert).

## 3. Phase by role in start-worker.sh

- [x] 3.1 In `start-worker.sh`, map the role to its phase and run `tracker.py set-phase "${issue%b}" <phase>` at the point design.md names, on fresh starts and on `--resume`. On failure print `Issue <issue>: cannot set the tracker phase; no worker started.` and exit with the tracker's status. Update the header comment in one line. Verify: tasks 3.2 and 3.3.
- [x] 3.2 In `test_state.py`, replace the copied skill's `scripts/tracker.py` with a stub that logs its arguments and exits with `$TRACKER_STATUS`. Test that planner, implementer, and reviewer starts log `set-phase 8 planning`, `building`, and `in-review`; that `ENG-7b` logs `set-phase ENG-7 building`; that `--resume` of an implementer logs `building`; that a stub exit of 1 makes `start-worker.sh` exit 1 with the stub's stderr and the new line, with no `planner_backend` in the record and no Herdr call. Verify: `python3 -m unittest discover -s switchyard/scripts -p 'test_state.py'` passes.
- [x] 3.3 One `test_state.py` test with the real `tracker.py`, a `tracker.md` saying `Tracker: linear`, and `LINEAR_API_KEY` removed from the environment: `start-worker.sh ENG-7 planner <provider>` exits 1, its stderr contains `LINEAR_API_KEY is not set`, and the record has no planner fields. Verify: same command passes. The existing GitHub start tests pass unchanged.

## 4. Docs

- [x] 4.1 `switchyard/tracker.md`: one line saying an optional `Phase | Status` table overrides Linear status names, pointing to the README section. Verify: `load_tracker` still reads the shipped file (existing test).
- [x] 4.2 `switchyard/SKILL.md`: in Plans, one or two sentences that `start-worker.sh` sets the phase and that `set-phase` does nothing on GitHub. In Per issue step 4, first bullet: run `tracker.py set-phase <issue> plan-review`. In Question queue, the Linear paragraph from design.md, with the marker line in backticks; the shared rules stay as they are. Verify: read the sections; GitHub steps are unchanged in meaning.
- [x] 4.3 `README.md` "Use Linear": a table of phases and default statuses, which three to add in the team's Started group, the `tracker.md` override with a one-row example, that questions arrive as a Linear comment and answers are replies, and one sentence that Linear's GitHub integration may also move the issue when the PR opens and merges, and that Done comes from it. Verify: read it against the Writing rules in `AGENTS.md`.
- [x] 4.4 `CHANGELOG.md` Unreleased, `### Added`: one line for #150 that says it is untested against live Linear. Verify: read it.

## 5. Checks

- [x] 5.1 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 5.2 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 5.3 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck -S info` passes.
- [x] 5.4 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 5.5 `git fetch --no-tags --depth=1 origin '+refs/tags/v*:refs/tags/v*' && npm test --prefix create-switchyard` passes.
- [x] 5.6 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it, and check the archive folder and the updated `openspec/specs/issue-tracker/spec.md` exist before reporting.
- PR body: say it is untested against live Linear.
