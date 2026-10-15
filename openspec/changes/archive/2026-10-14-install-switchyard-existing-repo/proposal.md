# Proposal

## Why

Issue #25 asks for a safe way to install Switchyard into a repository that has never used it. The README currently requires copying files and hand-merging three shared configuration files, and the updater only supports repositories with a prior Switchyard version.

## What Changes

- Add `update-switchyard.py --install` to install the latest Switchyard release into an existing Git repository without a prior `VERSION`.
- Reuse the updater's source clone, `update-paths.txt`, action report, and `VERSION` tracking.
- Merge Switchyard's `AGENTS.md` Workflow and Writing sections, `.gitignore` `.claude` rules, and `openspec/config.yaml` rules without replacing unrelated project content.
- Replace the README's manual existing-repo steps with the install command and update the later-release guidance for repositories without a prior installation.

## Capabilities

### New Capabilities

None. This change is scoped to the template's updater and documentation. The repository keeps `skip_specs: true` because its shipped `openspec/specs/` directory is intentionally empty.

### Modified Capabilities

None.

## Impact

- `.claude/skills/work-issues/scripts/update-switchyard.py`
- `.claude/skills/work-issues/scripts/test_update_switchyard.py`
- `.claude/skills/work-issues/update-paths.txt`
- README sections "Add it to an existing repo" and the refusal guidance in "Take a later release"
- One `CHANGELOG.md` entry
- No new dependencies or shared service changes
