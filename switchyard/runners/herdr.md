# Runner: Herdr

Use this when the coordinator runs inside Herdr (`HERDR_ENV=1`). Each worker is an interactive agent in its own pane, so the maintainer can watch it and step in.

`setup-worktree.sh` creates the worktree under `~/.herdr/worktrees/<repo>` and prints its `pane` and `workspace`. The coordinator must be able to write to `~/.herdr/worktrees/<repo>`; its setup note is in the Coordinator section of `switchyard/routing.md`.

| Verb | Command |
|---|---|
| Start an agent | `scripts/start-worker.sh <issue> <role> <provider> -- <flags>` when the provider's On Herdr cell is `agent`. With `--resume` in place of `-- <flags>`, it reopens the role's running agent |
| Start a turns provider | `scripts/start-worker.sh <issue> <role> <provider> --turns` when its On Herdr cell is `turns`. `--resume` reuses the role's recorded session |
| Prompt | `herdr agent prompt <name> "<one line>" --wait --until working --until blocked --timeout 30000` |
| Wait | `scripts/wait-agents.sh [--timeout <seconds>] <name>...` |
| Read | `herdr agent read <name> --source recent-unwrapped --lines 80` |
| End | `scripts/end-worker.sh <issue> [<role>]`. Without a role it ends every agent of the issue |

Read the provider's commands, flags, and End value from `switchyard/routing.md`. The script names agents `<role>-<issue>`. The implementer keeps running while the reviewer works, so `implementer-<issue>` and `reviewer-<issue>` live at once. The reviewer starts in a pane split below the worktree's pane, and ending it closes that pane. `--resume` exits 4 when the agent has exited or ran on another provider; start a fresh one then. Herdr rejects names that start with a digit; names must start with a lowercase letter.

Multi-line prompt text does not submit reliably. Put the content in a file and prompt with one line that points to it.

`wait-agents.sh` returns when a named agent is `idle`, `done`, `blocked`, or `unknown`. Follow the coordinator note in `routing.md` for harness-specific waiting. Without `--timeout`, the wait runs with no limit. Pass `--timeout <seconds>` to bound it: on a timeout the script prints one line per still-working agent, `name status <seconds>s`, counting from when the wait started, and exits `4`.

If a prompt stalls or times out, read the agent before resending. If `start-worker.sh` exits 3 with `status=blocked`, it has written the record; read the agent and clear its startup screen before prompting.

## Providers that run as turns

If a provider's On Herdr cell is `turns`, run its First turn or Later turns command from `routing.md` in the pane:

```sh
herdr pane run <pane> "clear; <provider turn command>; echo \"TURN-DONE-<issue>-<turn> exit=\$?\""
```

Use the printed pane and session for each turn. Herdr's agent states do not apply to a turns provider. Use a new `<turn>` number each time, because a reused marker matches the old output. A turn is over when `herdr pane read <pane> --source visible` shows that turn's marker. A provider whose Herdr kind is unsupported by Herdr fails at start; set its On Herdr cell to `turns` in `routing.md`.
