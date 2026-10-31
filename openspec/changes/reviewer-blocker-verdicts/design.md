# Design

## Context

`switchyard/roles/reviewer.md` defines nine review sections and ends with "The verdict is `changes requested` when any line in sections 1 to 7 fails." `switchyard/SKILL.md` says "You never implement an issue yourself" and, under Act on the verdict, sends every `changes requested` to a new implementer and a new reviewer.

#114 (fix rounds resume the implementer) and #116 (small fast path) edit nearby text in the same milestone. Several issues edit different sections of `SKILL.md` in parallel.

## Goals / Non-Goals

**Goals:**
- Only blockers cost a fix round.
- The coordinator closes small findings itself and leaves a record in the PR body.

**Non-Goals:**
- How a fix session starts or resumes (#114).
- Skipping plan review for small issues (#116).
- Running checks before the reviewer starts (#117).
- Any script change. `state.py` and the runners do not read the review body.

## Decisions

### 1. Label failing lines, not every line

Each failing line in sections 1 to 7 starts with `Blocker:` or `Note:`. A passing line says met or pass and has no label. Labelling a met line "note" would read as a finding.

Alternative: label every line. Rejected: noise, and "Note: 1.1 met" misleads.

### 2. Blocker list, per section

| Section | Blocker | Note |
|---|---|---|
| 1 Findings | a scenario or task not met | none |
| 2 Answers | the code does not follow an answer | the change's design or tasks lag an answer the code follows |
| 3 Scope | a change outside the brief's paths, other than an appended section in a shared doc | none |
| 4 Code | a security or data-loss problem; behaviour removed or reordered that the change does not call for (a scope breach) | DRY, test gaps no task asks for, other code quality |
| 5 Checks | a check that fails | PR body numbers that differ from the reviewer's run |
| 6 Writing | none | every finding |
| 7 Screenshots | none | a missing or incomplete comparison page |

The reviewer text states the four blocker kinds and says everything else is a note. It does not reprint this table: the table is the reasoning, the four kinds are the rule. Rows 2, 4, and 7 are open questions for the coordinator.

### 3. Coordinator wording

The Coordinator paragraph replaces "You never implement an issue yourself." with "You never build an issue yourself. After review you may make small fixes, as Act on the verdict says." The bullet list is unchanged. This is the narrowest change that makes the new permission consistent.

### 4. Small fixes, in Act on the verdict

A new bullet, **Small fixes**, appended to the section:
- Fix notes and blockers yourself when all your fixes for the review together are about 10 changed lines or fewer, as `git diff --stat` counts them, code included.
- Edit in the worktree and commit there. Do not amend.
- Run every check in the brief. If one fails, undo your commit and run a fix round instead.
- Record each fix in the PR body's Review section: the finding and the file.
- Leave a note unfixed when you disagree with it.

The `Verdict: pass` bullet becomes: make any small fixes, then open the PR.

The `changes requested` bullet gains a first sentence: when every blocker fits a small fix, fix them and open the PR without another review. The rest of the bullet stays as written, so #114's edits to the fix-session text rebase cleanly.

The intro sentence "Open the diff only to rule on a finding the implementer disputes or a question the reviewer raises." gains "or to make a small fix".

Alternative: after coordinator fixes to blockers, run one more reviewer. Rejected as the default: it costs the session this issue removes, and the checks rerun anyway. Raised as a question.

### 5. Budget is per review, not per fix

"About 10 lines" counts all coordinator fixes for one review together. A per-fix limit would let the coordinator rebuild a task in 10-line pieces.

## Risks / Trade-offs

- [The coordinator fixes a blocker wrong and no reviewer sees it] → the budget is small, every check reruns, and the fix is listed in the PR body for the human reviewer.
- [Reviewers label a real defect as a note] → the four blocker kinds are listed in the role text; the coordinator still reads every note and may send any finding to a fix round.
- [Parallel edits to `SKILL.md`] → edits are confined to two sentences in the Coordinator paragraph and to the Act on the verdict section, mostly appended.
