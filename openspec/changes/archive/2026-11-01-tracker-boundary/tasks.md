# Tasks

## 1. Tracker script

- [x] 1.1 Add `switchyard/tracker.md` with the header and `Tracker: github`, as design.md shows. Verify: `python3 switchyard/scripts/tracker.py view 148` prints the issue.
- [x] 1.2 Add `switchyard/scripts/tracker.py` with `load_tracker`, `BACKENDS`, the `GitHub` backend, and the `view` and `set-change` subcommands, as design.md describes. Header of a few lines; no other comments unless a line needs a reason. Verify: tasks 1.3 and 1.4.
- [x] 1.3 Add `switchyard/scripts/test_tracker.py`. Use a fake `gh` on `PATH`, as `test_merge_queue.py` does, that logs its arguments and stdin. Cover: `view` prints title, state, body, and comments; `view` with no comments prints `No comments.`; `set-change` prepends the line and a blank line; `set-change` replaces an existing `Change:` first line; the body reaches `gh issue edit --body-file -` unchanged; a non-digit key exits non-zero without calling `gh`; a failing `gh` passes its exit status and stderr through. Verify: `python3 -m unittest discover -s switchyard/scripts -p 'test_tracker.py'` passes.
- [x] 1.4 In the same test file, cover `tracker.md` parsing with a temp file: unknown name exits 1 and lists `github`; no `Tracker:` line exits 1; two `Tracker:` lines exit 1; a missing file uses `github` and prints the note on stderr. Make the file path injectable for tests (an argument to `load_tracker`), not an environment variable. Verify: the same command passes.

## 2. Updater

- [x] 2.1 Add `switchyard/tracker.md` to `PROJECT_OWNED` in `update-switchyard.py`. Verify: `update-paths.txt` already covers it through `switchyard`.
- [x] 2.2 In `test_update_switchyard.py`, add tests that `tracker.md` is added when missing on install and update, and kept unchanged when the project edited it, following the `lessons.md` tests. Verify: `python3 -m unittest discover -s switchyard/scripts -p 'test_update_switchyard.py'` passes.

## 3. Callers and docs

- [x] 3.1 `switchyard/brief-template.md`: the Issue line reads `Read it with \`python3 switchyard/scripts/tracker.py view {issue}\`.` Verify: `git grep -n "gh issue" switchyard .claude AGENTS.md` returns nothing.
- [x] 3.2 `switchyard/roles/planner.md` step 2: name the command, `python3 switchyard/scripts/tracker.py set-change <issue> openspec/changes/<name>`.
- [x] 3.3 `AGENTS.md` Workflow: replace "with `gh issue edit`" with the `tracker.py set-change` command.
- [x] 3.4 `switchyard/SKILL.md`: in Before starting step 1, read issues with `tracker.py view`. Add one short paragraph, near Plans, saying `switchyard/tracker.md` names the tracker, the project owns it, and `scripts/tracker.py` is the only place that calls it; PRs stay on `gh pr`.
- [x] 3.5 `README.md`: add `tracker.md` to the install merge list, the "Make it yours" table, the updater paragraph that names project-owned files, and the layout tree. One line each.
- [x] 3.6 `CHANGELOG.md` Unreleased, `### Changed`: one line for #148 naming `tracker.py`, `tracker.md`, and the fixed empty issue read.

## 4. Checks

- [x] 4.1 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes. Stage the new files first so `git ls-files` sees them.
- [x] 4.2 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 4.3 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck -S info` passes.
- [x] 4.4 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 4.5 `git fetch --no-tags --depth=1 origin '+refs/tags/v*:refs/tags/v*' && npm test --prefix create-switchyard` passes.
- [x] 4.6 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it, and check the archive folder exists before reporting.
