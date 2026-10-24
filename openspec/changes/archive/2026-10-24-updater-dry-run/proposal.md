# Proposal

## Why

Issue #92: `update-switchyard.py` writes files as soon as it runs. To see what an update would change, a user has to run it and then undo it by hand.

## What Changes

- New `--dry-run` flag on `switchyard/scripts/update-switchyard.py`. It computes the same actions and prints the same per-file lines and totals as a real run, then ends with one line saying nothing was written.
- A dry run writes nothing in the project, `switchyard/VERSION` included.
- It works with and without `--install`.
- Exit codes match the real run: 1 when the report has `conflict` or `kept`, 0 otherwise, 2 on a refusal. Every refusal still applies, the clean-tree check included.
- README: one sentence about `--dry-run` in "Take a later release".
- CHANGELOG: one `Added` line under Unreleased.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`, like earlier updater and installer changes, because the template ships an empty `openspec/specs/`. The updater's tests are the acceptance check, and the behaviour is listed in the design.

## Impact

- `switchyard/scripts/update-switchyard.py`: argument parsing and the write loop only, so #93 and #95 can edit the updater after this merges without conflicts.
- `switchyard/scripts/test_update_switchyard.py`: new dry-run tests.
- `README.md`, `CHANGELOG.md`.
- No change to `create-switchyard`. #91 forwards arguments after `update` to the updater, so `--dry-run` reaches it.
