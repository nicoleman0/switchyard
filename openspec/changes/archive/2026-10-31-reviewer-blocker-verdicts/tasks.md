# Tasks

## 1. Reviewer role

- [x] 1.1 In `switchyard/roles/reviewer.md`, change "check that each of their findings is fixed" to "check that each of their blockers is fixed". Verify with `grep -n "blockers is fixed" switchyard/roles/reviewer.md`.
- [x] 1.2 In section 4 (Code), add one sentence: check for a security or data-loss problem. Keep the section number and title. Verify by reading the section.
- [x] 1.3 Replace the verdict paragraph ("The verdict is `changes requested` when any line in sections 1 to 7 fails. ...") with: mark each failing line in sections 1 to 7 `Blocker:` or `Note:`; a passing line says met or pass with no mark; a blocker is a scenario or task not met, a check that fails, a scope breach, or a security or data-loss problem; everything else is a note, such as writing, style, or code quality; the verdict is `changes requested` only when a line is a blocker; notes alone give `Verdict: pass`. Keep "Write "none" under a section with nothing to report." Apply design.md decision 2 to the answers it settles. Verify the first-line rule and the nine section headings are unchanged with `git diff switchyard/roles/reviewer.md`.

## 2. Coordinator skill

- [x] 2.1 In `switchyard/SKILL.md`, replace "You never implement an issue yourself." with "You never build an issue yourself. After review you may make small fixes, as Act on the verdict says." Leave the bullet list as it is. Verify with `git diff switchyard/SKILL.md`: one line changed in that paragraph.
- [x] 2.2 In Act on the verdict, append "or to make a small fix" to the sentence about opening the diff.
- [x] 2.3 Change the `Verdict: pass` bullet to: make any small fixes, then open the PR.
- [x] 2.4 Prepend to the `Verdict: changes requested` bullet: when every blocker fits a small fix, fix them and open the PR without another review. Leave the rest of the bullet word for word.
- [x] 2.5 Append a **Small fixes** bullet with the rules in design.md decision 4: about 10 changed lines for all fixes to one review, as `git diff --stat` counts them, code included; edit and commit in the worktree without amending; run every check in the brief, and on a failure undo the commit and run a fix round; record each fix in the PR body's Review section with the finding and the file; leave a note unfixed when you disagree with it.
- [x] 2.6 Verify no other section of `SKILL.md` changed: `git diff switchyard/SKILL.md` shows hunks only in the Coordinator paragraph and Act on the verdict.

## 3. Shared files (only with the coordinator's approval in `.switchyard/answers/`)

- [x] 3.1 Append `- #115: Only blockers (an unmet scenario or task, a failed check, a scope breach, a security or data-loss problem) request changes. The coordinator may fix notes and small findings itself, up to about 10 lines.` under Unreleased, in a `### Changed` section of `CHANGELOG.md`. Append only.
- [x] 3.2 If the answers approve it, in `switchyard/roles/implementer.md` change "fix each finding it marks not met" to "fix each finding it marks `Blocker:`". Nothing else in that paragraph.

## 4. Repository checks

- [x] 4.1 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 4.2 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 4.3 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` passes.
- [x] 4.4 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 4.5 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
