# Proposal

Delivers GitHub issue #122.

## Why

Traps found during a batch, such as a flag a CLI rejects, a check that needs a service, or a review finding that keeps coming back, live only in that coordinator session. The next batch finds them again and pays for them again.

## What Changes

- New project-owned file `switchyard/lessons.md`. A short header gives the rules: one line per trap with the date found, grouped under an area heading, stale lines deleted, lasting facts moved to `routing.md` or `AGENTS.md`. It ships with a few real traps from this repo's runs as examples.
- `update-switchyard.py`: `switchyard/lessons.md` joins `PROJECT_OWNED`. Both `--install` and a normal update add it when it is missing and never change, merge, or remove it after that, as with `routing.md`.
- `switchyard/SKILL.md`:
  - Per issue, step 2 (Brief): the known traps bullet names the lines from `switchyard/lessons.md` that apply to the issue.
  - A new short section after teardown: add a line for each trap that cost time, delete lines that no longer apply, and commit the file.
- Tests in `test_update_switchyard.py` for the new project-owned file.
- Unchanged: `brief-template.md` (the traps go under the existing coordinator notes), `init-project.py` (a new project keeps the file), the role files.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty in this repo and every change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- New: `switchyard/lessons.md`.
- `switchyard/scripts/update-switchyard.py`: one entry in `PROJECT_OWNED`.
- `switchyard/scripts/test_update_switchyard.py`: new tests.
- `switchyard/SKILL.md`: one bullet in Per issue step 2, one new section.
- Shared, pending the coordinator's answer: `README.md` (the lists of project-owned files), `CHANGELOG.md` (one line under Unreleased).
- #117 adds `switchyard/hooks/checks.sh` to the same `PROJECT_OWNED` line in parallel. The merge conflict keeps both entries.
