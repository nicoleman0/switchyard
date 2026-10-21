# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed

- The updater no longer migrates 0.6.0 and older projects, and refuses a base release from before the `switchyard/` layout. Update those to 0.7.0 first. The `.claude/skills/work-issues/update-paths.txt` guard for old updaters is gone; a project can delete its copy.

## [0.7.0] - 2026-10-21

### Added

- The review lists up to five places a human should read first, and the coordinator puts that list at the top of the PR body.

### Changed

- Moved the provider-neutral workflow to `switchyard/` and runtime files to `.switchyard/`.
- Projects on 0.6.0 or older must run the new updater once from a Switchyard checkout. Update any pi `routing.md` row that uses `.claude/sessions/` to `.switchyard/sessions/`.

### Fixed

- #61: `start-worker.sh` records agents blocked during startup so the coordinator can recover them.
- #62: The Herdr runner ends workers through a command that checks the agent and clears the pane input line.
- #63: Herdr prompts wait until the agent starts working or becomes blocked before returning.

## [0.6.0] - 2026-10-15

### Added

- A preflight check reports missing batch requirements before a worktree is created.
- `teardown-worktree.sh` takes `--abandon`: it prints the uncommitted files and local-only commits it is about to discard, then removes the worktree, branches, and record without a prompt. Ordinary teardown now stops before the down hook when the worktree holds uncommitted changes and says to use `--abandon`.
- Planner, implementer, and reviewer roles run on any provider listed in `routing.md`. pi ships as example rows.
- `init-project.py` moves the workflow guide to `docs/WORKFLOW.md` and deletes Switchyard-only files in a new project, changes nothing when `README.md` is not Switchyard's guide, and `preflight.sh` warns while the `AGENTS.md` Project section still holds the shipped placeholder.
- `update-switchyard.py --install` installs the workflow into a repo that has never had Switchyard. It adds the workflow's files, merges the project's `AGENTS.md` sections, `.gitignore` lines, and `openspec/config.yaml` rules without touching the rest, writes `VERSION`, and prints the `openspec init` step when the repo has no `openspec/` directory.

### Changed

- The coordinator can run on any CLI that reads `AGENTS.md` and can run the skill's scripts. Per-CLI setup lives in `routing.md`.
- Milestones are optional. The workflow passes `--milestone` to `gh pr create` only for an issue that has one.
- Models, effort, and provider flags now live in `.claude/skills/work-issues/routing.md`. The opencode Implementer example uses the CLI's default model; it no longer pins GLM 5.3 Flash or Kimi K3. The updater adds the file when missing and never changes it. Claude role profiles no longer set models. After updating, review an added routing file; for a conflict in `SKILL.md` or a profile, take the release's side and move your values to `routing.md`.
- Workers use any provider named after its CLI command. `start-worker.sh` accepts `--turns`, gives each turns worker a fresh session, and no longer refuses an opencode reviewer or a missing `routing.md`. When the file does not settle a choice, the coordinator chooses and reports it. `preflight.sh` takes provider names, and runner commands come from `routing.md`.
- Updating from 0.5.0 adds Codex and opencode rows without model IDs. Those workers use the CLI's default model until the project pins one. See the provider notes in `routing.md`: use `-m <model>` for Codex and `--model <provider/model>` for opencode.
- The README's sequence diagram for one issue is drawn as pixel-art rail tracks, `docs/workflow.svg`, by `docs/pixelart.py`, in place of the Mermaid diagram.

### Fixed

- `teardown-worktree.sh` now removes the record even when the remote branch delete fails, and a branch GitHub deletes between the check and the push no longer fails the teardown. A remote branch that still exists after a rejected delete prints an error and exits non-zero.
- `check-scope.sh` no longer fails under bash 3.2 when an issue owns no paths. It now reports every changed file outside `openspec/` and exits 1.
- On the headless runner, the Claude coordinator note now runs each worker turn in the background and reads the turn log when the command exits, because Claude Code stops a foreground command after 10 minutes. The updater never changes `routing.md`, so update your project's own Claude note to match.

## [0.5.0] - 2026-10-11

### Added

- A reviewer role. After the implementer commits, a fresh session on another provider checks the diff against the change's scenarios and tasks and writes a verdict to `.claude/reviews/<n>.md`. Each issue now runs one more worker session.
- `start-worker.sh` refuses a reviewer on the implementer's provider. Set `SWITCHYARD_SAME_PROVIDER=1` when only one provider is available.
- `setup-worktree.sh` disables the push URL in each new worktree, so workers cannot push. It turns on git's `extensions.worktreeConfig` in the repo. The coordinator now pushes from the main checkout.
- `scripts/check-scope.sh <issue>` lists files a branch changed outside the owned paths recorded with `state.py set <issue> "owned=..."`.

### Changed

- The coordinator reads the reviewer's verdict, not the diff. Its PR review checklist moved to `roles/reviewer.md`. Fixes go to a fresh implementer session that reads the review file.
- At plan review, the coordinator reads the change files on disk, not the planner's summary.
- The PR body has a Review section.

## [0.4.0] - 2026-10-11

### Changed

- Switchyard's checks moved from `.github/workflows/ci.yml` to `.github/workflows/switchyard.yml`, and the updater no longer touches `ci.yml`. A repo with its own `ci.yml` got a whole-file conflict when a release changed the template's. After you update, delete the Switchyard steps from your `ci.yml` if it still has them.

## [0.3.0] - 2026-10-11

### Added

- `scripts/state.py status` shows the coordinator each issue's phase, worker, and PR. `scripts/start-worker.sh` starts a worker and records its session or agent name.
- `update-switchyard.py` updates project workflows from later releases, with `VERSION` tracking the base release.

### Fixed

- The Herdr runner now names agents `<role>-<issue>` because Herdr rejects names that start with a digit.

## [0.2.0] - 2026-10-11

### Added

- A CI workflow that lints the skill's scripts and validates the OpenSpec files.
- An issue template for the short issue the workflow starts from.
- A contributing guide.
- README badges that link to the workflow's tools.

### Changed

- The README banner is now pixel art.

## [0.1.0] - 2026-10-10

First release.

### Added

- The `work-issues` skill: the coordinator's playbook, the routing table for models, effort, and providers, and the planner and implementer roles.
- Claude agent profiles for the planner and the implementer.
- Two runners: Herdr panes and headless CLI turns on Claude Code, Codex, and opencode.
- Scripts for worktree setup and teardown, before and after screenshots, and merge helpers.
- Hooks for per-issue isolation, so the scripts carry no stack details.
- OpenSpec workflows generated for Claude Code, Codex, and opencode.
- `AGENTS.md` with the workflow and writing rules every agent reads.
- A README that explains the workflow and how to start a project from the template.

[Unreleased]: https://github.com/nicoleman0/switchyard/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/nicoleman0/switchyard/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/nicoleman0/switchyard/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/nicoleman0/switchyard/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/nicoleman0/switchyard/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/nicoleman0/switchyard/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/nicoleman0/switchyard/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/nicoleman0/switchyard/releases/tag/v0.1.0
