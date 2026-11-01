# Tasks

## 1. Checks hook

- [x] 1.1 Add executable `switchyard/hooks/checks.sh` with a header of a few lines in the style of `worktree-up.sh`: what it is for, that it runs in the issue's worktree with `ISSUE`, `BRANCH`, `WORKTREE`, and `MAIN_CHECKOUT` set, and that exit non-zero fails the gate. It runs `py_compile` over `switchyard/*.py`, the `unittest` suite in `switchyard/scripts`, `shellcheck` over `switchyard/*.sh`, and `node --check` over `switchyard/*.mjs`, exactly as `.github/workflows/switchyard.yml` writes them. Each command prints a header line and runs even when an earlier one failed; the hook exits 1 if any failed. End with a one-line comment saying to add the project's checks below. Verify: run it from this worktree and it exits 0; break one Python file locally and it exits 1 and still runs the later commands, then revert.
- [x] 1.2 In `switchyard/scripts/update-switchyard.py`, add `"switchyard/hooks/checks.sh"` to `PROJECT_OWNED`. Change that line only. Verify the existing updater tests pass.

## 2. Gate script

- [x] 2.1 Add executable `switchyard/scripts/pre-review.sh <issue>` as `design.md` describes: main checkout and record from `state.py`; steps clean tree, scope, OpenSpec, project checks, all run; log at `<worktree>/.switchyard/checks/<n>.log`; one `PASS`/`FAIL`/`SKIP` line per step and `Log: <path>` on stdout; exit 0, 1, or 2. Header comment of a few lines with the usage line, like `check-scope.sh`. Verify with 2.2.
- [x] 2.2 Add `switchyard/scripts/test_pre_review.py`. Build a temp main checkout with a copy of `switchyard/`, a bare origin, a pushed `main`, a worktree on a branch, and a record from `state.py init` plus `owned`, as `test_state.py` does. Stub `npx` on `PATH`. Cases:
  - every step passes: exit 0, four `PASS` lines, `checks/1.log` exists and holds each step's header.
  - a second run writes `checks/2.log`.
  - the hook exits 1: exit 1, `FAIL project checks`, the hook's output is in the log, and the earlier steps still show `PASS`.
  - the hook runs from the main checkout's copy, with the worktree as its working directory and the four variables set. Give the worktree's copy different content and show it did not run.
  - no hook: `SKIP` line, exit 0 when the rest pass.
  - hook present but not executable: `FAIL`, exit 1.
  - a committed file outside `owned`: `FAIL scope`, exit 1, and the later steps still run.
  - stubbed `npx` exits 1: `FAIL openspec`, exit 1.
  - an uncommitted tracked change: `FAIL clean tree`, exit 1. A file under `.switchyard/` alone does not fail it.
  - no record: exit 2 and no log written.
  Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`.

## 3. Coordinator and docs

- [x] 3.1 In `switchyard/SKILL.md`, Per issue step 7, add the gate as `design.md` gives it: run `scripts/pre-review.sh <issue>` before the reviewer starts, the scope-only ruling, the fix prompt, the two-failures stop, and that gate rounds do not count toward review rounds. Append to step 7; do not reword its existing sentences or touch any other section. Short imperative sentences, no em-dashes. Verify with `git diff switchyard/SKILL.md` showing changes inside step 7 only.
- [x] 3.2 In `README.md`, append one row to the project-owned table after the `worktree-up.sh` row: `switchyard/hooks/checks.sh` holds the commands a branch must pass before review, with Switchyard's own checks shipped, and the project adds its own. Verify the table renders with the same column count.
- [x] 3.3 Under Unreleased in `CHANGELOG.md`, in an `### Added` section, append this line. Append only.

  ```
  - #117: `pre-review.sh` runs the checks, the scope check, and OpenSpec validation before a reviewer starts. Projects put their checks in `switchyard/hooks/checks.sh`.
  ```

## 4. Repository checks

- [x] 4.1 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` passes.
- [x] 4.2 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 4.3 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 4.4 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 4.5 `npm test --prefix create-switchyard` passes, after `git fetch --no-tags --depth=1 origin '+refs/tags/v*:refs/tags/v*'`.
- [x] 4.6 `npx @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
