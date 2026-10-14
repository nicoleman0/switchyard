# Tasks

## 1. Add install mode and merge strategies

- [x] 1.1 Add `--install` release selection, validation, `VERSION` writing, and existing action reporting; reject `--from` with `--install` and refuse a repository that already has `VERSION`; verify local-clone integration tests install into a repository without `VERSION` and reject incompatible options without changing files.
- [x] 1.2 Implement scoped merging for `AGENTS.md` (whole release file when absent; Workflow/Writing sections otherwise), `.gitignore`, and `openspec/config.yaml`; verify tests preserve unrelated content, add missing Switchyard content, report conflicts with markers, and refuse malformed structures before any write.
- [x] 1.3 Preserve the project-owned `routing.md` rule in install mode; verify an existing file remains byte-for-byte unchanged and a missing file is added.
- [x] 1.4 Print the OpenSpec init command as the next step only when the repo had no `openspec/` directory, verified in a scratch repo; print the project-checks next step when `AGENTS.md` already existed.

## 2. Document installation

- [x] 2.1 Replace the manual existing-repo recipe with the install command and its OpenSpec next step; verify the README command matches the CLI behavior.
- [x] 2.2 Update only the later-release guidance that refers to the refusal for repositories without `VERSION` or the updater; verify unrelated README sections remain unchanged.
- [x] 2.3 Add one concise entry under `Unreleased` / `Added` in `CHANGELOG.md`; verify it describes installation into an existing repo.

## 3. Repository checks

- [x] 3.1 Run `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck` and verify all tracked shell scripts pass.
- [x] 3.2 Run `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile` and verify all tracked Python files compile.
- [x] 3.3 Run `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check` and verify the tracked JavaScript file passes.
- [x] 3.4 Run `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'` and verify the complete script test suite passes.
- [x] 3.5 Run `npx --yes @fission-ai/openspec validate --all --strict` and verify all OpenSpec changes validate.
