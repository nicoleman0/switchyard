# Tasks

## 0. Before starting

- [x] 0.1 Confirm #91 is merged and this branch is rebased on it: `git log --oneline main | grep '#91'` shows the merge, and `create-switchyard/scripts/build.mjs` builds `dist/release.bundle`.

## 1. Release notes in the updater

- [x] 1.1 In `switchyard/scripts/update-switchyard.py`, add a function that takes the target's `CHANGELOG.md` bytes (or `None`), the base and target versions, and the target tag, and returns either the notes text or an unavailable reason. Use the section and reason rules in design.md, and the heading pattern `^## \[(\d+\.\d+\.\d+)\] - `. Verify with the tests in 1.3.
- [x] 1.2 In `run()`, for an update (not `--install`) past the "Already at" check, read `<target>:CHANGELOG.md` from the bare clone before the write loop. After the totals and `Next:` lines, and before `Dry run: nothing was written.`, print a blank line, `Release notes, <base> to <target>:`, a blank line, and the notes; or print `Release notes unavailable: <reason>`. Do not change the write loop, the dry-run guard, or the return value. Verify with the tests in 1.3.
- [x] 1.3 Add tests to `switchyard/scripts/test_update_switchyard.py`, reusing `make_target`, `make_project`, and `run_update`. Give the fixture a `CHANGELOG.md` with `Unreleased`, release sections, and link definitions at the bottom. Cover:
  - 0.1.0 to 0.2.0 prints the 0.2.0 section and not 0.1.0, `Unreleased`, or a link definition.
  - 0.1.0 to 0.3.0 (one more tag) prints 0.3.0 then 0.2.0; `--to 0.2.0` from the same source prints only 0.2.0.
  - `--dry-run` prints the same notes, and its stdout still ends with `Dry run: nothing was written.`.
  - "Already at" output is unchanged.
  - `--install` prints no notes.
  - A target with no `CHANGELOG.md`, with an unknown `## ` heading, with no section for itself, and with non-UTF-8 bytes each print one `Release notes unavailable:` line, write the update, and keep the exit code (0 for a clean update, 1 with a conflict).
  - `CHANGELOG.md` is never written into the project.

  Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`.

## 2. The npm bundle

- [x] 2.1 In `create-switchyard/scripts/build.mjs`, add `CHANGELOG.md` to every bundled release commit: from the tag for older releases and from the working tree for the packed one. Fail the build with a clear message if a release has none. Keep the empty-path-list check counting only files under the path list. Verify with the tests in 2.2.
- [x] 2.2 In `create-switchyard/test/install.test.mjs`, add: every bundled tag has `CHANGELOG.md` with its own `## [X.Y.Z] - ` heading; an install leaves no `CHANGELOG.md` in the project; `update` from 0.7.2 prints `Release notes, 0.7.2 to <version>:` and the `## [<version>] - ` heading, and not `## [0.7.2] - ` or `Unreleased`. Verify with `npm test --prefix create-switchyard`.

## 3. Docs

- [x] 3.1 In `README.md` "Take a later release", replace "See the [Switchyard releases](...) for release notes." with a sentence saying the updater prints the changelog sections for the releases it moves across. Keep the link for readers who want older notes. Change no other line. Verify with `git diff README.md`.
- [x] 3.2 Add an `### Added` line for #93 under Unreleased in `CHANGELOG.md`. Verify the CI heading pattern still finds the newest release first.

## 4. Repository checks

- [x] 4.1 Run `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` and confirm it exits 0.
- [x] 4.2 Run `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` and confirm it exits 0.
- [x] 4.3 Run `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` and confirm it exits 0.
- [x] 4.4 Run `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` and record the counts.
- [x] 4.5 Run `npm test --prefix create-switchyard` and record the counts.
- [x] 4.6 Run `npx --yes @fission-ai/openspec validate --all --strict` and confirm it exits 0.

## Workflow follow-up

- Archive the change in the PR that completes it.
