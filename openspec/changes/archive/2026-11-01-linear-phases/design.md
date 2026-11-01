# Design

## Context

`tracker.py` has `view`, `set-change`, and `check` on GitHub and Linear (#148, #149). `load_tracker` reads one `Tracker:` line from `switchyard/tracker.md`, which the project owns: the updater adds it when missing and never changes it, so existing Linear installs will not get new lines. `start-worker.sh` records a worker and starts it; it already exits 1 on bad input and 4 when a resume is impossible. The question queue in `SKILL.md` is one local file, `.switchyard/questions.md`, and `state.py` records `waiting=questions`.

## Goals / Non-Goals

**Goals:**
- Linear issues show the current phase and carry the open questions and their answers.
- GitHub projects see no change in behaviour or output.
- A wrong status name fails at the first worker start, not halfway through a batch.

**Non-Goals:**
- Delivery order and blocked-by relations (#151).
- A status for Done or for an abandoned issue. Linear's GitHub integration moves the issue on merge; an abandoned issue keeps its status for the maintainer to set.
- Checking status names in preflight. Statuses belong to a team, and preflight does not know the batch's teams until #151.

## Decisions

### Linear API

From Linear's SDK schema (https://raw.githubusercontent.com/linear/linear/master/packages/sdk/src/schema.graphql, read 2026-11-01):
- `Issue.team: Team!`; `Team.states(first, after, filter): WorkflowStateConnection!`; `WorkflowState.id`, `name`, `type`.
- `IssueUpdateInput.stateId: String`.
- `commentCreate(input: CommentCreateInput!): CommentPayload!`, with `CommentCreateInput.issueId` and `body`; `CommentPayload.success`.
- `Comment.parentId` and `CommentFilter.parent` exist, so `Issue.comments` returns thread replies as well as top-level comments. `view` already reads every comment and sorts by `createdAt`, so a reply in the question comment's thread shows up after it.

Queries, all with variables:
- set-phase: `issue(id: $id) { id team { name states(first: 250) { nodes { id name } pageInfo { hasNextPage } } } }`, then `issueUpdate(id: $id, input: { stateId: $stateId }) { success }`. `hasNextPage` true fails with "more than 250 statuses": a team that large is not worth paging for, and a silent miss would be worse.
- comment: `commentCreate(input: { issueId: $id, body: $body }) { success }` with the issue's UUID. The schema types `issueId` as a plain string and does not say it takes an identifier, so look up the UUID as `set_change` does.
- `success: false` fails as in `set_change`.

The UUID lookup (`issue(id) { id }` plus the "Linear has no issue" error) is now needed by three operations. Move it into one `Linear` method first, as its own refactor task with the tests unchanged, then use it in the new operations.

### Phases and default statuses

Phases: `planning`, `plan-review`, `building`, `in-review`, `needs-input`. Lowercase with dashes, so they are plain CLI words.

Linear's default team workflow has Backlog, Todo, In Progress, In Review, Done, and Canceled. Defaults:

| Phase | Status | In Linear's defaults |
| --- | --- | --- |
| `planning` | `Planning` | no, add it |
| `plan-review` | `Plan review` | no, add it |
| `building` | `In Progress` | yes |
| `in-review` | `In Review` | yes |
| `needs-input` | `Needs input` | no, add it |

Todo is an unstarted status, so it is wrong for an issue a planner is working on. Mapping planning and plan review to In Progress would hide the phases the issue asks to show. The README tells the maintainer to add the three statuses in the team's Started group. The maintainer approved three new statuses so each phase is visible.

Names match exactly. On a miss the error lists the team's statuses, which makes a case slip a one-line fix; a fuzzy match could pick the wrong status.

The defaults live in a `PHASES` dict in `tracker.py`: one home, and existing installs get them without editing `tracker.md`.

### Override table in tracker.md

```
| Phase | Status |
| --- | --- |
| needs-input | Blocked |
```

`load_tracker` reads every line that starts with `|`. It skips the header (first cell `Phase`) and the separator. Any other row must name a known phase once with a non-empty status, or `load_tracker` raises `TrackerError` quoting the row. The result is passed to `Linear(statuses=...)`. GitHub ignores it but the table is still checked, so a typo fails on every tracker the same way.

The shipped `tracker.md` gets one line saying the table is optional and the README lists the defaults. It does not repeat the defaults, which would be a second home.

Alternative: `Phase: status` lines. A table reads better beside the README's table, and `routing.md` already uses tables.

### set-phase on GitHub

A no-op that still checks the key and the phase. `SKILL.md` and `start-worker.sh` then call `set-phase` the same way on every tracker, and a typo in a phase name fails on GitHub projects too. The cost is one Python start per worker start.

Alternative: branch in `SKILL.md` and `start-worker.sh` on the tracker. That puts the tracker choice in two more files.

### comment on GitHub

`gh issue comment <n> --body-file <file>`. Nothing on GitHub calls it yet; it is a few lines and keeps the backends' operations the same, so `load_tracker` callers never ask which operations exist. The blank-file check happens before either backend runs.

### Telling the question comment from replies

The question comment's first line is `Questions from Switchyard`. Answers are the comments after the newest comment whose first line is exactly that. `view` already prints comments oldest first with their times, so no new read operation is needed.

Alternatives:
- Record the comment id or time in the state file. That needs `comment` to print the id and `view` to print ids, and a coordinator in a new session reads the same thing from the marker anyway.
- A `replies` operation. More code for something `view` already shows.

The marker is SKILL knowledge used in two places in one section, the post and the read. `tracker.py comment` stays generic and does not add it.

When new questions come up while earlier ones are open, the new comment repeats the unanswered ones, so the newest marker comment always holds every open question.

### Phase by role in start-worker.sh

`start-worker.sh` maps role to phase (planner `planning`, implementer `building`, reviewer `in-review`) and runs `python3 "$script_dir/tracker.py" set-phase "${issue%b}" "$phase"`:
- after its argument and record checks, including the reviewer's provider check and the resume checks that exit 4, so those still win;
- before the Herdr pane split, the agent start, and any `state.py set`, so a failure leaves nothing to clean up.

On failure it prints `Issue <issue>: cannot set the tracker phase; no worker started.` after the tracker's own stderr, and exits with the tracker's status. The tracker's message passes through unchanged, so `LINEAR_API_KEY is not set` reaches the coordinator.

A failure stops the start. The likely failures are a missing key or a status the team lacks, and both are config errors that would fail every later call too; stopping at the first planner start shows them before any work. The cost: a Linear outage blocks worker starts. The maintainer chose to stop the start.

A fix round resumes the implementer with `--resume`, which sets `building` again, moving the issue back from In Review. A fast-path implementer plans and builds in one session and shows `building` throughout.

The coordinator sets `plan-review` and `needs-input` itself, since no script runs at those points.

### Question queue on Linear

`SKILL.md`, Question queue, gets a Linear paragraph. The rules about what to queue, recording `waiting=questions`, and showing the maintainer every open question in one message stay shared. On Linear:
1. Write the issue's questions to `<path>/.switchyard/question-comment.md`: the marker line, then numbered questions with options and a recommendation. Run `tracker.py comment <issue> <file>` and `tracker.py set-phase <issue> needs-input`.
2. Each time a wait returns, run `tracker.py view` for each issue waiting on questions and read the comments after the newest marker comment.
3. When every question is answered, in Linear or in the chat, copy the answers to the answers file, clear the wait, and set the phase the issue left: `plan-review` for plan questions, `building` for an implementer's.

`questions.md` is not used on Linear.

### Key agreement test

`test_tracker.py` imports `state` and checks a fixed list (`ENG-123`, `A1-7`, `ENG-1234567`, `eng-123`, `ENG-`, `ENG-12a`, `-12`, `E-1`, `1ENG-2`): for each key that is not all digits, `state.valid_key` and the Linear key check agree. It does not import one pattern into the other script, which would couple two orthogonal scripts.

## Risks / Trade-offs

- [No live Linear call was possible] → Queries follow the published schema and are pinned with the fake transport #149 uses. The PR body says it is untested against live Linear.
- [Linear's GitHub integration also moves statuses, for example on PR open] → Our moves happen at phase starts and theirs at PR events; the last write wins and Done comes from theirs. The maintainer accepted this overlap. The README says the integration may also move the issue when the PR opens and merges, and that Done comes from it.
- [A team lacks a status] → First `start-worker.sh` fails with the team's status list.
- [Linear down] → Worker starts stop until it is back.
- [Comments posted between the marker and the answer that are not answers] → The coordinator reads them as text and judges; no parsing relies on reply format.

## Migration Plan

GitHub projects: nothing. Linear projects: add Planning, Plan review, and Needs input to each team, or add a table to `tracker.md` naming existing statuses. Until then the first worker start fails with the team's status list.
