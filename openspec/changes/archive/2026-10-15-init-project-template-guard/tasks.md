# Tasks

Read `.claude/answers/plan.md` first if it exists. Update the design and these tasks if an answer changes a decision.

## 1. Template guard

- [x] 1.1 In `init-project.py`, add `TEMPLATE_HEADING = "# Switchyard"` and a helper that reports whether a path is a regular file whose first line (UTF-8, `errors="replace"`, leading BOM stripped) starts with it (design D1). Verify with the tests in 1.4.
- [x] 1.2 Add `verify_template(root)` implementing design D2 with the messages in D5, called from `main` after `verify_work_tree` and before `changed_paths` (D4). Update the module docstring (D6). Verify no file operation runs before the call by reading `main`.
- [x] 1.3 In `test_init_project.py`, change `test_an_uncommitted_guide_is_not_moved` to write `# Switchyard: an agent coordination framework\n\nmy notes\n` and assert that exact content stays (design D3). Verify it passes.
- [x] 1.4 Add tests, each asserting exit 1, `not a fresh copy` and the deciding path on stderr, and every fixture file byte-identical after the run:
  - a committed `README.md` whose first line is `# My project`;
  - no `README.md` and no `docs/WORKFLOW.md`, with `LICENSE` present;
  - no `README.md` and a `docs/WORKFLOW.md` whose first line is not the marker;
  - a `README.md` whose marker is on the second line, after a blank line.
  Add a passing test where the first line is `# Switchyard for teams`. Verify `test_rerun_skips_absent_and_keeps_the_moved_guide` and `test_existing_destination_is_not_overwritten` pass unchanged. Run `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_init_project.py'` and verify all pass.

## 2. Changelog

- [x] 2.1 Edit the existing Unreleased / Added line for `init-project.py` in `CHANGELOG.md` to say it changes nothing when `README.md` is not Switchyard's guide. Keep it one line. Verify `git diff CHANGELOG.md` shows one line removed and one added.

## 3. Repository checks

- [x] 3.1 Run `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck`. Verify it exits 0.
- [x] 3.2 Run `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile`. Verify it exits 0.
- [x] 3.3 Run `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check`. Verify it exits 0.
- [x] 3.4 Run `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'`. Verify all tests pass and record the count.
- [x] 3.5 Run `npx --yes @fission-ai/openspec validate --all --strict`. Verify it exits 0.

## Workflow follow-up

- Archive the change after review, then verify the archived result.
