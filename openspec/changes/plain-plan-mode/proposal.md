# Proposal

Delivers GitHub issue #82.

## Why

Every issue needs a full OpenSpec change. The workflow needs a written plan with scenarios and tasks, not OpenSpec itself. A solo developer on small issues pays for ceremony the workflow does not use.

## What Changes

- A project uses OpenSpec when its repo has an `openspec/` folder. Without one it runs in plain mode.
- Plain mode: the planner copies a new `switchyard/plan-template.md` to `.switchyard/plan.md` and fills it with why, what changes, decisions, impact, scenarios, and tasks. The implementer works from it and ticks its tasks. The reviewer grades the diff against it. Nothing is archived, and the issue gets no `Change:` line.
- `SKILL.md` gains a short Plans section: "the change" means the OpenSpec change, or `.switchyard/plan.md` in plain mode. Other text keeps saying "the change".
- Roles, agent profiles, `AGENTS.md` Workflow, and the brief template name the plain-mode step where they name an OpenSpec step.
- `check-scope.sh`: `openspec/` is always in scope only when the main checkout has `openspec/`.
- `pre-review.sh`: in plain mode it skips "change archived" and "openspec", and adds a "plan" step that fails when `.switchyard/plan.md` is missing or has an unticked task.
- `setup-worktree.sh` (after #120): a best-of-N candidate also gets a copy of `.switchyard/plan.md`.
- Installer work moves to #138 with its own change: the OpenSpec question, flags, config filtering, and init hint.
- CI workflow: the OpenSpec validate step skips when there is no `openspec/` folder.
- README and CHANGELOG lines.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty in this repo and every change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- New: `switchyard/plan-template.md`.
- `switchyard/SKILL.md`: description, a new Plans section before Before starting, Per issue step 4 (two bullets), Open the PR step 1 (one clause). `.claude/skills/work-issues/SKILL.md`: description.
- `switchyard/roles/planner.md`, `implementer.md`, `reviewer.md`; `.claude/agents/*.md` descriptions.
- `AGENTS.md` Workflow; `switchyard/brief-template.md` Shared files.
- `switchyard/scripts/check-scope.sh`, `pre-review.sh`, `setup-worktree.sh`, and their tests.
- Shared, approved in answer 1: `.github/workflows/switchyard.yml`, `.github/ISSUE_TEMPLATE/issue.yml`.
- Not changed: `merge-queue.py` (its `openspec/specs/` rule never matches in plain mode), `state.py`, `teardown-worktree.sh`, `preflight.sh`, `init-project.py`, `update-switchyard.py`, and `create-switchyard/` (installer work is #138).
- Meets in-flight work: #114 (implementer Fix rounds paragraph), #119 (`check-scope.sh` loop), #120 (`setup-worktree.sh` copy, reviewer paragraph). Independent tasks may start after #114 and #119 merge, per the coordinator answer on 2026-11-01. Candidate-plan copying waits for #120.
