# Project routing

This file belongs to the project. The updater adds it when missing and never changes it. Every value here is an example: edit it to choose providers, models, effort, flags, and commands. What the maintainer names in a session wins over this file. Row selection rules are in `SKILL.md`.

A provider is named after its CLI command. To add one, add a Providers row and a Workers row for each role it should run.

## Workers

| Role | Provider | Flags | Use |
|---|---|---|---|
| Planner | claude | `--agent issue-planner --model opus --effort high --permission-mode auto` | |
| Planner | codex | `-c model_reasoning_effort=high --approve-for-me` | |
| Planner | pi | | when named |
| Implementer | claude | `--agent issue-implementer --model sonnet --effort medium --permission-mode auto` | |
| Implementer | claude | `--agent issue-implementer --model opus --effort high --permission-mode auto` | escalation |
| Implementer | codex | `-c model_reasoning_effort=medium --approve-for-me` | |
| Implementer | opencode | `--auto` | |
| Implementer | pi | | when named |
| Reviewer | claude | `--agent issue-reviewer --model opus --effort high --permission-mode auto` | |
| Reviewer | codex | `-c model_reasoning_effort=high --approve-for-me` | |
| Reviewer | pi | | when named |

## Providers

| Provider | On Herdr | End | First turn | Later turns |
|---|---|---|---|---|
| claude | agent | `/exit` | `claude -p --session-id <session> <flags> "<prompt>"` | `claude -p --resume <session> <flags> "<prompt>"` |
| codex | agent | `/exit` | `codex exec <flags> "<prompt>"` | `codex exec resume --last <flags> "<prompt>"` |
| opencode | turns | | `opencode run <flags> --session ses_<session> "<prompt>"` | the same command |
| pi | agent | `/quit` | `pi -p <flags> --session .claude/sessions/<session>.jsonl "<prompt>"` | the same command |

The runner files explain these columns and placeholders.

Provider notes:
- claude: the status line shows usage used. Pin a model with `--model <alias or id>`.
- codex: the status line shows usage left ("5h N% left"). Later turns forget the model, so pass the row's flags again, and the pinned model if there is one. `codex exec resume` rejects `--approve-for-me`; pass `-c approvals_reviewer=auto_review` in its place. `--last` picks the newest session for the current folder, so run it from the worktree. Pin a model with `-m <model>`.
- opencode: interactive mode ignores model settings and reopens the last model picked, so it runs as turns on Herdr. Session IDs must start with `ses`. No known way to read usage from a script. Pin a model with `--model <provider/model>`.
- pi: no permission prompts, so no approval flag. `--session` needs a file path; an id pi did not create fails. A model the key cannot reach exits 1 with a 404, so check `pi --list-models` against a real turn. A key with a per-minute token limit below pi's base request fails every turn with a 413, so try a real turn in the repo before relying on a model. No usage window to read. With no `--model`, pi uses the model from its own settings; a project pins one by adding `--model <provider/id>` to the row.
- codex on Herdr: Codex may open on an update prompt. Dismiss it with `herdr agent send-keys <name> esc`, and tell the maintainer an update is available. Do not update Codex without asking.
- codex on Herdr: Codex asks questions in a picker. Open it with `herdr agent send-keys <name> shift+left`, move to "Other" with `down`, type a one-line pointer to the answers file with `herdr pane send-text <pane> "..."`, and submit with `enter`.

## Coordinator

Add a note for every CLI this project uses as a coordinator. Each note states how to start it on the main checkout, what it needs writable, how it asks for approval, and how it waits for a worker.

| Provider | Model | Effort |
|---|---|---|
| claude | `opus` | high |
| codex | | medium |
| opencode | | |

An empty Model cell means the CLI's own default. These values are examples.

### Coordinator notes

- **claude:** Start `claude` from the main checkout, inside Herdr if you use it. The coordinator needs write access to the worktree root used by the selected runner: `../<repo>.worktrees` for headless or `~/.herdr/worktrees/<repo>` for Herdr. Claude Code permission prompts can request access, but merge only after the maintainer explicitly approves in the coordinator conversation. Run `scripts/wait-agents.sh` in the background so the session resumes when it returns.
- **codex:** `codex -p coordinator` layers `~/.codex/coordinator.config.toml` over the user config. The file lives outside the repo, so create it once:

  ```toml
  model_reasoning_effort = "<Coordinator table effort>"
  approvals_reviewer = "user"
  ```

  Copy the values from the `codex` row of the Coordinator table in `.claude/skills/work-issues/routing.md`. Add `model = "<Coordinator table model>"` only when that Model cell is not empty.

  `approvals_reviewer = "user"` sends approval requests to the maintainer, as Claude's permission prompts do. Without it they go to Codex's automatic reviewer, which decides case by case and has refused pushes. Workers keep `--approve-for-me`.

  The Codex sandbox can write the checkout, apart from `.git`, and nothing outside the checkout. Worktrees live outside it, so start Codex with the `--add-dir` the runner file names, which makes them writable for briefs and answers. Request everything else that writes outside the sandbox up front: the two worktree scripts, and git commands that change refs (`push`, `fetch`, `rebase`, `merge`). A sandboxed `git push` still reaches the remote but cannot record the upstream.

  At an approval prompt, the maintainer answers "Yes, proceed". "Don't ask again" saves an allow rule under `~/.codex/rules/`, which every Codex session reads, workers included. This setting does not replace explicit maintainer approval before a merge. On headless, wait for the worker command to exit; in Herdr, run `scripts/wait-agents.sh` in the background when Claude Code is the coordinator.
- **opencode:** The [official CLI docs](https://dev.opencode.ai/docs/cli/) say `opencode` starts the TUI in the current directory; start it from the main checkout. The coordinator needs write access to the selected runner's worktree root: `../<repo>.worktrees` for headless or `~/.herdr/worktrees/<repo>` for Herdr. Request approval from the maintainer in the coordinator conversation and wait for the worker command or Herdr wait script to finish before reading its report. The docs describe `opencode run` as non-interactive and `--auto` as auto-approving permissions. The installed `opencode --help` could not be confirmed because it attempted to write a log outside the worktree. Verify session continuation, prompts, and wait behavior during the proof for #41 before relying on this note.
