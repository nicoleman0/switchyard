# Design

## Context

- `PROJECT_OWNED = {"switchyard/routing.md"}` in `update-switchyard.py`. In both the install loop and the update loop, a path in that set is added when the project lacks it and otherwise skipped with no report line. Adding a path to the set is the whole updater change.
- `switchyard/` is already in `update-paths.txt`, so a new file under it ships and installs with no other change.
- `init-project.py` deletes Switchyard-only files. A new project should keep its lessons file, so init does not change.
- Worktrees branch from the main checkout's local `HEAD` (`setup-worktree.sh`). Workers never read `lessons.md` themselves. The coordinator copies the lines that apply into each brief.
- `routing.md` provider notes already hold two of the traps the coordinator named: Codex `exec resume` rejects `--approve-for-me`, and opencode interactive mode ignores model settings.

## Goals / Non-Goals

**Goals:**
- One place where a trap survives from one batch to the next.
- The updater adds it once and then leaves it to the project.
- The SKILL tells the coordinator when to read it and when to write it.

**Non-Goals:**
- A script that appends or filters lessons. The coordinator edits a short Markdown file.
- Workers reading the file directly. The brief stays the only handoff.
- Moving existing provider notes out of `routing.md`.

## Decisions

### File name and place: `switchyard/lessons.md`

Next to `routing.md`, the other project-owned file. Covered by the existing `switchyard` entry in `update-paths.txt`.

### Format

```markdown
# Lessons

This file belongs to the project. The updater adds it when missing and never changes it.

Traps that cost time in a batch, so the next batch does not find them again. The coordinator adds a line after each issue and copies the lines that apply into each brief's coordinator notes.

- One line per trap: the date found, the trap, and what to do instead.
- Group lines under an area heading, such as a provider, a check, or a review finding.
- Delete a line when it no longer applies. This file is not a history.
- When a trap becomes a lasting fact about a provider or a check, move it to `routing.md` or `AGENTS.md` and delete it here.

## <Area>

- YYYY-MM-DD: <trap>. <What to do instead>.
```

The last rule keeps each fact in one home. A provider quirk that every run needs belongs in its `routing.md` note, where the runner reads it.

### Seed lines

The coordinator's answer to question 1: ship only traps written down nowhere else, three lines. A Claude Code line dated 2026-10-29 (folder trust is per folder), a zsh coordinator line dated 2026-10-31 (an unquoted `$FLAGS` is not word-split), and a Herdr line dated 2026-10-31 (`herdr agent start` waits for readiness, about 30 s on a failure). The Codex update-prompt trap is dropped: `routing.md` already has it, as do the Codex `--approve-for-me` and opencode model traps.

### SKILL edits, kept small for parallel rebases

- Per issue, step 2: replace the bullet `- any known traps.` with `- any known traps, with the lines from \`switchyard/lessons.md\` that apply to this issue.` One line changed, nothing else in the step.
- A new `## Record lessons` section appended at the end of the file, after Abandon an issue. It covers merged and abandoned issues alike. Appending a section is the edit least likely to conflict with the other Faster delivery issues.
- The coordinator's answer to question 2 fixes the section's last sentence: the coordinator edits `lessons.md` in the main checkout during a batch and commits it on its own small PR at the end of the batch.

### Updater: one entry

`PROJECT_OWNED = {"switchyard/routing.md", "switchyard/lessons.md"}`. No new code path. #117 edits the same line; whoever merges second keeps both entries.

### Tests

Mirror the routing tests for the new path, using the real `PROJECT_OWNED` through the script:
- update: a local edit survives an upstream change, with no report line;
- update: a missing file is added and reported `added`;
- install: an existing file is kept;
- install: a missing file is added.

## Risks / Trade-offs

- [Seed lines go stale in a stranger's project] The header tells them to delete stale lines, and the updater never refreshes them. Accepted: the same holds for `routing.md` examples.
- [The coordinator forgets to commit the file] The new section names when to commit. Until then the file lives only in the main checkout, which is what the batch needs.
- [`PROJECT_OWNED` conflict with #117] One-line conflict, resolved by keeping both entries.
