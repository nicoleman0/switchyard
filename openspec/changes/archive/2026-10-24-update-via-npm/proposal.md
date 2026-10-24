# Proposal

## Why

Issue #91: install is `npm init switchyard`, but updating needs `python3 switchyard/scripts/update-switchyard.py`, which clones github.com/nicoleman0/switchyard at run time. Users learn two tools, and a sandboxed session needs git access to GitHub to update. The npm package cannot update today: its bundle holds one synthetic release commit, so there is no base release to merge against.

## What Changes

- `create-switchyard update [args...]` updates the repo from releases bundled in the package. It runs the bundled updater with `--source <bundle>` and the forwarded arguments. The base comes from `switchyard/VERSION` and the target is the newest bundled release, so the report and exit codes are the updater's own. `npm init switchyard@latest update` and `npx create-switchyard@latest update` both reach it.
- `update` refuses `--source` and `--install` (and their abbreviations and `=value` forms) with exit 2. Every other argument goes to the updater unchanged, so later updater flags such as #92's `--dry-run` need no bin change.
- Plain `create-switchyard` in a repo that already has `switchyard/VERSION` refuses with exit 2. The message names the installed version and the update command. Today the updater's refusal says "run the updater without --install", which is wrong advice for an npm user.
- The bundle carries every release from v0.7.0 (the oldest base the updater accepts) through the version being packed. Earlier releases come from their git tags; the packed version comes from the working tree, as today. The build fails when a release named in `CHANGELOG.md` has no tag, such as in a shallow clone.
- Docs use the `@latest` form for install and update. Without it, `npm init switchyard` reuses a stale copy from the npx cache (verified on npm 11.19; see design D1). README "Take a later release" leads with the npm command and keeps the in-repo Python updater as the way without Node.
- CI fetches the release tags before it packs the package.
- `update-switchyard.py` does not change.

## Capabilities

### New Capabilities

None. Like #74, this change covers the template's tooling and docs and sets `skip_specs: true`, because the template ships an empty `openspec/specs/` that new projects copy.

### Modified Capabilities

None.

## Impact

- `create-switchyard/bin/create-switchyard.mjs`, `scripts/build.mjs`, `test/install.test.mjs`, `README.md`.
- `.github/workflows/switchyard.yml`: the "Test the npm installer" step fetches `v*` tags first. The step stays guarded to `nicoleman0/switchyard`, so projects that take this file see no change.
- `README.md`, `CONTRIBUTING.md` (release step: publish from a checkout with tags), `CHANGELOG.md`.
- Bundle size: about 65 KB today, about 72 KB with v0.7.0 through v0.8.0 (prototype measurement).
- Out of scope: `--dry-run` (#92), printing the changelog (#93), the newer-release check (#94), undo commands (#95).
