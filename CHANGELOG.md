# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/nicoleman0/switchyard/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/nicoleman0/switchyard/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/nicoleman0/switchyard/releases/tag/v0.1.0
