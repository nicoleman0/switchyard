# Proposal

## Why

Issue #93: the updater's report lists files only. Behaviour changes are in `CHANGELOG.md`, which users have to look up. A project updating from 0.7.2 learns only from the changelog that 0.8.0 changed how an `escalation` row in `routing.md` is used.

## What Changes

- After an update, `switchyard/scripts/update-switchyard.py` prints the `CHANGELOG.md` sections for every release newer than the base, up to and including the target. It reads them from the target release's `CHANGELOG.md` and leaves out `Unreleased`.
- `--dry-run` prints the same notes. `Dry run: nothing was written.` stays the last line.
- `--install` and "Already at X" print no notes.
- When the target has no `CHANGELOG.md`, or the file cannot be read, the updater prints one line saying the release notes are unavailable and why. The exit code does not change.
- The npm package's bundle carries `CHANGELOG.md` in every release commit, so `npm init switchyard@latest update` prints the notes offline. `CHANGELOG.md` is not in `update-paths.txt`, so the updater never copies it into a project.
- README: the "Take a later release" section says the updater prints the release notes.
- CHANGELOG: one `Added` line under Unreleased.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`, like earlier updater changes, because the template ships an empty `openspec/specs/` to every project made from it. The updater's tests are the acceptance check, and the behaviour is listed in the design.

## Impact

- `switchyard/scripts/update-switchyard.py`: a changelog reader and the report's output. No new writes.
- `switchyard/scripts/test_update_switchyard.py`: release-note tests.
- `create-switchyard/scripts/build.mjs` (as rewritten by #91): add `CHANGELOG.md` to each bundled commit.
- `create-switchyard/test/install.test.mjs`: bundle and update tests.
- `README.md`, `CHANGELOG.md`.
- Depends on #91. The implementer starts after #91 merges and this branch is rebased.
