# Tasks

No scenarios: docs-only, no observable behaviour changes (one line per task below instead).

## 1. Wrong sentences

- [x] 1.1 `switchyard/roles/implementer.md`: fix line 1 per design decision 1, and change nothing else in the file.
- [x] 1.2 `README.md`: fix the "Planning and building are separate sessions" bullet and the "at three points" sentence per design decision 1, and change nothing else in the file.
- [x] 1.3 `switchyard/SKILL.md`: fix the "Each phase starts a fresh session" sentence per design decision 1; do not touch Several PRs or Stacked issues (f134 owns them).

## 2. Record and ship

- [x] 2.1 `CHANGELOG.md`: one line under Unreleased, Changed, for #130.
- [x] 2.2 Run `switchyard/hooks/checks.sh` from the worktree root and record each check's result with real numbers.
- [x] 2.3 Run `npx --yes @fission-ai/openspec validate --all --strict` and confirm it exits 0.

## Workflow follow-up

- [x] 2.4 Archive the change under `openspec/changes/archive/<date>-align-docs` in the PR that completes it.
