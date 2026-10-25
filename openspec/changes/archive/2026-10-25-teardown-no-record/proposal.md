# Proposal

Delivers GitHub issue #86.

## Why

`teardown-worktree.sh <issue> <branch>` reports success when the issue has no record and nothing exists to remove. With no record for 57 and no branch `wrong`, it prints the setup hint from `state.py get`, three `Skipped:` lines, `Removed issue 57 record.`, and exits 0. The hint is wrong advice here, and the last line names a record that never existed. A typo in both the issue number and the branch reads as a finished teardown.

## What Changes

- No record, and no worktree, stale entry, local branch, or remote branch to remove: teardown exits 1 and prints `Issue <n>: no record, and nothing to remove for branch <branch>.` on stderr. No `Removed ...` line.
- Teardown no longer shows `state.py get`'s setup hint. Any other `state.py get` failure still exits with its status and shows its message.
- Unchanged: no record with something removed (remove it, exit 0); a record with nothing else left (`Removed issue <n> record.`, exit 0); the `Skipped:` lines; `--abandon` semantics; `state.py`'s messages for other callers.
- CHANGELOG: one line under Unreleased, Fixed.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty and this is a bug fix to match intent, so the change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- `switchyard/scripts/teardown-worktree.sh`.
- `switchyard/scripts/test_state.py`: new teardown tests.
- `CHANGELOG.md`.
