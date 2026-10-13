# Proposal

Delivers issue #24, "The template decides which models a project uses".

## Why

Model names, effort levels, and provider flags sit in files the updater owns: the routing table and the Codex coordinator profile in `SKILL.md`, and the frontmatter of the three Claude profiles. A project that wants another model edits those files, so the edit conflicts with later releases or goes upstream as if it were generic.

## What Changes

- Add `.claude/skills/work-issues/routing.md`. It holds every model, effort level, and provider flag: one row per role and provider, the escalation row, and the coordinator's model and effort for each provider. The template ships it with today's values as examples, except the opencode Implementer model moves to GLM 5.3 Flash because Kimi K3 uses too many tokens.
- The project owns `routing.md`. The updater adds it when the project has no such file, and never updates, merges, or removes it.
- `SKILL.md` keeps the generic rules and reads the values from `routing.md`: which roles exist, the planner on the coordinator's provider, the implementer rotation, the reviewer on another provider, and when to skip a provider. The rules are reworded so they hold when a provider is absent from the file or has two rows for one role.
- **BREAKING** The Claude profiles in `.claude/agents/` drop `model` and `effort`. Claude workers get both from `--model` and `--effort` in their `routing.md` row. A project that edited a profile's model gets a conflict on update and moves the value to `routing.md`.
- `start-worker.sh` refuses to start a worker when `routing.md` is missing, and says how to get it.
- The runner files, `AGENTS.md`, and the README point to `routing.md` as the one home for models.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`, as the reviewer-role change did. `openspec/specs/` ships empty to every project made from the template, so the workflow's own rules live in the skill and the README.

## Impact

- `.claude/skills/work-issues/routing.md`: new.
- `.claude/skills/work-issues/SKILL.md`: Routing section, the escalation step, the Codex coordinator profile, and the steps that name the routing table.
- `.claude/agents/issue-planner.md`, `issue-implementer.md`, `issue-reviewer.md`: no `model` or `effort`.
- `.claude/skills/work-issues/scripts/update-switchyard.py`, `test_update_switchyard.py`: the project-owned rule and its tests.
- `.claude/skills/work-issues/scripts/start-worker.sh`, `test_state.py`: the missing-file check and its test.
- `.claude/skills/work-issues/runners/headless.md`, `runners/herdr.md`: references.
- `AGENTS.md`, `README.md`, `CHANGELOG.md`: where models are set, how the updater treats the file, and the migration note. `CHANGELOG.md` is outside the issue's owned paths; see the question in design.md.
- `VERSION` does not change. Earlier feature PRs left it alone and a separate release PR bumped it with the changelog heading.
- Projects on 0.3.0 to 0.5.0 that update get `routing.md` added by their own updater. See design.md.
