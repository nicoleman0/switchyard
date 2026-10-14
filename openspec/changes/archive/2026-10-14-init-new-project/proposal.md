# Proposal

Delivers issue #26, "A new project starts with ten manual edits".

## Why

New projects must remove or relocate several Switchyard files before they can use the workflow, and the shipped `AGENTS.md` Project section leaves agents without project checks or conventions. A single initializer and a preflight warning make these setup steps clear and repeatable.

## What Changes

- Add an init command that moves the workflow guide to `docs/WORKFLOW.md`, adjusts its image references, and deletes the listed Switchyard-only files.
- Report each moved, deleted, or skipped path. Tell the project to add its own `README.md` and `LICENSE`, and fill in the `AGENTS.md` Project section.
- Extend preflight to warn when that Project section still contains the shipped placeholder. The warning does not block a batch.
- Update the README's new-project instructions and `Make it yours` table to describe the command and the remaining manual edits.
- Add tests and one Unreleased changelog entry.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Set `skip_specs: true`: this template ships no specs, and its workflow behavior is documented in its skill and README.

## Impact

- `.claude/skills/work-issues/scripts/init-project.py` and its tests.
- `.claude/skills/work-issues/scripts/preflight.sh` and `test_preflight.py`.
- The README sections "Start a new project" and "Make it yours".
- One line under Unreleased in `CHANGELOG.md`.
- No new dependencies or provider-specific behavior.
