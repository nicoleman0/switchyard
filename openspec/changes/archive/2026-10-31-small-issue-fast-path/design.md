# Design

## Context

- `start-worker.sh` records `implementer_backend` only when the role is `implementer`, and refuses to start a reviewer without it. It also requires `roles/<role>.md` to exist.
- The Claude agents in `.claude/agents/` each say "Read `switchyard/roles/<role>.md` and follow it. It is your full role." `issue-planner`'s description says it never implements. Codex, opencode, and pi have no agent files; the prompt names the role file.
- Per issue step 4 re-sizes after the plan review. Step 5 ends the planner and starts an implementer on the new size.
- Issue #115 edits the opening Coordinator paragraph and Act on the verdict in parallel. This change does not touch them.

## Goals / Non-Goals

**Goals:**
- One session for a `small` issue, with a stop only for questions or a size mismatch.
- The same prompt and flow on every provider.

**Non-Goals:**
- Making OpenSpec optional (#82).
- Changing the reviewer role, the scripts, or `routing.md`.

## Decisions

### Run the fast path as the implementer role

The session starts with role `implementer` on the implementer provider's `small` row. Its prompt: `Read switchyard/roles/implementer.md, then .switchyard/brief.md, and take the fast path for issue #<issue>.`

- `implementer.md` holds the fast-path paragraph and sends the worker to `planner.md` steps 1 to 3. So "It is your full role" in `issue-implementer` stays true, and the same prompt works on Claude, Codex, opencode, and pi.
- `start-worker.sh` records `implementer_backend`, so step 7 and the same-provider check work unchanged. The worker is named `implementer-<issue>`.
- Alternative: start with role `planner` and prompt both roles. Rejected: `issue-planner` says it never implements, and the reviewer would refuse to start with no `implementer_backend`.
- Alternative: a new `fast` role file and agent. Rejected: a fourth role duplicates both and needs script and routing changes.

### Text for `implementer.md`

Insert before the "Fix rounds:" paragraph:

> Fast path: when the prompt says fast path, no change exists yet. Plan it first: follow `switchyard/roles/planner.md` steps 1 to 3. Do not re-size; the issue stays `small`. Stop with the planner's summary when you have numbered questions, or when the issue is bigger than `small`; then say which and why. Otherwise go on to step 1 above. When the coordinator answers, read `.switchyard/answers/` and go on.

### Text for `planner.md`

Append as the last line:

> On the fast path, an implementer session runs steps 1 to 3 of this role. `switchyard/roles/implementer.md` says when it stops.

### Text for `SKILL.md` Per issue step 3

Append to step 3, indented as part of it:

> Fast path: a `small` issue skips the plan review. Record `size=small` as well. Pick the implementer provider and its `small` row as in step 5, record `implementer_row`, and start it with role `implementer`. Prompt it: `Read switchyard/roles/implementer.md, then .switchyard/brief.md, and take the fast path for issue #<issue>.` Then go to step 6. When it stops with numbered questions, read the change, write the answers to `answers/plan.md`, and prompt the same session to go on. When it stops because the issue is bigger than `small`, end its session and run steps 4 and 5. At step 7, read the change along with the review, since the plan had no review of its own.

Steps 4 and 5 stay as they are. The fallback reuses them: step 4 re-sizes, step 5 starts a new implementer on the new row.

### Text for `SKILL.md` Size section

Append after the two-bullet list under "Size every issue ... twice":

> A `small` issue sizes once and takes the fast path (Per issue, step 3). Its size stays `small` unless its worker stops because the issue is bigger.

### Answers on the fast path go to the same session

The coordinator answers questions by prompting the live session, as in step 6. Ending it would cost the context reload the fast path exists to save. On headless this is the provider's Later turns command; on Herdr, a prompt to `implementer-<issue>`.

### Shared docs (approved in answers/plan.md)

`README.md` says "the planner stops at a plan" (line 33) and "You are asked something at three points" (line 63). Both become partly wrong. Proposed append, after step 5 in "One issue, start to finish":

> A `small` issue skips steps 4 and 5: one session plans and builds, and stops after the plan only when it has questions.

`CHANGELOG.md`, under Unreleased, a new `### Changed` section:

> - #116: A `small` issue is planned and implemented in one session. It stops for a plan review only when it has questions.

## Risks / Trade-offs

- [Planning runs at the implementer's `small` effort, lower than the Planner `small` row on Claude and Codex] → The reviewer grades the diff against the change, and the coordinator reads the change at step 7. A wrong size makes the worker stop.
- [Nobody checks the plan against the issue before code is written] → The coordinator reads the change at step 7. A fix round costs less than the plan stop on most small issues.
- [`state.py status` shows phase `implementer` while the session is still planning] → Accepted. The phase names the role, not the step.
- [The Claude agent description currently assumes a reviewed change] → Reword it to cover planning first on the fast path, as approved in `answers/plan.md`. Keep it one sentence.

## Reviewed decisions

- The coordinator approved the README and CHANGELOG lines and added those lines to the owned paths.
- Reword `.claude/agents/issue-implementer.md`'s description as one sentence covering planning first on the fast path and the existing delivery duties.
- Lower planning effort on the implementer's `small` row is accepted.
- The coordinator reads the change at step 7. Leave `reviewer.md` unchanged.
- Issue #115 owns the Fix rounds wording in `implementer.md`. Insert before it and leave it unchanged.
- This issue was reviewed as `medium`; that does not change the fast path's `small` size rule.
