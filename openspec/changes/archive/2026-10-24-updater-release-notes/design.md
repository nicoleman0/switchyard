# Design

## Context

See proposal.md for why. The updater clones the release source into a bare repo, so the target's `CHANGELOG.md` is one `git show <target>:CHANGELOG.md` away. With #91, the npm package's source is a git bundle of synthetic commits, one per release from 0.7.0, holding only the files under the release path lists. Those commits have no `CHANGELOG.md` yet.

The CI "Check release version" step and #91's `build.mjs` both parse release headings with `^## \[(\d+\.\d+\.\d+)\] - `. This change reuses that pattern.

## Goals / Non-Goals

**Goals:**

- Show the behaviour changes a user takes on, in the terminal where they run the update.
- Keep the npm path offline.

**Non-Goals:**

- Notes for `--install`. A first install has no base to compare against.
- Notes from the project's installed updater for releases before this one. An old updater prints what it always printed.
- The npm `update` command (#91), the newer-release check (#94), undo commands (#95).

## Decisions

### Which sections

A section starts at a heading matching `^## \[(\d+\.\d+\.\d+)\] - `. It ends at the next `## ` line, or at the first link reference definition (`^\[[^\]]+\]: `), or at end of file. The link definitions at the bottom of the file never reach the output.

The updater prints each section whose version is greater than the base and less than or equal to the target, in file order (newest first, as the changelog reads). `## [Unreleased]` is skipped. Each section is printed verbatim, with trailing blank lines trimmed and one blank line between sections.

The target's `CHANGELOG.md` is the only source. It holds every older section, and it is the text that matches the files being written.

### Output

The notes go after the totals and the `Next:` lines, and before `Dry run: nothing was written.`:

```
updated: switchyard/SKILL.md
updated: 4
merged: 1

Release notes, 0.7.2 to 0.8.0:

## [0.8.0] - 2026-10-24

### Added

- #74: ...
Dry run: nothing was written.
```

A blank line comes before the `Release notes` header. Everything goes to stdout, like the rest of the report. The #92 test that a dry run's stdout equals a real run's stdout plus the final line still holds.

### Read before writing

The updater reads and parses the target's changelog before the write loop, next to the other reads from the bare clone. A failure there is caught and turned into the unavailable line. It is never a `Refusal`, so it cannot exit 2.

### When notes are unavailable

One line, then the report carries on:

`Release notes unavailable: <reason>`

Reasons:

- the target has no `CHANGELOG.md` (`v0.9.0 has no CHANGELOG.md`)
- the file is not UTF-8
- a `## ` line is neither `## [Unreleased]` nor a release heading (`CHANGELOG.md in v0.9.0 has an unknown heading: ## Foo`)
- the target's own section is missing (`CHANGELOG.md in v0.9.0 has no 0.9.0 section`)

A release between base and target with no section of its own is not an error. The updater prints the sections it finds.

The exit code stays what the file report sets: 0, or 1 for `conflict` or `kept`.

### The npm bundle

`build.mjs` adds `CHANGELOG.md` to every bundled commit: from `v<release>:CHANGELOG.md` for older releases and from the working tree for the packed one. The build fails if a release has no `CHANGELOG.md` or its changelog has no matching `## [X.Y.Z] - ` heading for that release. Every tag from v0.7.0 on has both.

The existing check that a release has files under its path list must still count only those files. Adding `CHANGELOG.md` must not make an empty path list pass.

The updater still reads `update-paths.txt` and ignores every other path, so `CHANGELOG.md` never reaches a project. Tests built with `git archive` from the bundle will now find `CHANGELOG.md` in the scratch project; that file is untracked by the updater and changes nothing.

## Risks / Trade-offs

- [Long notes push the file report off screen] → The totals still print above the notes, and `git status` shows the files. A jump across many releases is rare because the bundle starts at 0.7.0.
- [A changelog edited by hand breaks the heading format] → The updater prints the unavailable line instead of failing, and CI's release-version check uses the same pattern.
- [Projects on an old installed updater see no notes] → Accepted. The npm path runs the package's own updater, which has this change.
