# Tasks

Read `.claude/answers/plan.md` first. Where an answer differs from design.md, update design.md and these tasks before you write code.

## 1. Tracer: one required check, end to end

- [x] 1.1 Add `scripts/preflight.sh`, executable, with the `git` check only: an `ok` or `MISSING` line, the summary line, and exit status 1 when anything is missing. Use only bash builtins and the checked tools. Verify: `git ls-files -s` shows mode `100755`, and shellcheck passes.
- [x] 1.2 Add `scripts/test_preflight.py` with a harness that builds a stub directory, sets `PATH` to it alone, sets `HOME` and `CODEX_HOME` to temporary folders, and runs the script with bash by absolute path. Verify: one test passes with a stub `git`, and one asserts exit 1 and a `MISSING` line naming git without it.

## 2. Required checks

- [x] 2.1 Add Python 3, Node.js with `npx`, and the GitHub CLI. Verify: a test per item asserts exit 1 and a `MISSING` line that names the item and a fix.
- [x] 2.2 Add the sign-in check with `gh auth status`, run only when `gh` is found. Verify: tests cover a stub `gh` that exits 0, one that exits 1, and no `gh`; the last prints one line for `gh`, not two.
- [x] 2.3 Add the worker CLI check as design.md's table has it. Verify: tests cover `claude` alone, `codex` alone, `opencode` alone, and none.
- [x] 2.4 Verify that nothing exits early: a test with no stubs at all asserts that every required item has a `MISSING` line and the summary counts them.

## 3. Optional checks

- [x] 3.1 Add Herdr and the image tool. Verify: tests assert a `warn` line and exit 0 when each is absent, and that `magick` alone and `sips` alone both pass.
- [x] 3.2 Add the Playwright probe through `node`, reading `SHOTS_PACKAGE_DIR` as `shots.mjs` does. Add a one-line comment in the script and in `shots.mjs` that names the other file. Verify: tests with a stub `node` cover found and not found, and a run without `node` prints the Node.js `MISSING` line and no second failure.
- [x] 3.3 Add the second-provider warning. Verify: tests assert the warning with one CLI and no warning with two.
- [x] 3.4 Add the Codex profile check under `${CODEX_HOME:-$HOME/.codex}`. Verify: tests cover `codex` with the file, `codex` without it, `CODEX_HOME` unset with the file under `HOME`, and no `codex`, which prints no profile line.
- [x] 3.5 Verify the full pass: a test with every stub present asserts exit 0, no `MISSING`, and no `warn`.

## 4. Docs

- [x] 4.1 In `SKILL.md`, add the paragraph from design.md above the numbered list in "Before starting". Change no other line. Verify: `git diff --stat` shows only added lines in `SKILL.md`, all inside that section.
- [x] 4.2 In `README.md`, add the one line from design.md at the end of the Requirements list. Change no other line. Verify: `git diff` shows one added line in `README.md`.
- [x] 4.3 If the plan answers allow it, add one line under Unreleased in `CHANGELOG.md`. Verify: the diff adds lines only.

## 5. End to end

- [x] 5.1 Run `scripts/preflight.sh` from the worktree's standard layout on a real machine. Then run it again with `gh` and with every worker CLI hidden from `PATH`. Verify: the PR body quotes both outputs and their exit statuses, and says which runner and providers were present.

## 6. Repository checks

- [x] 6.1 `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck` passes.
- [x] 6.2 `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 6.3 `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 6.4 `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'` passes, with the test count in the PR body.
- [x] 6.5 `npx @fission-ai/openspec validate --all --strict` passes.
