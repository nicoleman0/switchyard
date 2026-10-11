# Proposal

Delivers issue #9, "The coordinator reviews work it briefed itself".

## Why

One session writes the brief, reviews the plan, and reviews the diff, so nothing independent checks the work before the maintainer sees the PR. That session also holds every brief, plan, and diff of the batch in one context, and its reviews can grade the planner's summary instead of the change on disk.

## What Changes

- Add a reviewer role. After the implementer commits, a fresh session reads the brief, the answers, the OpenSpec change, and the diff, and writes a verdict to a file in the worktree.
- The reviewer runs on a different provider from the implementer. `start-worker.sh` refuses a reviewer on the implementer's provider unless the coordinator overrides it.
- The reviewer checks the diff against each scenario and task of the change, and checks that every plan answer was folded into the change before it was archived.
- The coordinator reads the verdict, not the diff. It opens the diff only to rule on a finding. Its PR review checklist moves to the reviewer.
- Fixes go back as the review file. A fresh implementer session reads it from disk, so the coordinator does not restate findings.
- The coordinator keeps plan review, and must read the change files there, not the planner's summary.
- The PR body gains a Review section that names the reviewer's provider and verdict.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`. Switchyard is a template, and `openspec/specs/` ships empty to every project made from it, so the workflow's own rules live in the skill and the README.

## Impact

- `.claude/skills/work-issues/SKILL.md`: routing table, per-issue steps, PR review, the fix loop.
- `.claude/skills/work-issues/roles/reviewer.md`: new. `roles/implementer.md`: fix rounds.
- `.claude/agents/issue-reviewer.md`: new Claude profile.
- `.claude/skills/work-issues/scripts/start-worker.sh`, `state.py`, `test_state.py`: record the implementer's provider and enforce the reviewer's.
- `.claude/skills/work-issues/brief-template.md`, `runners/*.md`: mention the reviewer where they name the roles.
- `README.md`, `CHANGELOG.md`: roles table, sequence diagram, steps, and an Unreleased entry.
- Projects that update from a release get the new role through the existing update paths. Each issue costs one more worker session.
