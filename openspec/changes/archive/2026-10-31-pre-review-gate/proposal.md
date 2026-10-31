# Proposal

Delivers GitHub issue #117.

## Why

The coordinator starts a reviewer session after every implementer commit, even when a test, lint, scope check, or OpenSpec validation would fail. Those checks are cheap and give the same answer every time. A review session is neither. A failed check should go straight back to the implementer.

## What Changes

- New `switchyard/scripts/pre-review.sh <issue>`. On the issue's worktree it runs, in order: a clean-tree check, `check-scope.sh <issue>`, `openspec validate --all --strict`, and the project's checks hook. Every step runs even after one fails.
- It writes the full output to `<worktree>/.switchyard/checks/<n>.log`, numbered like reviews. Stdout gets one `PASS`, `FAIL`, or `SKIP` line per step and the log path.
- Exit 0 when nothing failed. Exit 1 when a step failed. Exit 2 when the gate cannot run, such as no record or no worktree.
- New project-owned hook `switchyard/hooks/checks.sh`, the one home for the commands a branch must pass. The shipped copy runs the checks for Switchyard's own files, which hold in every project that uses Switchyard, and says where to add the project's own.
- `update-switchyard.py`: `switchyard/hooks/checks.sh` joins `PROJECT_OWNED`, so the updater adds it when missing and never overwrites it.
- `SKILL.md`, Per issue step 7: run the gate before the reviewer starts. On a failed check, start an implementer fix session pointed at the log, without a reviewer. A scope-only failure goes to the coordinator's ruling first.
- README: one row for the hook in the project-owned table. CHANGELOG: one line under Unreleased, Added.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty in this repo and every change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- New: `switchyard/scripts/pre-review.sh`, `switchyard/scripts/test_pre_review.py`, `switchyard/hooks/checks.sh`.
- `switchyard/SKILL.md`, Per issue step 7 only.
- `switchyard/scripts/update-switchyard.py`: one line, `PROJECT_OWNED`. Issue #122 edits the same line in parallel.
- `README.md`: one appended table row. `CHANGELOG.md`: one line.
- Not changed: `switchyard/roles/reviewer.md` (owned by #115), `switchyard/roles/implementer.md`, the Open the PR section of `SKILL.md`.
