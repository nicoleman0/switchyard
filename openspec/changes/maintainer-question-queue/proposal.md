# Proposal

Delivers GitHub issue #118.

## Why

When a plan or a worker raises a product question, the coordinator brings it to the maintainer and waits. Other issues could keep moving, and questions from several issues reach the maintainer one at a time.

## What Changes

- Open maintainer questions go to one queue file, `.switchyard/questions.md` in the main checkout. It is already ignored, like the state records. One section per issue, each question with options, a recommendation, and an `Answer:` line.
- The coordinator shows the maintainer the whole queue in one message, goes on with the other issues, and checks the queue each time a wait returns. When an issue's questions are all answered, it copies the answers into that worktree's `.switchyard/answers/`, removes the section, and resumes the issue.
- An issue with open questions records `waiting=questions`. `state.py status` shows its phase as `<phase>, waiting`. `state.py set <issue> waiting=` clears it.
- `switchyard/SKILL.md`:
  - A new `## Question queue` section after Batch state holds the rules and the format.
  - Per issue step 4: product decisions go to the queue.
  - Per issue step 6: maintainer questions go to the queue; leave a waiting issue's agent out of `wait-agents.sh`.
  - Act on the verdict, Questions bullet: product decisions go to the queue.
- `CHANGELOG.md`: one line under Unreleased.
- No new script. The queue is a Markdown file the coordinator edits.
- Unchanged: Before starting step 1 (questions asked before any agent starts already arrive in one pass), the role files, `brief-template.md`, the runners, README.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty in this repo and every change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- `switchyard/SKILL.md`: one new section, one line each in step 4, step 6, and the Questions bullet.
- Shared, pending the coordinator's answer: `switchyard/scripts/state.py` (`status` reads the `waiting` field, about three lines) and `switchyard/scripts/test_state.py` (one test). The new SKILL section sits outside the named sections.
- `CHANGELOG.md`: one line.
- #114 edits steps 5 to 7 and Act on the verdict in parallel. This change touches only step 6's last paragraph and the Questions bullet there.
