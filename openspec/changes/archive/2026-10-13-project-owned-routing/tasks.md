# Tasks

## 1. Updater: project-owned paths

- [x] 1.1 In `scripts/update-switchyard.py`, add a `PROJECT_OWNED` constant holding `.claude/skills/work-issues/routing.md`. In the loop over paths, handle a project-owned path first: add it when the target has the file and the project has no file there, and otherwise take no action. Verify: the tests in 1.2 pass.
- [x] 1.2 In `scripts/test_update_switchyard.py`, add tests for `routing.md`, each asserting the file's bytes, the exit code, and the report lines:
  - the project edited it and the release changed it: unchanged, exit 0, no line for the path;
  - the project did not edit it and the release changed it: unchanged, no `updated` line;
  - the project has no file and the release has one: `added`, with the release's content;
  - the base release had no file, the project has its own, and the release adds one: unchanged, no `conflict`;
  - the release deletes it: the project's file stays, no `removed` or `kept` line;
  - another file under the same folder still updates in the same run.
- [x] 1.3 Confirm `update-paths.txt` needs no change. Verify: `git diff origin/main -- .claude/skills/work-issues/update-paths.txt` is empty.

## 2. The routing file

- [x] 2.1 Add `.claude/skills/work-issues/routing.md` with the header, the worker table, and the Coordinator table from design.md. Verify: every model, effort level, and flag in the `v0.5.0` `SKILL.md` and profiles appears in the file except `opencode-go/kimi-k3`, and the header says the file is the project's and names the provider limits.
- [x] 2.2 Remove `model` and `effort` from the three profiles in `.claude/agents/`, and drop the body sentence about model and effort. Verify: `grep -n "model\|effort" .claude/agents/*.md` prints nothing.

## 3. The skill and the runners

- [x] 3.1 Rewrite the Routing section of `SKILL.md`: remove the table, point to `routing.md`, and state the rules from design.md for the planner, the rotation, a second row, the reviewer, escalation, and a missing file or row. Keep the usage threshold text, the fresh-session paragraph, and the no-push paragraph as they are. Verify: `grep -n "gpt-\|kimi\|opus\|sonnet\|--effort\|model_reasoning_effort=" .claude/skills/work-issues/SKILL.md` prints nothing.
- [x] 3.2 In the Codex coordinator profile section, replace the model and effort values with placeholders that name the Coordinator table. Keep `approvals_reviewer = "user"` and its explanation. Verify: the section tells a maintainer where both values come from.
- [x] 3.3 Read the Routing rules against three edited copies of the file: no opencode rows, no codex rows, and a second Implementer row for opencode. Verify: each rule gives one answer in each case, with no edit to the skill. Put the three walk-throughs in the PR body under Decisions to review.
- [x] 3.4 Check every other mention of the routing table: `SKILL.md` steps 3, 5, and 7, `runners/headless.md`, `runners/herdr.md`, and the usage line of `start-worker.sh`. Add the path where a reader would otherwise look in `SKILL.md`. Verify: `grep -rn -i "routing" .claude/skills/work-issues AGENTS.md README.md` shows no line that places a model or a flag anywhere but `routing.md`.
- [x] 3.5 In `scripts/start-worker.sh`, exit 1 before any record change when `routing.md` is not a file in the skill folder, with a one-line message that names the path and how to get the file. Add `routing.md` to the fixture in `scripts/test_state.py`, and a test that a start without it fails and leaves the record unchanged. Verify: the new test passes and the existing start-worker tests still pass.

## 4. Docs

- [x] 4.1 Update `AGENTS.md`: the line that says what the skill holds. Verify: it names `routing.md` as the project's file for models, effort, and flags.
- [x] 4.2 Update `README.md`: add a `routing.md` row to the "Make it yours" table, remove the sentence that names two places, say in "Take a later release" that the updater adds the file once and never changes it, and fix the layout tree for `agents/`, `SKILL.md`, and the new file. Verify: `grep -n -i "model" README.md` shows no line that sends a reader to `SKILL.md` or `.claude/agents/` to change a model.
- [x] 4.3 If answer 4 allows it, add an Unreleased entry to `CHANGELOG.md` under Changed. It says: models, effort, and flags moved to `routing.md`; the updater adds the file and never changes it; the profiles no longer set a model; and what to do after updating (review the added file, and resolve a conflict in `SKILL.md` or a profile by taking the release's side and moving the values to `routing.md`). Do not change `VERSION`. Verify: `git diff origin/main -- .claude/skills/work-issues/VERSION` is empty.

## 5. End to end

- [x] 5.1 In a scratch repo, build a project from `git archive v0.5.0`, tag this branch's tree as a later release in a scratch clone, and run the project's own updater against it. Repeat with a project that changed a profile's model and one that changed a row of the `SKILL.md` table. Verify: the first run reports `added` for `routing.md` and exits 0; the others report `conflict` on the edited file and exit 1. Put the report lines in the PR body.
- [x] 5.2 In the updated scratch project, edit `routing.md`, commit, tag a further scratch release that changes the example values, and update again. Verify: `routing.md` keeps the project's edit and the report has no line for it.
- [x] 5.3 Start a headless Claude worker with the Implementer row's flags and a prompt that asks which model it runs on, then again with the escalation row. Verify: each run reports the row's model, which shows `--model` applies to a profile with no `model`. Put both answers in the PR body.

## 6. Repository checks

- [x] 6.1 `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck` passes.
- [x] 6.2 `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 6.3 `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 6.4 `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'` passes, with the test count in the PR body.
- [x] 6.5 `npx @fission-ai/openspec validate --all --strict` passes.
