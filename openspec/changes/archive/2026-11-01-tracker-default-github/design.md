# Design

## Context

- `update-switchyard.py` adds a missing project-owned file from the release tree. For `tracker.md` it swaps the `Tracker:` line only when `--tracker` was passed (`replace_tracker_line`). The update path adds a missing `tracker.md` from the release with no swap.
- No release tag has `tracker.md` yet (it arrived after 0.10.0). The npm package bundles `HEAD` for its own version, so the next release carries whatever this repo has committed.
- `init-project.py` deletes and moves template files and prints one line per path. It does not touch `switchyard/`.
- `tracker.py` reads `Path(__file__).parents[1] / "tracker.md"`. `TrackerTest` and its subclasses `GitHubListTest` and `GitHubPhaseAndCommentTest` run the real script in place, so they read the repo's own file. With it set to `linear`, 19 tests fail (checked in this worktree, then restored).

## Goals / Non-Goals

**Goals:**
- The repo's own `Tracker:` value never reaches a new install, an update, a template project, or a test.

**Non-Goals:**
- Changing this repo's `tracker.md`. That is the `use-linear-tracker` branch.
- Copying or stripping a `| Phase | Status |` table. Only the `Tracker:` line is reset.
- Fixing `routing.md` dependencies (none found; see below).

## Decisions

- **Default in code, not in argparse.** Keep `--tracker` defaulting to `None` and use `args.tracker or "github"` where `tracker.md` is added. The "release has no tracker.md" refusal and the "Keeping ..." message stay tied to an explicit flag. A `default="github"` would refuse every install of 0.10.0 or older, which have no `tracker.md`, and would print "Keeping" for installs that asked for nothing.
- **Updates write github when they add the file.** The update branch that adds a missing project-owned file passes `tracker.md` through `replace_tracker_line(content, "github")`. Every project that predates `tracker.md` used GitHub, so this is its real tracker. An existing file is still never touched.
- **Init imports the line format from `tracker.py`.** `init-project.py` runs from `switchyard/scripts/`, so `from tracker import TRACKER_LINE` works and keeps one reader's definition of the line. Alternative: a third local regex. `update-switchyard.py` keeps its own because it must not depend on the local `tracker.py`, which may be from another release.
- **Init rewrites only the `Tracker:` line.** It uses the same skip rules as the other paths (absent, uncommitted changes), so a committed copy stays in history. It prints `reset`, `kept`, or `skipped`, padded like the other lines.
- **Tests copy the script.** `TrackerTest.setUp` copies `tracker.py` to `<tmp>/switchyard/scripts/` and writes `<tmp>/switchyard/tracker.md` with `Tracker: github`; `run_tool` runs the copy. `test_preflight.py` already does this. No environment variable or new flag, so nothing user-facing is added.

## Other dependencies on this repo's project-owned files

- `test_state.py`, `test_pre_review.py`, `test_merge_queue.py` copy the whole `switchyard/` folder, including `tracker.md` and `routing.md`. `test_state.py` replaces `tracker.py` with a stub and overwrites `routing.md` in `setUp`; its one real-`tracker.py` test writes its own `tracker.md`. `pre-review.sh` and `merge-queue.py` read neither file. No fix needed.
- `test_preflight.py` stubs `tracker.py` through a fake `python3`, and its real-tracker test writes its own `tracker.md`. No fix needed.
- `test_update_switchyard.py` builds synthetic releases. `test_shipped_update_paths_names_the_claude_stub` reads the repo's `update-paths.txt`, which is not project-owned.
- `create-switchyard/test/install.test.mjs` installs bundled releases and checks no tracker contents. With this change, its newest bundle installs `github` whatever `HEAD` names.
- `routing.md`: no test or script reads the repo's own copy in place.

## Risks / Trade-offs

- [Release `tracker.md` without a `Tracker:` line] → `replace_tracker_line` now runs on every add, so install and update would refuse. That is a broken release, and refusing is the crash-early answer.
- [Init now edits a file under `switchyard/`] → Only the one line, only when committed and clean.
