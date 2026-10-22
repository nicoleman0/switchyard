# Tasks

One commit. Plain, short sentences, no em-dashes, per the Writing section of `AGENTS.md`.

## 1. Roles

- [x] 1.1 `switchyard/roles/planner.md` step 2: replace "Skip OpenSpec only where AGENTS.md says to." with: every issue gets a change; when `AGENTS.md` says no observable behaviour changes, append `skip_specs: true` to the change's `.openspec.yaml` right after `openspec new change` and before any artifact, so the change has no spec delta. Do not copy the list of cases from `AGENTS.md`. Verify: `grep -n "Skip OpenSpec" switchyard/roles/planner.md` prints nothing and `grep -n skip_specs switchyard/roles/planner.md` finds the new text.
- [x] 1.2 `switchyard/roles/implementer.md` step 4: sync the spec delta into `openspec/specs/` only when the change has one; a `skip_specs: true` change goes straight to the archive move. Verify: the step reads right for both kinds of change.
- [x] 1.3 `switchyard/roles/reviewer.md` section 1 (Findings): add that a `skip_specs: true` change has no scenarios, so the reviewer writes one line per task and checks the diff against the design's decisions when the change has a `design.md`. Verify: `grep -n skip_specs switchyard/roles/reviewer.md` finds it in the Findings item.

## 2. Coordinator skill

- [x] 2.1 `switchyard/SKILL.md` Per issue step 4 (Review the plan): the spec delta is absent for a `skip_specs: true` change, and the coordinator checks the flag is set only when no observable behaviour changes. Keep it to one or two short additions in the existing bullets. Verify: `grep -n skip_specs switchyard/SKILL.md` finds it in step 4.

## 3. Docs

- [x] 3.1 `AGENTS.md` Workflow: rewrite the "Skip OpenSpec when..." bullet in place, still one bullet. Keep the list of cases. Say that through the `work-issues` skill such an issue still gets a change with `skip_specs: true` in its `.openspec.yaml`, and that a PR made by hand outside the skill may use an issue and PR with no change. Touch no other bullet. Verify: `git diff AGENTS.md` changes one bullet only.
- [x] 3.2 `README.md`: in "Not everything needs the crew", the no-behaviour-change line says the crew uses a change with `skip_specs: true` and a hand-made PR needs none. In "One issue, start to finish" step 4, note that a `skip_specs: true` change has no spec delta. Verify: `grep -n skip_specs README.md` finds both.
- [x] 3.3 `CHANGELOG.md`: add a line under the existing Unreleased `### Changed`, in the `#NN:` form used there, saying the roles now cover changes with `skip_specs: true`. No version bump. Verify: `switchyard/VERSION` is unchanged.

## 4. Checks

- [x] 4.1 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` passes.
- [x] 4.2 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 4.3 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 4.4 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes. Record the test count.
- [x] 4.5 The release version check from `.github/workflows/switchyard.yml` prints "VERSION matches newest release".
- [x] 4.6 `npx @fission-ai/openspec validate --all --strict` passes.
- [x] 4.7 `git grep -nP '\x{2014}' -- switchyard/roles switchyard/SKILL.md AGENTS.md README.md CHANGELOG.md` prints nothing (no em-dashes).

## Workflow follow-up

- Archive the change to `openspec/changes/archive/<date>-roles-skip-openspec-path` in the same commit. There is no spec delta to sync.
