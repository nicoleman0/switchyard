# Design

## Context

Every script keys an issue by its record, `.switchyard/state/<issue>.json`. `state.py` rejects any key that is not all digits. One record holds one worktree `path`, one `branch`, one Herdr `pane`, and the current worker. `start-worker.sh` names Herdr agents `<role>-<issue>`. Project hooks get `ISSUE`, and the shipped `worktree-up.sh` derives the port with `$((ISSUE % 1000))`, which fails on a non-digit value.

The planner commits nothing. After plan review, the change lives untracked in the issue's worktree, with the answers in `.switchyard/answers/`.

## Goals / Non-Goals

**Goals:**
- Two implementers on different providers build one reviewed change in parallel, off the same base.
- One reviewer compares them and names the one to keep.
- The kept candidate goes through the rest of the flow unchanged.

**Non-Goals:**
- More than two candidates.
- Best-of-N for planners or reviewers.
- Choosing best-of-N automatically. Only the maintainer names it.

## Decisions

### 1. A second record keyed `<issue>b`

Candidate a is the issue's own record, worktree, and branch. Candidate b is a full record under the key `<issue>b`, with branch `<branch>-b`. Every script that takes `<issue>` then works on either candidate unchanged: `start-worker.sh`, `end-worker.sh`, `wait-agents.sh`, `pre-review.sh`, `check-scope.sh`, `teardown-worktree.sh`, `state.py timings`. Herdr names become `implementer-120` and `implementer-120b`, so both agents run at once.

`state.py` accepts `^[0-9]+b?$` and rejects anything else with "issue key must be digits, optionally followed by b". `status` sorts by the number, then the suffix. `history.jsonl` keeps both summaries, so `timings` shows the loser as abandoned and counts its phases toward its provider.

Alternatives:
- Both candidates in one record, with per-candidate fields. Rejected: every script reads `path`, `pane`, and `worker` from the record and would need a candidate argument.
- A free suffix, any letter. Rejected: the issue asks for two. One fixed suffix is simpler to validate and to read.
- A made-up numeric key. Rejected: it can collide with a real issue.

### 2. `setup-worktree.sh` sets up candidate b

`setup-worktree.sh <issue>b <branch>-b`:
- reads `path`, `branch`, and `owned` from record `<issue>`, and exits 1 when it is missing;
- creates the worktree from candidate a's branch, not the checkout's branch, so both start from the same commit;
- copies each folder under candidate a's `openspec/changes/` except `archive`, and `.switchyard/answers/` when present;
- records `owned` and `candidate_of=<issue>` on the new record;
- copies `parent`, `parent_branch`, and `parent_head` when candidate a is stacked, so the scope check and `restack.sh` treat both candidates alike, and a parent's teardown waits for both;
- rejects `--parent` with a `b` key, since the base comes from candidate a.

The brief stays the coordinator's job. It copies candidate a's brief and changes the worktree, branch, and isolation lines.

Alternative: a new `setup-candidate.sh`. Rejected: it would still need `setup-worktree.sh` to take a base and split the hook variables, so it adds a file without removing any logic.

### 3. Hooks get `ISSUE` as digits and a new `CANDIDATE`

`setup-worktree.sh`, `teardown-worktree.sh`, and `pre-review.sh` pass `ISSUE=<digits>` and `CANDIDATE=<b or empty>`. A hook written for ordinary issues keeps working: its `ISSUE` is still a number. A hook that ignores `CANDIDATE` gives both candidates the same isolation values. Decision 7 covers that.

The shipped `worktree-up.sh` prints `port=4<nnn>` for candidate b and `port=3<nnn>` otherwise, so issue 120 gets 3120 and 4120. The headers of `worktree-up.sh`, `worktree-down.sh`, and `checks.sh` name `CANDIDATE`.

Alternative: pass `ISSUE=120b`. Rejected: it breaks the shipped port line and any project hook that does arithmetic on `ISSUE`.

### 4. Who builds and who reviews

- Best-of-N needs a reviewed change, so the issue takes the planner path even when it sizes `small`.
- After plan review, the coordinator picks two implementer providers in rotation order, each with its row for `size`. When the rows allow, it picks a pair that leaves a Reviewer row on a third provider.
- The reviewer uses the first Reviewer row whose provider differs from both. With none, it uses one that differs from candidate a's implementer, and the PR's Review section says "not independent of candidate b". `start-worker.sh` checks only candidate a's `implementer_backend`, because the reviewer starts on candidate a's record.
- Answers to either implementer go to both worktrees, so both build the same plan.

### 5. Gate before the comparison

The coordinator runs `pre-review.sh` on both keys. A failing candidate gets gate rounds as today, on its own key. After two failed gate runs in a row, it is abandoned and the other goes on to an ordinary review. When both fail, stop and bring the logs to the maintainer, as today.

### 6. One comparison review, on candidate a's record

The reviewer starts on candidate a's record. The prompt names both branches: `Read switchyard/roles/reviewer.md and follow it for issue #<issue>. Compare candidates <branch> and <branch>-b.`

The new reviewer paragraph says:
- Diff each candidate with `git diff origin/main...<branch>`. Branches are shared across worktrees, so no checkout is needed.
- Run the checks in each candidate's worktree, from `git worktree list`, with that worktree's brief's isolation values.
- Keep the candidate with fewer blockers. On a tie, keep the one that follows the design more closely and is easier to change.
- Write one review. Line 1 is the verdict for the kept candidate. Line 2 is `Keep: <branch>`. Sections 1 to 9 cover the kept candidate. A Comparison section, before Questions, gives each candidate's blockers and check results and the reasons for the pick.

### 7. Shared isolation falls back to one implementer

When candidate b's hook prints the same non-empty values as candidate a's, the project hook does not isolate candidates. Both would share ports or databases, and abandoning the loser would run the down hook on state the winner uses. The coordinator tells the maintainer, abandons candidate b, and runs the issue with one implementer.

### 8. After the pick

1. End the loser's sessions with `end-worker.sh <loser key>`.
2. When the kept candidate is b, copy the review into its `.switchyard/reviews/`, so fix rounds and `timings` read it there.
3. Run `teardown-worktree.sh --abandon <loser key> <loser branch>`.
4. Go on at Act on the verdict with the kept candidate's key and branch for every later step. The PR's head is the kept branch.

### 9. Where the text goes

- `SKILL.md`: a new `## Best-of-N` section after Abandon an issue, holding Decisions 4 to 8 as short steps. Per issue step 5 gets one appended sentence: "When the maintainer named best-of-N for this issue, follow Best-of-N instead." No other section changes.
- `roles/reviewer.md`: one paragraph after section 9's paragraph, holding Decision 6.

### 10. Meeting points with in-flight work

- #114 warm fix rounds: implementers stay alive through review. Ending the loser in Decision 8 uses `end-worker.sh <loser key>`, which with #114 ends every role of that record. The reviewer's split pane opens from candidate a's pane, and teardown of candidate a closes it. A fix round on candidate b resumes `implementer-<issue>b`.
- #121 merge queue, merged: `merge-queue.py` checks keys with `state.py`'s `valid_key`, so a kept candidate b queues as `<issue>b`.
- #124 busy time, merged: the overlap in `state.py` is the key check and the `status` sort.
- #119 stacked worktrees, merged: see Decision 2 for the parent fields.
- #118 question queue: questions from two implementers on one issue may queue twice. The answer goes to both worktrees (Decision 4).

## Risks / Trade-offs

- [About twice the implementer usage] → Opt-in per issue, named by the maintainer.
- [A project hook ignores `CANDIDATE`] → Decision 7 falls back to one implementer.
- [Main moves between the two setups] → Candidate b branches from candidate a's branch, not from the checkout.
- [The reviewer shares a provider with one candidate] → Decision 4 prefers a third provider and says so in the PR otherwise.
