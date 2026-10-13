# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A preflight check reports missing batch requirements before a worktree is created.

### Changed

- Milestones are optional. The workflow passes `--milestone` to `gh pr create` only for an issue that has one.

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

[Unreleased]: https://github.com/nicoleman0/switchyard/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/nicoleman0/switchyard/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/nicoleman0/switchyard/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/nicoleman0/switchyard/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/nicoleman0/switchyard/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/nicoleman0/switchyard/releases/tag/v0.1.0
