# Tasks

## 1. The skill

- [x] 1.1 In `switchyard/SKILL.md` Routing, add a "Size" subsection with the three sizes, the criteria, and "between two sizes, take the larger", as in design.md. Verify: it names no language, framework, or tool.
- [x] 1.2 Replace "The first row for a role and provider is the default..." with the row-by-size rule from design.md: first row naming the size, else the first row with no size, else the first row and tell the maintainer. Say that a Use cell of `escalation` counts as `large`, and that a size and `when named` can share a cell. Verify: the provider rules for planner, implementer rotation, and reviewer are unchanged in wording.
- [x] 1.3 Extend rule 1 and the model paragraph: a size the maintainer names replaces the coordinator's; a named model replaces the model in the row the size picks. Verify: rules 1 to 3 keep their order.
- [x] 1.4 Remove the two escalation paragraphs ("For escalation, use..." and "Escalate a single issue only when..."). Verify: `git grep -n -i escalat switchyard/SKILL.md` prints only the `escalation` counts as `large` line.
- [x] 1.5 Replace "Say which provider and model each issue got." with the reporting rule from design.md.
- [x] 1.6 Per issue steps:
  - Step 3: size the issue from the Before starting read, record `plan_size` and `planner_row`, then start the planner on the row for that size.
  - Step 4: as the last bullet, size the reviewed change, record `size`, and tell the maintainer.
  - Step 5: pick the implementer row for `size` and record `implementer_row`.
  - Step 7 and the fix round in "Act on the verdict": use `size`, record `reviewer_row` and `implementer_row`. A fix round does not re-size.
  Give each `state.py set` as a full command with the row value quoted as one argument. Verify: in a scratch `git init` repo under the scratchpad, never the main checkout, `state.py init`, then each `set` command, then `get` returns the value with its spaces.

## 2. Routing file, README, changelog

- [x] 2.1 In `switchyard/routing.md`, add the header sentence and replace the Workers table with the one in design.md. Leave Providers, provider notes, and Coordinator unchanged. Verify: `git diff -- switchyard/routing.md` touches only the header and the Workers table, and `grep -nE 'gpt-|glm|kimi|claude-(opus|sonnet|haiku)-' switchyard/routing.md` prints nothing.
- [x] 2.2 In `README.md`, update the `routing.md` row in Make it yours and the "Several providers share the load" bullet. Change no other README text.
- [x] 2.3 Append one `#78` line under Unreleased, Added in `CHANGELOG.md`, with the content listed in design.md. Do not change `switchyard/VERSION`.

## 3. Check the rules

- [x] 3.1 Walk the new rules through three files, for each size and each role, with claude and codex as implementer:
  - `git show v0.7.2:switchyard/routing.md`: every pick matches today's row, except a `large` claude implementer gets the `escalation` row;
  - the new shipped file;
  - a copy where codex Implementer has only `small` and `large` rows, for a `medium` issue: the first codex Implementer row, with a note to the maintainer.
  Verify: each case has exactly one answer from the text of `SKILL.md`. Put the three tables in the PR body under Decisions to review.
- [x] 3.2 Run one headless turn with each new sized row's flags: claude Planner, Implementer, and Reviewer `small`, and codex Implementer `small` and `large`, each with the prompt `Reply with the word ok and nothing else.` Run from a scratch folder, not the worktree. Verify: each exits 0 and replies. Put the commands and exit codes in the PR body. If a provider's CLI is missing or over the usage threshold, say so in the PR body instead.

## 4. Repository checks

- [x] 4.1 Run `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` and confirm it exits 0.
- [x] 4.2 Run `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` and confirm it exits 0.
- [x] 4.3 Run `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` and confirm it exits 0.
- [x] 4.4 Run `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` and record the counts.
- [x] 4.5 Run `npx --yes @fission-ai/openspec validate --all --strict` and confirm it exits 0.

## Workflow follow-up

- Archive the change in the PR that completes it.
