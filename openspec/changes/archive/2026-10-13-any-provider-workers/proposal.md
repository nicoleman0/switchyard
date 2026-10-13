# Proposal

Delivers issue #34, "A project cannot run every role on the provider it chooses". It covers #27 (the one-provider setup) and #40 (where `<flags>` comes from on the headless runner).

## Why

The workflow knows three providers and gives them unequal roles. `start-worker.sh` holds the list and refuses a reviewer on opencode. The runner files hold each CLI's commands, and the updater owns those files, so a fourth CLI is a skill change. The project's maintainer should choose the providers and models. The template's values are examples.

## What Changes

- `routing.md` gains a Providers table: one row per provider with how it runs on Herdr, how to end it, and its first-turn and later-turn commands. Provider notes sit under the table. The project adds a provider by adding rows to this file only.
- pi is the fourth provider, shipped as example rows for all three roles.
- `routing.md` says its values are examples. `SKILL.md` states one order of precedence: what the maintainer names in the session, then the row in `routing.md`, then the coordinator's own choice, which it reports before the worker starts.
- **BREAKING** `SKILL.md` no longer says "Never choose a model yourself", and no longer stops when `routing.md` or a row is missing. `start-worker.sh` no longer refuses to start without `routing.md`.
- `start-worker.sh` takes any provider. A provider is named after its CLI command, and the script refuses a name that is not a command on `PATH`. It no longer refuses a reviewer on opencode.
- Every worker that runs as turns gets a new session id at each start, so a second role or a fix round on the same provider starts fresh. opencode no longer reuses `ses_issue<issue>`.
- The same-provider rule and `SWITCHYARD_SAME_PROVIDER` stay in `start-worker.sh`. A project with one provider needs no setting: the coordinator sets the override when no other Reviewer row is usable, and the docs say the review is then not independent.
- The planner runs on the Planner row for the coordinator's provider when there is one, and otherwise on the first Planner row.
- The runner files become provider-neutral. They explain the placeholders and read every command from the Providers table.
- `preflight.sh` takes the provider names as arguments. It still requires Claude Code or Codex for the coordinator, which #41 will lift.
- `CONTRIBUTING.md` gains a "Design principles" section that states the goal a change is judged by. The planner and reviewer role files read `CONTRIBUTING.md` when the repo has one.
- The README intro says the workflow does not depend on one provider. The rest of the README, `AGENTS.md`, and the changelog follow.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`, as the routing and preflight changes did. `openspec/specs/` ships empty to every project made from the template, so the workflow's own rules live in the skill and the README.

## Impact

- `.claude/skills/work-issues/routing.md`: header, pi rows, the Providers table, and provider notes.
- `.claude/skills/work-issues/SKILL.md`: the description line, Routing, the preflight paragraph, and steps 3, 5, and 7 where they name a provider.
- `.claude/skills/work-issues/runners/headless.md`, `runners/herdr.md`: rewritten around the Providers table.
- `.claude/skills/work-issues/scripts/start-worker.sh`, `test_state.py`: any provider, `--turns`, a session id per start, and no `routing.md` check.
- `.claude/skills/work-issues/scripts/preflight.sh`, `test_preflight.py`: provider arguments.
- `.claude/skills/work-issues/roles/reviewer.md`, `roles/implementer.md`, `brief-template.md`: one line each that says the reviewer is on another provider.
- `.claude/skills/work-issues/roles/planner.md`, `roles/reviewer.md`: the reading list.
- `README.md`, `AGENTS.md`, `CHANGELOG.md`, `CONTRIBUTING.md`.
- Not changed: `state.py` and its field names `backend` and `implementer_backend`, the updater, `update-paths.txt`, `VERSION`, and `.claude/agents/`.
- `routing.md` is in no release yet, so its format changes without a migration. A project on 0.5.0 gets the file from its updater at the next release, already in this shape.
