# Design

## Context

See proposal.md for the motivation. The constraints that shape the approach:

- The planner and implementer already hand off through files in the worktree: the brief, `.claude/answers/`, and the change under `openspec/changes/`. Each phase starts a fresh session.
- The implementer archives the change before it commits, so at review time the change is in `openspec/changes/archive/<date>-<name>`.
- `start-worker.sh` accepts any role that has a file in `roles/`, and overwrites `role`, `backend`, `worker`, and `session` in the issue record. A record describes one current worker.
- Herdr gives each issue one pane. opencode always uses the session `ses_issue<issue>`.
- Workers never push. The coordinator pushes after review.

## Goals / Non-Goals

**Goals:**
- An independent check of each diff against the change, on a provider other than the one that wrote it.
- The coordinator's context holds verdicts, not diffs.
- Every handoff is a file on disk. No stage depends on a summary another session wrote in chat.

**Non-Goals:**
- A second reviewer for the plan. The coordinator keeps plan review because it owns the product decisions and the relay to the maintainer.
- Enforcing that workers do not push or leave their owned paths. That is issue #6.
- A reviewer on opencode.
- Review of several PRs together. The coordinator still runs the combined merge check.

## Decisions

**The reviewer is a third worker role, run after the implementer commits and before the push.**
It uses the same start, prompt, wait, read, and end verbs as the other roles. Alternative: a subagent of the coordinator. Rejected, because its report would land in the coordinator's context and it could not run on another provider.

**The reviewer's output is a file: `.claude/reviews/<round>.md`.**
The first line is `Verdict: pass` or `Verdict: changes requested`. The body has these sections:
- Findings, one per scenario and task of the change, each marked met or not met. A finding that is not met gives the file and line, what the change says, and what the diff does.
- Answers: each file in `.claude/answers/`, and whether the change's design and tasks reflect it.
- Scope: paths changed outside the brief's owned paths.
- Checks: the reviewer runs every check itself and gives real numbers.
- Screenshots and writing, as the coordinator's checklist has them today.
- Questions for the coordinator: places where the reviewer thinks the change itself is wrong.

The reviewer grades the diff against the change, not against its own preferences. A disagreement with the change goes under Questions and does not change the verdict. Alternative: the verdict as the last chat message, as the planner does. Rejected, because the implementer could then only get the findings through the coordinator's retelling.

**The reviewer does not edit code, commit, or push.**
It may run checks on the issue's isolation values. The only file it writes is its review.

**Each phase stays a fresh session, including fix rounds.**
On `changes requested`, the coordinator ends the reviewer and starts a new implementer session with a prompt that points to the review file. On the next round it starts a new reviewer, which writes `.claude/reviews/<round+1>.md`. Alternative: resume the implementer's session. Rejected, because the record and the Herdr pane hold one worker at a time, so a resumable implementer needs a second set of record fields and a second pane. A fresh session reads the same files and costs one re-read on a cheap model.

**Fix rounds do not rewrite history.**
The fix-round implementer adds commits. If a fix changes the design or the tasks, it edits the archived change to match. The PR is squash-merged, so the extra commits do not reach `main`.

**Two rounds, then the maintainer.**
After a second `changes requested`, the coordinator stops and brings the open findings to the maintainer. Without a cap, two models that disagree can loop.

**Provider routing.**
- Implementer on Claude: reviewer on Codex, `gpt-5.6-sol`, high.
- Implementer on Codex or opencode: reviewer on Claude, the `issue-reviewer` profile, Opus, high.
- When the other provider is not installed or is over the usage threshold, the coordinator runs the reviewer on the implementer's provider and tells the maintainer.

Review is judgment work, so it gets the planner's tier, not the implementer's.

**`start-worker.sh` enforces the provider rule.**
When the role is `implementer`, it also records `implementer_backend`. When the role is `reviewer`, it fails if:
- the record has no `implementer_backend`,
- the backend is `opencode`,
- the backend equals `implementer_backend` and `SWITCHYARD_SAME_PROVIDER=1` is not set.

A failed start leaves the record unchanged, as it does today. Alternative: leave the rule as prose in the skill. Rejected, because issue #6 exists for the reason that prose rules are not enforced, and the check is a few lines.

**The coordinator's part after a verdict.**
- Read the newest file in `.claude/reviews/`.
- On `pass`: push, fill the Screenshots and Review sections of the PR body, open the PR.
- On `changes requested`: start the fix round.
- Answer the reviewer's questions, or bring them to the maintainer.
- Open the diff only to rule on a finding the implementer disputes or a question the reviewer raised.

The Scope, Writing, Code, and Screenshots checks move from the skill's PR review section into `roles/reviewer.md`. They have one home.

**Plan review reads the change.**
Step 4 tells the coordinator to read the proposal, design, spec delta, and tasks on disk. The planner's last message is only the list of questions.

## Risks / Trade-offs

- [One more session per issue, on the strong tier] → It replaces diff reading in the coordinator's context, which is the most expensive context in the batch.
- [The reviewer passes work the coordinator would have caught] → The maintainer still reviews the PR, and the Review section names the provider so a weak reviewer shows up over time.
- [A fresh fix-round implementer misreads why the code is as it is] → It has the change, the answers, the diff, and the review file. If a finding is unclear it asks the coordinator, as its role already requires.
- [Herdr may reject a second agent named `reviewer-<issue>` after the first one ended] → Checked: Herdr frees a name when its agent exits, so the names are reused.
- [With one provider installed, the review is not independent of the model family] → The override is explicit and the coordinator reports it.
