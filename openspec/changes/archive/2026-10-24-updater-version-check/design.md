# Design

## Context

`update-switchyard.py` owns the release source (`DEFAULT_SOURCE`), the release tag rule (`VERSION_RE`, `release_tuple`, `list_releases`), and the `VERSION` read. Today it learns the releases by cloning the source into a bare repo, which is too slow for preflight.

`preflight.sh` runs from the project root, prints `ok`, `warn`, or `MISSING` lines, and exits non-zero only when `missing` is above zero. Its tests put stub commands on an isolated `PATH`, including a `python3` stub that exits 0.

The maintainer decided:

- The check is a read-only `--check` flag on the updater, and preflight calls it.
- Preflight prints one `warn` line when `VERSION` is behind, naming both versions and `npm init switchyard@latest update`. It never adds to `missing`.
- When the source cannot be reached, preflight skips the check without a warning, so it works offline.

## Goals / Non-Goals

**Goals:**

- Preflight can tell "current", "behind", and "could not reach the source" apart from the exit code alone.
- A hanging network delays preflight by at most the time limit.
- No test reaches the network.

**Non-Goals:**

- Changing what an update prints, or the write loop (#95 edits both).
- A check from the npm package. `npm init switchyard@latest update -- --check` reaches the bundled updater, which compares against its own source; the README does not document it.
- Checking more than once per preflight run, or caching the result.

## Decisions

### Tags through `git ls-remote`

`--check` runs `git ls-remote --tags --refs <source> v*`. Each output line is `<sha>\trefs/tags/<name>`. The tag names go through the same filter and sort as `list_releases`, so the release rule has one home.

To get there, `list_releases` is split first, as a separate refactor commit: a new `release_tags(names)` keeps the names that `release_tuple` accepts and sorts them; `list_releases` calls it with the `git tag --list` output. The check calls it with the `ls-remote` names. No behaviour changes in that commit.

`ls-remote` works for URLs and for local paths, so tests pass a local repo as `--source`.

### Order of work in `run()`

`--check` returns before the clean-tree check and before the clone:

1. Refuse `--check` with `--install`, `--from`, `--to`, or `--dry-run` (exit 2). `--source` is allowed.
2. Find the project root with `git rev-parse --show-toplevel` (refuse outside a work tree, exit 2).
3. Read `VERSION` with the existing checks. Missing, not a regular file, or not `X.Y.Z` / `vX.Y.Z`: refuse, exit 2. The message for a missing file is `no VERSION found; nothing to compare`.
4. List the source's release tags. No release tags: refuse, exit 2.
5. Compare and print.

The `VERSION` read moves into a small helper used by both the update path and the check, so the regular-file rule stays in one place. This is part of the refactor commit.

No clean tree is required: `--check` writes nothing.

### Exit codes and output

| Exit | Meaning | stdout / stderr |
| --- | --- | --- |
| 0 | `VERSION` equals or is newer than the newest release | stdout: `0.8.0 is the newest release` or `0.9.0 is newer than the newest release, 0.8.0` |
| 3 | `VERSION` is behind | stdout: `0.8.0 is behind the newest release, 0.9.0. Update with: npm init switchyard@latest update` |
| 4 | Source not reached: `ls-remote` failed or timed out | stderr: `update-switchyard: could not reach <source>: <git error or "timed out after 10s">` |
| 2 | Refused: a local problem or a source with no release tags | stderr: `update-switchyard: <reason>`, as today |

3 and 4 are new codes because Python already uses 1 for an uncaught exception and 2 for argparse errors. A crash can never look like "behind" or "offline".

Versions print as `X.Y.Z`, the form `VERSION` uses.

### Time limit

`CHECK_TIMEOUT = 10` seconds, a constant next to `DEFAULT_SOURCE`. `ls-remote` to GitHub takes about half a second, so 10 seconds only matters when the network hangs.

`subprocess.run(timeout=...)` is not enough: it kills `git`, but `git-remote-https` can keep the output pipe open and `run` then waits on it. The check starts `git` with `start_new_session=True`, waits with `communicate(timeout=...)`, and on timeout kills the whole process group with `os.killpg` before reading the rest. Supported platforms are macOS and Linux, so `killpg` is available.

The child also gets `GIT_TERMINAL_PROMPT=0` and `stdin=DEVNULL`, so a source that asks for credentials fails at once instead of waiting on a prompt.

The listing lives in a function `remote_releases(source, timeout)` so a test can import the module and call it with a short timeout and a stub `git` that sleeps.

### Preflight

After the existing checks and before the totals, and only when `python3` is on `PATH` (a missing Python is already reported):

```bash
output=$(python3 "$(dirname "${BASH_SOURCE[0]}")/update-switchyard.py" --check 2>&1)
```

Then by exit code:

- 0: `ok       Switchyard release`.
- 3: `warning "Switchyard release: $output"`.
- 4: nothing.
- Anything else: `warning "Switchyard release: could not check. $output"`. This covers a missing or malformed `VERSION` and a crash.

The updater is found next to `preflight.sh`, not in the current directory, so the project's own copy runs. Preflight passes no `--source`, so the URL stays in the updater.

### Tests

Updater (`test_update_switchyard.py`, local `--source`):

- `VERSION` equal to the newest tag: exit 0, the "newest release" line.
- `VERSION` behind: exit 3, the line names both versions and `npm init switchyard@latest update`.
- `VERSION` newer than every tag: exit 0.
- Missing `VERSION`, malformed `VERSION`: exit 2.
- `--check` with `--install`, `--from`, `--to`, or `--dry-run`: exit 2.
- A dirty tree: still checks (exit 0 or 3), and `git status --porcelain` is unchanged afterwards.
- `--source` pointing at a path that does not exist: exit 4.
- Timeout: import the module, put a stub `git` that sleeps 30 seconds first on `PATH`, call `remote_releases` with a 0.5 second limit, and assert it returns the "could not reach" result in under 5 seconds.
- A source with no release tags: exit 2.

Preflight (`test_preflight.py`, stub `python3` that logs its arguments and exits with `$CHECK_STATUS`, printing `$CHECK_OUTPUT`):

- Exit 0: `ok       Switchyard release`, no new warning.
- Exit 3: one `warn     Switchyard release: <output>` line, preflight still exits 0, `0 missing`.
- Exit 4: no `Switchyard release` line at all, no warning added.
- Exit 2: one `warn     Switchyard release: could not check.` line.
- The stub saw `update-switchyard.py --check` with the path next to `preflight.sh`.
- No `python3`: no `Switchyard release` line.

The existing preflight tests keep passing: the stub `python3` exits 0, so they gain only an `ok` line.

## Risks / Trade-offs

- [Preflight now makes a network call.] → One `ls-remote`, at most 10 seconds, silent when it fails.
- [A source that cannot be reached for other reasons, such as a typo in a fork's `DEFAULT_SOURCE`, is silent too.] → Accepted: the maintainer chose the quiet fallback, and running `--check` by hand shows the git error.
- [Exit codes 3 and 4 differ from the update's 1 for conflicts.] → They belong to `--check` only, and the README names them.
