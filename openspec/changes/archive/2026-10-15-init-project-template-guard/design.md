# Design

## Context

`init-project.py` runs `verify_work_tree`, then `changed_paths`, then moves `README.md` and deletes `DELETED_PATHS`. Nothing checks what those files contain. The updater does not ship or touch `README.md`, so an existing project's README is its own. Switchyard's `README.md` starts with `# Switchyard: an agent coordination framework`, and `edit_guide` keeps that line when it moves the guide to `docs/WORKFLOW.md`.

## Goals / Non-Goals

**Goals:**
- Refuse, with no file changed, anywhere the guide is not Switchyard's.
- Keep a rerun after a successful init working.

**Non-Goals:**
- Checking each deleted file's content. The guide's heading decides for the whole run.
- Stopping the updater or `--install` from shipping `init-project.py`.

## Decisions

### D1. Marker: the first line starts with `# Switchyard`

Add `TEMPLATE_HEADING = "# Switchyard"`. A file carries the marker when it is a regular file and its first line, decoded as UTF-8 with `errors="replace"` and a leading BOM stripped, starts with that string. A prefix match lets a reworded tagline pass. Undecodable bytes count as no marker rather than a crash, since such a file is not Switchyard's guide.

Alternatives: the banner image or `docs/switchyard.svg` (ruled out by the maintainer); scanning past leading blank lines (no Switchyard version starts that way, and a looser match lets more foreign files pass).

### D2. Which file decides

- `README.md` exists: it must carry the marker, whether or not `docs/WORKFLOW.md` exists.
- `README.md` absent: `docs/WORKFLOW.md` must exist and carry the marker.
- Anything else: stop.

So `README.md` that is Switchyard's beside a project's own `docs/WORKFLOW.md` still passes, and the current "destination is not overwritten" skip is unchanged. A repo with no README and no Switchyard guide stops, so its `LICENSE` stays.

### D3. Read the working tree, not `HEAD`

The check reads the file on disk, the same file init would move. A fresh copy whose `README.md` was replaced but not committed now stops instead of skipping `README.md` and deleting the rest. The message says how to proceed. Reading `git show HEAD:README.md` would keep today's skip in that case, but adds a git call and judges a file init does not touch. See Question 1.

`test_an_uncommitted_guide_is_not_moved` writes `my notes\n` to `README.md`. Under D3 that run stops. The test's edit becomes `# Switchyard: an agent coordination framework\n\nmy notes\n`, so it still covers the uncommitted skip.

### D4. Order

`main` runs `verify_work_tree`, then the new `verify_template(root)`, then `changed_paths`. The non-git message stays first and unchanged; the template check still runs before any file changes.

### D5. Messages

Both go through `stop()`, which prefixes `Stopping. ` and exits 1.

- README present: `README.md does not start with Switchyard's heading ("# Switchyard"), so this is not a fresh copy of the template. Init changed nothing. Run it only in a new project made from Switchyard.`
- README absent: `Neither README.md nor docs/WORKFLOW.md starts with Switchyard's heading ("# Switchyard"), so this is not a fresh copy of the template. Init changed nothing. Run it only in a new project made from Switchyard.`

Tests assert on the path name and `not a fresh copy`, not the full sentence.

### D6. Docstring

The module docstring adds one sentence: init stops before any change unless the guide starts with Switchyard's heading.

## Risks / Trade-offs

- [A project's own README happens to start with `# Switchyard`] → Init still runs there. Accepted: the maintainer chose the heading as the marker, and every deletion stays in git history.
- [An uncommitted README in a fresh copy now stops the whole run] → The message names the file; committing or restoring it lets init run.

## Open Questions

- README "Start a new project" says init "refuses to run outside a git work tree". That stays true. Whether to add the new refusal is Question 2 for the coordinator; it does not change the tasks except for one optional line.
