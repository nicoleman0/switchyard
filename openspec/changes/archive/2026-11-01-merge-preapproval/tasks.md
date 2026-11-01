# Tasks

## 1. Skill

- [x] 1.1 In `switchyard/SKILL.md`, replace the Coordinator section's approval sentence with the text from design.md. Verify with `git diff` that no other sentence in that section changed.
- [x] 1.2 In the Merge and clean up section, replace the first three sentences with the wording from design.md, keep the squash-merge sentence, and insert the added mechanics sentences before "Then end its worker's session". Leave the teardown sentences, the rebase list, and the Several PRs section untouched. Verify with `git diff`.

## 2. Shared docs (per the brief)

- [x] 2.1 In `CHANGELOG.md`, add the line from design.md under Unreleased, in `### Changed`. Verify with `git diff` that no existing line changed.
- [x] 2.2 In `README.md`, append the sentence from design.md after the "three points" line in "One issue, start to finish". Verify with `git diff` that no existing line changed.

## 3. Repository checks

- [x] 3.1 `switchyard/hooks/checks.sh` passes from the worktree root.
- [x] 3.2 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
