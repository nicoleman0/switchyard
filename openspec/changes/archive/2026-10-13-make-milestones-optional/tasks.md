# Tasks

Edit only the lines each task names. Do not reflow, reorder, or reword text around them. The wording is in design.md.

## 1. Skill and brief

- [x] 1.1 In `.claude/skills/work-issues/SKILL.md`, rewrite step 5 of "Open the PR": the command without `--milestone`, and one sentence that adds the flag when the brief names a milestone. Verify: `grep -n "milestone" .claude/skills/work-issues/SKILL.md` shows only the description line and step 5.
- [x] 1.2 In `.claude/skills/work-issues/brief-template.md`, change the milestone placeholder to `{milestone, or "none"}`. Verify: the line still starts with `- Milestone for the PR:` and the file has no other change.

## 2. Project rules

- [x] 2.1 In `AGENTS.md`, replace the first Workflow bullet with the wording in design.md. Verify: the bullet names the source of delivery order with milestones and without them.
- [x] 2.2 In `AGENTS.md`, change `(problem and milestone)` in the "New work" bullet. Verify: `git diff AGENTS.md` shows two changed lines and nothing else.

## 3. README

- [x] 3.1 In `README.md`, rewrite step 1 of "One issue, start to finish". Verify: the step no longer requires a milestone.
- [x] 3.2 In `README.md`, rewrite step 1 of "Use it" and drop `--milestone "M1"` from its command. Verify: the list still renders with the code block inside item 1, and "Run the next steps of milestone M2." is unchanged.

## 4. Depends on the coordinator's answers

- [x] 4.1 Approved: in `openspec/config.yaml`, reword the `context` line so milestones are not assumed. Verify: `npx @fission-ai/openspec validate --all --strict` passes.
- [x] 4.2 Approved: add a line under Unreleased, in a Changed group, in `CHANGELOG.md`. Verify: the entry says milestones are optional and that `--milestone` is passed only for an issue that has one.
- [x] 4.3 Dropped per the coordinator's answer: "Run the next steps of milestone M2." stays as it is, with no note.

## 5. Check the result

- [x] 5.1 Run `grep -rni milestone --exclude-dir=.git --exclude-dir=archive .` and confirm every remaining mention reads as optional or is a valid example for a project with milestones. Put the list in the PR body.
- [x] 5.2 Run `git diff --stat origin/main...HEAD` and confirm only the files named above changed, plus this change's files.

## 6. Repository checks

- [x] 6.1 `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck` passes.
- [x] 6.2 `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 6.3 `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 6.4 `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'` passes, with the test count in the PR body.
- [x] 6.5 `npx @fission-ai/openspec validate --all --strict` passes.
