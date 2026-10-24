# Proposal

## Why

Issue #74: to add Switchyard to an existing repo, you first clone the Switchyard repo beside the project, only to run `update-switchyard.py --install`. People trying a tool expect one command.

## What Changes

- Add an npm package, `create-switchyard`, in a new top-level folder `create-switchyard/`. Running `npx create-switchyard` with no arguments from inside a git repo does what `update-switchyard.py --install` does today. No clone is needed.
- The package bundles one release: the workflow files listed in `switchyard/update-paths.txt`, stored as a git bundle with a `vX.Y.Z` tag, plus a copy of the updater. At run time it calls the bundled updater with `--install --source <bundle>`. It does not reach the network or the Switchyard repo.
- The package version equals `switchyard/VERSION`. The build refuses a mismatch, and the CI release-version check (only on `nicoleman0/switchyard`) checks it too.
- `init-project.py` deletes the `create-switchyard/` folder from new projects made from the template, just as it deletes the other Switchyard-only files.
- README: the "Add it to an existing repo" section uses `npx create-switchyard`, and the Layout and init text list the new folder. CONTRIBUTING gains release steps that include the npm publish, which the maintainer runs. CHANGELOG gets an Unreleased entry.
- `update-switchyard.py` does not change. Later updates keep using the copy installed in the repo.

## Capabilities

### New Capabilities

None. This change covers the template's tooling and docs. Like earlier installer changes, the change sets `skip_specs: true`, because the template deliberately ships an empty `openspec/specs/`.

### Modified Capabilities

None.

## Impact

- New: `create-switchyard/` (package.json, bin script, build script, test, .gitignore).
- `switchyard/scripts/init-project.py` and `test_init_project.py`.
- `.github/workflows/switchyard.yml`: the release-version step also checks the package version, and a new step packs and tests the package. Both run only on `nicoleman0/switchyard`.
- `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`.
- Requirements stay as they are: git, Python 3, Node.js. No runtime dependencies on npm.
- Out of scope: creating new projects through npx, updating through npx, writing `routing.md` from the CLIs it detects (#75), an OpenSpec install prompt (#82).
