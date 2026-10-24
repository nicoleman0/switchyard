# Proposal

## Why

Issue #94: a project learns about a new Switchyard release only by watching GitHub. Nothing in the workflow compares `switchyard/VERSION` with the newest release.

## What Changes

- New read-only `--check` flag on `switchyard/scripts/update-switchyard.py`. It lists the source's release tags with `git ls-remote`, compares the newest with `switchyard/VERSION`, and reports the result through its exit code and one line of output. It writes nothing, clones nothing, and does not need a clean tree.
- `--check` gives up after 10 seconds, so a hanging network cannot stall preflight.
- `switchyard/scripts/preflight.sh` calls `--check`. When the project is behind, it prints one `warn` line naming both versions and `npm init switchyard@latest update`. When the source cannot be reached, it prints nothing for this check. The check never adds to `missing` and never fails preflight.
- The source URL, tag listing, and version parsing stay in `update-switchyard.py`. The shell script holds none of them.
- README: one sentence in "Take a later release" and one in the requirements list.
- CHANGELOG: one `Added` line under Unreleased.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`, like earlier updater changes, because the template ships an empty `openspec/specs/`. The tests are the acceptance check, and the behaviour is listed in the design.

## Impact

- `switchyard/scripts/update-switchyard.py`: argument parsing, `list_releases`, and a new check path that returns before the clone. The write loop and the update's output, which #95 edits, are untouched.
- `switchyard/scripts/test_update_switchyard.py`: `--check` tests against a local source.
- `switchyard/scripts/preflight.sh`, `switchyard/scripts/test_preflight.py`: the new check and its tests, with a stub `python3`, so no test reaches the network.
- `README.md`, `CHANGELOG.md`.
- No change to `create-switchyard` or `switchyard/SKILL.md`. The skill already says to pass preflight warnings on.
