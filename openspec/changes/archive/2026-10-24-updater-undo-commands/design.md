# Design

## Context

See proposal.md for why. Line references are to `switchyard/scripts/update-switchyard.py` on `updater-release-notes` (#93).

- The run refuses when tracked files have uncommitted changes (line 502). Untracked files are allowed. So before the run, every tracked file equals `HEAD` and the index, and `git restore -- <path>` returns a tracked file to its pre-run content and mode.
- All writes happen in one loop (lines 659-677): each action is `removed` (unlink) or a write with an optional chmod, then `switchyard/VERSION` is written. Statuses `kept` and `None` write nothing. Parent directories are made with `mkdir(parents=True)`.
- Output order today: one line per file, totals, `Next:` lines (install) or release notes (update), then `Dry run: nothing was written.` on a dry run.
- `openspec_existed` (line 520) checks `openspec/` with `is_dir()`. An empty `openspec/` left by an undo would make a second `--install` skip the `Next: run ... openspec init` line.

## Goals / Non-Goals

**Goals:**
- Commands that, pasted into a POSIX shell right after the run, return the work tree to its pre-run state.
- Output only: no new writes, no new refusals, no exit-code change.

**Non-Goals:**
- Undoing after the user stages or commits the result.
- Restoring files git did not track. The updater keeps no backup.
- Windows `cmd` or PowerShell syntax.
- The newer-release check (#94).

## Decisions

### Plan undo entries before the write loop, print what the disk shows

Before writing, plan one undo entry per writing action, in loop order, then one for `VERSION`:
- restore: `updated`, `merged`, `conflict`, and `removed` actions that git tracks, and `VERSION` when it existed and is tracked.
- delete: `added` actions, and `VERSION` when it did not exist.
- not undone: a changing action on a path git does not track, and `VERSION` when it existed untracked.
- created directories: for each delete entry, the parent directories that do not exist yet.

Tracked paths come from one `git --literal-pathspecs ls-files -z -- <paths>` call at the project root. `--literal-pathspecs` stops a path with `*` or `[` being read as a glob.

The loop keeps a count of entries it has started. One function turns the started entries into the block, filtered by what is on disk now:
- restore entries are always kept. Restoring a tracked file the run did not change is a no-op.
- delete entries are kept only when the path exists.
- created directories are kept only when they exist, deepest first, without duplicates.

The same function serves a full run and a failed one. On a full run every entry has started and every path exists, so the filter changes nothing. Planning before the loop keeps the dry run free of new branches: the dry run plans and prints nothing.

### A write that fails partway

The write loop and the `VERSION` write sit in a `try` that catches `OSError`. On a failure, it prints the block for the entries started so far, the failing one included, then re-raises. The existing handler then prints `update-switchyard: <error>` to stderr and returns 2. The block goes to stdout like a full run's. The per-file report lines stop at the failing file, so the totals, `Next:` lines, and release notes do not print.

The failing entry counts as started because a failed write can still leave a truncated file, a changed file whose chmod failed, or new parent directories. The disk filter then decides what to print for it: a tracked file gets `git restore`, and an added file gets `rm` only if it exists. Alternative: count only finished writes. That misses those leftovers.

Only `OSError` is caught. `local_file` checks every path before the loop, so a `Refusal` cannot happen mid-loop.

`added` from `--install`'s project-owned path (`switchyard/routing.md`) and from merges like `merge_agents_sections` returning `added` both mean the file did not exist, so `rm` is right for all of them.

### Output format

```

To undo this run before you stage or commit, run:
git restore -- AGENTS.md switchyard/VERSION
rm -- switchyard/new.txt 'switchyard/it'"'"'s new.txt'
rmdir -- switchyard/sub
```

- A blank line, a header, then one command per kind, each listing all its paths. Kinds with no paths are left out. Order: `git restore`, `rm`, `rmdir`, so files go before their directories.
- `--` before the paths so a path starting with `-` is not read as an option.
- Every line under the header is a command, so the block pastes as is. No `#` comment lines: zsh, the macOS default shell, does not treat `#` as a comment interactively.
- An untracked file the run changed gets a line before the header: `Not undone: <path> was not tracked by git; restore it by hand.` The path is quoted the same way.
- Alternative: one command per file. An install adds about 40 files, so that is 40 lines for no gain.

### Placement: last, after the release notes

The block goes after the totals, the `Next:` lines, and #93's release notes, as the last output of a real run.
- It is the action the user takes after reading everything else, and it sits next to the prompt for copying.
- A dry run keeps a simple relation to a real run: dry output equals real output minus the undo block, plus `Dry run: nothing was written.`
- Alternative: before the release notes. Long notes would then sit between the commands and the prompt.

### `git restore --`, not `git restore --source=HEAD --staged --worktree --`

The updater stages nothing, and the index equals `HEAD` before the run, so plain `git restore --` restores from the right content. The longer form would also undo the user's own staging of those files, but `rm` would still leave staged added files in the index, so the two kinds would disagree. The header says "before you stage or commit" instead.

### Tests run the printed commands

Tests take the lines after the header and run them with `sh -c` in the project. They then check `git status --porcelain --untracked-files=all` matches its pre-run value, and that no directory exists that did not exist before. This proves the commands paste and work, not only that they look right.

The partial-failure test makes a real write fail. It makes an existing project directory read-only (`0o555`), so creating a file inside it raises `PermissionError`. `local_file` only runs `lstat`, so the checks before the loop still pass. The test is skipped when running as root, because root ignores directory permissions. GitHub Actions runs as a non-root user, so the test runs in CI. Alternative: run the script through a wrapper that patches `Path.write_bytes`. That works under root, but it also hits the merge temp files and tests a fake failure.

#92's tests that assert `dry_run.stdout == real_run.stdout + b"Dry run: nothing was written.\n"` become: the real run's output up to the undo block, plus the final line, equals the dry run's output; and the dry run has no undo header. A helper splits the real output at the header.

## Risks / Trade-offs

- [The user stages or edits files before running the commands] → The header says to run them before staging or committing. `rmdir` fails loudly on a directory that is no longer empty, which is the safe outcome.
- [A write fails midway] → The block covers the writes started so far. A file truncated by the failed write is restored or removed with the rest.
- [POSIX quoting only] → The README's commands are already POSIX, and `create-switchyard` needs a shell with `python3`. Windows users under Git Bash or WSL are covered.
- [`git restore` reads paths as pathspecs, so a printed path with glob characters can match other files] → Every other tracked file is clean before the run, so restoring it is a no-op. Release paths do not use glob characters.
