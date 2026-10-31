# Proposal

Delivers GitHub issue #116.

## Why

Every issue stops after planning for the coordinator to review the plan, then starts a new implementer session. For a `small` issue the review rarely changes anything, and the stop costs a session start and a context reload.

## What Changes

- A `small` issue takes a fast path: one implementer session plans and implements.
- The session stops after the plan only when it has numbered questions, or when it finds the issue is bigger than `small`. Otherwise it goes on to build, check, archive, and commit as an implementer does today.
- The coordinator skips the plan review and the second sizing for a fast-path issue. The size stays `small`. At the review step it reads the change along with the reviewer's verdict.
- When the session says the issue is bigger than `small`, the coordinator falls back to the normal plan review and re-size, then starts a new implementer.
- `medium` and `large` issues keep the plan stop.
- The fast-path session uses the Implementer row for `small` and starts with role `implementer`, so the existing scripts record it as the implementer and the reviewer check works unchanged. No new routing row.
- `README.md` and `CHANGELOG.md` get one line each (approved in the coordinator's answers).

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty and this repo sets `skip_specs: true` on every change.

### Modified Capabilities

None.

## Impact

- `switchyard/SKILL.md`: Per issue step 3 and the Size section.
- `switchyard/roles/implementer.md`: one fast-path paragraph.
- `switchyard/roles/planner.md`: one sentence pointing to the fast path.
- `README.md`, `CHANGELOG.md`: one appended line each.
- `.claude/agents/issue-implementer.md`: one-sentence description covering planning first on the fast path.
- No script, test, or routing change.
