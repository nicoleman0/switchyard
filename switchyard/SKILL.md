---
name: work-issues
description: How the coordinator session delivers GitHub issues in this repo. Each issue gets its own worktree, a planner that writes the change and stops, an implementer on any provider the project lists that applies the reviewed change and commits it, and a reviewer that checks the commit against the change. Use whenever the user asks to work on, implement, or run one or more issues, or a milestone's next steps.
---

# Work issues

You are the coordinator. You run on the main checkout. You never build an issue yourself. After review you may make small fixes, as Act on the verdict says. Your work is the judgment and the glue:
- splitting the work,
- writing briefs,
- reviewing plans,
- acting on review verdicts,
- relaying questions to the maintainer,
- merging and cleaning up.

Agents do the planning, the building, and the review of the diff. Scripts do the mechanical steps. Paths below are relative to this skill's folder unless they start with `switchyard/` or a dot.

## Runner

The runner is how you start a worker in its worktree, prompt it, wait for it, read its report, and end its session. Pick one per session and read its file:
- Inside Herdr (`HERDR_ENV=1`): `runners/herdr.md`. Prefer it. Workers run in panes the maintainer can watch.
- Anywhere else: `runners/headless.md`. Each worker turn is one CLI command.

The steps below say start, prompt, wait, read, and end. The runner file gives the commands.

## Routing

The providers, models, effort, flags, and commands for workers live in `switchyard/routing.md`. That file is the project's to edit, and its values are examples. Its Workers table is the routing table. Its Providers table holds each provider's commands.

Who decides, in this order:
1. What the maintainer names in the session: a provider, a model, a size, a row, or a command.
2. The row in `routing.md`.
3. Your own choice, when there is no usable row, no Providers row for the provider, or no file. Pick a provider, a model, and the command to run. Tell the maintainer what you chose and why before the worker starts. Do not wait for approval.

When the maintainer names a model, use the row the issue's size picks for that provider and role, with the model replaced. When the maintainer names a size, it replaces yours. When the maintainer names a row or a command, use it as named. When the row has no model flag and the maintainer names a model, add the model flag using the syntax in that provider's note in `routing.md`. Otherwise use the provider's own default.

- A row is usable when its provider's CLI is installed and the provider is under the usage threshold. If its first turn fails to start or reach its model, skip that provider for the batch, move to the next usable row, and tell the maintainer which provider failed and the error.
- Planner: use the Planner row for your provider. If there is none, use the first Planner row.
- Implementers: rotate through providers with an Implementer row, in the order they first appear. Leave out a provider whose CLI is not installed.
- Once a provider is chosen for a role, the size picks the row (see Size).
- A row marked `when named` is used only when the maintainer names its provider. A Use cell may hold a size and `when named` together, such as `large, when named`.
- Skip a provider when more than about 70% of its usage window is used. The provider notes in `routing.md` say how to read each one. Ask the maintainer when a provider has no note or its note says usage cannot be read.
- At each sizing, say it in one line per issue: the size, and each role's provider, model, and effort from the chosen row. When the second size differs from the first, say both. Do not wait for approval.

The reviewer uses the first Reviewer row whose provider differs from the implementer's. When there is none, or it is not usable, review on the implementer's provider with `SWITCHYARD_SAME_PROVIDER=1` on that `start-worker.sh` command. Tell the maintainer once per batch that the review is not independent, and write "same provider, not independent" in the PR body's Review section. A choice under rule 3 still prefers another provider than the implementer's.

### Size

Size every issue `small`, `medium`, or `large`, twice:
- Before the planner starts, from your read of the issue against the code (Before starting, step 1). The planner uses this size.
- After the plan review, from the reviewed change: its Impact list, tasks, design decisions, and `answers/plan.md`. The implementer, its fix rounds, and the reviewer use this size. A fix round does not re-size.

A `small` issue sizes once and takes the fast path (Per issue, step 3). Its size stays `small` unless its worker stops because the issue is bigger.

Criteria:
- `small`: one concern in one place. The issue states the exact result, and the fix follows from reading the code. Examples: a wording or config change, a bug with a known cause in one function. No new interface, data format, or dependency.
- `large`: any one of these:
  - the work spans several components or owned folders;
  - it changes a data format, stored data, a public interface, or anything other code, projects, or users depend on;
  - a mistake could lose data, open a security hole, or break concurrency;
  - the plan leaves judgment the plan cannot capture.
- `medium`: everything else.

Between two sizes, take the larger. An under-powered worker costs a fix round; a larger row costs some usage.

A Workers row names a size in its Use cell. Size picks a whole row, model and effort together, as the project wrote it. Never edit a row's flags to change effort. Once a provider is chosen for a role, take:
1. the first row for that role and provider whose Use cell names the size;
2. otherwise the first row with no size, the default;
3. otherwise, when every row names a size and none matches, the first row for that role and provider. Tell the maintainer.

A Use cell of `escalation`, from an older `routing.md`, counts as `large`. A row names one size; for two sizes, write two rows. A file with no sized rows picks its default row for every size.

Record the sizes and rows with `state.py set`, passing each key as one quoted argument (see Per issue, steps 3, 4, 5, and 7).

Each phase starts a fresh session. Fix rounds and gate rounds resume the implementer's session when its provider can; the reviewer is always fresh. Every handoff is a file in the worktree: the brief, the answers, the change, and the review. A worker reads them from disk, not from another session's context or from your summary, so the expensive context is not carried into the cheap phase.

Workers never push. Implementers commit and write `.switchyard/pr-body.md`, then stop, so nothing reaches the remote before the review passes. `setup-worktree.sh` disables the push URL in each worktree, so a push works only from the main checkout. The coordinator pushes from there and opens the PR.

## Coordinator

The coordinator must be able to read `AGENTS.md` and this skill, run the skill's scripts, write to issue worktrees, and push from the main checkout. It must get the maintainer's approval before merging, per PR or as a pre-approval that names the batch's condition (see Merge and clean up). These requirements apply even when the CLI runs commands without permission prompts. Follow the matching coordinator note in `switchyard/routing.md` for setup, permissions, and waiting behavior.

## Batch state

Issue records live in `.switchyard/state/<issue>.json` in the main checkout. `setup-worktree.sh`, `start-worker.sh`, and `teardown-worktree.sh` write or remove them. Run `python3 switchyard/scripts/state.py status` first in a new coordinator session, then read each worker with the runner's Read command. On headless, read the newest log in `<path>/.switchyard/turns/`.

`start-worker.sh` and `end-worker.sh` record when each phase starts and ends. Headless phases end at the next start or at teardown. Run `python3 switchyard/scripts/state.py turn-end <issue>` as soon as a worker's wait returns, before you read it. Run `python3 switchyard/scripts/state.py turn-start <issue>` before you prompt or unblock the same session again. Run `python3 switchyard/scripts/state.py timings [issue]` for time per phase with its BUSY and WAIT columns, review rounds, and the verdict. Teardown appends each issue's summary to `.switchyard/history.jsonl`, so the report covers finished issues.

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

## Plans

A project uses OpenSpec when its main checkout has an `openspec/` folder. Without one it uses plain mode. "The change" means the OpenSpec change or, in plain mode, `.switchyard/plan.md` in the issue's worktree.

In plain mode the planner copies `switchyard/plan-template.md` to `.switchyard/plan.md` and fills it in. The implementer ticks its tasks. The reviewer checks its scenarios, tasks, and decisions. There is no `Change:` issue line and nothing to archive. Teardown deletes the plan; the PR body keeps the summary.

## Before starting

Run `scripts/preflight.sh <provider>...` first, passing the provider names in `routing.md`. It checks the requirements and says how to fix each missing one. Stop on a non-zero exit and tell the maintainer what is missing. Pass its warnings on.

1. Read the issues and `AGENTS.md`. Check the issues against the code. For each one, write down anything the issue leaves undecided, and ask the maintainer before any agent starts.
2. Split the issues by ownership. Each issue owns folders that no other issue in the batch edits. Issues that touch the same files run one after another, not in parallel. Run first the one whose result the others build on. The maintainer may name issues to stack instead; see Stacked issues.
3. Make sure the shared services `AGENTS.md` names are up in the main checkout.

## Per issue

1. **Set up.** Run `scripts/setup-worktree.sh <issue> <branch>`. It records the issue and prints the worktree path, the runner's handles, and the isolation values from the project's `hooks/worktree-up.sh`. Keep them for the brief.
2. **Brief.** Copy `brief-template.md` to `<path>/.switchyard/brief.md` and fill every `{placeholder}`. Under the coordinator notes, put:
   - the decisions already made,
   - what is out of scope and which issue owns it,
   - any known traps, with the lines from `switchyard/lessons.md` that apply to this issue.
   `.switchyard/` holds the ignored runtime files.

   Record the owned paths for the scope check: `python3 scripts/state.py set <issue> "owned=<path> <path>"`. Separate them with spaces and end folders with `/`.
3. **Plan.** Size the issue from your Before starting read. Record it: `python3 scripts/state.py set <issue> plan_size=<size>`. Pick the planner row for that size from `switchyard/routing.md` and record it: `python3 scripts/state.py set <issue> "planner_row=<provider> <flags>"`. Start the planner with those flags, then prompt it: `Read switchyard/roles/planner.md, then .switchyard/brief.md, and plan issue #<issue>.` Include the role path so every provider can read the same instructions.

   Fast path: instead of starting the planner, a `small` issue skips the plan review. Record `size=small` as well; there is no `planner_row`. Pick the implementer provider and its `small` row as in step 5, record `implementer_row`, and start it with role `implementer`. Prompt it: `Read switchyard/roles/implementer.md, then .switchyard/brief.md, and take the fast path for issue #<issue>.` Then go to step 6. When it stops with numbered questions, read the change, write the answers to `answers/plan.md`, and prompt the same session to go on. When it stops because the issue is bigger than `small`, end its session and run steps 4 and 5. At step 7, read the change along with the review, since the plan had no review of its own.
4. **Review the plan.**
   - Read the change on disk: the proposal, the design, the spec delta, and the tasks, or `.switchyard/plan.md` in plain mode. The planner's last message is only its list of questions.
   - Check the change against the code and the specs. Verify any claim it makes about the code or the data before you rely on it.
   - A change with `skip_specs: true` has no spec delta. In plain mode, `Scenarios: none` serves the same purpose. Check that the planner used either only when the work changes no observable behaviour.
   - Answer what you can.
   - Bring product decisions to the maintainer: anything that changes behaviour the issue does not settle, or that reaches past the paths the issue owns. Add them to the question queue.
   - Write the answers to `<path>/.switchyard/answers/plan.md`.
   - Size the reviewed change again and record it: `python3 scripts/state.py set <issue> size=<size>`. Tell the maintainer.
5. **Implement.** End the planner's session. Pick the implementer provider from the routing table in `switchyard/routing.md`, then the row for `size`. Record it: `python3 scripts/state.py set <issue> "implementer_row=<provider> <flags>"`. Start it in the same worktree. Then prompt it: `Read switchyard/roles/implementer.md, then .switchyard/brief.md and .switchyard/answers/, and implement the change for issue #<issue>.` When the maintainer named best-of-N for this issue, follow Best-of-N instead.
6. **Watch.** Wait for the worker, then read its report. Answer it with a file in `.switchyard/answers/` and a one-line prompt that points to the file. Add questions only the maintainer can answer to the question queue.
   Give `wait-agents.sh` a `--timeout <seconds>` bound. Name the agents to wait for, and leave out any whose issue waits on questions. On exit 4 the script has printed each agent still working: read that agent's pane, then nudge, end, or reassign it.
   Run `state.py turn-end <issue>` when a wait returns and `state.py turn-start <issue>` before you prompt the same session again (Batch state).
7. **Review.** When the implementer reports its commit, leave its session running. Start the reviewer on another usable provider when available. Otherwise set `SWITCHYARD_SAME_PROVIDER=1` and use the implementer's provider. Pick the row for `size` and pass its flags from `switchyard/routing.md`. Record it: `python3 scripts/state.py set <issue> "reviewer_row=<provider> <flags>"`. Then prompt it: `Read switchyard/roles/reviewer.md and follow it for issue #<issue>.` Wait for it, then read the newest file in `<path>/.switchyard/reviews/`.
   Before the reviewer starts, run `scripts/pre-review.sh <issue>`. Exit 0: go on. Exit 2: fix what it names yourself. Exit 1 with only `FAIL scope`: rule on each listed file as in Open the PR, step 1, accept one by adding it to `owned` with `state.py set`, and run the gate again. Any other exit 1: resume the implementer with `scripts/start-worker.sh <issue> implementer <provider> --resume`. If that exits 4, start a new one on the same row and record `implementer_row`. Prompt it: `Read switchyard/roles/implementer.md, then .switchyard/brief.md, .switchyard/answers/, and the newest file in .switchyard/checks/, and fix the failed checks for issue #<issue>. The change is already built: follow the Fix rounds paragraph with that log in place of a review.` Then run the gate again. After two failed gate runs in a row, stop and bring the log to the maintainer. Gate rounds do not count toward the two `changes requested` rounds.

## Act on the verdict

The reviewer checks the diff against the change. Read its review, not the diff. Open the diff only to rule on a finding the implementer disputes or a question the reviewer raises, or to make a small fix.

- **`Verdict: pass`:** make any small fixes, then open the PR.
- **`Verdict: changes requested`:** when every blocker fits a small fix, fix them and open the PR without another review. Otherwise end the reviewer's session, with role `reviewer` on Herdr, and resume the implementer with `scripts/start-worker.sh <issue> implementer <provider> --resume`. If that exits 4, start a new implementer session. Prompt it: `Read switchyard/roles/implementer.md, then .switchyard/brief.md, .switchyard/answers/, and the newest file in .switchyard/reviews/, and fix the findings for issue #<issue>.` Do not restate the findings. For a new session, pick its row for `size` without re-sizing, and record `implementer_row` again. Then run step 7 again with a new reviewer session.
- **A second `changes requested`:** stop. Bring the open findings to the maintainer.
- **Questions for the coordinator:** answer what you can in `.switchyard/answers/`, and add product decisions to the question queue. If an answer changes the change, run a fix round.
- **Small fixes:** fix notes and blockers yourself when all your fixes for one review total about 10 changed lines or fewer, as `git diff --stat` counts them, code included. Edit and commit in the worktree. Do not amend. Run every check in the brief. If one fails, undo your commit and run a fix round. Record each fix in the PR body's Review section with the finding and the file. Leave a note unfixed when you disagree with it.

## Open the PR

After `Verdict: pass`:
1. Run `scripts/check-scope.sh <issue>`. It lists the files the branch changed outside its owned paths. The change's files under `openspec/` are always in scope when the repo uses OpenSpec. Rule on each listed file: accept an appended section in a shared doc, and send anything else back as a fix round.
2. From the main checkout, push with `git push -u origin <branch>`.
3. Fill the Review section of `.switchyard/pr-body.md` with the reviewer's provider, the verdict, and the number of rounds. Copy the Where to look list from the passing review to the top of the PR body, under a `## Where to look` heading.
4. Fill the Screenshots section. If your harness can publish a page, as Claude Code's Artifact tool can, publish `<path>/.switchyard/shots/compare.html` and put the link there. Otherwise write that the comparison page was not published, and give its local path.
5. Run `gh pr create --head <branch> --body-file <path>/.switchyard/pr-body.md`. Add `--milestone <milestone>` when the brief names one.

## Several PRs

End each issue's worker sessions. Run `python3 scripts/merge-queue.py <issue>...` in merge order. It rebases each worktree, resolves append-only conflicts, runs `pre-review.sh`, pushes with a lease, and waits for CI.

Exit 3 prints the merge command. Run it on its own after the maintainer approves, then run the queue again with the issues not yet torn down. Pass `--merge` only when the maintainer pre-approved merges for the batch; it merges and tears down each issue before moving on.

Exit 1 names the file or step that stopped. Fix it in the worktree, commit, and run the queue again. Run the queue in the background when the CLI limits command time. `--timeout <seconds>` bounds the CI wait for each PR (default 1800).

## Stacked issues

Stack only when the maintainer names the issues in the session, and only after the parent's review passes. Keep one level; a parent may have several children.

1. Run `scripts/setup-worktree.sh --parent <parent> <child> <branch>`. The child's record stores `parent`, `parent_branch`, and `parent_head` at branch time.
2. Tell the child's reviewer in its brief to diff `<parent_head>...HEAD`. Open its PR with `gh pr create --base <parent_branch>`.
3. After the parent merges, run `scripts/restack.sh <child>` from the main checkout for each child. It fetches, rebases only the child's commits with `--onto origin/main <parent_head>`, pushes with a lease when the remote branch exists, retargets any open PR to `main`, and clears the parent fields. Run every check after the rebase. On conflict it lists the files and aborts; resolve the restack by hand, then finish the push, retarget, and state update.
4. Tear down the parent after every child is restacked or abandoned. Both teardown modes refuse while a child names the parent.

Do not queue a child with its parent in `merge-queue.py`. Parent teardown stops while children remain stacked. Restack the children after the parent merges, then rerun the queue for the parent and children. Queue integration is a follow-up.

## Merge and clean up

The maintainer approves each merge, or pre-approves a batch by naming the condition in the coordinator conversation, for example reviewer pass and green CI. A pre-approval is explicit, covers that batch only, and the maintainer can withdraw it. Without a pre-approval, merge only after the maintainer explicitly approves that PR. The rule applies on every CLI, including those that can run commands without a permission prompt. A CLI prompt is not maintainer approval. Squash-merge one PR with `gh pr merge <pr> --squash`, without `--delete-branch`. Tell the maintainer after each merge. With a pre-approval, when the repo allows auto-merge (`gh api repos/{owner}/{repo} --jq .allow_auto_merge`), append `--auto`: `gh pr merge <pr> --squash --auto` merges when CI finishes. When CI has already passed, `--auto` refuses, so merge without it. When the repo does not allow auto-merge, wait for CI with `gh pr checks <pr> --watch`, then merge. Run each `gh pr merge` as its own command, not chained with a CI wait or another merge. With `--auto`, wait for the merge to land before the teardown. When the maintainer withdraws a pre-approval, cancel each pending one with `gh pr merge <pr> --disable-auto`. Then end its worker's session and run `scripts/teardown-worktree.sh <issue> <branch>`. It runs the project's `hooks/worktree-down.sh`, removes the worktree, deletes the local and remote branch, and removes the record. Teardown skips steps that are already done and still removes the record.

For each PR still open, run the queue as Several PRs says.

## Abandon an issue

When an issue is dropped before its worktree is committed, run `scripts/teardown-worktree.sh --abandon <issue> <branch>`. It prints the uncommitted files and the local-only commits it is about to discard, then removes the worktree, the branch, and the record. Passing `--abandon` is the consent; it never prompts. Ordinary teardown stops instead of removing a dirty worktree.

## Best-of-N

Run it only when the maintainer names it for an issue. It roughly doubles implementer usage. Candidate a is the issue's own record, worktree, and branch. Candidate b is record `<issue>b` on branch `<branch>-b`. Every script that takes `<issue>` takes either key.

1. **Plan.** Take the planner path even when the issue sizes `small`, so both candidates build a reviewed change.
2. **Set up candidate b.** After the plan review, run `scripts/setup-worktree.sh <issue>b <branch>-b`. It branches from candidate a's branch, copies the open change and `.switchyard/answers/`, and records `owned` and `candidate_of`. Copy candidate a's brief into the new worktree and change its worktree, branch, and isolation lines.
3. **Check isolation.** When candidate b's hook printed the same non-empty values as candidate a's, the project hook ignores `CANDIDATE`. Tell the maintainer, run `scripts/teardown-worktree.sh --abandon --skip-hook <issue>b <branch>-b` so the down hook leaves candidate a's state alone, and go on at Per issue step 5 with one implementer.
4. **Implement.** Pick two implementer providers in rotation order, each with its row for `size`. When the rows allow, pick a pair that leaves a Reviewer row on a third provider. Record and start one on each key as in Per issue step 5. Write every answer to both worktrees, so both build the same plan.
5. **Gate.** Run `scripts/pre-review.sh` on both keys. A failing candidate gets gate rounds on its own key, as in Per issue step 7. After two failed gate runs in a row, drop it as in step 7 below and give the other an ordinary review at Per issue step 7. When both fail, stop and bring the logs to the maintainer.
6. **Compare.** Leave both implementers' sessions running. Start one reviewer on candidate a's key, with the first Reviewer row whose provider differs from both implementers. With none, use one that differs from candidate a's implementer, and write "not independent of candidate b" in the PR's Review section. Prompt it: `Read switchyard/roles/reviewer.md and follow it for issue #<issue>. Compare candidates <branch> and <branch>-b.` Line 2 of its review names the kept branch: `Keep: <branch>`.
7. **Keep one.** End the loser's sessions, with `scripts/end-worker.sh <loser key>` on Herdr. When the kept candidate is b, copy the review into its `.switchyard/reviews/`. Run `scripts/teardown-worktree.sh --abandon <loser key> <loser branch>`. Go on at Act on the verdict with the kept candidate's key and branch for every later step. Fix rounds resume the kept candidate's implementer with `scripts/start-worker.sh <kept key> implementer <provider> --resume`, and the PR's head is its branch.

## Record lessons

After each teardown, merged or abandoned, update `switchyard/lessons.md` in the main checkout. Add a line for each trap that cost time on that issue, such as a flag a CLI rejected, a check that needed a service, or a review finding that came back. Follow the format in its header. Delete lines that no longer apply. At the end of the batch, commit the file on its own small PR.
