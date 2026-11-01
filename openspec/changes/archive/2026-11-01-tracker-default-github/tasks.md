# Tasks

## 1. Tests stop reading this repo's tracker.md

- [x] 1.1 In `test_tracker.py`, make `TrackerTest.setUp` copy `tracker.py` to `<tmp>/switchyard/scripts/` with `<tmp>/switchyard/tracker.md` holding `Tracker: github`, and make `run_tool` run the copy. Verify: with `switchyard/tracker.md` set to `Tracker: linear`, `python3 -m unittest discover -s switchyard/scripts -p 'test_tracker.py'` passes (it fails 19 today). Restore the file.

## 2. Updater writes github when it adds tracker.md

- [x] 2.1 In `update-switchyard.py` install, pass the added `tracker.md` through `replace_tracker_line` with `args.tracker or "github"`. Leave the explicit-flag refusal and the "Keeping" message as they are. Verify with a new test: a release `tracker.md` naming `linear` and no flag adds a file saying `Tracker: github`, with the rest of the release text kept.
- [x] 2.2 In the update path, pass an added `tracker.md` through `replace_tracker_line(content, "github")`. Verify with a new test: updating from a release without `tracker.md` to one naming `linear` adds `Tracker: github`; the existing tests that keep an existing `tracker.md` still pass.
- [x] 2.3 Add a test: install with no flag, an existing `tracker.md` naming `linear`, keeps the file and prints no `tracker.md` line.
- [x] 2.4 Update the `--tracker` help text if needed, and the README Install and Update lines for `tracker.md` (around lines 98 and 156) to say the added file names `github` unless `--tracker` names another. Verify by reading the rendered lines.

## 3. Template init resets the tracker

- [x] 3.1 In `init-project.py`, after the deletions, set the `Tracker:` line of `switchyard/tracker.md` to `github` using `TRACKER_LINE` from `tracker.py`. Print `reset`, `kept`, or `skipped   ... (absent|uncommitted changes)` as the spec says. Verify with new tests in `test_init_project.py` for linear, github, uncommitted, and absent, with `switchyard/tracker.md` and `switchyard/scripts/tracker.py` added to the test template as needed.
- [x] 3.2 Add the reset to the README's init paragraph (around line 114). Verify by reading it.

## 4. Changelog

- [x] 4.1 Add a `#157` line under Unreleased, Changed, in `CHANGELOG.md`: install and update write `Tracker: github` when they add `tracker.md`, and template init resets it.

## 5. Checks

- [x] 5.1 With this worktree's `switchyard/tracker.md` set to `Tracker: linear`, run `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` in the foreground and confirm it passes. Restore the file and confirm `git diff switchyard/tracker.md` is empty.
- [x] 5.2 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile`
- [x] 5.3 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`
- [x] 5.4 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck -S info`
- [x] 5.5 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check`
- [x] 5.6 `git fetch --no-tags --depth=1 origin '+refs/tags/v*:refs/tags/v*' && npm test --prefix create-switchyard`
- [x] 5.7 `npx --yes @fission-ai/openspec validate --all --strict`

## Workflow follow-up

- Archive the change in the PR that completes it, and check the archive folder exists before reporting.
