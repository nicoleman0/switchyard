# Tasks

## 1. Package scaffold and build

- [x] 1.1 Create `create-switchyard/package.json` (name `create-switchyard`, version equal to `switchyard/VERSION`, `bin`, `files: ["bin", "dist"]`, scripts `prepack`, `prepublishOnly`, `test`, license MIT, `engines.node >=18`, no dependencies), `create-switchyard/.gitignore` (`dist/`, `*.tgz`), and `create-switchyard/README.md`. Verify `git status` lists no `dist/` or `.tgz` after a build.
- [x] 1.2 Write `create-switchyard/scripts/build.mjs` as design D2 describes. Verify that `npm pack --dry-run` in `create-switchyard/` lists `dist/release.bundle` and `dist/update-switchyard.py`, that `git clone --bare dist/release.bundle` shows tag `v<VERSION>`, that the bundle's tree holds only the `update-paths.txt` paths, `.gitignore` included, and that the Switchyard repo gains no new refs.
- [x] 1.3 Make the build fail loudly, before it writes `dist/`, when `package.json` and `switchyard/VERSION` differ, or when a tracked file under a listed path is missing from the working tree. Verify both by hand with a temporary edit that you revert afterwards.
- [x] 1.4 Make `prepublishOnly` refuse when `git status --porcelain` shows changes. Verify by running the script directly (`npm run prepublishOnly`) with a dirty tree. Never run `npm publish` or `npm login`.

## 2. CLI

- [x] 2.1 Write `create-switchyard/bin/create-switchyard.mjs` as design D4 describes: no arguments runs the bundled updater with `--install --source <bundle>` and passes its exit code through, `--help`/`-h` exits 0, other arguments exit 2 with usage, and a missing `python3` gets the stated message and exits 2. Verify with `node --check` and the tests in 2.2.
- [x] 2.2 Write `create-switchyard/test/install.test.mjs` as design D7 describes, with a temporary `npm_config_cache` and an isolated git config. Verify that `npm test --prefix create-switchyard` passes.

## 3. Keep the package out of new projects

- [x] 3.1 Teach `switchyard/scripts/init-project.py` to delete the `create-switchyard` directory (design D6), with a prefix match for uncommitted changes. Update its docstring if needed. Verify with new tests in `test_init_project.py`: a fresh template loses `create-switchyard/` and prints `deleted   create-switchyard`; an uncommitted change under it skips the folder with the reason; a rerun reports it absent; ignored `dist/` output does not block the delete.
- [x] 3.2 Update the README init paragraph to list `create-switchyard/` among the deleted files. Verify the list matches `DELETED_PATHS`.

## 4. CI

- [x] 4.1 In `.github/workflows/switchyard.yml`, extend "Check release version" so it also fails when `create-switchyard/package.json` `version` differs from `switchyard/VERSION`. Run the step's script locally and verify it passes, then fails after a temporary version edit.
- [x] 4.2 Add a step "Test the npm installer", guarded by `if: github.repository == 'nicoleman0/switchyard'`, that runs `npm test --prefix create-switchyard`. Verify the YAML parses (`python3 -c "import yaml..."` or by reading it) and that the command passes locally.

## 5. Docs

- [x] 5.1 README "Add it to an existing repo": replace the clone recipe with `npx create-switchyard` (and the `npm init switchyard` line), and state that it needs Python 3. Keep the merge explanation. Add the "later releases use the installed updater" line to "Take a later release". Add `create-switchyard/` to Layout. Verify the commands match the CLI and that unrelated sections are unchanged.
- [x] 5.2 CONTRIBUTING: add a short "Release" section (design D8). Verify each step names a real file or command.
- [x] 5.3 CHANGELOG: under Unreleased, add `### Added` with one line for #74. Verify the release-version CI script still passes.

## 6. Repository checks

- [x] 6.1 Run `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` and verify it passes.
- [x] 6.2 Run `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` and verify it passes.
- [x] 6.3 Run `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` and `node --check` on each `create-switchyard/**/*.mjs`, and verify they pass.
- [x] 6.4 Run `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` and verify the full suite passes.
- [x] 6.5 Run the "Check release version" script from `.github/workflows/switchyard.yml` and verify it passes.
- [x] 6.6 Run `npm test --prefix create-switchyard` and verify it passes.
- [x] 6.7 Run `npx --yes @fission-ai/openspec validate --all --strict` and verify it passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
- The maintainer publishes the package. Workers never run `npm publish` or `npm login`.
