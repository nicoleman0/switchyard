# Design

## Context

- The Coordinator section says "It must get explicit maintainer approval before merging." Merge and clean up opens with "Merge only after the maintainer explicitly approves", then the rule on CLI prompts, then the squash-merge sentence, the teardown sentences, and the rebase list.
- The coordinator's decision (brief, Issue notes): pre-approval is explicit, covers that batch only, and the maintainer can withdraw it. Without it, today per-PR approval stands.
- Issue #121 edits the Several PRs section and the rebase list under Merge and clean up in parallel. This change touches only the approval wording.
- `gh pr merge <pr> --squash --auto` needs the repo to allow auto-merge: check with `gh api repos/{owner}/{repo} --jq .allow_auto_merge`. When the PR's checks already pass, `--auto` refuses; a direct `gh pr merge <pr> --squash` then merges immediately.
- The same wording lives in two places: the Coordinator section's requirement sentence and the rule at the top of Merge and clean up.

## Goals / Non-Goals

**Goals:**
- The maintainer decides the batch's merge conditions once, not once per PR.
- Without a pre-approval, nothing changes.
- Tight, additive edits that keep the merge small against parallel edits in the same file.

**Non-Goals:**
- A script for any of it: #121 owns the merge-queue work. This change writes prose.
- Changing how checks run, what CI requires, or the rebase flow.

## Decisions

### Approval wording for Merge and clean up

Replace the first three sentences (today's approval rule and the CLI-prompt rule):

> The maintainer approves each merge, or pre-approves a batch by naming the condition in the coordinator conversation, for example reviewer pass and green CI. A pre-approval is explicit, covers that batch only, and the maintainer can withdraw it. Without a pre-approval, merge only after the maintainer explicitly approves that PR. The rule applies on every CLI, including those that can run commands without a permission prompt. A CLI prompt is not maintainer approval.

Keep the existing squash-merge sentence. Insert after it, before "Then end its worker's session":

> Tell the maintainer after each merge. With a pre-approval, when the repo allows auto-merge (`gh api repos/{owner}/{repo} --jq .allow_auto_merge`), append `--auto`: `gh pr merge <pr> --squash --auto` merges when CI finishes. When CI has already passed, `--auto` refuses, so merge without it. When the repo does not allow auto-merge, wait for CI with `gh pr checks <pr> --watch`, then merge. Run each `gh pr merge` as its own command, not chained with a CI wait or another merge. With `--auto`, wait for the merge to land before the teardown.

- Alternative: on a withdrawn pre-approval, run `gh pr merge <pr> --disable-auto` on the PRs still open. Deferred: the maintainer withdraws before enabling anything, and disabling auto-merge is one command a coordinator can reach for; it does not need rule text. Covered in the PR body as a decision to review.
- Alternative: put the auto-merge logic in a script. Rejected: #121 may script the queue; prose keeps this change small and the conflict trivial.

### Approval sentence for the Coordinator section

Replace "It must get explicit maintainer approval before merging." with:

> It must get the maintainer's approval before merging, per PR or as a pre-approval that names the batch's condition (see Merge and clean up).

### README sentence

"You are asked something at three points: before work starts, after the plan, and at the merge." is incomplete once a batch is pre-approved. Append one sentence:

> Pre-approve the batch's merges and step 9 asks nothing more: the coordinator merges on the condition you named.

### CHANGELOG line

Under Unreleased, in `### Changed`:

> - #113: The maintainer can pre-approve a batch's merges by naming the condition in the coordinator conversation. The approval covers that batch only and can be withdrawn. With a repo that allows auto-merge, `gh pr merge --squash --auto` merges each PR when its CI finishes.

## Risks / Trade-offs

- [A merge enabled with `--auto` cannot be withdrawn] → The maintainer withdraws a pre-approval before CI finishes. Pulling that into rule text would grow the batch's wording; the PR body lists it as a decision to review.
- [The Coordinator section and Merge and clean up say near-same things] → DRY: the second names the mechanics and points the first at it. The existing text already repeats the rule this way.
- [Claude Code's classifier may refuse a chained command] → The skill says to run each merge as its own command, which matches what worked this batch.
