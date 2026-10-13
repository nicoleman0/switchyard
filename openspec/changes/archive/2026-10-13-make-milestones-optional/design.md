# Design

## Context

See proposal.md for the motivation. What the code and docs do today:

- `grep -rni milestone` finds seven places: `AGENTS.md` lines 5 and 7, `README.md` lines 73, 162 to 164, and 170, `SKILL.md` line 3 (the description) and line 122, `brief-template.md` line 9, and `openspec/config.yaml` line 6.
- No script reads or writes a milestone. `state.py`, `setup-worktree.sh`, and `start-worker.sh` do not know the field. The milestone exists only as text the coordinator fills in.
- The role files and `.github/ISSUE_TEMPLATE/issue.yml` do not mention milestones. A GitHub issue form cannot set one.
- Issues #24, #28, and #31 edit `README.md`, `AGENTS.md`, and `SKILL.md` in parallel branches.

## Goals / Non-Goals

**Goals:**
- A coordinator in a project without milestones has a written rule for the brief and the PR.
- A project that uses milestones sees no change in behaviour.

**Non-Goals:**
- Any script that reads milestones from GitHub.
- Changing how the coordinator orders a batch. "Before starting" step 2 of `SKILL.md` stays as it is.
- Removing "Run the next steps of milestone M2" from the README. It stays valid for projects that use milestones.

## Decisions

**The rule is per issue, not per project.**
The PR takes the milestone of its issue. An issue without one gets no `--milestone` flag, whether or not the repository has milestones. Alternative: a project-wide setting in `AGENTS.md`. Rejected, because the issue already carries the fact, and a setting would be a second home for it.

**The brief keeps its milestone line and says "none".**
The placeholder becomes `{milestone, or "none"}`. Alternative: drop the line when there is no milestone. Rejected: step 2 of "Per issue" tells the coordinator to fill every placeholder, and an explicit "none" shows the field was considered, not forgotten.

**Step 5 of "Open the PR" names the condition in the step itself.**
The command is shown without the flag, and one sentence says to add `--milestone <milestone>` when the issue has one. The coordinator reads the milestone from the brief, which is the only place it is recorded.

**Delivery order is stated once, in `AGENTS.md`.**
The first Workflow bullet makes issues the source of truth for the breakdown, and names the source of order for both cases. The README and the skill do not repeat it. The ordering rule in "Before starting" still applies inside a batch: issues that share files run one after another, and the one the others build on runs first.

**Edits stay inside the sections the brief names.**
Each edit replaces one line or one list item. Nothing else is reflowed, so the parallel branches rebase cleanly.

**The skill's description keeps "or a milestone's next steps".**
It is a trigger phrase, and it is still true for projects with milestones.

## Wording

`AGENTS.md`, first Workflow bullet:

> Use the GitHub issues as the source of truth for implementation breakdown. Milestones are optional. With them, they set the delivery order. Without them, the order is the one the maintainer names the issues in.

`AGENTS.md`, "New work" bullet: replace `(problem and milestone)` with `(the problem, and a milestone if the project uses them)`. The rest of the bullet is unchanged.

`SKILL.md`, "Open the PR" step 5:

> Run `gh pr create --head <branch> --body-file <path>/.claude/pr-body.md`. Add `--milestone <milestone>` when the brief names one.

`brief-template.md`, milestone line:

> - Milestone for the PR: {milestone, or "none"}.

`README.md`, "One issue, start to finish" step 1:

> **You open an issue.** State the problem. Pick a milestone if the project uses them. Keep it short: acceptance criteria belong in the change, not the issue.

`README.md`, "Use it" step 1:

> Create an issue. Add `--milestone` if the project uses milestones:

with the command changed to `gh issue create --title "Password reset emails arrive twice" --body "..."`.

The implementer may adjust a word to fit the surrounding text, but not the rule.

## Risks / Trade-offs

- `AGENTS.md` is in `update-paths.txt`. A project that reworded either bullet gets a conflict on update. The edit touches two bullets only, so the conflict is small.
- The first bullet grows from one sentence to four. It is the one home for the ordering rule, so the length is accepted.

## Open Questions

Answered by the coordinator. The tasks mark the work each answer drove.

1. `openspec/config.yaml` line 6 says "Delivery order and issue breakdown live in GitHub milestones and issues." Approved: reword that line only. The file is in the implementer's owned paths.
2. `CHANGELOG.md` is outside the owned paths. Approved: add one line under Unreleased, in a Changed group.
3. "Use it" step 3 of the README keeps "Run the next steps of milestone M2." with no note that it needs milestones. Answer: leave it as it is.
