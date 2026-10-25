# Design

## Context

- `state.py get` exits 3 with `Issue <n>: no record. Run setup-worktree.sh, or state.py init` on stderr when the record file is missing. Teardown treats 3 as "no record" and carries on with `record_path` empty. Other statuses exit as is.
- Teardown already knows what exists: `entry_path`/`worktree_present`, `local_present`, and the remote check further down.
- `test_teardown_without_record_succeeds` covers no record with a real worktree and stays valid.

## Decisions

### Capture the `get` stderr instead of discarding it

Run `state.py get` with stderr redirected to a `mktemp` file, removed on exit. On status 3, drop it and note there is no record. On any other nonzero status, copy the file to stderr and exit with that status. A `2>/dev/null` would hide those errors, so it is not used. Alternative: test for the record file directly. Rejected, it adds a second source of truth for "no record".

### Decide "nothing to remove" before the hook and the abandon report

When `has_record` is empty and `entry_path` is empty and `local_present` is empty, probe the remote with `remote_branch_state`. If the branch is absent there too, print the new message and exit 1. This runs before `worktree-down.sh` and before the `--abandon` report, so a typo does not run the project's down hook for an issue that has nothing to tear down.

`remote_branch_state` moves above this check. The later remote block keeps its own call, so it still handles a delete race and an `ls-remote` error. The cost is one extra `ls-remote` in the no-record, nothing-local case only. An `ls-remote` status other than 2 exits with that status, as the later block does.

`state.py rm` is not reached on this path, so nothing is written.

### Message

`Issue <n>: no record, and nothing to remove for branch <branch>.` on stderr, exit 1. The `Skipped:` lines print before it, as they do today.

## Risks / Trade-offs

- [Extra `ls-remote` call] Only when there is no record and nothing local. Accepted.
- [`--abandon` with no record and nothing left] Also exits 1. The maintainer's rule names no exception.
