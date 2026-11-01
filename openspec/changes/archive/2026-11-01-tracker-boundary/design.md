# Design

## Context

Two workflow steps touch issues: the brief tells each worker to run `gh issue view {issue} --comments`, and the planner adds the `Change:` line, which `AGENTS.md` says to do with `gh issue edit`. Everything else on GitHub is PRs (`gh pr`) and stays as it is. Scripts find project files next to themselves: `end-worker.sh` reads `routing.md` from the skill folder.

## Goals / Non-Goals

**Goals:**
- One script owns tracker calls, with a backend layout that #149 extends by adding a class and a table entry.
- GitHub projects see the same issue content and the same issue edits.

**Non-Goals:**
- Comment, status, and list operations (#150, #151).
- Linear keys, the `--tracker` install flag, and preflight checks (#149).

## Decisions

### `tracker.md` format

A short Markdown file with one line the script reads:

```
# Project tracker

This file belongs to the project. The updater adds it when missing and never changes it.

Tracker: github
```

The script takes the one line matching `^Tracker:\s*(\S+)\s*$`. Zero or several such lines exit 1 with the file path and what is wrong. An unknown name exits 1 and lists the known names. Markdown matches `routing.md`, people read it without a parser, and #150 can add a phase-to-status table below the line. Alternatives: TOML needs `tomllib`, which is Python 3.11, and the updater supports 3.10; YAML needs a dependency; JSON is awkward to annotate.

### No `tracker.md`

A repo with no `tracker.md` behaves as `github`, so an older install or a deleted file keeps working. The script prints one line to stderr saying it assumed `github` and that the updater adds the file. stdout stays the issue text. See Question 1 in the plan summary.

### Script layout

One file, `switchyard/scripts/tracker.py`:
- `BACKENDS = {"github": GitHub}`. Each backend class has `view(key) -> str` and `set_change(key, path) -> None`, and validates its own keys. GitHub accepts digits only.
- `load_tracker(path)` parses `tracker.md` and returns a backend instance.
- `main()` parses `view <issue>` and `set-change <issue> <change-path>` with `argparse`.
- `tracker.md` is read from the skill folder, `Path(__file__).resolve().parents[1] / "tracker.md"`, as `end-worker.sh` does for `routing.md`.

A package or one file per backend is premature for two backends.

### GitHub `view`

`gh issue view <n> --json number,title,state,body,comments`, formatted as plain text:

```
#148 Issue operations are tied to the GitHub CLI
State: OPEN

<body>

## Comments

### <author>, <createdAt>

<comment body>
```

With no comments the section reads `No comments.` Reading JSON avoids the non-terminal output of `--comments`, which drops the title and body.

### GitHub `set-change`

Read the body with `gh issue view <n> --json body`. If the first line starts with `Change:`, replace that line. Otherwise prepend `Change: <path>` and a blank line, matching existing issues such as #138. Write with `gh issue edit <n> --body-file -` on stdin, so bodies with quotes or newlines pass unchanged. The path is passed as given; the planner already knows its change path, and plain mode skips this step.

### Errors

A failed `gh` call exits with its status and passes its stderr through. Bad arguments exit 2 (argparse). Config errors exit 1 with the file path.

## Risks / Trade-offs

- [The view output format differs from `gh`'s terminal output] → Workers read it as text; the fields are the same. Tests pin the format.
- [`set-change` reads then writes; a concurrent edit to the body in between is lost] → Same window as a manual `gh issue edit`; the planner is the only writer at that point.
- [The stderr note on a missing `tracker.md` could be missed] → It only matters for a deleted file; the updater re-adds it.

## Migration Plan

The updater adds `tracker.md` with `github` and updates the brief template and roles together, so an updated project calls `tracker.py` with a valid file. A project that edited `brief-template.md` gets a merge or conflict there, as with any upstream change to that file.
