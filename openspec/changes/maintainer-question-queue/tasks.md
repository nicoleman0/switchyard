# Tasks

## 1. SKILL

- [x] 1.1 In `switchyard/SKILL.md`, insert the `## Question queue` section from the SKILL edits in `design.md`, word for word, between `## Batch state` and `## Before starting`.
- [x] 1.2 Per issue step 4: append ` Add them to the question queue.` to the bullet that starts `- Bring product decisions to the maintainer:`. Change no other line in the step.
- [x] 1.3 Per issue step 6: append ` Add questions only the maintainer can answer to the question queue.` after `Answer it with a file in \`.switchyard/answers/\` and a one-line prompt that points to the file.` Append ` Name the agents to wait for, and leave out any whose issue waits on questions.` after `Give \`wait-agents.sh\` a \`--timeout <seconds>\` bound.`
- [x] 1.4 Act on the verdict, Questions bullet: replace `and bring product decisions to the maintainer.` with `and add product decisions to the question queue.`
- [x] 1.5 Verify with `git diff switchyard/SKILL.md` that no other line changed and the new text has no em-dashes.

## 2. State

- [x] 2.1 In `switchyard/scripts/state.py` `status()`, after `phase = record.get("role") or "setup"`, add `if record.get("waiting"): phase += ", waiting"` (two lines). No other change.
- [x] 2.2 In `switchyard/scripts/test_state.py`, add `test_status_shows_waiting`: init a record with `role=planner` and `waiting=questions`, assert status prints `planner, waiting`; run `set <issue> waiting=`, assert status prints `planner` and not `waiting`.

## 3. Changelog

- [x] 3.1 `CHANGELOG.md`, under Unreleased `### Changed`, append: `- #118: Open maintainer questions wait in one queue, \`.switchyard/questions.md\`, so the coordinator goes on with other issues meanwhile. \`state.py status\` shows an issue with open questions as waiting.`

## 4. Checks

- [x] 4.1 `switchyard/hooks/checks.sh` passes from the worktree root.
- [x] 4.2 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
