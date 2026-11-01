# Proposal

Delivers GitHub issue #157.

## Why

This repo's `switchyard/tracker.md` is also the shipped default and a test fixture. Setting it to `Tracker: linear` for Switchyard's own work would give Linear to installs without `--tracker`, to projects made from the GitHub template, and to projects that update from a release without the file. It would also fail 19 GitHub tests in `test_tracker.py`.

## What Changes

- Install with no `--tracker` writes `Tracker: github` into a newly added `tracker.md`, whatever the release's file names. An existing file is still kept.
- An update that adds a missing `tracker.md` (a project coming from a release before the file existed) writes `Tracker: github` too. Updates still never change an existing file.
- `init-project.py` sets the `Tracker:` line of `switchyard/tracker.md` to `github` and prints a line for it, like its other moves.
- The GitHub tests in `test_tracker.py` run a copy of `tracker.py` beside their own `tracker.md`, so the repo's value no longer matters.
- README and CHANGELOG say what install, update, and init write.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `issue-tracker`: adds requirements for the tracker an updater-added `tracker.md` names, and for init resetting it. Existing requirements are unchanged.

## Impact

- `switchyard/scripts/update-switchyard.py`: the install and update paths that add `tracker.md`.
- `switchyard/scripts/init-project.py`: a new reset step.
- Tests: `test_update_switchyard.py`, `test_init_project.py`, `test_tracker.py`.
- `README.md`, `CHANGELOG.md`.
- No change to `tracker.py` behaviour, the npm wrapper, or this repo's own `tracker.md`.
