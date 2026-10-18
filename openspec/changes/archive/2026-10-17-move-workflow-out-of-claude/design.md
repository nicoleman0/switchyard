# Design

## Context

See proposal.md for why. Constraints that shape the approach:

- Every release from 0.1.0 to 0.6.0 puts the workflow under `.claude/skills/work-issues/`. The tree at `HEAD` equals `v0.6.0`.
- Updaters from 0.3.0 to 0.6.0 run the same code path. They read `update-paths.txt` from the target release at the fixed path `.claude/skills/work-issues/update-paths.txt`, and read and write `VERSION` at `.claude/skills/work-issues/VERSION`. Adopters run their own copy, so this PR cannot change what the old updater does. It can only change what the next release's tree looks like.
- Projects on 0.1.0 and 0.2.0 have no updater. README already tells them to run the updater from a Switchyard checkout with `--from`.
- `routing.md` is project-owned. The updater never changes it, so an adopter's pi row keeps `--session .claude/sessions/...`.
- Prototype (throwaway, against the real `v0.6.0` updater and a local tag with the moved layout): with no file at the old `update-paths.txt` path, the 0.6.0 updater exits 2 with "v0.7.0 has no .claude/skills/work-issues/update-paths.txt; update from a release that includes the update path" and writes nothing. With a compat file whose line starts with `../`, it exits 2 with "unsafe path in .claude/skills/work-issues/update-paths.txt: <the line>" and writes nothing.

## Goals / Non-Goals

**Goals:**

- Nothing provider-neutral is left under `.claude/`.
- An adopter on 0.6.0 or older reaches the new layout with one documented command, keeping local edits, `routing.md`, and files they added.
- An adopter who runs their old updater gets a clear instruction and no partial update.

**Non-Goals:**

- Renaming files inside the workflow, such as `SKILL.md`. The move keeps every name.
- Skill stubs for Codex or opencode. They read `AGENTS.md`, which names `switchyard/SKILL.md`.
- Rewriting an adopter's `routing.md`.
- Version bump and release.

## Decisions

### Runtime files go to `.switchyard/`

All runtime files move to one git-ignored folder at the repo root: `.switchyard/brief.md`, `answers/`, `reviews/`, `turns/`, `state/`, `sessions/`, `pr-body.md`, `shots/`. `.gitignore` gets one line, `.switchyard/`.

- It names the tool, not a provider.
- It sits outside the tracked `switchyard/` tree. The updater, its migration, `init-project.py`, and the CI globs only look at tracked files under `switchyard/`, so none of them can meet a runtime file.
- A leading dot marks it as tool state, like `.git/`.

Alternatives: `switchyard/run/` keeps one folder but mixes tracked and ignored files, so the migration's "move every tracked file" rule and any future `rm -r switchyard/` need an exception. `.work/` is generic and may clash with a project's own folder.

Trade-off: `switchyard/` and `.switchyard/` differ by one dot. The README layout tree names both with a one-line purpose each.

### `.claude/*` ignore lines are dropped

The `.claude/*` block with its three negations goes. Switchyard writes nothing under `.claude/` after this change, and Claude Code keeps its own `settings.local.json` out of git: "The first time Claude Code writes the file in a git repository that doesn't already ignore it, it adds `**/.claude/settings.local.json` to your global git excludes file" (code.claude.com/docs/en/settings). `install_gitignore_merge` picks release lines that name `.switchyard` instead of `.claude`.

Effect on adopters: a pi row that still names `.claude/sessions/` writes session files git no longer ignores. The CHANGELOG tells them to change the row to `.switchyard/sessions/`.

### `.claude/` keeps a stub skill

`.claude/skills/work-issues/SKILL.md` keeps the current frontmatter (`name`, `description`) so Claude Code still lists the skill. The body says the workflow lives in `switchyard/` and to read `switchyard/SKILL.md` and follow it. The three `.claude/agents/*.md` wrappers point at `switchyard/roles/<role>.md`.

### The updater works on the new layout

- `VERSION_PATH = "switchyard/VERSION"`, `PATHS_PATH = "switchyard/update-paths.txt"`, `PROJECT_OWNED = {"switchyard/routing.md"}`.
- `switchyard/update-paths.txt` lists `.claude/agents`, `.claude/skills/work-issues/SKILL.md`, `switchyard`, `.github/ISSUE_TEMPLATE`, `.github/workflows/switchyard.yml`, `.gitignore`, `AGENTS.md`, `openspec/config.yaml`. It names the stub so it reaches projects on each update.
- A target release without `switchyard/update-paths.txt` predates the move. The updater refuses: "<target> predates the switchyard/ layout; run that release's own updater".

### The updater migrates a legacy install

A base release is legacy when its tree has no `switchyard/update-paths.txt`. This identifies pre-move releases, including 0.1.0 to 0.6.0. New-layout releases keep a compat `.claude/skills/work-issues/update-paths.txt`, so the presence of files under the old folder does not identify a legacy base.

For a legacy base:

1. Read `VERSION` from `switchyard/VERSION`, falling back to `.claude/skills/work-issues/VERSION`.
2. Select base entries with the target's roots plus `.claude/skills/work-issues`, then rename every `.claude/skills/work-issues/X` to `switchyard/X`. The target's paths list does not name the legacy folder, so without the extra root the base would miss those files.
3. For each renamed path, read the local file from its legacy location. The ordinary three-way merge then runs on new paths: unedited files update, edited files merge, conflicts get markers at the new path. A file deleted upstream but edited locally is kept at its new path.
4. `routing.md` moves unchanged to `switchyard/routing.md`, reported `moved`.
5. Tracked files under the legacy folder that no base entry names were added by the project. They move to the same relative path under `switchyard/`, reported `moved`. Untracked files stay where they are.
6. The stub `.claude/skills/work-issues/SKILL.md` is reported `added`: the local `SKILL.md` was consumed by step 3.
7. After all writes, delete every legacy file that was read or moved, the legacy `VERSION`, and directories left empty. Write `switchyard/VERSION`.

The first output line says the workflow is moving from `.claude/skills/work-issues/` to `switchyard/`. Exit codes stay as they are: 1 on `conflict` or `kept`.

Refusals, all before any write:

- Both `switchyard/VERSION` and `.claude/skills/work-issues/VERSION` exist.
- The base is legacy and `switchyard/` already holds files: the project looks half-migrated.
- `.claude/state/` holds `*.json` issue records. An in-flight worktree runs the old scripts and would keep writing there. The message lists the issues and says to finish or tear them down first.
- `--install` when either `VERSION` file exists (the existing refusal, naming the file it found).

Alternative: physically move the folder first, then run a normal update. Rejected because a refusal or merge error halfway would leave a moved tree with no record of the base.

### A compat file stops old updaters

`.claude/skills/work-issues/update-paths.txt` stays in the template with a comment and one line:

```
# Read by Switchyard 0.6.0 and older updaters. Keep it.
../ Switchyard moved the workflow to switchyard/. Update once with the new updater from a Switchyard checkout. See "Take a later release" in its README.
```

The line must hold a `..` path part and no `#`. Old updaters refuse with that text before writing anything, including `VERSION`. A permanent test pins that shape. `init-project.py` deletes the file in a new project, where no old updater will ever read it.

Alternatives:

- No compat file. Also safe, but the old message ("update from a release that includes the update path") points the user the wrong way.
- A compat paths list that lets the old updater write part of the new layout. Rejected: the old updater then writes the target version into the legacy `VERSION`, and the real migration loses its base.

### Three commits

1. Pure move: `git mv` the tracked workflow to `switchyard/`, add the stub, update every tracked-file reference, updater constants, `update-paths.txt`, and the CI globs. Runtime paths unchanged.
2. Runtime folder: every `.claude/<runtime>` reference becomes `.switchyard/<runtime>`, and `.gitignore` changes.
3. Updater migration, compat file, `init-project.py`, README upgrade steps, CHANGELOG.

Each commit passes every check on its own.

## Risks / Trade-offs

- [This run's own `.claude/brief.md` and `.claude/answers/` become untracked-visible after commit 2] → The implementer stages explicit paths and checks `git status` before each commit. Neither file is committed.
- [Adopters run their old updater and stop] → The compat message names the fix. CHANGELOG and README give the command.
- [A merge in the migration conflicts in a heavily edited `SKILL.md`] → Markers land in `switchyard/SKILL.md`, the same handling any update gets today.
- [The two folder names look alike] → README layout tree explains both.

## Migration Plan

For an adopter on 0.6.0 or older, from a clean checkout on a new branch, with no issues in flight:

```sh
git clone https://github.com/nicoleman0/switchyard.git ../switchyard
python3 ../switchyard/switchyard/scripts/update-switchyard.py
```

Then review the diff, resolve markers, and change any `.claude/sessions/` in `switchyard/routing.md` to `.switchyard/sessions/`. Undo before committing with `git restore .` and `rm -r switchyard/`: every legacy file is tracked, and every file under `switchyard/` is new. Later releases update with `python3 switchyard/scripts/update-switchyard.py`.
