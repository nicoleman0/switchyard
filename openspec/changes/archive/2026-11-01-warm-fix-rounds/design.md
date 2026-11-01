# Design

## Context

Today the record holds one `worker`, one `session`, and the worktree's `pane`. `start-worker.sh` overwrites them for every phase, and the coordinator ends each agent before the next starts. Herdr reuses a name once its agent exits, so `implementer-<n>` and `reviewer-<n>` never coexist. On headless, the Later turns commands in `routing.md` already resume a session, but only the planner's answers use them. Codex's Later turns use `codex exec resume --last`, which picks the newest Codex session for the folder.

The coordinator prototyped this on Herdr in the current batch: it left the implementer running, split its pane with `herdr pane split <pane> --direction down --cwd <worktree>`, started the reviewer there, and prompted `implementer-<n>` again for the fix round. It worked.

## Decisions

### 1. Role-prefixed fields hold each worker

`start-worker.sh` writes `<role>_worker`, `<role>_session`, `<role>_backend`, and on Herdr `<role>_pane`, next to the unprefixed fields it writes today. The unprefixed `role`, `backend`, `worker`, and `session` still name the phase in progress, so `state.py status`, `phase-start`, and `timings` work unchanged. `pane` stays the worktree's root pane from `setup-worktree.sh`.

`implementer_backend` already exists and keeps its meaning; it is now one case of `<role>_backend`. The reviewer's same-provider check keeps reading it.

Alternative: a nested `workers` object per role. Rejected: `state.py set` and `get` take flat `key=value` fields, and nesting would change `state.py` and every reader for no gain.

### 2. `start-worker.sh --resume` opens a phase on a recorded session

`start-worker.sh <issue> <role> <provider> --resume` starts nothing. It checks there is a session to resume, sets the unprefixed fields from the role's recorded ones, runs `phase-start`, and prints `path`, `pane`, `name`, and `session` as a start does. The coordinator then prompts the agent, or runs the provider's Later turns command with the printed session.

It exits 4, with one line saying to start a fresh session, when:
- `<role>_backend` differs from `<provider>`;
- Herdr agent: `herdr agent get <role>_worker` reports `agent_not_found`;
- turns or headless: `<role>_session` is missing.

It exits 1 when the Herdr agent is `working` or `blocked`: the coordinator must read it first, as `end-worker.sh` already requires.

`--resume` is one entry point for every phase, so phase timing and the status table need no second path. It works for any role, but only the implementer uses it.

### 3. The reviewer runs in a split pane on Herdr

On Herdr, `start-worker.sh` gives the reviewer a new pane: `herdr pane split <pane> --direction down --cwd <path>`, reading the id from `.result.pane.pane_id`. It records `reviewer_pane`, starts the agent there, and prints that pane. A turns reviewer runs its commands in the printed pane too. Planner and implementer keep the root pane.

The split happens on every reviewer start, whether or not the implementer is still running. One rule is easier to follow and test than a branch on the implementer's state.

### 4. `end-worker.sh` takes an optional role

`end-worker.sh <issue> <role>` ends `<role>_worker` the way it ends `worker` today, using `<role>_backend` for the End value and `<role>_pane` for the shell check. For the reviewer it then runs `herdr pane close <reviewer_pane>` and clears `reviewer_pane` and `reviewer_worker`. A turns reviewer has no agent, so only its pane closes.

`end-worker.sh <issue>` with no role ends every role with a recorded live worker, reviewer first, then closes the split pane. This keeps "End the planner's session" and "end its worker's session" in Merge and clean up correct without edits.

`phase-end` runs once per call, after the last agent ends. Each ended agent prints `ended=<name>`, and a closed split pane prints `closed=<pane>`. A split pane the maintainer already closed counts as closed, and so does its agent. Ending the reviewer also clears the unprefixed `worker` when it names the reviewer.

A record written before this change names one `worker` for its current `role`, with no `<role>_worker`. Before either script uses or replaces the role fields, it copies that worker into `<role>_worker`, `<role>_backend`, and `<role>_pane` set to the root pane. An issue in flight across an update then keeps its implementer through a new reviewer start and ends both agents.

### 5. Phases stay sequential

`phase-start` closes every open phase, so starting the reviewer ends the implementer's phase although its session lives on. A resumed fix round opens a new implementer phase. Timings measure the stage of the issue, not session lifetime, which matches the `timings` report: a row per phase, one phase open at a time.

### 6. Codex resumes by id on headless

`codex exec` takes no session id; Codex makes one. The id `start-worker.sh` prints is ignored by Codex. After the first turn, the coordinator reads the id from the turn log and records it: `state.py set <issue> implementer_session=<id>`. Codex prints `session id: <uuid>` in the header of `codex exec` output. Task 1.6 checked this with codex-cli 0.166.0: the first turn printed `session id: 01a1947e-83e8-7593-b8be-c4178ecd59e6`, a second session ran in the same folder, and `codex exec resume 01a1947e-83e8-7593-b8be-c4178ecd59e6 -c approvals_reviewer=auto_review "..."` resumed the first one. `codex exec resume <id>` resumes it, as `codex exec resume --help` shows: "Conversation/session id (UUID) or thread name."

The headless runner states the rule for any provider whose First turn has no `<session>`, without naming Codex.

`--last` stays correct only when no other Codex session ran later in the folder. A Codex reviewer after a Codex implementer breaks it. So the shipped `routing.md` changes Codex's Later turns to `codex exec resume <session> <flags> "<prompt>"`, and its codex note says to record the id (answer 1). The `SKILL.md` Size paragraph that said every phase starts fresh now names the exception (answer 2).

### 7. Fallback to a fresh session

A provider cannot resume when its Later turns cell is empty, or when `start-worker.sh --resume` exits 4. Then the coordinator starts a fresh implementer as today, with the same prompt. The Fix rounds paragraph in `roles/implementer.md` works for both: it no longer says an earlier session built the change.

### 8. The implementer ends at merge

The implementer stays running until Merge and clean up runs `end-worker.sh <issue>` with no role (answer 3). After a pass, a fix round can still come from a coordinator answer, a CI failure, or a rebase. An idle agent costs a pane, not usage.

### 9. Prompts stay one line

The fix-round and gate-round prompts keep today's text. A resumed session re-reads the newest review or check log from disk, as a fresh one would. The prompt stays the same either way, so the coordinator does not branch on how the session started.

## Risks

- A resumed session carries more context. Rounds are capped at two, so growth is bounded.
- A Herdr implementer the maintainer closed by hand makes `--resume` exit 4; the coordinator falls back.
- Existing projects keep `--last` in their own `routing.md`. With a reviewer on another provider it still resumes the implementer. The CHANGELOG line says to update the row.
