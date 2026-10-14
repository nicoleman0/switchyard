# Design

## Context

See proposal.md for the motivation. The updater currently requires a base release, compares the project's files with that release, and writes the target release to `VERSION`. Installation has no common base. A whole-file merge against an empty base would mark any existing shared file as a conflict.

Checked in scratch repos with OpenSpec 2026-10 (maintainer's answers confirmed the user-facing choices):

- In an empty repo, `npx @fission-ai/openspec init --tools claude,codex,opencode` writes a comments-only `openspec/config.yaml` (just `schema: spec-driven`) and never replaces an existing file.
- The README sequence ran against a local release clone into a repo with its own `AGENTS.md`, `.gitignore`, and CI workflow: 29 files added, `.gitignore` merged, `AGENTS.md` left conflict markers scoped to the Workflow section (local title, Style, and appended Writing preserved), a minimal `openspec/config.yaml` written, `VERSION` = 0.5.0, exit 1. The default-source run (network, GitHub) installed the newest release into a bare repo: 31 files added, exit 0.
- Running `npx @fission-ai/openspec init --tools claude,codex,opencode` after install left `openspec/config.yaml` byte-for-byte unchanged and created `openspec/changes/` and `openspec/specs/`, so install writes the config first and prints init as the next step when the repo had no `openspec/` directory.
- `git merge-file --diff3` with an empty base still resolves cleanly when one side is empty; two non-empty sides conflict in whole-region markers. Clean section merges need no diff3; install merges use markers that name the sides (`yours`, `switchyard <target>`).

## Goals / Non-Goals

**Goals:**

- Reuse the updater's source selection, target release selection, path list, report format, and version file.
- Preserve files and configuration owned by the adopting project.
- Keep installation and later updates explicit modes of the existing command.

**Non-Goals:**

- Change how projects update after installation, including the project-owned `routing.md` rule.
- Initialize provider or editor tools beyond the existing workflow installation.
- Add dependencies or alter unrelated README sections owned by issue #26.

## Decisions

### Install mode and release selection

Add `--install` to the existing updater. It selects the newest valid release unless `--to` names another release, uses that release's `update-paths.txt`, and writes its version to `VERSION`. It does not require `--from`; reject `--from` with `--install` so the base-less mode stays clear. A repository that already has a `VERSION` already has the workflow, so `--install` refuses there with a pointer to the plain updater; uninstallation is out of scope. Keep the current clean tracked-worktree check. Existing ordinary files are added when absent; where a project already has a differing updater-managed file, run the existing git merge-file path against an empty base and write the result: report `merged` when it resolves and `conflict` when it leaves markers. No release version is written beside a conflicting file; the markers carry both sides. `routing.md` remains added only when absent and is never replaced.

Alternative considered: a separate install script. Rejected because it would duplicate source, path-list, version, and report behavior already owned by this updater.

### Merge the three shared files by owned content

- `AGENTS.md`: identify the top-level `## Workflow` and `## Writing` sections by heading boundaries. Merge only those section bodies against an empty section base, retaining unrelated headings. If either section is absent locally, add the release section at the end (Workflow before Writing). If a local section differs from the release section, run the empty-base merge and keep the result inside that section without replacing the rest of the file: identical bodies stay untouched, one empty body takes the release body as a clean merge, and differing bodies keep markers naming the sides. If the file is absent, write the release's whole `AGENTS.md`, Project placeholder included, so the project still has a Project section to fill; a later preflight warning points at it. When the file exists, do not add the Project placeholder; print a next step saying to list the project's checks in `AGENTS.md`.
- `.gitignore`: preserve existing lines and add only the release's `.claude` patterns (lines mentioning `.claude` that are not comments), skipping lines the file already has. If absent, create a file containing those patterns only.
- `openspec/config.yaml`: update only the top-level `rules` mapping and preserve `context` and other keys. Merge the release's rule entries into their matching rule lists, avoiding exact duplicate entries, and add release rule keys the file lacks at the end of its `rules` block. If `rules` is absent, append it; if the file is absent, create a minimal config with `schema: spec-driven` and the release's rules, so `openspec init` afterwards keeps the file untouched and the rules in place.

These scoped strategies avoid merging unrelated project content. Malformed or unsupported structures (a `rules:` that is not a top-level mapping, two `## Workflow` sections, a rules entry whose value is not a list) fail before any write with a clear error naming the file and the problem: that is the batch-cannot-run case for this command. Do not add a YAML dependency; use a narrow, validated text transformation for the known top-level sections.

Alternative considered: run a whole-file merge with an empty base. Rejected because it treats all existing content as a conflict and obscures which content Switchyard owns.

### OpenSpec initialization guidance

Install never runs `npx @fission-ai/openspec init`; that keeps a networked tool setup out of the updater. When the repo had no `openspec/` directory before install, print the init command as the next step after writing `openspec/config.yaml`; Verified above that init keeps that file. When the repo already has `openspec/`, print nothing about init.

### README and reporting

Replace the copy-and-merge recipe in "Add it to an existing repo" with the sequence the maintainer chose: clone Switchyard beside the repo, then run its updater from the repo's root with `--install`. The default `--source` already fetches the release, so no `--source` is needed there; tests and any manual verification use a local clone with `--source`. Update the sentence in the README intro that still describes the copy-and-hand-merge path, and update only the later-release passage that covers repositories without `VERSION` or the updater: it keeps `--from` for projects made from 0.1.0 or 0.2.0, which already had the old workflow files, and points repositories that never had the workflow at install. Keep the existing action labels and summary counts so users can inspect additions, merges, conflicts, and kept project files.

## Risks / Trade-offs

- A heading or YAML structure that differs from the expected template may be ambiguous → validate the structure and stop before writing rather than guessing.
- Section-level merges can still produce conflict markers within an owned section → report the conflict and preserve it for manual review.
- Printing an OpenSpec init step means installation and tool setup remain two actions → make the next step explicit in output and README.

## Migration Plan

No migration is required. Install writes the selected release to `VERSION`; later runs use the existing updater path. Users can review the reported diff and restore changes using the existing README recovery guidance.
