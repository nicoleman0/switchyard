# Proposal

Delivers issue #28, "Nothing checks the requirements before a batch starts".

## Why

The workflow needs `git`, Python 3, Node.js, a signed-in `gh`, and at least one worker CLI. Nothing verifies them up front. A missing piece shows up mid-run, after a worktree exists and a planner has spent usage.

## What Changes

- Add `scripts/preflight.sh`. It checks each item in the README's Requirements section, prints one line per item, and says how to fix each one that is missing.
- Required items fail the run with exit status 1: `git`, Python 3, Node.js with `npx`, a signed-in `gh`, and a worker CLI.
- Optional items print a warning and do not change the exit status: Herdr, Playwright, `sips` or ImageMagick, a second provider for the reviewer, and the Codex coordinator profile when `codex` is installed.
- Every check runs on every run, so one run lists everything that is missing.
- The coordinator runs it in "Before starting", before the first worktree.
- The README's Requirements section names the command.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`. Switchyard is a template, and `openspec/specs/` ships empty to every project made from it, so the workflow's own rules live in the skill and the README.

## Impact

- `.claude/skills/work-issues/scripts/preflight.sh`: new.
- `.claude/skills/work-issues/scripts/test_preflight.py`: new. CI already runs `test_*.py` and shellcheck on every `.sh` in the skill folder.
- `.claude/skills/work-issues/SKILL.md`: one paragraph at the top of "Before starting". No other section changes.
- `README.md`: one line under Requirements. No other section changes.
- `CHANGELOG.md`: one line under Unreleased, if the coordinator allows it. The file is shared with the other branches in flight.
- Projects that update from a release get the script through the existing `.claude/skills/work-issues` update path.
