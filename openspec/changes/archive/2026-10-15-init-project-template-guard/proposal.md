# Proposal

Delivers issue #55, "init-project.py can delete an existing project's own README, LICENSE, and changelog".

## Why

The updater and `--install` copy `init-project.py` into existing projects. Run there, it moves the project's own `README.md` and deletes its `CHANGELOG.md`, `CONTRIBUTING.md`, and `LICENSE`, because it never checks that those files are Switchyard's.

## What Changes

- Before any file moves or is deleted, init checks that it runs in a fresh copy of the template. The marker is the first line of Switchyard's guide: it starts with `# Switchyard`.
- When `README.md` exists, its first line must carry the marker. When `README.md` is absent, `docs/WORKFLOW.md` must exist and carry it, which keeps a rerun after a successful init working.
- Otherwise init changes nothing, prints why on stderr through the existing `stop()`, and exits 1.
- The git work tree check and the per-path uncommitted-changes skip stay as they are.
- Tests cover each refusal and the reworded-tagline pass. The existing uncommitted-README test keeps the marker in its edited content.
- The existing Unreleased / Added changelog line for `init-project.py` mentions the refusal.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Set `skip_specs: true`: this template ships no specs, and its workflow behavior is documented in its skill and README.

## Impact

- `.claude/skills/work-issues/scripts/init-project.py` and `test_init_project.py`.
- One edited line under Unreleased in `CHANGELOG.md`.
- No README change unless the coordinator asks for one (see design, Open Questions).
- No new dependencies.
