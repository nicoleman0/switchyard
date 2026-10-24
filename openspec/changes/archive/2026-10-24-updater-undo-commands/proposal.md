# Proposal

Delivers GitHub issue #95.

## Why

To undo an update, the README gives a manual recipe: `git restore .`, remove each file reported as `added`, and remove `VERSION` if the project did not have one. The updater already knows which files it changed, added, and removed, and whether `VERSION` existed. It should print the commands itself.

## What Changes

- After a run that wrote files, update and `--install` alike, `update-switchyard.py` ends with a block of shell commands that undo that run:
  - `git restore --` for tracked files it updated, merged, conflicted, or removed, and for `switchyard/VERSION` when it existed and was tracked.
  - `rm --` for files it added, and for `switchyard/VERSION` when it did not exist before the run.
  - `rmdir --` for directories the run created, deepest first, so a later `--install` sees the repo as it was.
- A file the run changed that git did not track gets one line before the block saying it cannot be restored by these commands.
- Paths are quoted with `shlex.quote`, so a path with spaces or quotes is safe to paste.
- When a write fails partway, the updater prints the undo block for the writes it made, then the error, and still exits 2.
- A dry run and `Already at X` print no undo block. Exit codes are unchanged.
- The block is the last output of a real run, after the totals, the `Next:` lines, and #93's release notes.
- README: the manual undo recipes in "Add it to an existing repo" and "Take a later release" become one sentence saying the updater prints the commands.
- CHANGELOG: one line under Unreleased.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty and the updater has no spec yet, so the change sets `skip_specs: true` like the earlier updater changes. The behaviour is pinned by the tests and the README.

### Modified Capabilities

None.

## Impact

- `switchyard/scripts/update-switchyard.py`: records what each write did and prints the block. Every write stays under #92's dry-run guard.
- `switchyard/scripts/test_update_switchyard.py`: new tests run the printed commands with `sh` and check the repo is back to its pre-run state. #92's dry-run equality tests compare against the real run without its undo block.
- `README.md`, `CHANGELOG.md`.
- `npm init switchyard update` runs the same Python updater, so it prints the block with no change in `create-switchyard/`.
- Builds on #93 (`updater-release-notes`). Implementation starts after #93 merges and this branch is rebased.
