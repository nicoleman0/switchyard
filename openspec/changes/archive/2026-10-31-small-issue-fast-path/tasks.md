# Tasks

## 1. Roles

- [x] 1.1 In `switchyard/roles/implementer.md`, insert the fast-path paragraph from design.md before the "Fix rounds:" paragraph. Verify the rest of the file is unchanged with `git diff`.
- [x] 1.2 In `switchyard/roles/planner.md`, append the fast-path sentence from design.md as the last line. Verify with `git diff`.

- [x] 1.3 Reword the description in `.claude/agents/issue-implementer.md` as one sentence covering planning first on the fast path and the existing delivery duties. Leave the body unchanged.

## 2. Skill

- [x] 2.1 In `switchyard/SKILL.md`, append the fast-path text from design.md to Per issue step 3. Do not edit steps 4 and 5, the Coordinator section, or Act on the verdict. Verify with `git diff` that only step 3 and the Size section changed.
- [x] 2.2 In the Size section of `switchyard/SKILL.md`, append the fast-path line from design.md after the two-bullet list. Verify with `git diff`.

## 3. Shared docs (approved)

- [x] 3.1 In `README.md`, append the fast-path line from design.md after step 5 of "One issue, start to finish". Verify no existing line changed with `git diff`.
- [x] 3.2 In `CHANGELOG.md`, add the line from design.md under Unreleased in a new `### Changed` section. Verify with `git diff`.

## 4. Repository checks

- [x] 4.1 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 4.2 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 4.3 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` passes.
- [x] 4.4 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 4.5 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
