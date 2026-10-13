# Design

## Context

See proposal.md for the motivation. `.claude/answers/maintainer-principle.md` holds the maintainer's principle and its order of precedence. It overrides the brief where they differ.

What the code does today, checked on this branch:

- `start-worker.sh` has `case "$backend" in claude|codex|opencode)`, refuses a reviewer on `opencode`, and refuses to start when `routing.md` is missing. It gives opencode the session `ses_issue<issue>`, gives headless Claude a UUID, and gives headless Codex no session.
- On Herdr it runs `herdr agent start <role>-<issue> --kind <backend> --pane <pane> -- <flags>` for every provider but opencode.
- `herdr agent start --help` lists 24 kinds, pi among them, and calls a kind the "canonical executable". So a Herdr kind is the CLI's command name.
- `runners/headless.md` has a first-turn and later-turn command per CLI. It says where `<flags>` comes from for Claude only (#40).
- `runners/herdr.md` has an opencode section with the marker `OPENCODE-DONE-<issue>-<turn>`, and Codex notes.
- `preflight.sh` counts `claude`, `codex`, and `opencode`, and fails unless `claude` or `codex` is found.
- `SKILL.md` Routing puts the planner on the coordinator's provider, names three providers in the usage rule, says "Never choose a model yourself", and stops when `routing.md` or a row is missing.
- `test_state.py` asserts the opencode refusal, `ses_issue11`, an empty Codex session, and the missing-file refusal. It has no stub for any worker CLI.

Checked by running the CLIs, in scratch folders:

- pi 0.75.4, `pi -p --model <m> --session <file>.jsonl "<prompt>"`: creates the file and any missing parent folder, and the same command resumes it. The second turn recalled a word from the first.
- `pi --session <uuid>` with an id pi did not create: `No session found matching '<uuid>'`. So pi needs a file path, not an id.
- A model the key cannot reach: pi prints `404 The model ... does not exist or you do not have access to it.` and exits 1.
- pi has no permission prompts (`docs/usage.md`: "It intentionally does not include ... permission popups"). Its quit command is `/quit`, not `/exit`.
- pi reads `AGENTS.md` at startup. It does not load `.claude/skills/`. The role prompt names the role file by path, so that is enough.
- opencode 2.0.20, `opencode run --session <id>`: "Session ID to continue, or to create if it does not exist". A bare UUID fails with `Expected a string starting with "ses"`. `ses_<uuid>` creates the session, and a second turn resumed it.
- `pi --list-models` here offers 18 Groq models and one Ollama model. Of seven tried, three answered: `groq/openai/gpt-oss-120b`, `groq/openai/gpt-oss-20b`, and `ollama/qwen3.5:9b-32k`. Four listed Groq models returned 404. `--thinking high` works with `gpt-oss-120b`.

The coordinator verified pi as an interactive Herdr agent: `herdr agent start smoke-pi --kind pi` started it, `herdr agent prompt` delivered a prompt and returned `done`, and `/quit` ended it.

## Goals / Non-Goals

**Goals:**
- Planner, implementer, and reviewer can each run on any provider the project lists.
- A project adds a provider by editing `routing.md` only.
- The shipped values read as examples. The maintainer's word wins, then the file, then the coordinator's reported choice.
- A wrong provider name fails loudly before the record changes.
- A project with one provider runs a batch with no per-command setting from the maintainer.

**Non-Goals:**
- The coordinator on another CLI (#41). It still runs on Claude Code or Codex.
- Scripts that parse `routing.md`.
- The install and init scripts (#25, #26) and the script fixes in #37, #38, and #39.
- Renaming the record fields `backend` and `implementer_backend`. That is a refactor for its own PR.
- Example rows for opencode as Planner or Reviewer. The script allows them, and a project adds the rows.

## Decisions

**A provider is named after its CLI command.**
`claude`, `codex`, `opencode`, and `pi` already are. Herdr's `--kind` uses the same names. This one rule replaces the hard-coded list.

**`start-worker.sh` takes any provider and checks it is a command.**

```
Usage: start-worker.sh <issue> <role> <provider> [--turns] [-- <routing flags>...]
```

Checks, in this order, all before the record changes:
1. `roles/<role>.md` exists. Unchanged.
2. The provider name matches `[a-z][a-z0-9_-]*` and `type -P` finds it. Otherwise exit 1 with `Unknown provider: <name> is not a command on PATH. A provider is named after its CLI command.`
3. The runner is `herdr` or `headless`. Unchanged.
4. For a reviewer: an implementer has run, and the provider differs from the implementer's unless `SWITCHYARD_SAME_PROVIDER=1`. Unchanged.

Removed:
- the `claude|codex|opencode` list,
- the refusal of a reviewer on opencode,
- the refusal when `routing.md` is missing. The principle says the coordinator may choose when there is no file, so the script must not block that. The implementer lists this removal under Decisions to review in the PR body.

What a wrong name does: `start-worker.sh 8 planner claud` exits 1 and names the provider. A typo that happens to be another command passes the script. On Herdr the next line fails, because `herdr agent start --kind` rejects a kind it does not know. On headless the coordinator finds no Providers row and falls to rule 3 of the precedence order, which makes it tell the maintainer. Alternative: `grep` the name in `routing.md`. Rejected, because that is parsing the file.

**How a worker runs is one of two modes, and the script does not need the provider to pick one.**
- `agent`: an interactive Herdr agent. The script runs `herdr agent start <role>-<issue> --kind <provider> --pane <pane> -- <flags>` and records the name. This is the default on the Herdr runner.
- `turns`: one CLI command per turn. The script makes a lowercase UUID, records it as `session`, and prints it. This is the only mode on the headless runner, and the mode on Herdr when the coordinator passes `--turns`.

The coordinator reads the mode from the provider's On Herdr cell and passes `--turns` when it says `turns`. `--turns` on the headless runner is accepted and changes nothing. Flags after `--` are used only for `herdr agent start`.

Codex gets a session id it does not use. That is harmless, and it removes the last provider name from the script.

**Every start makes a new session id.**
The Providers row says how the id is used: `--session-id <session>` for Claude, `ses_<session>` for opencode, `.claude/sessions/<session>.jsonl` for pi. A planner, an implementer, a reviewer, and each fix round on one provider therefore get separate sessions. Today an opencode fix round reuses `ses_issue<issue>`, which breaks the skill's own rule that each phase starts fresh.

**`routing.md` layout.**

Header:

> This file belongs to the project. The updater adds it when missing and never changes it. Every value here is an example: edit it to choose providers, models, effort, flags, and commands. What the maintainer names in a session wins over this file. Row selection rules are in `SKILL.md`.
>
> A provider is named after its CLI command. To add one, add a Providers row and a Workers row for each role it should run.

The sentence "Supported worker providers are ..." goes.

Workers: today's eight rows with versioned model IDs removed from Codex and opencode, then three pi rows. Keep Claude aliases, effort settings, and all approval flags. Remove only the Codex `-m` values and opencode `--model` value. pi rows stay empty.

| Role | Provider | Flags | Use |
|---|---|---|---|
| Planner | pi | | when named |
| Implementer | pi | | when named |
| Reviewer | pi | | when named |

The template ships no versioned model IDs. Keep Claude's `opus` and `sonnet` aliases, effort levels, and approval flags. Remove model IDs from Codex and opencode rows, retaining effort and approval flags. All pi rows have empty Flags. Each CLI uses its own default unless the project pins a model in its row: Claude uses `--model <alias or id>`, Codex `-m <model>`, opencode `--model <provider/model>`, and pi `--model <provider/id>`. The pi rows sit last in each role's group, so the order of the existing rows does not change. They carry `when named`, so pi does not join the default rotation.

Providers, a new section after Workers:

| Provider | On Herdr | End | First turn | Later turns |
|---|---|---|---|---|
| claude | agent | `/exit` | `claude -p --session-id <session> <flags> "<prompt>"` | `claude -p --resume <session> <flags> "<prompt>"` |
| codex | agent | `/exit` | `codex exec <flags> "<prompt>"` | `codex exec resume --last <flags> "<prompt>"` |
| opencode | turns | | `opencode run <flags> --session ses_<session> "<prompt>"` | the same command |
| pi | agent | `/quit` | `pi -p <flags> --session .claude/sessions/<session>.jsonl "<prompt>"` | the same command |

One line under the table says the runner files explain the columns and placeholders.

Provider notes, a list under the table. These move here from the runner files and from `SKILL.md`:
- claude: the status line shows usage used. Pin a model with `--model <alias or id>`.
- codex: the status line shows usage left ("5h N% left"). Later turns forget the model, so pass the row's flags again, and the pinned model if there is one. `codex exec resume` rejects `--approve-for-me`; pass `-c approvals_reviewer=auto_review` in its place. `--last` picks the newest session for the current folder, so run it from the worktree. Pin a model with `-m <model>`. The two Herdr notes on the update prompt and the question picker, word for word from `runners/herdr.md`.
- opencode: interactive mode ignores model settings and reopens the last model picked, so it runs as turns on Herdr. Session ids must start with `ses`. No known way to read usage from a script. Pin a model with `--model <provider/model>`.
- pi: no permission prompts, so no approval flag. `--session` needs a file path; an id pi did not create fails. A model the key cannot reach exits 1 with a 404, so check `pi --list-models` against a real turn. A key with a per-minute token limit below pi's base request fails every turn with a 413, so try a real turn in the repo before relying on a model. No usage window to read. With no `--model`, pi uses the model from its own settings; a project pins one by adding `--model <provider/id>` to the row.

The Coordinator table keeps the Claude row and has an empty Model cell for Codex. Its closing line says an empty Model cell means the CLI's own default. The Codex coordinator profile omits the `model` line from its TOML when that cell is empty.

**The runner files become provider-neutral.**

`runners/headless.md`:
- Keeps the worktree location, the Codex coordinator `--add-dir` line, and the paragraph on turns.
- Replaces the Backend table with: the turn commands are the First turn and Later turns cells of the provider's row in the Providers table of `.claude/skills/work-issues/routing.md`.
- Says, for every provider: `<flags>` is the Flags cell of the worker's row in the Workers table, `<session>` is the value `start-worker.sh` printed, and `<prompt>` is the role prompt. Run the command from the worktree. This covers #40.
- Keeps the Verb table, with `<provider>` in place of `<backend>`.
- Loses the Codex list, which moves to the provider notes.

`runners/herdr.md`:
- Start: `scripts/start-worker.sh <issue> <role> <provider> -- <flags>` for a provider whose On Herdr cell is `agent`, and `scripts/start-worker.sh <issue> <role> <provider> --turns` for `turns`.
- End: send the provider's End cell to the agent.
- The opencode section becomes "Providers that run as turns". It keeps the `herdr pane run` command, with the provider's turn command in place of `opencode run ...` and the marker `TURN-DONE-<issue>-<turn>`. It keeps the rules on reading the pane and on a new `<turn>` number each time.
- A Herdr `--kind` that Herdr does not support fails at start. The fix is `turns` in that provider's row. One line says so.
- Loses the Codex section, which moves to the provider notes.

**`SKILL.md` Routing states the order of precedence once.**

Text for the section, in this shape:

> The providers, models, effort, flags, and commands for workers live in `.claude/skills/work-issues/routing.md`. That file is the project's to edit, and its values are examples. Its Workers table is the routing table. Its Providers table holds each provider's commands.
>
> Who decides, in this order:
> 1. What the maintainer names in the session: a provider, a model, or a command.
> 2. The row in `routing.md`.
> 3. Your own choice, when there is no usable row, no Providers row for the provider, or no file. Pick a provider, a model, and the command to run. Tell the maintainer what you chose and why before the worker starts. Do not wait for approval.
>
> When the maintainer names a model, use that provider's row for the role with the model replaced.

Row rules that follow it:
- A row is usable when its provider's CLI is installed and the provider is under the usage threshold. An empty Flags cell leaves the model to the provider's own settings; when the maintainer names a model, the coordinator adds that provider's model flag.
- Planner: the Planner row for your own provider. If there is none, the first Planner row. See question 3.
- Implementers: rotate through the providers with an Implementer row, in the order they first appear. Unchanged.
- The first row for a role and provider is the default. Use a later row only when its Use cell says so or the maintainer names it. Unchanged.
- A row marked `when named` is used only when the maintainer names its provider. See question 6.
- Usage: skip a provider when more than about 70% of its usage window is used. The provider notes in `routing.md` say how to read each one. Ask the maintainer when a provider has no note or its note says usage cannot be read.
- First turn: if a provider's first turn fails to start or reach its model, skip it for the batch, move to the next usable row, and tell the maintainer which provider failed and the error.
- Say which provider and model each issue got.
- Reviewer: the first Reviewer row whose provider differs from the implementer's. When there is none, or it is not usable, review on the implementer's provider with `SWITCHYARD_SAME_PROVIDER=1` on that `start-worker.sh` command. Tell the maintainer once per batch that the review is not independent, and write "same provider, not independent" in the PR body's Review section. A choice under rule 3 still prefers another provider than the implementer's.
- Escalation: the Implementer row marked `escalation`. Without one, follow the order above.

Removed: "Never choose a model yourself", and the instruction to stop when `routing.md` or a usable row is missing.

Elsewhere in `SKILL.md`:
- The frontmatter description says "an implementer on any provider the project lists" in place of "on Claude, Codex, or opencode".
- The preflight paragraph says to pass the providers named in `routing.md`.
- Step 7 says "another provider" as today. No other step names a provider.

**The one-provider setup needs no setting.**
A project with one provider keeps only that provider's rows. The reviewer rule then finds no other Reviewer row, and the coordinator sets `SWITCHYARD_SAME_PROVIDER=1` itself on each reviewer start. The maintainer sets nothing per command. `start-worker.sh` keeps the enforcement, so a coordinator that forgets the override still gets a refusal. See question 2.

**`preflight.sh` takes the providers as arguments.**

```
Usage: preflight.sh [provider...]
```

- `Coordinator CLI`, required: `claude` or `codex` is found. This replaces the `Worker CLI` item. Fix text: "Claude Code or Codex is required to run the coordinator. Install one." #41 removes it.
- One line per named provider: `ok       Provider <name>`, or `warn     Provider <name>: not installed. The coordinator leaves it out.`
- Names given and none installed: `warn     Worker providers: none of the named providers is installed. The coordinator will choose one and tell you.` It is a warning, not a failure: the coordinator's own CLI can run every worker role under rule 3, so a batch can still run.
- Names given and exactly one installed: `warn     Second provider: only <name> is installed. The reviewer runs on the implementer's provider, so the review is not independent.`
- Names given and two or more installed: `ok       Second provider`.
- No names: `warn     Worker providers: none named. Pass the providers in routing.md: preflight.sh <provider>...` and no Second provider line.
- The other items do not change. The script still uses only builtins and the tools it checks.

The pass rule for a batch is unchanged while #41 is open: the coordinator needs Claude Code or Codex, and either one can also run every worker role. So every provider check is a warning, and only the coordinator CLI can fail the run. See question 1.

**`CONTRIBUTING.md` gets a "Design principles" section.**
`.claude/answers/contributing-principles.md` asks for it and adds the file to the owned paths. It goes after the opening paragraph, which stays as it is. Proposed text:

> ## Design principles
>
> Judge a change by these.
>
> - Anyone can adopt it. A stranger with another provider, operating system, or repository can use the change without editing a file the updater owns.
> - No provider is special. Planner, implementer, and reviewer run on any provider the project lists. The skill and the scripts do not name a provider where a project-owned file can.
> - The project chooses its models. Shipped values are examples, not recommendations. The maintainer's word comes first. The order of choice is in the Routing section of `.claude/skills/work-issues/SKILL.md`.
> - Prefer a stated default over a refusal. Fail hard only when a batch cannot run at all, such as a missing `git` or a signed-out `gh`.
> - What a project changes lives in files the project owns. The updater never replaces them.

- The order of precedence has one home, `SKILL.md` Routing, because the coordinator reads the skill on every batch. `CONTRIBUTING.md` states the principle and points there.
- The provider bullet names the three worker roles, so it is true now and stays true when #41 lands.
- The section does not repeat "Keep changes small and generic. Nothing should assume a stack."
- Where this design still names a provider in a script or the skill, it is the coordinator: the `Coordinator CLI` and Codex profile checks in `preflight.sh`, and the Codex coordinator profile section in `SKILL.md`. Those are #41.
- The refusals that remain are a provider that is not a command on `PATH`, which cannot run at all, and the same-provider review without its override, which the maintainer kept.

**How a worker on Switchyard itself comes to read the principles.**
Workers read `AGENTS.md` and the brief. Both ship to projects, so neither can hold Switchyard's own principles. `roles/planner.md` and `roles/reviewer.md` gain one generic clause in their reading list: read `CONTRIBUTING.md` if the repo has one. It names no Switchyard rule, and it holds for any project whose contributing guide says how changes are judged. The implementer's role file does not change, because it builds a plan that was already judged. See question 7.

**Role files and the brief template.**
`roles/reviewer.md` says the code was written "on another provider", and `roles/implementer.md` and `brief-template.md` say the reviewer is "on another provider". With one provider that is false. Each line changes to say "on another provider when the project has one". `.claude/agents/issue-reviewer.md` has the same claim in its description. It is outside the owned paths, so it stays, and the PR body flags it.

**README intro wording, for the coordinator to review.**
`.claude/answers/readme-framing.md` asks the intro to stress that the setup is easy to adopt and does not depend on one provider, with no new section. Proposed text for lines 12 to 20, in this order:

> Switchyard is a template repository that was born out of my own personal AI development setup.
>
> Start a new project from it, and the project begins with a delivery workflow for coding agents already in place: issues, specs, isolated worktrees, and review gates.
>
> To adopt it, [start a new project](#start-a-new-project) from the template with one command, or [add the workflow to a repo you already have](#add-it-to-an-existing-repo) with a few copy commands and three hand merges.
>
> It does not depend on one AI provider. Use any agent CLI for the worker roles, and change a provider or a model by editing one file, `.claude/skills/work-issues/routing.md`. The values it ships with are examples. The coordinator runs on Claude Code or Codex.
>
> It holds no application code. You add your stack on top.
>
> One session coordinates. For each issue, a planner writes a spec change, an implementer builds it, and a reviewer checks it, in a git worktree of its own. The reviewer runs on another provider than the implementer when the project lists more than one. You answer the product questions and approve the merges.

- The first two paragraphs are unchanged. Line 12 stays word for word.
- The adoption sentence is today's closing link sentence, moved up and made specific. The old line 20 goes, so the links appear once.
- Each claim holds at this commit: worker roles on any listed provider, the coordinator on Claude Code or Codex until #41, and the manual steps for an existing repo until #25.

Proposed "Several providers share the load" bullet:

> - **Several providers share the load.** Worker roles run on any agent CLI the project lists in `routing.md`, and you choose the models there. Implementers rotate across the listed providers, so one usage window does not stall a batch.

**The rest of the README, `AGENTS.md`, and the changelog.**
- "Who does what": the Planner row drops "strong model" for "any provider", and the Reviewer row says "another provider than the implementer's when the project lists one".
- Requirements: Claude Code or Codex for the coordinator. Workers run on any CLI with rows in `routing.md`. The preflight line shows the provider arguments.
- One new bullet in the Requirements list, not a section: a project with one provider keeps only that provider's rows, the reviewer then runs on the implementer's provider, and the review is not independent. This covers #27.
- Runners: the headless cell says "One CLI command per turn, from the Providers table".
- "Make it yours": the `routing.md` row says the shipped values are examples and names the Providers table.
- "Planning and building are separate sessions": say that the planner and implementer can use different effort settings, and the planner's context is not carried into the implementer session. Keep the updated wording listed under Decisions to review in the PR body.
- Layout: the `routing.md` line adds the provider commands. The `runners/` line stays.
- No doc calls a shipped model the recommended one. The Coordinator table's closing line in `routing.md` says "recommends"; it changes to "is an example for".
- Badges stay. None becomes false.
- `AGENTS.md`: the line on `routing.md` adds "and each provider's commands".
- `CHANGELOG.md`: correct the Unreleased #36 sentence about opencode's example model; other existing entries keep their wording. Add that projects updating from 0.5.0 receive no model for Codex and opencode, run on CLI defaults, and can pin models using the provider notes.

## Risks / Trade-offs

- [Provider notes live in a file the updater never changes, so an upstream fix to a Codex note does not reach existing projects] → The same holds for every row of that file. The changelog announces it. See question 4.
- [The coordinator forgets `--turns` for a `turns` provider on Herdr] → An interactive agent starts, and for opencode it ignores the model. The runner file puts both Start commands side by side. Not caught by a script.
- [A typo that is a real command passes `start-worker.sh`] → It fails at `herdr agent start`, or surfaces as a reported rule 3 choice on headless.
- [Rule 3 lets a coordinator run a model nobody chose] → It must say what and why before the worker starts, and the reviewer rule still applies.
- [CLI defaults can change] → The project can pin a model using the provider-specific syntax in `routing.md`; the template avoids versioned model IDs that can go stale.
- [pi's model list names models the key cannot reach] → pi exits 1 with a 404, and the provider note says so.
- [Without the `routing.md` check, a deleted file no longer stops a batch] → Intended by the principle. The coordinator reports its choice.

## Resolved decisions

- Preflight takes provider names as arguments. Provider gaps are warnings; only a missing coordinator CLI fails.
- When no other Reviewer row exists, the coordinator sets `SWITCHYARD_SAME_PROVIDER=1` for each reviewer start.
- The Planner row for the coordinator's provider is preferred, then the first Planner row.
- All provider notes live in `routing.md`.
- The coordinator's Herdr smoke test started pi with `herdr agent start smoke-pi --kind pi`, sent a prompt with `herdr agent prompt` which returned `done`, and ended it with `/quit`.
- The implementer's headless pi proof uses `--model ollama/qwen3.5:9b-32k` on the command line. This model is not in the shipped row.
- pi rows say `when named`; empty Flags means pi uses its own configured model. A maintainer-named model is passed using that provider's model flag.
- Planner and reviewer roles ask workers to read `CONTRIBUTING.md` when present. The precedence rule remains in `SKILL.md` only.
