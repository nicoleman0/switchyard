# Tasks

## 1. Shared Change-line rule (refactor only)

- [x] 1.1 In `tracker.py`, move GitHub's prepend-or-replace logic into a module-level `with_change_line(body, path)` and call it from `GitHub.set_change`. No behaviour change. Verify: `python3 -m unittest discover -s switchyard/scripts -p 'test_tracker.py'` passes with the test file unchanged.

## 2. Linear backend

- [x] 2.1 Add `graphql_post(url, key)` and the `Linear` class with `check_key`, `view`, `set_change`, and an injectable `transport`, as design.md describes (queries, paging, errors, `LINEAR_API_KEY` read at call time, key never printed). Register `BACKENDS["linear"]`. Update the module docstring to list `check`. Verify: tasks 2.3 and 2.4.
- [x] 2.2 Add the `check` subcommand. GitHub's returns at once; Linear's runs `viewer { id }`. On success print the tracker name on stdout. Verify: task 2.3 covers both.
- [x] 2.3 In `test_tracker.py`, with a fake transport that records queries and variables: `view` prints `ENG-123 <title>`, `State: <name>`, description, comments sorted by `createdAt` across two pages, `unknown` for a null user, `No comments.` when empty, and an empty body for a null description; `set-change` sends the prepended and the replaced description through `issueUpdate` variables, and `success: false` exits 1; `errors` in a response exit 1 with each message; `149` and `eng-123` exit 2 without calling the transport; a missing `LINEAR_API_KEY` exits 1 before any call and the message names the variable; `check` on GitHub prints `github` and calls nothing. Verify: `python3 -m unittest discover -s switchyard/scripts -p 'test_tracker.py'` passes.
- [x] 2.4 In the same file, run `graphql_post` against an `http.server` on `127.0.0.1` in a thread: the request has `Authorization: <key>` with no `Bearer`, JSON content type, and the query and variables in the body; a 400 with a JSON `errors` body reports the messages; a 500 with a non-JSON body names the status; a closed port raises `TrackerError` naming the URL; no message contains the key. Verify: same command passes.
- [x] 2.5 `load_tracker` tests: `Tracker: linear` returns a `Linear`; the unknown-name message lists `github` and `linear`. Verify: same command passes.

## 3. Issue keys in the workflow scripts

- [x] 3.1 `state.py`: `valid_key` accepts `([0-9]+|[A-Z][A-Z0-9]*-[0-9]+)b?`; `key_order` returns `(team, number, key)` with `team = ""` for digits; the `fail` message names both forms; add `check-key <key>` (exit 0, or the `fail` message and exit 1) and list it in the usage line. Verify: new `test_state.py` tests for `ENG-123`, `ENG-123b`, `A1-7`, rejects for `eng-123`, `ENG-`, `ENG-12a`, `-12`; `status` lists `9`, `10`, `ENG-2`, `ENG-10`, `OPS-1` in that order; `check-key` exit codes.
- [x] 3.2 `setup-worktree.sh`: call `state.py check-key` first for the issue and for `--parent`, and remove the digits `case`. Update the usage lines to `<issue>[b]`. Verify: `test_state.py` tests that `setup-worktree.sh ENG-123 eng-123-x` creates the record, `ENG-123b` sets up candidate b from `ENG-123`, and `setup-worktree.sh eng-123 topic` exits non-zero with no worktree directory and no `topic` branch.
- [x] 3.3 `start-worker.sh`: lowercase the key in the Herdr agent name with `tr`, as design.md shows. Verify: a `test_state.py` test with the Herdr stub accepting `planner-eng-7` starts `ENG-7` and records `planner_worker=planner-eng-7`.
- [x] 3.4 `hooks/worktree-up.sh`: port from `${ISSUE##*-}` with `10#`, and one comment line that two teams' equal numbers share a port. Verify: a test runs the hook with `ISSUE=ENG-123` and `CANDIDATE=` then `b` and gets `port=3123` and `port=4123`; with `ISSUE=8` it still prints `port=3008`.
- [x] 3.5 `merge-queue.py`: no code change expected; add a `test_merge_queue.py` case that `ENG-5` is accepted as a key and children sort with `key_order`. Verify: `python3 -m unittest discover -s switchyard/scripts -p 'test_merge_queue.py'` passes.
- [x] 3.6 Usage lines that say `<issue-number>` in `check-scope.sh`, `pre-review.sh`, `restack.sh`, `teardown-worktree.sh`, `end-worker.sh`, and `start-worker.sh` say `<issue>`. Verify: `git grep -n "issue-number\|issue number required" switchyard` returns nothing.
- [x] 3.7 `runners/herdr.md`: agent names use the lowercased key. Verify: one sentence changed.

## 4. Install and preflight

- [x] 4.1 `update-switchyard.py`: add `--tracker` with `choices=("github", "linear")` and the install, update, and `--check` behaviour in design.md. Verify: `test_update_switchyard.py` tests that install with `--tracker linear` adds `tracker.md` with `Tracker: linear` and the rest of the target's content; an existing `tracker.md` is kept and the keep message printed; a target without `tracker.md` and `--tracker linear` exits 2 and writes nothing; `--tracker jira` exits 2; an update with `--tracker` prints the ignore line; `--check --tracker linear` exits 2; the `choices` equal `tracker.BACKENDS` keys.
- [x] 4.2 `create-switchyard.mjs`: accept one OpenSpec flag plus `--tracker <name>` or `--tracker=<name>`, forward them, fall back to `npm_config_tracker`, and update the usage text. Verify: `install.test.mjs` tests that `--tracker jira` and `npm_config_tracker=jira` each exit 2 with `invalid choice` from the updater; `--tracker` with no value prints usage and exits 2; both OpenSpec flags still exit 2.
- [x] 4.3 `preflight.sh`: after the GitHub CLI check, run `python3 "$script_dir/tracker.py" check`. Print `ok       Linear` when it prints `linear`, nothing when it prints `github`, and `MISSING  Tracker: <stderr>` on failure, counted as missing. Move the `script_dir` lines up so both uses share them. Verify: `test_preflight.py` tests with a temp skill folder whose `tracker.md` says `linear`: unset key prints `MISSING` naming `LINEAR_API_KEY` and exits non-zero; GitHub output has no tracker line.

## 5. Docs

- [x] 5.1 `switchyard/SKILL.md` Per issue step 1: one sentence that on Linear the branch starts with the lowercased key, such as `eng-123-fix-login`. Verify: read the step.
- [x] 5.2 `README.md`: a short "Use Linear" section (install flag with `--`, `LINEAR_API_KEY`, branch names, PRs on GitHub, Linear's GitHub integration must be connected), and `--tracker linear` next to `--no-openspec` in the install section. Verify: read it against the Writing rules in `AGENTS.md`.
- [x] 5.3 `CHANGELOG.md` Unreleased, `### Added`: one line for #149. Verify: read it.

## 6. Checks

- [x] 6.1 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes. Stage new files first.
- [x] 6.2 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 6.3 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck -S info` passes.
- [x] 6.4 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 6.5 `git fetch --no-tags --depth=1 origin '+refs/tags/v*:refs/tags/v*' && npm test --prefix create-switchyard` passes.
- [x] 6.6 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it. This is the first change with a spec delta, so archiving creates `openspec/specs/issue-tracker/spec.md`. Check the archive folder and the spec exist before reporting.
- PR body: say it is untested against live Linear.
