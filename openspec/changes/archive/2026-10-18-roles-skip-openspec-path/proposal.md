# Proposal

## Why

Delivers GitHub issue #64. `AGENTS.md` lets work that changes no observable behaviour skip OpenSpec, but the planner, implementer, and reviewer roles assume a change with a spec delta. While delivering #61, #62, and #63, the coordinator overrode all three roles and invented a git-ignored `.switchyard/plan.md`. Every coordinator would have to invent that again.

## What Changes

- One path for every issue delivered through the `work-issues` workflow: it gets an OpenSpec change. Work with no observable behaviour change sets `skip_specs: true` in the change's `.openspec.yaml`. No second path and no separate plan file.
- `switchyard/roles/planner.md`: replace "Skip OpenSpec only where AGENTS.md says to" with how to set `skip_specs: true` and when.
- `switchyard/roles/implementer.md`: the archive step syncs a spec delta only when the change has one.
- `switchyard/roles/reviewer.md`: with `skip_specs: true` there are no scenarios. Grade each task, and the diff against the design's decisions when the change has a design.
- `switchyard/SKILL.md`: the plan review reads no spec delta for a `skip_specs: true` change, and checks the flag is only set when no observable behaviour changes.
- `AGENTS.md` Workflow: say which rule applies where. Through the workflow, a change with `skip_specs: true`. A hand-made PR outside it may still use an issue and PR with no change.
- `README.md`: the same split in "Not everything needs the crew", and the planner step notes that a `skip_specs: true` change has no spec delta.
- CHANGELOG entry under Unreleased.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty and this change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- Docs and role files only: `switchyard/roles/{planner,implementer,reviewer}.md`, `switchyard/SKILL.md`, `AGENTS.md`, `README.md`, `CHANGELOG.md`.
- `AGENTS.md`'s Workflow section is merged into adopters' repos by the updater, so the edit stays one self-contained bullet.
- Out of scope: OpenSpec-generated files (`.claude/skills/openspec-*`, `.claude/commands/`, `.opencode/`, `.agents/`), the `.claude/agents/*.md` wrappers, scripts, and a version bump.
