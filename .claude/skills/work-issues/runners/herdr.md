# Runner: Herdr

Use this when the coordinator runs inside Herdr (`HERDR_ENV=1`). Each worker is an interactive agent in its own pane, so the maintainer can watch it and step in.

`setup-worktree.sh` creates the worktree under `~/.herdr/worktrees/<repo>` and prints its `pane` and `workspace`. A Codex coordinator needs that folder writable: `--add-dir ~/.herdr/worktrees/<repo>`.

| Verb | Command |
|---|---|
| Start | `herdr agent start <name> --kind <claude\|codex> --pane <pane> -- <flags from the routing table>` |
| Prompt | `herdr agent prompt <name> "<one line>"` |
| Wait | `scripts/wait-agents.sh <name>...` |
| Read | `herdr agent read <name> --source recent-unwrapped --lines 80` |
| End | send `/exit` to the agent |

- Name agents `<issue>-plan` and `<issue>-build`.
- Multi-line prompt text does not submit reliably. Put the content in a file and prompt with one line that points to it.
- `wait-agents.sh` returns when a named agent is `idle`, `done`, `blocked`, or `unknown`. On Claude Code, run it in the background so you are re-invoked when it returns.

## opencode

opencode's interactive mode ignores model settings and reopens the last model you picked, so the opencode implementer runs headless in its pane. Each turn is one `herdr pane run`, and every turn reuses one session, so answers keep their context:

```
herdr pane run <pane> "clear; opencode run <flags> --session ses_issue<issue> '<prompt>'; echo \"OPENCODE-DONE-<issue>-<turn> exit=\$?\""
```

Herdr's agent states do not apply to it. A turn is over when `herdr pane read <pane> --source visible` shows that turn's marker. Use a new `<turn>` number each time, because a reused marker matches the old output.

## Codex

- Codex may open on an update prompt. Dismiss it with `herdr agent send-keys <name> esc`, and tell the maintainer an update is available. Do not update Codex without asking.
- Codex asks questions in a picker. Open it with `herdr agent send-keys <name> shift+left`, move to "Other" with `down`, type a one-line pointer to the answers file with `herdr pane send-text <pane> "..."`, and submit with `enter`.
