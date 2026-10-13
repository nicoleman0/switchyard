# Design

## Context

See proposal.md for the motivation. What the code does today:

- `update-paths.txt` lists `.claude/skills/work-issues` and `.claude/agents` as folders, so every file under them is updater-owned. The one exception is `VERSION`, excluded by a constant in `update-switchyard.py` (`selected_entries`).
- The updater a project runs is its own copy, at the base release. It reads `update-paths.txt` from the target release. The script replaces itself during the run, so new updater logic first applies one update later.
- The script at `v0.5.0` is the same as on `main`. It refuses when a line of the target's `update-paths.txt` matches no file in the target.
- `start-worker.sh` takes the provider flags after `--` and passes them to `herdr agent start`. On headless it takes no flags; the coordinator puts them in the turn command. It hard-codes the providers `claude`, `codex`, and `opencode`, and refuses a reviewer on opencode.
- `claude` accepts `--agent`, `--model`, and `--effort` together. The skill's escalation step already relies on that.
- "The routing table" is named in `SKILL.md` (Routing, steps 3, 5, 7), `runners/headless.md`, `runners/herdr.md`, the usage line of `start-worker.sh`, `AGENTS.md`, and the README. The role files do not name it.

Checked in a scratch repo: a `v0.5.0` project ran its own updater against a release that adds `routing.md` and strips `model` and `effort` from the profiles.
- Unedited project: `added: routing.md`, three profiles `updated`, exit 0.
- Project that changed a profile's model: `conflict` on that profile, with both sides in the markers, exit 1.
- A release whose `update-paths.txt` has a `!path` line: the `v0.5.0` updater refuses with "path !... is missing".

## Goals / Non-Goals

**Goals:**
- One project-owned file holds every model, effort level, and provider flag.
- The updater never changes that file once the project has it.
- A project can drop a provider or add a second model for one by editing only that file.
- A project without the file gets a loud failure, not default models.

**Non-Goals:**
- A fourth provider. `start-worker.sh` and the runners know three. Adding one is still a skill change.
- Scripts that parse `routing.md`. The coordinator reads it and passes the flags.
- Changing how `hooks/worktree-up.sh` and `hooks/worktree-down.sh` update.
- Per-provider usage rules in the file. How to read each provider's usage stays in the skill.

## Decisions

**The file is `.claude/skills/work-issues/routing.md`, a Markdown table.**
The coordinator is the only reader, and it already reads Markdown tables for the runners. Alternative: YAML or JSON. Rejected, because nothing parses it and a table is easier to edit by hand.

**Layout of `routing.md`.**
A short header says the file is the project's, that the updater adds it when missing and never changes it, and that the rules for choosing a row are in `SKILL.md`. It names the providers the scripts accept, and that a reviewer runs on `claude` or `codex`. Then two tables.

Workers:

| Role | Provider | Flags | Use |
|---|---|---|---|
| Planner | claude | `--agent issue-planner --model opus --effort high --permission-mode auto` | |
| Planner | codex | `-m gpt-5.6-sol -c model_reasoning_effort=high --approve-for-me` | |
| Implementer | claude | `--agent issue-implementer --model sonnet --effort medium --permission-mode auto` | |
| Implementer | claude | `--agent issue-implementer --model opus --effort high --permission-mode auto` | escalation |
| Implementer | codex | `-m gpt-6-luna -c model_reasoning_effort=medium --approve-for-me` | |
| Implementer | opencode | `--model opencode-go/kimi-k3 --auto` | |
| Reviewer | claude | `--agent issue-reviewer --model opus --effort high --permission-mode auto` | |
| Reviewer | codex | `-m gpt-5.6-sol -c model_reasoning_effort=high --approve-for-me` | |

Coordinator:

| Provider | Model | Effort |
|---|---|---|
| claude | `opus` | high |
| codex | `gpt-5.6-sol` | medium |

The values match 0.5.0 except the opencode Implementer model is `opencode-go/glm-5.3-flash`, because Kimi K3 uses too many tokens. The model appears only inside the flags, not in a second column, so a row cannot disagree with itself. Today's escalation flags lack `--permission-mode auto`; the escalation row adds it so every Claude worker row has it.

**Rules stay in `SKILL.md` and are written against the file, not against provider names.**
- The planner uses the Planner row of the coordinator's provider.
- Implementers: use the provider the maintainer names. Otherwise rotate through the providers that have an Implementer row, in the order they first appear in the file. Leave out a provider whose CLI is not installed. The usage threshold and how to read it stay as they are.
- The first row for a role and provider is the default. Use a later row only when its Use column says so or the maintainer names it. This is how a project lists a second model for one provider.
- The reviewer uses the first Reviewer row whose provider is not the implementer's. With the example values that gives today's pairs: Claude to Codex, Codex or opencode to Claude.
- When no such row exists, or that provider is not installed or is over the threshold, the existing `SWITCHYARD_SAME_PROVIDER=1` override applies and the coordinator tells the maintainer.
- Escalation uses the Implementer row whose Use column says `escalation`. If the file has none, the coordinator tells the maintainer and does not escalate.
- If a role has no usable row, or `routing.md` is missing, the coordinator stops and tells the maintainer. It never picks a model itself.

Dropping a provider is deleting its rows. The rotation and the reviewer rule then skip it with no edit to the skill.

**The Codex coordinator profile keeps its shape in `SKILL.md` and takes its values from `routing.md`.**
The TOML block shows `model = "<model>"` and `model_reasoning_effort = "<effort>"`, with a line that says both come from the Coordinator table. `approvals_reviewer = "user"` is a workflow rule, not a model choice, so it stays in the skill. The Claude coordinator row is a recommendation for the maintainer's own session, as it is today.

**The Claude profiles drop `model` and `effort`.**
Decided by the maintainer. Each profile keeps `name` and `description`, and its body keeps the pointer to the role file. The sentence "This profile only sets your model and effort" goes. The profiles stay updater-owned.

**The updater's rule: a project-owned path is added when the project has no file there, and is otherwise left alone.**
- `update-switchyard.py` gets a constant `PROJECT_OWNED` beside `VERSION_PATH`, holding `.claude/skills/work-issues/routing.md`.
- For a path in `PROJECT_OWNED`: if the target release has the file and the project has no file at that path, the action is `added`. In every other case the updater does nothing and reports nothing: no update, no merge, no conflict, no removal. Upstream changes to the example values never reach an existing file.
- This is how the rule tells "the template ships it" from "the updater ignores it". Shipping needs no rule: the file is committed, so a new project made from the template has it. `update-paths.txt` still covers it through the folder line, so the updater sees it in the target tree and can add it. The constant then stops every action except that first add.
- `update-paths.txt` does not change.

Alternative: a `!path` line in `update-paths.txt`. Rejected. The updater that runs is the project's old copy, and the 0.5.0 updater refuses a target whose list has a line that matches no file. Every project on 0.3.0 to 0.5.0 would be unable to update.

Alternative: a second list file read from the target release. It would let a later release mark more files as project-owned without waiting one update. Not needed for one file. See question 2.

Alternative: never add the file at all. Rejected, see question 1.

**How a project without the file gets it.**
- A project on 0.3.0, 0.4.0, or 0.5.0 runs its own updater, which has no project-owned rule. It adds `routing.md` as a new file and reports `added`. Checked, see Context.
- A project on 0.1.0 or 0.2.0 runs the updater from a Switchyard clone, as the README says. That is the new updater, and its rule adds the file.
- From 0.6.0 on, the rule adds the file only if the project deleted it.
- In each case the report line `added: .claude/skills/work-issues/routing.md` tells the maintainer the file is new. The changelog entry says to review it.

A project that edited the routing table in `SKILL.md`, or a model in a profile, gets a `conflict` on that file when it updates. The changelog entry says to resolve it by taking the release's side and moving the values to `routing.md`.

**A missing file fails in `start-worker.sh`, not only in prose.**
`start-worker.sh` exits 1 before it touches the record when `routing.md` is not a file in the skill folder. The message names the path and says to copy the file from the Switchyard release the project follows. This is an existence check, not parsing. Every worker start on both runners goes through this script, so no worker can start on models the coordinator made up. See question 5.

**One home for each reference.**
- `SKILL.md` Routing: the rules, and one sentence that says "the routing table" means the worker table in `routing.md`.
- Steps 3, 5, and 7 of `SKILL.md`, `runners/headless.md`, `runners/herdr.md`, and the usage line of `start-worker.sh` keep the words "routing table" and need at most a path added.
- `AGENTS.md`: the skill holds the roles and the routing rules; `routing.md` holds the models, effort, and flags, and is the project's to change.
- README: "Make it yours" gains a row for `routing.md` and loses the sentence that names two places. The updater section says the file is added once and never changed. The layout tree lists the file and fixes the `agents/` line.

**`VERSION` stays at 0.5.0.**
PRs #16 and #17 changed behaviour and did not touch `VERSION`. The release PR #18 bumped it together with the changelog heading, and CI checks the two match. This change adds an Unreleased entry only.

## Risks / Trade-offs

- [A project on 0.5.0 gets example models it did not choose] → They are the models it already ran on 0.5.0, the updater reports the file as `added`, and the changelog says to review it.
- [A project that edited models upstream-side gets conflicts on update] → Conflicts are loud and exit 1. The changelog gives the steps.
- [Rules in prose depend on the coordinator reading the file correctly] → The table is small, and `start-worker.sh` still enforces the reviewer's provider and the file's existence.
- [A project puts a reviewer on opencode or names a fourth provider in the file] → `start-worker.sh` refuses both. The file's header names the limits.
- [A release improves the example values and existing projects never see it] → Intended. The changelog is where a new recommendation is announced.
- [A Claude worker started without its row's flags runs on the session's default model] → The profiles no longer carry a fallback. The runner commands always take the row's flags, and the end-to-end task checks the model a worker reports.

## Open Questions

1. **Should the new updater add `routing.md` when a project lacks it?**
   - a. Yes, add when missing and report `added`. Recommended. It covers 0.1.0 and 0.2.0 projects, matches what the 0.5.0 updater does anyway, and the report line is visible.
   - b. No, never write the file. The project copies it by hand after `start-worker.sh` refuses. Stricter reading of "never fall back to defaults", but projects on 0.3.0 to 0.5.0 still get it from their old updater, so behaviour would differ by base release.

2. **Where does the list of project-owned paths live?**
   - a. A constant in `update-switchyard.py`, beside `VERSION_PATH`. Recommended. One file needs it today.
   - b. A new list file, read from the target release. A later release could add entries that take effect at once. Old updaters ignore it safely.
   - Neither covers the two hooks for free. With (a) they would be two more entries in the constant, taking effect one update later. That is out of scope here.

3. **How does the coordinator pick between two rows for one role and provider?**
   - a. The first row is the default; a later row is used when its Use column says so or the maintainer names it. Recommended. Escalation becomes one such row.
   - b. Each row is its own slot in the implementer rotation.
   - c. No Use column: only the maintainer picks a later row.

4. **May the implementer append to `CHANGELOG.md`?** It is outside the owned paths, and `CONTRIBUTING.md` asks for an Unreleased entry.
   - a. Yes, one entry under Unreleased. Recommended.
   - b. No, the coordinator adds it in the release PR.

5. **Should `start-worker.sh` refuse when `routing.md` is missing?**
   - a. Yes. Recommended. A few lines and one test, and the failure does not depend on the coordinator following prose.
   - b. No, the skill's prose is enough.
