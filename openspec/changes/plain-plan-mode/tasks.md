# Tasks

## 1. Plan template and workflow text

- [x] 1.1 Add `switchyard/plan-template.md` with the sections in design Decision 3. Verify by reading it against the reviewer's Findings section.
- [x] 1.2 `switchyard/SKILL.md`: description; a `## Plans` section before Before starting (Decisions 1 to 4, short); Per issue step 4: read `.switchyard/plan.md` in plain mode, and check "Scenarios: none" as for `skip_specs`; Open the PR step 1: "when the repo uses OpenSpec". Same description in `.claude/skills/work-issues/SKILL.md`. Verify with `git diff`: no other lines change.
- [x] 1.3 Roles: planner step 2 gets the plain branch (copy the template, no issue line); implementer reads the plan, ticks tasks, skips step 4, and edits the plan in fix rounds; reviewer reads `.switchyard/plan.md` in plain mode. `.claude/agents/*.md` descriptions say "change", not "OpenSpec change". Verify with `git diff`.
- [x] 1.4 `AGENTS.md` Workflow: one bullet that says the OpenSpec bullets apply when the repo has `openspec/`, and what plain mode does. `brief-template.md` Shared files: prefix "When the repo uses OpenSpec,". Verify with `git diff`.

## 2. Scripts

- [x] 2.1 `check-scope.sh`: add `openspec/` to the in-scope prefixes only when the main checkout has `openspec/`. Verify with a test: plain repo reports an `openspec/` file; OpenSpec repo does not.
- [x] 2.2 `pre-review.sh`: in plain mode SKIP "change archived" and "openspec" with the reason, and run a "plan" step (Decision 5). Verify with `test_pre_review.py` cases: plain pass, missing plan, unticked task, OpenSpec mode unchanged.
- [ ] 2.3 `setup-worktree.sh`: a `<issue>b` candidate also copies `.switchyard/plan.md` when present. Verify with a `test_state.py` case. Blocked until #120 merges; the coordinator approved independent tasks first on 2026-11-01.
- [x] 2.4 `.github/workflows/switchyard.yml`: guard the OpenSpec validate step when `openspec/` is absent; reword `.github/ISSUE_TEMPLATE/issue.yml` for both modes, per answer 1. Verify the run block with `bash -n` and execute it in temporary plain and OpenSpec repos. The coordinator verifies the hosted CI run after push.

## 3. Docs

- [x] 3.1 `README.md`: the "Issue, then spec, then code" bullet names the plain-mode workflow. Keep the install paragraph unchanged until #138 updates the installer. One CHANGELOG line under Unreleased, Added.

## 4. Repository checks

- [x] 4.1 `switchyard/hooks/checks.sh` exits 0.
- [x] 4.2 `npx --yes @fission-ai/openspec validate --all --strict` passes.
- [x] 4.3 `npm test --prefix create-switchyard` passes, after `git fetch --no-tags --depth=1 origin '+refs/tags/v*:refs/tags/v*'`.
