# Tasks

## 1. Dry run in the updater

- [x] 1.1 Add `--dry-run` to the argument parser in `switchyard/scripts/update-switchyard.py`. Verify `python3 switchyard/scripts/update-switchyard.py --help` lists it.
- [x] 1.2 In the write loop, skip the file writes, removals, `mkdir`, `chmod`, and the `VERSION` write when `--dry-run` is set. Keep the prints, counts, totals, `Next:` lines, and return value. Print `Dry run: nothing was written.` as the last line. Verify with the tests in 1.3.
- [x] 1.3 Add tests to `switchyard/scripts/test_update_switchyard.py`, reusing `make_target`, `make_project`, and `run_update`: a mixed-status update (dry run leaves `git status --porcelain` empty and `VERSION` unchanged; its stdout equals a following real run's stdout plus the final line; same exit code, 1 with `conflict` or `kept`); a clean update exiting 0; `--install --dry-run` creating no files and matching a real install; a dirty tree and a binary merge both refused with exit 2 and no changes. Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`.

## 2. Docs

- [x] 2.1 In `README.md` "Take a later release", add one sentence as a new paragraph after the report paragraph: `--dry-run` prints the report a real run would print and writes nothing. Do not change other lines in the section. Verify with `git diff README.md` showing only added lines.
- [x] 2.2 Add an `### Added` line for #92 under Unreleased in `CHANGELOG.md`.

## 3. Repository checks

- [x] 3.1 Run `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` and confirm it exits 0.
- [x] 3.2 Run `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` and confirm it exits 0.
- [x] 3.3 Run `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` and confirm it exits 0.
- [x] 3.4 Run `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` and record the counts.
- [x] 3.5 Run `npm test --prefix create-switchyard` and record the counts.
- [x] 3.6 Run `npx --yes @fission-ai/openspec validate --all --strict` and confirm it exits 0.

## Workflow follow-up

- Archive the change in the PR that completes it.
