# Proposal

Delivers issue #151, "Delivery order cannot come from a Linear project".

## Why

The maintainer names the issues and their order in every session. On Linear, a project already holds that order: its milestones, the issue order inside each, and "blocked by" relations. #149 and #150 made Linear a tracker; this change lets the coordinator read the order from it.

## What Changes

- `tracker.py list <project>` prints a Linear project's open issues in delivery order. Each line has the key, status, milestone, open blockers, and title. Completed, canceled, and duplicate issues are left out. Results are paged.
- The project is named by its name, matched without case, or its slug id. No match fails and lists close names, or every visible project. Several matches fail and list each with its slug id.
- The script orders the issues: milestones in their project order, issues without a milestone last, then Linear's manual issue order. An issue blocked by an open issue in the project moves after it. A cycle in "blocked by" fails and names the issues in it.
- An open blocker outside the project is shown, marked `outside`. A closed blocker is ignored and not shown.
- On GitHub, `list` exits 2 and says to name the issues. GitHub delivery order does not change.
- `SKILL.md` Before starting, steps 1 and 2: on Linear, when the maintainer names a project, run `list`, deliver in its order, and hold an issue until its open blockers merge.
- `AGENTS.md` Workflow, README "Use Linear", and CHANGELOG mention a Linear project as a source of order.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `issue-tracker`: adds the `list` operation, project naming, the ordering rule, and how the coordinator uses it. Existing requirements are unchanged.

## Impact

- `switchyard/scripts/tracker.py`, `test_tracker.py`: `list` and its tests with the injected transport.
- `switchyard/SKILL.md`: Before starting, steps 1 and 2.
- `AGENTS.md`, `README.md`, `CHANGELOG.md`.
- No new dependency. Untested against live Linear: no API key in this environment.
