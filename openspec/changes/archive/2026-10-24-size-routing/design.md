# Design

## Context

See proposal.md for the motivation. What the code and files do today:

- `switchyard/SKILL.md` Routing: rule 1 (maintainer) beats rule 2 (the row) beats rule 3 (coordinator's own choice). The first row for a role and provider is the default. A later row is used only when its Use cell says so or the maintainer names it. A `when named` row is used only when the maintainer names its provider.
- Escalation is in two places in `SKILL.md`: "For escalation, use the Implementer row marked `escalation`" and "Escalate a single issue only when the plan review shows judgment the plan cannot capture."
- `switchyard/routing.md` Use cells hold only empty, `escalation`, or `when named`. The one `escalation` row is the claude Implementer on `--model opus --effort high`.
- `update-switchyard.py` lists `switchyard/routing.md` in `PROJECT_OWNED`: added when missing, never changed after. Projects on 0.7.2 and older keep their file, `escalation` row included.
- `start-worker.sh` writes `role`, `backend`, `worker`, and `session` on every start, so those keys hold the latest worker only. `state.py set` stores any other key and keeps it until teardown. `state.py status` prints a fixed set of columns.
- No script reads the Use cell. The coordinator reads `routing.md` and passes the flags.
- `claude --help` lists `--effort` levels `low, medium, high, xhigh, max`. Codex takes `-c model_reasoning_effort=<level>`.

## Goals / Non-Goals

**Goals:**
- Each role's row follows the size of the issue at the time the role starts.
- Criteria a coordinator can apply in one read of an issue or a change, with no stack assumptions.
- A `routing.md` with no sized rows behaves as it does today.

**Non-Goals:**
- OpenRouter rows (#76), recording the model a worker actually ran on (#77), cost tracking (#79).
- Parsing or rewriting provider flags to change effort. A size picks a row the project wrote.
- Script changes. Nothing parses `routing.md`.
- Telling workers their size. No role reads it.

## Decisions

**Sizes and criteria, in `SKILL.md`.**
A new "Size" subsection under Routing:

- `small`: one concern in one place. The issue states the exact result, and the fix follows from reading the code. Examples: a wording or config change, a bug with a known cause in one function. No new interface, data format, or dependency.
- `large`: any one of these:
  - the work spans several components or owned folders;
  - it changes a data format, stored data, a public interface, or anything other code, projects, or users depend on;
  - a mistake could lose data, open a security hole, or break concurrency;
  - the plan leaves judgment the plan cannot capture.
- `medium`: everything else.
- Between two sizes, take the larger. An under-powered worker costs a fix round; a larger row costs some usage.

The first size reads the issue against the code, in Before starting step 1. The second applies the same criteria to the reviewed change: its Impact list, tasks, design decisions, and the answers in `answers/plan.md`. The last `large` criterion is today's escalation trigger, so it now lives in the criteria.

Alternative: numeric limits such as files or tasks. Rejected. They depend on the stack and on how a planner splits tasks.

**Picking a row by size.**
Rules 1 to 3 and the provider rules stay. After the provider for a role is chosen, the row within it is:
1. The first row for that role and provider whose Use cell names the size.
2. Otherwise the first row with no size. This is the default row.
3. Otherwise, when every row names a size and none matches, the first row for that role and provider. Tell the maintainer.

A `when named` row still needs the maintainer to name its provider. A Use cell may hold a size and `when named` together, such as `large, when named`. A row names one size; a project that wants one row for two sizes writes two rows.

The planner uses the first size. The implementer, its fix rounds, and the reviewer use the second. A fix round does not re-size.

**The maintainer's word.**
Rule 1 extends to size. When the maintainer names a size, it replaces the coordinator's. When the maintainer names a model, take the row the size picks for that provider and replace its model. When the maintainer names a row or a command, use it as named.

**`escalation` counts as `large`.** (Question 1.)
A Use cell of `escalation` reads as `large`. The escalation paragraphs in `SKILL.md` go. Escalating an issue becomes sizing it `large` after the plan review.
- A 0.7.2 file has one sized row: the claude Implementer `escalation` row. Every other role and provider has only default rows, so every size picks today's row. An implementer on claude for a `large` issue gets the `escalation` row.
- Today that row is used when the coordinator escalates, and the trigger is the last `large` criterion. The other `large` criteria are new, so a 0.7.2 project may run the opus row more often. The CHANGELOG entry says so. A project that does not want this deletes the row, and names the model in the session for the issues that need it.

Alternatives in question 1.

**State keys.**
The coordinator runs `state.py set` with:
- `plan_size=<size>` before the planner starts;
- `size=<size>` after the plan review;
- `planner_row`, `implementer_row`, `reviewer_row`, each set before that worker starts, to `<provider> <flags>`: the provider and the flags the coordinator passed, after any change the maintainer named. A fix round overwrites `implementer_row` and `reviewer_row`.

The flags are what ran, so they cover a maintainer override without a second field. `state.py set` quotes nothing, so the coordinator passes each key as one shell argument: `"implementer_row=claude --agent issue-implementer --model opus --effort high --permission-mode auto"`.

**What the maintainer is told.**
`SKILL.md` already says "Say which provider and model each issue got." It becomes: at each sizing, one line per issue with the size, and each role's provider, model, and effort from the chosen row. When the second size differs from the first, say both. Do not wait for approval.

**Shipped `routing.md`.**
Header gains one sentence: a Use cell may name a size, `small`, `medium`, or `large`, and `SKILL.md` says how sizes pick rows. The Workers table:

| Role | Provider | Flags | Use |
|---|---|---|---|
| Planner | claude | `--agent issue-planner --model opus --effort high --permission-mode auto` | |
| Planner | claude | `--agent issue-planner --model sonnet --effort medium --permission-mode auto` | small |
| Planner | codex | `-c model_reasoning_effort=high --approve-for-me` | |
| Planner | codex | `-c model_reasoning_effort=medium --approve-for-me` | small |
| Planner | pi | | when named |
| Implementer | claude | `--agent issue-implementer --model sonnet --effort medium --permission-mode auto` | |
| Implementer | claude | `--agent issue-implementer --model sonnet --effort low --permission-mode auto` | small |
| Implementer | claude | `--agent issue-implementer --model opus --effort high --permission-mode auto` | large |
| Implementer | codex | `-c model_reasoning_effort=medium --approve-for-me` | |
| Implementer | codex | `-c model_reasoning_effort=low --approve-for-me` | small |
| Implementer | codex | `-c model_reasoning_effort=high --approve-for-me` | large |
| Implementer | opencode | `--auto` | |
| Implementer | pi | | when named |
| Reviewer | claude | `--agent issue-reviewer --model opus --effort high --permission-mode auto` | |
| Reviewer | claude | `--agent issue-reviewer --model sonnet --effort medium --permission-mode auto` | small |
| Reviewer | codex | `-c model_reasoning_effort=high --approve-for-me` | |
| Reviewer | codex | `-c model_reasoning_effort=medium --approve-for-me` | small |
| Reviewer | pi | | when named |

- Default rows are today's values, so `medium` needs no rows.
- Planner and reviewer defaults are already the strongest example values, so they get no `large` row.
- opencode and pi keep one row each. They show that a provider with no sized rows still serves every size.
- No versioned model IDs. Codex rows change effort only.

**README and CHANGELOG.**
- README Make it yours, `routing.md` row: the Workers table can give an issue size its own row.
- README overview, "Several providers share the load": add that the coordinator picks each role's row by the issue's size.
- CHANGELOG, Unreleased, Added: one `#78` line: sizes, sized rows, `escalation` counts as `large`, a file with no sized rows works as before, and deleting the `escalation` row stops size from picking it.

## Risks / Trade-offs

- [Two coordinators size the same issue differently] → The criteria are short and lean to the larger size. The size is recorded and told to the maintainer, who can name another.
- [A 0.7.2 project runs its opus implementer more often] → Stated in the changelog with the one-line way out.
- [A sized row's model is not reachable] → The existing rule skips the provider for the batch. That is stricter than falling back to the default row, but it is today's rule, and a real turn in task 3.2 checks the shipped rows.
- [Rules in prose depend on the coordinator] → The table is small. Task 3.1 walks the rules through three files.

## Open Questions

1. **How does `escalation` map onto sizes?**
   - a. `escalation` counts as `large`, and the escalation step goes. Recommended. One mechanism, and re-sizing after the plan review is the point where escalation was decided. Old files keep working with no edit; their claude implementer may run on opus more often.
   - b. Keep escalation as its own step on top of size. `escalation` rows are used only when the coordinator escalates, and size ignores them. Old files behave exactly as today, but the skill has two overlapping ways to pick a stronger implementer.
   - c. Ignore `escalation`. Old files lose escalation until the project renames the row. Not recommended: it breaks a working file.

2. **Should `state.py status` show the size?**
   - a. No. Recommended. The brief prefers no script change, the coordinator reads the size with `state.py get <issue> size`, and the maintainer is told at each sizing.
   - b. Yes, add a SIZE column. Small change and one test, and a new coordinator session sees sizes in its first command.

3. **Which way does the coordinator lean between two sizes?**
   - a. Take the larger. Recommended. A fix round costs more than a stronger row.
   - b. Take the smaller. Saves more usage, which is the issue's motive, at the risk of more fix rounds.
