# Tasks

## 1. State the platforms

- [x] 1.1 Add the bullet from proposal.md as the first item of the Requirements list in `README.md`, with the wording the coordinator approved. Verify: `git diff --stat origin/main` shows `README.md` with one added line and no removed lines, apart from the change's own files.

## 2. Repository checks

- [x] 2.1 `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck` passes.
- [x] 2.2 `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 2.3 `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 2.4 `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'` passes, with the test count in the PR body.
- [x] 2.5 `npx @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the same branch.
