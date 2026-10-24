# Tasks

## 1. Refactor (own commit, no behaviour change)

- [x] 1.1 In `switchyard/scripts/update-switchyard.py`, split `list_releases` into `release_tags(names)` (filter with `release_tuple`, sort) and the `git tag --list` call. Move the `VERSION` read in `run()` into a helper that returns the stored text or `None` and keeps the regular-file refusal. Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passing unchanged, then commit on its own.

## 2. `--check` in the updater

- [x] 2.1 Add `--check` to the parser (help: "report whether VERSION is behind the newest release; writes nothing"). Refuse it with `--install`, `--from`, `--to`, or `--dry-run` (exit 2). Verify `--help` lists it.
- [x] 2.2 Add `CHECK_TIMEOUT = 10` and `remote_releases(source, timeout)`: `git ls-remote --tags --refs <source> v*` started with `start_new_session=True`, `stdin=DEVNULL`, and `GIT_TERMINAL_PROMPT=0`; on timeout kill the process group with `os.killpg`. Return the sorted release tags through `release_tags`, or a reason the source was not reached.
- [x] 2.3 In `run()`, handle `--check` before the clean-tree check and the clone: find the root, read `VERSION`, list remote releases, and exit 0, 3, 4, or 2 with the lines in the design's table. Do not touch the write loop or the update's output.
- [x] 2.4 Add the updater tests listed in the design to `switchyard/scripts/test_update_switchyard.py`, reusing `make_target`, `make_project`, and `run_update`. Verify with the unittest command.

## 3. Preflight

- [x] 3.1 In `switchyard/scripts/preflight.sh`, when `python3` is on `PATH`, run the updater next to the script with `--check` and handle exit 0, 3, 4, and anything else as the design says. Place it before the totals line.
- [x] 3.2 Extend the `python3` stub in `switchyard/scripts/test_preflight.py` so it logs its arguments and honours `CHECK_STATUS` and `CHECK_OUTPUT` (default exit 0, no output). Add the preflight tests listed in the design. Verify existing tests still pass.

## 4. Docs

- [x] 4.1 In `README.md` "Take a later release", add one paragraph: preflight warns when `VERSION` is behind the newest release, and `python3 switchyard/scripts/update-switchyard.py --check` runs the same check (exit 0 current, 3 behind, 4 source not reached). In the requirements list, add that preflight reaches GitHub once and skips the check offline. Verify `git diff README.md` shows only added lines.
- [x] 4.2 Add an `### Added` line for #94 under Unreleased in `CHANGELOG.md`.

## 5. Repository checks

- [x] 5.1 Run `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` and confirm it exits 0.
- [x] 5.2 Run `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` and confirm it exits 0.
- [x] 5.3 Run `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` and confirm it exits 0.
- [x] 5.4 Run `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` and record the counts.
- [x] 5.5 Run `npm test --prefix create-switchyard` and record the counts.
- [x] 5.6 Run `npx --yes @fission-ai/openspec validate --all --strict` and confirm it exits 0.

## Workflow follow-up

- Archive the change in the PR that completes it.
