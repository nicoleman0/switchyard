# Design

## Context

- Questions reach the maintainer in four places in `switchyard/SKILL.md`: Before starting step 1 (before any agent starts), Per issue step 4 (plan review), step 6 (a worker's report, which also covers the fast path's questions from step 3), and Act on the verdict's Questions bullet. Today each says "bring ... to the maintainer" and the coordinator waits.
- `.switchyard/` is git-ignored. The main checkout's `.switchyard/state/` already holds batch state that a new coordinator session reads first.
- `state.py set <issue> key=` stores an empty string. `state.py get` already treats an empty value as missing. `status` builds PHASE from `role`, or `setup` when there is none.
- `wait-agents.sh` with no names waits on every named Herdr agent and returns when one is `idle`. An agent that stopped with questions is idle, so an unnamed wait returns at once while its issue waits on the maintainer.
- A coordinator that ends its turn to ask a question stops every issue. One that keeps working can still read a file between steps. That is why answers can land in the file as well as in the chat.

## Goals / Non-Goals

**Goals:**
- One place that holds every open maintainer question, grouped by issue.
- The coordinator keeps the other issues moving while a question is open.
- `state.py status` shows which issues wait on answers, including in a new coordinator session.

**Non-Goals:**
- A script that adds, reads, or removes questions. The coordinator already writes answers files by hand.
- Changing Before starting step 1. Those questions come before any work starts and already go out in one pass.
- Changing what a worker writes. Workers still stop with numbered questions; only the coordinator touches the queue.

## Decisions

### Queue file: `.switchyard/questions.md` in the main checkout

Next to `.switchyard/state/`, so a new coordinator session finds it with the state records. Ignored, so it never reaches a commit. One file, so the maintainer reads every open question in one place.

### Format

```markdown
## #<issue> <title>

Answers go to: `<path>/.switchyard/answers/<file>.md`

1. <question>
   - A: <option> (recommended)
   - B: <option>
   Answer:
```

The `Answers go to` line names the worktree file the answers are copied to, so the coordinator resumes the right phase: `plan.md` for a plan review, another file for a worker's report or a review.

### State field: `waiting=questions`

One field. Set when an issue's section joins the queue, cleared with `waiting=` when its answers are copied. `status` appends `, waiting` to PHASE when the field is non-empty, so the live agent state in STATE stays visible. The value names the reason so `state.py get <issue> waiting` reads plainly; `status` only checks that it is non-empty.

### SKILL edits, kept small for parallel rebases

- New section `## Question queue` inserted after `## Batch state`, before `## Before starting`. It is the one home for the rules; the three call sites point to it. Text:

  ```markdown
  ## Question queue

  Open questions for the maintainer wait in one file, `.switchyard/questions.md` in the main checkout, so one issue's question does not stall the batch.
  - Queue only what you cannot answer: product decisions, and anything that reaches past the paths an issue owns. Answer the rest yourself.
  - Give each issue one section: a `## #<issue> <title>` heading, an `Answers go to:` line naming the answers file in its worktree, and numbered questions. Each question has two or three options, a recommendation, and an empty `Answer:` line.
  - Record the wait: `python3 scripts/state.py set <issue> waiting=questions`.
  - Show the maintainer the whole queue in one message, then go on with the other issues. The maintainer answers on the `Answer:` lines or in the chat.
  - Read the queue each time a wait returns.
  - When all of an issue's questions are answered, copy the answers to its answers file and delete its section. Clear the wait with `python3 scripts/state.py set <issue> waiting=`, then resume the issue where it stopped.
  - When no issue can move until an answer lands, end your turn with the queue.
  - Delete an issue's section when the issue is torn down.
  ```

- Step 4, the bullet `- Bring product decisions to the maintainer: ...`: append ` Add them to the question queue.` No other line in the step changes. The issue stays at step 4 until its answers land.
- Step 6, after the `Answer it with a file ...` sentence: append ` Add questions only the maintainer can answer to the question queue.` After the `wait-agents.sh` paragraph's first sentence: append ` Name the agents to wait for, and leave out any whose issue waits on questions.`
- Act on the verdict, Questions bullet: replace `and bring product decisions to the maintainer.` with `and add product decisions to the question queue.`

### `state.py status`

```python
phase = record.get("role") or "setup"
if record.get("waiting"):
    phase += ", waiting"
```

One test in `test_state.py`: a record with `role=planner` and `waiting=questions` shows `planner, waiting`; after `set <issue> waiting=` it shows `planner` alone.

## Risks / Trade-offs

- [The maintainer answers in the file while the coordinator blocks in a long wait] The answer waits until the wait returns. `wait-agents.sh --timeout` bounds that. Accepted.
- [Answers in chat on a CLI that does not deliver messages mid-turn] They arrive when the coordinator ends its turn, which is today's behaviour. The file path still works mid-turn.
- [The queue and the state field drift] Both change in the same step of the queue section. A stale `waiting` shows in `status`, which a new session reads first.
- [The new section sits outside the sections named for this issue] It is an insertion between two headings, not a reword. It conflicts only with another insertion at the same spot.
