# Design

## Context

`run()` in `update-switchyard.py` works in three phases:

1. Refusals and setup: clean-tree check, `VERSION` read, clone, release checks, `read_update_paths`.
2. Action list: every merge and every refusal for unmergeable content (binary file, malformed `AGENTS.md` or `openspec/config.yaml`) happens here, before any write. Merges run `git merge-file` on files in a temporary directory outside the project.
3. Write loop (lines 596-621): re-checks each path with `local_file`, then for each action writes or unlinks the file and prints `<status>: <path>`. It then writes `VERSION`, prints the totals, and, under `--install`, the `Next:` lines. It returns 1 when the totals have `conflict` or `kept`.

So everything a dry run needs to report is known before the first write.

## Goals / Non-Goals

**Goals:**
- A dry run prints the same lines as a real run, in the same order, plus one final line. If the project is already at the target release, it prints only `Already at X` and exits 0.
- A dry run leaves the project byte-for-byte unchanged, tracked and untracked files alike.

**Non-Goals:**
- Showing diffs or merged content. The report stays a list of paths and statuses.
- Printing the changelog (#93), the newer-release check (#94), undo commands (#95), the npm `update` verb (#91).

## Decisions

### Guard the writes in the existing loop

Add `--dry-run` (`action="store_true"`, help: "print the report without writing any file"). In the write loop, skip the `unlink`, `mkdir`, `write_bytes`, and `chmod` calls when it is set, and skip the `VERSION` write. The `local_file` re-check, the per-file prints, the counts, the totals, the `Next:` lines, and the return value stay as they are. After the last line a real run prints, a dry run prints `Dry run: nothing was written.`

Alternative: split the loop into a "plan" function and an "apply" function. Rejected for now: it moves code that #93 and #95 will edit next, and the guard is three conditionals.

### Behaviour the tests check

- Update with a mix of statuses: the dry run exits as the real run does, prints the real run's stdout plus the final line, and leaves `git status --porcelain` empty and `VERSION` unchanged. The test runs the dry run first, checks the tree, then runs the real update on the same project and compares stdout and exit code.
- A run with `conflict` or `kept` exits 1. A run with neither exits 0.
- `--install --dry-run` into a repo without the workflow creates no files, and its stdout and exit code match a real install plus the final line.
- `--dry-run` with uncommitted tracked changes is refused with exit 2, as today.
- `--dry-run` with a binary file that cannot merge is refused with exit 2 and changes nothing.
- `--dry-run` when already at the target release prints only `Already at X` and exits 0.
- The final line is printed once, as the last line of stdout.

### Temporary files

Merges and the clone already use `tempfile` directories outside the project, which are removed on exit. A dry run uses them too. "Writes nothing" means nothing in the project.

## Risks / Trade-offs

- [A real run can still fail on a write the dry run skipped, such as a read-only file.] → The dry run reports what would change, not that the writes will succeed. The real run's error handling is unchanged.
- [A dry run still clones the source, so it needs network access like a real run.] → No change; the README already says this.
