# Design

## Context

See proposal.md for why. The maintainer settled the shape: every workflow issue gets a change, and `skip_specs: true` marks one with no observable behaviour change.

How OpenSpec handles the flag, checked against CLI 1.14.1 in this repo:
- `openspec new change <name>` has no flag for it. The planner appends `skip_specs: true` to the new change's `.openspec.yaml` before writing any artifact.
- `openspec status` then reports `specs` as `skipped`. The propose skill treats a skipped artifact as satisfied and must not create it. The archive skill accepts `skipped` and has no delta to sync.
- `openspec validate --strict` rejects a change with no delta unless the flag is set.

## Goals / Non-Goals

**Goals:**
- Each role reads right for a `skip_specs: true` change without coordinator overrides.
- `AGENTS.md` says which rule applies inside the workflow and which outside it.

**Non-Goals:**
- Requiring `design.md` for `skip_specs: true` changes. OpenSpec keeps it optional, and each task already states its own check.
- Editing OpenSpec-generated files or the `.claude/agents/` wrappers. The reviewer wrapper's "scenarios and tasks" stays accurate when scenarios exist.

## Decisions

- **Planner decides the flag; coordinator checks it.** The planner applies the `AGENTS.md` rule when it proposes. The coordinator confirms it at plan review. Alternative: the coordinator sets it in the brief. Rejected: the planner has read the code and is better placed, and the coordinator can still say so in the brief notes.
- **Point at `AGENTS.md` for the cases, do not copy them.** The roles name the flag and how to set it. The list of cases (bugs where code diverges from the spec, tooling, infrastructure, refactors) stays only in `AGENTS.md`, so an adopter who edits it does not need to edit the roles.
- **Reviewer grades tasks, plus design decisions when a design exists.** With no scenarios, the tasks carry the acceptance checks. Alternative: require a design and grade it always. Rejected as a non-goal above.
- **AGENTS.md: rewrite the one existing bullet in place.** The updater merges the Workflow section, so a single self-contained bullet keeps the merge small.

## Risks / Trade-offs

- [A planner sets `skip_specs: true` on work that does change behaviour, so no spec records it] → The coordinator checks the flag at plan review, and SKILL.md says so.
- [Adopters who already merged the old `AGENTS.md` bullet with local edits] → The updater reports a conflict inside the owned section, as it does for any edit.
