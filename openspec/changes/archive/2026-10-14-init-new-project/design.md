# Design

## Context

See `proposal.md` for the motivation. The project uses Python for the updater and bash for preflight. `preflight.sh` runs under macOS bash 3.2 with `set -u`; its tests run with a stub-only `PATH`. The template has no specs, and the current README's two target sections list the manual setup steps.

## Goals / Non-Goals

**Goals:**
- Make initialization safe to rerun and clear about each file operation.
- Keep preflight's existing exit status tied to missing required tools.
- Keep the command independent of providers and additional packages.

**Non-Goals:**
- Commit changes or alter project-owned workflow configuration.
- Change the updater, which owns a separate issue.
- Rewrite other README sections or change the placeholder in this repository's `AGENTS.md`.

## Decisions

**Use a Python entry point named `init-project.py`.** Run it from the project root as `python3 .claude/skills/work-issues/scripts/init-project.py`. Python's standard library handles path checks, file moves, and guide edits without macOS-specific `sed` behavior. A bash implementation would need more shell-specific path and text handling.

**Protect uncommitted work, then apply the explicit cleanup list.** Move `README.md` to `docs/WORKFLOW.md`, creating `docs/` if needed. On that moved guide, remove the leading banner image line for `docs/switchyard.svg`, change the workflow chart reference to `workflow.svg`, and remove the `## License` section, because init also deletes `LICENSE`. Keep `docs/workflow.svg`. Delete `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `docs/switchyard.svg`, `docs/social-preview.png`, and `docs/pixelart.py` when present. Because git history keeps committed copies, init protects only what git cannot restore: first confirm the directory is inside a git work tree and stop before any change if it is not, then for each listed path run `git status --porcelain -- <path>` before any change and skip any path with uncommitted changes, reporting it as `skipped (uncommitted changes)`.

**Skip absent paths and destination collisions.** Print a status for every move or deletion. If `README.md` is absent, report it as skipped. If `docs/WORKFLOW.md` already exists, leave both files intact and report that the move was skipped. A second run therefore leaves the moved guide untouched and reports the already-absent template paths. Finish by telling the project to add its own `README.md` and `LICENSE` and fill in the Project section of `AGENTS.md`. Never commit.

**Warn on the exact Project placeholder.** In `preflight.sh`, inspect only the text under `## Project` up to the next level-two heading. If it contains the shipped placeholder sentence, call the existing warning function with a direction to fill in the section. A missing `AGENTS.md`, missing Project section, or placeholder sentence elsewhere does not trigger this warning. The warning increments the warning count and does not change the script's exit status. Use shell builtins so the stub-only test `PATH` remains sufficient.

**Test from temporary project roots.** Extend `test_preflight.py` so each test can provide a temporary `AGENTS.md` and run preflight with that directory as `cwd`. Cover placeholder, edited, absent, and out-of-section text; assert the placeholder warning leaves a passing batch at exit 0. Test the initializer against a temporary git repository with all listed files, verify the guide move and path changes, verify the retained workflow chart and deleted files, then rerun it and verify clean skip messages. Also test an existing destination so it is not overwritten, a listed path with uncommitted changes so it is skipped, a directory outside a git work tree so init stops before any change, and that the moved guide has no link to a deleted file.

## Risks / Trade-offs

- Init deletes named files even when locally edited. → Git history keeps committed copies; init refuses to run outside a git work tree and skips any listed path with uncommitted changes, printing each one. The brief documents that it does not commit; the cleanup list is explicit in the plan and README.
- A preflight warning can be missed among other optional warnings. → Name `AGENTS.md` and the Project section directly and include it in the warning count.
- The template's own preflight run will warn because its `AGENTS.md` still has the shipped placeholder. → This is expected; do not edit this repository's `AGENTS.md`.

## Migration Plan

No migration is needed. A new project runs the initializer after creating its repository, before relying on the listed template files. The command does not commit its changes.
