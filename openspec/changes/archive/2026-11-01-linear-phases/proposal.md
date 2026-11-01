# Proposal

Delivers issue #150, "Linear issues do not show questions or phases".

## Why

With Linear as the tracker, the maintainer still answers plan questions in the local `.switchyard/questions.md`, and the Linear issue does not show which phase it is in. #149 added the Linear backend; this change uses it for questions and status.

## What Changes

- `tracker.py set-phase <issue> <phase>` moves a Linear issue to the status for a phase: `planning`, `plan-review`, `building`, `in-review`, or `needs-input`. Default status names live in `tracker.py`. An optional `Phase | Status` table in `tracker.md` overrides them. A status the issue's team lacks fails and lists the team's statuses. On GitHub, `set-phase` checks its arguments and does nothing else.
- `tracker.py comment <issue> <file>` posts a file as an issue comment, on both trackers.
- `start-worker.sh` sets the phase for the role it starts: planner `planning`, implementer `building`, reviewer `in-review`. A tracker failure stops the start before any worker or record change, with the tracker's message.
- The coordinator sets `plan-review` when the planner stops, and `needs-input` when it posts questions.
- On Linear, an issue's open questions go out as one comment whose first line is a fixed marker. Answers are the comments after the newest marker comment, or the chat. The coordinator copies them to the answers file and moves the issue back to its phase. GitHub keeps `.switchyard/questions.md`.
- Done stays with Linear's GitHub integration, which moves the issue when the PR merges.
- A test pins that `state.py` and `tracker.py` accept the same Linear keys (deferred from #149's review).
- README "Use Linear" lists the statuses to add and the override table. CHANGELOG gets an Unreleased line.

GitHub behaviour does not change. Delivery order from a Linear project is #151.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `issue-tracker`: adds the phase and comment operations, phase status names and their override, worker phase updates, and Linear questions. Existing requirements are unchanged.

## Impact

- `switchyard/scripts/tracker.py`, `test_tracker.py`: `set-phase`, `comment`, the status table, the key-agreement test.
- `switchyard/scripts/start-worker.sh`, `test_state.py`: phase by role.
- `switchyard/tracker.md`: one line pointing to the optional table. Existing installs keep their file and get the defaults.
- `switchyard/SKILL.md`: plan-review phase, Linear branch of the Question queue.
- `README.md`, `CHANGELOG.md`.
- No new dependency. Untested against live Linear: no API key in this environment.
