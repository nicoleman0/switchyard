# Tasks

## 1. Bundle every release from v0.7.0

- [x] 1.1 In `create-switchyard/scripts/build.mjs`, list the releases from `CHANGELOG.md` headings as design D3 describes, and fail before writing `dist/` when a tag is missing or its `switchyard/VERSION` differs. Verify by running the build in a `git clone --depth 1 --no-tags file://<root>` in a temp dir: exit 1, message names the tag.
- [x] 1.2 Build one commit per release with the union of path lists, older releases from their tags and the packed version from the working tree, as design D2 describes. Print the release range and the bundle size. Verify with `git bundle list-heads dist/release.bundle` that `main` and v0.7.0 through v0.8.0 are present, that `git ls-tree -r v0.7.2` in a bare clone of the bundle holds only listed paths, and that executable modes match the source tags. Record the size for the PR.
- [x] 1.3 Add the bundle test from design D6 and the build failure test. Verify `npm test --prefix create-switchyard` passes.

## 2. The `update` command and the install refusal

- [x] 2.1 In `create-switchyard/bin/create-switchyard.mjs`, add `update [args...]` with the argument refusal rule from design D4, and pass the updater's exit code through. Update the usage string to name `npm init switchyard@latest` and `update`. Verify with the tests in 2.3.
- [x] 2.2 Add the install refusal for a repo with `switchyard/VERSION` from design D4. Verify that a run outside a git repo still prints the updater's `run this command inside a git work tree` and exits 2.
- [x] 2.3 Add the update, rerun, conflict, `--to`, and refused-argument tests from design D6, and change the second-run test to assert the new message. Verify `npm test --prefix create-switchyard` passes.

## 3. CI

- [x] 3.1 In `.github/workflows/switchyard.yml`, add the tag fetch from design D5 to the "Test the npm installer" step and keep its guard. Verify the YAML parses and that the fetch command works in a `git clone --depth 1 --no-tags` of the repo, after which the build passes.

## 4. Docs

- [x] 4.1 Update `README.md` as design D7 describes. Verify each command matches the bin's usage, that the "not through npx" line is gone, and that sections outside install and update are unchanged.
- [x] 4.2 Update `create-switchyard/README.md` and `CONTRIBUTING.md` Release step 3 as design D7 describes. Verify each command named runs as written.
- [x] 4.3 Add one `### Added` line for #91 under Unreleased in `CHANGELOG.md`. Verify the "Check release version" script from the workflow still passes.

## 5. Repository checks

- [x] 5.1 Run `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` and verify it passes.
- [x] 5.2 Run `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` and verify it passes.
- [x] 5.3 Run `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` and `node --check` on each `create-switchyard/**/*.mjs`, and verify they pass.
- [x] 5.4 Run `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` and verify it passes.
- [x] 5.5 Run `npm test --prefix create-switchyard` and verify it passes.
- [x] 5.6 Run `npx --yes @fission-ai/openspec validate --all --strict` and verify it passes.
- [x] 5.7 Verify `git diff --stat main -- switchyard/scripts/update-switchyard.py` is empty.

## Workflow follow-up

- Archive the change in the PR that completes it.
- Report the bundle size in the PR body.
- The maintainer publishes the package. Workers never run `npm publish` or `npm login`.
