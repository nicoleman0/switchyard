# Tasks

## 1. Enforce the reviewer's provider

- [x] 1.1 In `scripts/start-worker.sh`, record `implementer_backend` when the role is `implementer`. Verify: a new test starts an implementer and reads the field from the record.
- [x] 1.2 In `scripts/start-worker.sh`, fail a `reviewer` start when the record has no `implementer_backend`, when the backend is `opencode`, or when the backend equals `implementer_backend` without `SWITCHYARD_SAME_PROVIDER=1`. Each failure prints a one-line reason. Verify: new tests in `scripts/test_state.py` cover the three failures, the override, and a passing start on the other provider, and assert that a failed start leaves the record unchanged.
- [x] 1.3 Confirm `state.py status` shows `reviewer` in the PHASE column with no code change, or fix it. Verify: a test asserts the status row for a record with `role=reviewer`.
- [x] 1.4 In Herdr, start a reviewer, end it, and start a second one for the same issue. If Herdr rejects the reused name, name reviewers `reviewer-<issue>-<round>` and update `runners/herdr.md`. Verify: both starts succeed, and the PR body says which naming was needed.

## 2. Add the role

- [x] 2.1 Write `roles/reviewer.md`: what to read, the review file's path and sections, the checks moved from the skill's PR review section, and the limits (no code edits, no commit, no push, no subagents). Verify: the file covers every section listed in design.md.
- [x] 2.2 Add `.claude/agents/issue-reviewer.md` with Opus and high effort, pointing to the role file as the other profiles do. Verify: `claude --agent issue-reviewer` starts in a worktree and reads the role file.
- [x] 2.3 Add a fix-round paragraph to `roles/implementer.md`: read the newest file in `.claude/reviews/`, add commits, update the archived change when a fix changes the design or tasks, and ask when a finding is unclear. Verify: read the role top to bottom as a fresh implementer on a fix round and confirm no step is ambiguous.
- [x] 2.4 Update `brief-template.md` where it names who reviews the work, and add the Review section to the PR sections. Verify: `grep -n "review" brief-template.md` shows the reviewer and the new section.

## 3. Update the coordinator's instructions

- [x] 3.1 In `SKILL.md`, add the two Reviewer rows to the routing table and the rule that picks the reviewer's provider, including the same-provider override. Verify: the table and rule match design.md.
- [x] 3.2 In `SKILL.md` step 4, tell the coordinator to read the change files on disk. Verify: the step names the proposal, design, spec delta, and tasks.
- [x] 3.3 In `SKILL.md`, add the review step after Watch, with the reviewer prompt, the fix round, and the two-round cap. Verify: the steps name every command a coordinator needs for a pass and for a fix round.
- [x] 3.4 In `SKILL.md`, replace the PR review checklist with what the coordinator does on a verdict, and make "Open the PR" depend on `Verdict: pass`. Keep the combined merge check for several PRs. Verify: the Scope, Writing, Code, and Screenshots checks appear only in `roles/reviewer.md`.
- [x] 3.5 Update the coordinator's opening list in `SKILL.md` and the roles named in `runners/herdr.md` and `runners/headless.md`. Verify: `grep -rn "implementer" .claude/skills/work-issues/runners` shows no line that should also name the reviewer.

## 4. Docs

- [x] 4.1 Update `README.md`: the "reviews twice" bullet, the roles table, the sequence diagram, steps 5 to 7, and the file tree. Verify: the diagram renders on GitHub and shows the reviewer between the implementer and the push.
- [x] 4.2 Add an entry under Unreleased in `CHANGELOG.md`. Verify: the entry says each issue now runs a reviewer session and names the override variable.

## 5. End to end

- [x] 5.1 Run the review loop in a scratch repo made from this branch: a hand-made archived change and a first commit with a seeded defect the change forbids, then a Claude reviewer, a Codex fix round, and a second Claude reviewer, all headless. Verify: the reviewer returns `changes requested` naming the defect, the fix round clears it, and the second review returns `pass`.

## 6. Repository checks

- [x] 6.1 `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck` passes.
- [x] 6.2 `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 6.3 `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 6.4 `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'` passes, with the test count in the PR body.
- [x] 6.5 `npx @fission-ai/openspec validate --all --strict` passes.
