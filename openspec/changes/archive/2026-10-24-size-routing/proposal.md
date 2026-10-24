# Proposal

Delivers issue #78, "Planner, implementer, and reviewer settings ignore how large an issue is".

## Why

Every issue gets the same planner, implementer, and reviewer row from `routing.md`. A typo fix and a schema migration run on the same model and effort, so small issues spend usage they do not need and large ones start under-powered. The only lever today is the `escalation` row, used when the plan review shows judgment the plan cannot capture.

## What Changes

- The coordinator sizes each issue `small`, `medium`, or `large`, twice:
  - before the planner starts, from its read of the issue against the code. The planner uses this size.
  - after the plan review, from the reviewed change. The implementer, fix rounds included, and the reviewer use this size.
- `SKILL.md` gets short, generic criteria for each size, and the rule for picking a row by size.
- A Workers row can name a size in its Use cell. Size picks a whole row, model and effort together, as the project wrote it. Switchyard does not read or rewrite any provider's flags.
- A row with no size is the default for its role and provider. It serves every size that has no row of its own.
- Size only picks the row within the provider the existing rules chose. Planner provider choice, implementer rotation, and the reviewer's other-provider rule do not change.
- What the maintainer names in the session still wins, including a size.
- The coordinator records both sizes and the row each role ran with in the issue's state record with `state.py set`, and tells the maintainer.
- A Use cell of `escalation` counts as `large`. The separate escalation step goes away: re-sizing after the plan review replaces it. Old `routing.md` files keep working with no edit. See design.md and question 1.
- The shipped `routing.md` adds `small` and `large` example rows using model aliases and effort only, and renames its `escalation` row to `large`.
- `README.md` and `CHANGELOG.md` describe the change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`, as every earlier workflow change did. `openspec/specs/` ships empty to every project made from the template, so the workflow's own rules live in `SKILL.md` and the README.

## Impact

- `switchyard/SKILL.md`: Routing section, Per issue steps 3, 4, 5, and 7, and the fix-round step.
- `switchyard/routing.md`: header sentence and example rows. The updater never replaces this file in existing projects, so only new projects and projects that add it get the new rows.
- `README.md`: the `routing.md` row in Make it yours, and the routing bullet in the overview.
- `CHANGELOG.md`: one Unreleased entry.
- No script changes. `state.py set` already stores any key.
