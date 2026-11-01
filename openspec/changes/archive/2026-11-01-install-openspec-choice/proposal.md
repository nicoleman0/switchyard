# Proposal

Delivers GitHub issue #138.

## Why

Since #82, a project without an `openspec/` folder runs in plain mode. Install still writes `openspec/config.yaml` and prints the `openspec init` step, and the folder it creates switches the project into OpenSpec mode. A project that wants plain plans has to delete the folder by hand. Later updates treat the missing `openspec/config.yaml` as a local deletion and report it as `kept`, which exits 1.

## What Changes

- `update-switchyard.py --install` decides whether the project uses OpenSpec:
  - an existing `openspec/` folder means yes;
  - `--openspec` or `--no-openspec` answers without asking;
  - otherwise it asks on a terminal, default yes;
  - with no terminal and no flag, the answer is yes.
- With no, install skips every `openspec/` path in the release and does not print the `openspec init` step. It prints one line saying plans will be plain.
- An update without `--install` skips `openspec/` paths when the project has no `openspec/` folder.
- `--openspec` and `--no-openspec` choose the install mode. With an existing `openspec/` folder, `--no-openspec` warns and continues in OpenSpec mode. Updates accept and ignore either flag with a mode reminder.
- create-switchyard accepts `--openspec` or `--no-openspec` on install and passes it to the updater. Like `--dry-run`, it also reads npm's `npm_config_openspec` when npm swallowed the flag.
- README install section, create-switchyard README, and one CHANGELOG line.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty in this repo and every change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- `switchyard/scripts/update-switchyard.py` and `test_update_switchyard.py`.
- `create-switchyard/bin/create-switchyard.mjs`, `create-switchyard/test/install.test.mjs`, `create-switchyard/README.md`.
- `README.md` install section; `CHANGELOG.md` Unreleased.
- Not changed: `switchyard/update-paths.txt`, `init-project.py` (template path), `SKILL.md`, roles, the CI workflow. The OpenSpec-generated files (`.claude/skills/openspec-*`, `.claude/commands/opsx`, `.agents/`, `.opencode/`) come from `openspec init`, not from install, so skipping the init step covers them.
