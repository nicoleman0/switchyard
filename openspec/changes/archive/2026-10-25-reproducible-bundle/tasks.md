# Tasks

## 1. Dated commits

- [x] 1.1 In `create-switchyard/test/install.test.mjs`, hoist the unpacked tarball path to module scope and add a test that reruns `node scripts/build.mjs` in `pkgDir` with `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` set to `2000-01-01T00:00:00Z`, then asserts `dist/release.bundle` equals the tarball's bundle byte for byte. In the same test, assert each bundled `v<release>` has `%cI` and `%aI` equal to the source repo's `v<release>^{commit}` `%cI`, and the package version's tag has HEAD's. Verify with `npm test --prefix create-switchyard` that it fails on the current `build.mjs`.
- [x] 1.2 In `create-switchyard/scripts/build.mjs`, give each `commit-tree` call author and committer dates from `git show -s --format=%cI <rev>` in the source repo, where `<rev>` is `v<release>^{commit}` for older releases and `HEAD` for the packed release, as design.md describes. Keep the existing `GIT_CONFIG_*` isolation, tag names, and commit messages. Add at most a one-line comment saying why. Verify the test from 1.1 now passes with `npm test --prefix create-switchyard`, and build twice in a scratch clone (`git clone -q <worktree> <scratch>`, then `node create-switchyard/scripts/build.mjs` twice, copying the bundle between runs) and `cmp` the two bundles.
- [x] 1.3 Add `- #103: Building the same tag twice gives a byte-identical npm bundle.` under `## [Unreleased]`, `### Fixed` in `CHANGELOG.md` (add the `### Fixed` heading if Unreleased has none). Verify with `git diff CHANGELOG.md` showing only appended lines.

## 2. Repository checks

- [x] 2.1 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` passes.
- [x] 2.2 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 2.3 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 2.4 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 2.5 `npm test --prefix create-switchyard` passes, with release tags present (`git tag -l 'v*'`).
- [x] 2.6 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
