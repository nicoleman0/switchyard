# Proposal

Delivers issue #148, "Issue operations are tied to the GitHub CLI".

## Why

Workers read issues with `gh issue view` and the planner sets the `Change:` line with `gh issue edit`, so a project cannot use another tracker without editing files the updater owns. Linear support (#149 to #151) needs one place that talks to the tracker.

The brief's command is also broken today: when stdout is not a terminal, `gh issue view <n> --comments` prints only the comments. A worker reading an issue with no comments gets empty output.

## What Changes

- New `switchyard/scripts/tracker.py`, the only place that talks to the issue tracker. Two operations, the ones the workflow uses today:
  - `tracker.py view <issue>` prints the issue's title, state, body, and comments.
  - `tracker.py set-change <issue> <change-path>` makes `Change: <change-path>` the first line of the issue body, replacing an existing `Change:` line.
- A GitHub backend that shells out to `gh`. It reads with `gh issue view --json`, which also fixes the empty output above.
- New project-owned `switchyard/tracker.md` that names the tracker. It ships with `github`. The updater adds it when missing and never replaces it, as with `routing.md`.
- `brief-template.md`, `roles/planner.md`, `SKILL.md`, and `AGENTS.md` call `tracker.py` in place of `gh issue view` and `gh issue edit`.
- README and CHANGELOG describe the file and the script.

PRs stay on `gh pr`. Issue keys stay numeric.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`. `openspec/specs/` is empty and no spec lists the files install adds, so there is no requirement to extend; `project-owned-routing` set the same precedent for `routing.md`.

## Impact

- `switchyard/scripts/tracker.py`, `switchyard/scripts/test_tracker.py`: new.
- `switchyard/tracker.md`: new, project-owned.
- `switchyard/scripts/update-switchyard.py`, `test_update_switchyard.py`: `tracker.md` joins `PROJECT_OWNED`.
- `switchyard/brief-template.md`, `switchyard/roles/planner.md`, `switchyard/SKILL.md`, `AGENTS.md`: the commands.
- `README.md`, `CHANGELOG.md`: docs.
- Not touched: `merge-queue.py`, `restack.sh`, every `gh pr` call, `state.py` and `setup-worktree.sh` key checks (#149), the `--tracker` install flag (#149).
