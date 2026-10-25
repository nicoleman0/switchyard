# Proposal

## Why

Issue #105: `run()` in `switchyard/scripts/update-switchyard.py` finds the project root twice, once for `--check` and once for update and install. Both copies run `git rev-parse --show-toplevel`, refuse outside a work tree, and decode the path. A change to how the root is found must be made in both.

## What Changes

- Add `find_project_root()` in `update-switchyard.py`. It returns the root as a `Path` or raises `Refusal("run this command inside a git work tree")`.
- `--check` and the update/install path both call it.
- No behaviour change. The two copies are identical today (same git call, same message, same `os.fsdecode`), so messages, exit codes, and output stay as they are.
- Add a test that `--check` outside a work tree exits 2 with the same message. Only the update path is covered today.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`: it is a refactor with no observable behaviour change.

## Impact

- `switchyard/scripts/update-switchyard.py`: new helper, two call sites.
- `switchyard/scripts/test_update_switchyard.py`: one new test.
- No CHANGELOG entry, since nothing user-visible changes.
