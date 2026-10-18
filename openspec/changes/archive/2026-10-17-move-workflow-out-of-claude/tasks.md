# Tasks

Three commits, in this order. Each one passes the checks in group 4. Stage explicit paths and run `git status` before each commit: this run's `.claude/brief.md` and `.claude/answers/` must never be committed.

## 1. Commit 1: move the tracked workflow

- [x] 1.1 `git mv .claude/skills/work-issues/<each tracked file>` to the same relative path under `switchyard/`. Verify: `git diff --cached -M --stat` shows only renames (100% similarity) for the moved files.
- [x] 1.2 Add `.claude/skills/work-issues/SKILL.md` as the stub: the current frontmatter unchanged, then a body saying the workflow lives in `switchyard/` and to read `switchyard/SKILL.md` and follow it. Verify: the stub frontmatter is byte-identical to the old `SKILL.md` frontmatter.
- [x] 1.3 Point `.claude/agents/issue-{planner,implementer,reviewer}.md` at `switchyard/roles/<role>.md`. Verify: `git grep -n 'skills/work-issues/roles' .claude/agents` prints nothing.
- [x] 1.4 Change every tracked-file path `.claude/skills/work-issues/...` to `switchyard/...` in `switchyard/` (SKILL.md, roles, runners, brief template, routing.md, scripts and their usage lines), `AGENTS.md`, `CONTRIBUTING.md`, `README.md` (including the layout tree), and `.github/workflows/switchyard.yml` globs and paths. Leave runtime paths (`.claude/brief.md` and the like) for commit 2. Verify: `git grep -n 'skills/work-issues' -- ':!openspec/changes/archive' ':!CHANGELOG.md'` shows only the stub's own folder name where intended.
- [x] 1.5 Updater constants: `VERSION_PATH`, `PATHS_PATH`, `PROJECT_OWNED` move to `switchyard/`. `switchyard/update-paths.txt` lists `.claude/agents`, `.claude/skills/work-issues/SKILL.md`, `switchyard`, `.github/ISSUE_TEMPLATE`, `.github/workflows/switchyard.yml`, `.gitignore`, `AGENTS.md`, `openspec/config.yaml`. Update the constants and fixtures in the four test files to match. Verify: a test compares the shipped paths list with `COVERED`, including the stub path, and the unittest suite passes.
- [x] 1.6 Commit: "Move the workflow from .claude/skills/work-issues/ to switchyard/".

## 2. Commit 2: move runtime files to `.switchyard/`

- [x] 2.1 `state.py`: records live in `.switchyard/state/<issue>.json`, in `issue_path` and `status`. Update `test_state.py`. Verify: `test_state.py` passes and `python3 switchyard/scripts/state.py status` runs in the main checkout path of a temp repo.
- [x] 2.2 Change `.claude/brief.md`, `answers/`, `reviews/`, `turns/`, `sessions/`, `pr-body.md`, `shots/` to `.switchyard/...` in `switchyard/SKILL.md`, the three roles, both runners, `brief-template.md`, `routing.md` (pi row), and `README.md`. Verify: `git grep -nE '\.claude/(brief|answers|reviews|turns|state|sessions|pr-body|shots)' -- ':!openspec/changes/archive' ':!CHANGELOG.md'` prints nothing.
- [x] 2.3 `.gitignore`: replace the `.claude/*` block and its three negations with `.switchyard/` under a one-line comment. `install_gitignore_merge` picks release lines naming `.switchyard`; update its docstring and the gitignore install tests. README's install list says `.gitignore` gains the `.switchyard/` line. Verify: `git check-ignore .switchyard/brief.md` succeeds and the install gitignore tests pass.
- [x] 2.4 Commit: "Keep runtime files in .switchyard/".

## 3. Commit 3: updater migration and compat file

- [x] 3.1 Refuse a target without `switchyard/update-paths.txt` with "<target> predates the switchyard/ layout; run that release's own updater". Test it.
- [x] 3.2 Read `VERSION` from `switchyard/VERSION`, falling back to `.claude/skills/work-issues/VERSION`. Refuse when both exist. `--install` refuses when either exists and names the file. Tests for each.
- [x] 3.3 Legacy base (base tree has no `switchyard/update-paths.txt`): select base entries with the extra legacy root, rename them to `switchyard/`, read locals from legacy paths, run the ordinary merge on new paths, move `routing.md` and project-added tracked files unchanged (`moved`), add the stub, delete legacy files and empty folders after all writes, write `switchyard/VERSION`. Print a first line naming the move. Tests with a legacy-layout base tag and a new-layout target tag: unedited files update; an edited file merges at its new path; a same-line edit conflicts at its new path; edited `routing.md` moves byte for byte; a project-added script moves with its mode; an untracked file stays; the legacy folder holds only the stub afterwards; `switchyard/VERSION` names the target and the legacy `VERSION` is gone; a second run prints "Already at". Add a new-layout to new-layout test where both tags include the compat file: it must not migrate or touch the stub or compat file.
- [x] 3.4 Refuse a legacy base when `switchyard/` already holds files, and when `.claude/state/` holds `*.json` records (list the issues). Both refusals write nothing. Tests for each.
- [x] 3.5 Add `.claude/skills/work-issues/update-paths.txt` with the comment and `../` line from design.md. Add a test that reads it and asserts a non-comment line has a `..` path part and no `#`. Add it to `DELETED_PATHS` in `init-project.py` and extend `test_init_project.py`.
- [x] 3.6 One-time check against the real tag, recorded in the PR's Checks: in a scratch dir, make a project from `git archive v0.6.0` with an edited `routing.md` and an edited role, tag this branch's tip as `v0.7.0` in a local clone, then (a) run the project's own 0.6.0 updater with `--source` the clone: exit 2, the compat message, `git status` clean; (b) run this branch's updater from the clone: exit 0 or 1, edits kept under `switchyard/`, `routing.md` byte for byte, legacy folder holds only the stub.
- [x] 3.7 README "Take a later release": add the one-time step for projects on 0.6.0 or older (clone, run `../switchyard/switchyard/scripts/update-switchyard.py`, fix `.claude/sessions/` in `routing.md`). Keep it short.
- [x] 3.8 CHANGELOG under Unreleased, Changed: the move, the runtime folder, the one-time update step, and the pi `routing.md` row adopters must edit. Verify: the VERSION/CHANGELOG check still passes (VERSION stays 0.6.0).
- [x] 3.9 Commit: "update-switchyard.py: move a 0.6.0 install to switchyard/".

## 4. Checks

- [x] 4.1 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck`
- [x] 4.2 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile`
- [x] 4.3 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check`
- [x] 4.4 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`
- [x] 4.5 The "Check release version" step from `.github/workflows/switchyard.yml`, run locally.
- [x] 4.6 `npx @fission-ai/openspec validate --all --strict`
- [x] 4.7 `git grep -n '\.claude'` and list every remaining hit in the PR as intentional: stub, compat file, agents folder in update-paths and README tree, legacy constants and tests in the updater, CHANGELOG history, archived changes.

## Workflow follow-up

- Archive the change in the PR that completes it.
