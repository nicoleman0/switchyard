# Tasks

Read `.claude/answers/plan.md` first. Update the design and these tasks if an answer changes a decision.

## 1. Project initializer

- [x] 1.1 Add `scripts/init-project.py`, runnable from the project root. Move `README.md` to `docs/WORKFLOW.md`, create `docs/` when needed, remove its Switchyard banner line, update the workflow chart path, remove the guide's `## License` section, and delete the explicit template-only file list. Verify the command's output and resulting paths in a temporary project fixture.
- [x] 1.2 Report every moved, deleted, or skipped path, including missing sources and an existing `docs/WORKFLOW.md`; finish with the README, LICENSE, and `AGENTS.md` Project-section setup steps. Verify a second run skips absent sources and preserves an existing destination.
- [x] 1.3 Before any change, confirm the directory is inside a git work tree and stop if it is not; skip any listed path with uncommitted changes, reported as `skipped (uncommitted changes)`. Verify both behaviors.
- [x] 1.4 Add initializer tests in `scripts/test_init_project.py` for the complete file list, guide edits, retained `docs/workflow.svg`, missing paths, reruns, destination collision, uncommitted-changes skips, and the not-a-git-work-tree stop. Verify with `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_init_project.py'`.

## 2. Placeholder warning

- [x] 2.1 Extend `preflight.sh` to detect the shipped placeholder only within the `AGENTS.md` Project section and report it through the existing warning count without changing the exit status. Verify with a placeholder fixture and a passing batch.
- [x] 2.2 Extend `test_preflight.py` to cover the placeholder, edited section, missing file or section, and matching text outside the Project section. Verify the existing test suite still passes with its stub-only `PATH`.

## 3. README and changelog

- [x] 3.1 Update only "Start a new project" to name the init command, then edit "Make it yours" to remove rows handled by init and retain the remaining manual project edits. Verify the command and remaining steps match the design and the initializer's output.
- [x] 3.2 Add one line under Unreleased / Added in `CHANGELOG.md`. Verify the diff contains one changelog line.

## 4. Repository checks

- [x] 4.1 Run `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck`. Verify it exits 0.
- [x] 4.2 Run `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile`. Verify it exits 0.
- [x] 4.3 Run `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check`. Verify it exits 0.
- [x] 4.4 Run `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'`. Verify all discovered tests pass and record the count.
- [x] 4.5 Run `npx --yes @fission-ai/openspec validate --all --strict`. Verify it exits 0.

## Workflow follow-up

- Archive the change after review, then verify the archived result.
