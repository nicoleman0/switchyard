# Design

## Context

- `update-switchyard.py --install` reads a release by running `git clone --bare <source>`. It then reads `vX.Y.Z` tags, `switchyard/update-paths.txt` at the target tag, and the blobs and modes under those paths. The default source is the GitHub repo.
- `npm pack` always leaves out files named `.gitignore`, even when `files` lists their folder. During planning, a packed tarball lost `r/.gitignore`. The release ships a `.gitignore` that install merges. `npm pack` keeps executable bits.
- A git bundle is a valid `git clone` source. During planning, a bundle held one commit with the `update-paths.txt` files of HEAD, tagged `v0.7.2`. It was 61 KB. The current updater, run with `--install --source release.bundle` in a scratch repo, added 38 files and wrote `VERSION` 0.7.2. It kept `.gitignore` and the `0755` modes of the hook scripts.
- GitHub's "Use this template" copies every file. `init-project.py` deletes the Switchyard-only files listed in `DELETED_PATHS`. It handles files only (`Path.unlink`), and it matches paths with uncommitted changes exactly.

## Goals / Non-Goals

**Goals:**
- `npx create-switchyard` installs one release, offline once npm has fetched the package. It gives the same report, exit codes, and next steps as `update-switchyard.py --install`.
- One copy of the install logic: the updater.

**Non-Goals:**
- Choosing a release (`--to`), updating, and creating projects. The package holds exactly one release.
- Windows support beyond what the updater already has.

## Decisions

### D1. Bundle the release as a git bundle and leave the updater unchanged

The package ships `dist/release.bundle`. It holds one commit with the release's files under the paths in `switchyard/update-paths.txt`. The branch `main` and the tag `v<VERSION>` point at it. The bin script runs `python3 dist/update-switchyard.py --install --source dist/release.bundle`.

Alternatives considered:
- Plain files plus a new `--release-dir` mode in the updater. npm drops `.gitignore`, so the build would have to rename it and the updater would have to rename it back. The updater would also need a second way to read a release, with its own tests. This adds work for no gain to the user.
- The bin script builds a temporary git repo from plain files at run time. This gives the same result as D1. It moves the git work onto every user's machine and still has the `.gitignore` problem.

### D2. The build script

`create-switchyard/scripts/build.mjs` runs as the `prepack` script, so both `npm pack` and `npm publish` build first. It uses only Node built-ins and `git`. Steps:
1. Find the repo root (`git rev-parse --show-toplevel`, from the package folder).
2. Read `switchyard/VERSION`. Stop with a clear message unless it is `X.Y.Z` and equals `version` in `package.json`.
3. Read `switchyard/update-paths.txt`, skipping comments as the updater does. List the tracked files under those paths with `git ls-files -z`.
4. In a fresh temporary directory, copy each file from the working tree with its executable bit. Commit with a fixed author and committer (`Switchyard`), so the build does not depend on the user's git config. Tag `v<VERSION>`. Run `git bundle create dist/release.bundle main v<VERSION>`.
5. Copy `switchyard/scripts/update-switchyard.py` to `dist/update-switchyard.py`.

The build reads tracked files from the working tree, not HEAD. The package test can then run before the implementer's single commit. A `prepublishOnly` script refuses to publish when `git status --porcelain` shows changes, so a published package always matches a commit. The build never writes refs or objects to the Switchyard repo.

### D3. Package layout

```
create-switchyard/
  package.json        name, version (= switchyard/VERSION), bin, files, scripts, license MIT, engines
  bin/create-switchyard.mjs
  scripts/build.mjs
  test/install.test.mjs
  .gitignore          dist/ and *.tgz
  README.md           three lines: what it does and a link to the main README
```

`files` is `["bin", "dist"]`. npm adds `package.json` and `README.md` on its own. The `files` field overrides `.gitignore`, so `dist/` ends up in the package even though git ignores it. The package has no dependencies. `engines.node` is `>=18`, because the code uses only `node:child_process`, `node:fs`, `node:path`, `node:url`, and `node:test`.

### D4. CLI behaviour

- No arguments: run the bundled updater with `stdio: "inherit"` in the user's working directory, and exit with its exit code (0, 1 for conflicts, 2 for a refusal). The updater finds the repo root and refuses when the directory is not a repo, has uncommitted changes, or already has `VERSION`.
- `--help` or `-h`: print a usage line and exit 0.
- Any other argument: print the usage line to stderr and exit 2.
- `python3` missing (spawn `ENOENT`): print `create-switchyard: Python 3 is required (python3 not found on PATH)` and exit 2.
- A signal ends the child: exit 1.

`npm init switchyard` maps to the same command, and the README mentions it in one line.

### D5. Keep the version in step

The version lives in two places: `switchyard/VERSION` is the authority, and npm needs `package.json` to say the same. Three checks keep them equal:
- The build refuses a mismatch (D2).
- The CI step "Check release version" also compares `create-switchyard/package.json` with `switchyard/VERSION`. The step already runs only on `nicoleman0/switchyard`.
- The CONTRIBUTING release steps bump both files in the release PR.

### D6. Keep the package out of users' projects

- The updater: `switchyard/update-paths.txt` does not list `create-switchyard`, and `test_shipped_update_paths_names_the_claude_stub` already asserts the exact list. No change.
- The npm install: the bundle holds only the `update-paths.txt` paths. The package test checks that `create-switchyard/` does not appear in the target repo.
- The template: add `create-switchyard` to `init-project.py` as a deleted directory. Remove it with `shutil.rmtree`. Skip it, and say why, when `git status --porcelain -uall` reports any path under `create-switchyard/` (prefix match). Ignored build output (`dist/`, `node_modules/`) does not block the delete, because a rebuild recreates it.
- CI: both package steps in `switchyard.yml` run only `if: github.repository == 'nicoleman0/switchyard'`. Projects receive the file, but the steps skip there.

### D7. The package test

`create-switchyard/test/install.test.mjs` runs with `node --test` (`npm test`). It:
- runs `npm pack --pack-destination <tmp>`, which also exercises `prepack`;
- creates a scratch git repo with one commit, using an isolated git config like the Python tests;
- runs `npm exec --yes --package=<tgz> -- create-switchyard`, then asserts exit 0, `switchyard/VERSION` equal to the package version, `.gitignore` containing `.switchyard/`, `switchyard/hooks/worktree-up.sh` executable, and no `create-switchyard/` in the repo;
- runs it again in the same repo, committed, and asserts exit 2 with the updater's "already names" refusal;
- asserts `--help` exits 0 and an unknown argument exits 2.

CI runs it as a step guarded by the repository check: `npm test --prefix create-switchyard`.

### D8. Docs

- README "Add it to an existing repo": replace the clone recipe with `npx create-switchyard`, run from the repo root. Say that it runs the bundled release's `update-switchyard.py --install` and needs Python 3. Keep the merge explanation. "Take a later release": one line saying later releases come through the installed updater, not npx.
- README init paragraph and Layout: add `create-switchyard/` ("the npm installer; init deletes it").
- CONTRIBUTING: a "Release" section listing these steps: bump `switchyard/VERSION`, `create-switchyard/package.json`, and the CHANGELOG heading in one PR; merge; tag `vX.Y.Z`; from a clean checkout of the tag, `cd create-switchyard && npm publish`.
- `create-switchyard/README.md` is the npm page.

## Risks / Trade-offs

- [The npm page shows a binary bundle, not readable files] → The package README links to the tagged source. The bundle comes from tracked files at a commit that `prepublishOnly` enforces.
- [Run time needs `git` and `python3`] → Both are already requirements. The bin script gives a clear message when `python3` is missing, and the updater refuses when git is missing.
- [Two version fields] → D5's three checks.
- [`npm exec` with a local tarball in tests uses the npx cache] → The test uses a temporary `npm_config_cache`, so it does not touch the user's cache.

## Migration Plan

None for users. The first `npm publish` happens after this merges, at the next release. Until then, the README's npx command does not work. Publish 0.7.3 (or the next release) right after merge, or merge this with the release PR.
