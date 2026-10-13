# Proposal

Delivers issue #29, "The workflow assumes every issue has a milestone".

## Why

`AGENTS.md` names milestones as the source of delivery order, the README tells the maintainer to pick one, the brief has a milestone field, and the PR step always passes `--milestone`. A project without milestones, this repository included, has no instruction to follow, so the coordinator drops the flag by its own judgment.

## What Changes

- Milestones become optional. An issue with a milestone is handled as before.
- The PR step passes `--milestone` only when the issue has one.
- The brief's milestone line reads "none" for an issue without one.
- `AGENTS.md` says where delivery order comes from in each case: the milestones when the project uses them, otherwise the order the maintainer names the issues in.
- The README no longer tells the maintainer to pick or create a milestone as a required step.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`. Switchyard is a template, and `openspec/specs/` ships empty to every project made from it, so the workflow's own rules live in the skill and the README.

## Impact

- `AGENTS.md`: the first Workflow bullet and the "New work" bullet.
- `.claude/skills/work-issues/SKILL.md`: step 5 of "Open the PR".
- `.claude/skills/work-issues/brief-template.md`: the milestone line.
- `README.md`: step 1 of "One issue, start to finish" and step 1 of "Use it".
- `openspec/config.yaml` and `CHANGELOG.md` only if the coordinator approves them. Both are outside the owned paths. See design.md.
- Projects that update from a release get the `AGENTS.md`, skill, and brief template edits through the updater's merge. No script changes.
