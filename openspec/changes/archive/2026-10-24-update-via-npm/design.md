# Design

## Context

- `create-switchyard` today: the bin accepts no arguments and runs `python3 dist/update-switchyard.py --install --source dist/release.bundle`. `build.mjs` copies the tracked files under `switchyard/update-paths.txt` from the working tree into a temporary repo, makes one commit tagged `v<VERSION>`, and bundles `main` plus that tag.
- The updater takes any git URL as `--source`, including a bundle file: it runs `git clone --bare`, lists `vX.Y.Z` tags, uses `switchyard/VERSION` as the base and the newest tag as the target. It reads `update-paths.txt` from the target and filters both base and target trees by it. A base without `update-paths.txt`, or one that is not a tag in the source, is refused with exit 2.
- Release tags are lightweight commits. v0.7.0 through v0.8.0 all exist and list the same eight paths.
- `actions/checkout` fetches one commit and no tags. `.github/workflows/switchyard.yml` ships to every project through `update-paths.txt`.
- PR #96 (merged) changed the README install lines to `npm init switchyard`. This change builds on that wording.

## Goals / Non-Goals

**Goals:**
- `update` runs the updater's normal path with no changes to `update-switchyard.py`.
- The documented commands always run the newest published package.

**Non-Goals:**
- A bin-side check for a `VERSION` newer than the newest bundled release, or older than v0.7.0. The updater's refusal already names the available releases (see Risks).
- Changing the in-repo updater's own refusal text.

## Decisions

### D1. Document the `@latest` form

Read in npm 11.19's `libnpmexec` and checked with a stale fake `create-switchyard@0.0.1` placed in a scratch npx cache:

| Command | Ran |
|---|---|
| `npm init switchyard` | the stale cached copy |
| `npm init switchyard@latest` | the registry's 0.8.0 |
| `npx create-switchyard` | 0.8.0 from the npx cache check, but a global install wins with any version |
| `npx create-switchyard@latest` | 0.8.0 |

`npm init switchyard` becomes the spec `create-switchyard@*`. A `*` range matches any copy already in the npx cache, the global prefix, or the project's `node_modules`. A tag spec (`@latest`) fetches the manifest and reinstalls when the cached copy resolves elsewhere. So the docs use `npm init switchyard@latest` for install and `npm init switchyard@latest update` for update, and name `npx create-switchyard@latest` as the same thing. This overrides PR #96's plain `npm init switchyard`.

Alternative: plain `npm init switchyard`. Shorter, but an update could run an old package and report "Already at" or "unknown base release".

### D2. Bundle: one synthetic commit per release

`build.mjs` builds a chain of commits in a temporary repo, one per bundled release in version order. Each commit is a lightweight tag `vX.Y.Z`, and `main` points at the newest. Each commit's tree holds that release's files under the union of every bundled release's `update-paths.txt` entries. Older releases are read from their tags with `git ls-tree -r -z` and `git cat-file`, keeping modes. The packed version is read from the working tree's tracked files, as today. Any tree entry that is not a regular file fails the build.

The union matters because the updater filters the base by the target's path list. With `--to` forwarded, the target can be an older bundled release whose list differs from the newest one.

Alternatives:
- Bundle the repo's real tag history. It needs a full clone and ships every non-workflow file in history.
- Filter each release by its own path list. A path added to the list later would have no base content and merge against an empty base.

Measured with a prototype: 72,469 bytes for v0.7.0 through v0.8.0, against 64,872 bytes for today's one-release bundle. The updater ran a 0.7.2-to-0.8.0 update against it with exit 0 and `--to` worked.

### D3. Which releases, and the missing-tag failure

The releases are the `## [X.Y.Z] - ` headings in `CHANGELOG.md` from 0.7.0 up to, not including, the packed version. The CI release-version check already parses that heading format. For each one the build requires a tag `vX.Y.Z` whose `switchyard/VERSION` names that version. A missing tag fails before `dist/` is written:

```
create-switchyard build: tag v0.7.1 is missing; fetch release tags with `git fetch --tags` (a shallow clone has none)
```

`0.7.0` is a constant in `build.mjs`, with a one-line comment that it is the oldest base the updater accepts. The build prints the release range and bundle size, for the PR and for release notes.

Alternative: list the `v*` tags that exist. A missing tag cannot be detected that way.

### D4. Bin arguments

- No arguments: install. Before running the updater, the bin runs `git rev-parse --show-toplevel`. If that succeeds and `<top>/switchyard/VERSION` is a regular file, it prints `create-switchyard: switchyard/VERSION already names <v>; to update, run npm init switchyard@latest update` and exits 2. Otherwise it runs the updater with `--install --source <bundle>` as today, which reports a missing work tree or a non-regular `VERSION` itself.
- `update [args...]`: runs the updater with `--source <bundle>` followed by the forwarded arguments, and passes its exit code through. An argument is refused with exit 2 when its part before `=` starts with `--`, is longer than `--`, and is a prefix of `--source` or `--install`. That covers `--source x`, `--source=x`, and argparse abbreviations such as `--sou` and `--inst`, which argparse would otherwise accept.
- `--help` or `-h` alone: usage, exit 0. Anything else: usage on stderr, exit 2.
- `update --help` reaches the updater's own help, which lists `--source` and `--install`. Accepted: the bin's usage names the npm form.

Alternative for the install refusal: edit the updater's message. #92, #93, and #95 edit that file next, and the in-repo message is right for in-repo users.

### D5. CI fetches tags in the guarded step

The "Test the npm installer" step runs `git fetch --no-tags --depth=1 origin '+refs/tags/v*:refs/tags/v*'` before `npm test`. The step keeps its `if: github.repository == 'nicoleman0/switchyard'` guard.

Alternative: `fetch-depth: 0` on the checkout. It would slow the checkout for every project that takes this file.

### D6. Tests

`create-switchyard/test/install.test.mjs` keeps its four tests, with the second-run test asserting the new message, and adds:

- The packed bundle lists a tag for every release from v0.7.0 through the package version.
- Update from an older release: a scratch repo holding the v0.7.2 tree from the bundle, with `VERSION` 0.7.2, committed. `update` exits 0, prints `updated:` lines, and writes the package version.
- A rerun prints `Already at <version>` and exits 0.
- A local edit that conflicts with the release: `update` exits 1 and the file has conflict markers.
- `update --to 0.7.2` from 0.7.2 prints `Already at 0.7.2`, which shows forwarding works.
- `update --source x`, `update --source=x`, `update --inst`, and `update --install` each exit 2 without changing the repo.
- The build fails in a `git clone --depth 1 --no-tags file://<root>` of the repo, and its message names a missing tag.

### D7. Docs

- `README.md`: both install blocks use `npm init switchyard@latest`, with `npx create-switchyard@latest` named once as the same. One line says why `@latest`. "Take a later release" leads with `npm init switchyard@latest update`, then names `python3 switchyard/scripts/update-switchyard.py` as the way without Node. Drop "Later releases come through the updater installed in your repo, not through npx." The network line says the npm form reaches the npm registry and the Python form clones GitHub. The install paragraph drops "holds one release" and "works offline once npm has fetched it": with `@latest`, npm checks the registry, and offline behaviour was not verified.
- `create-switchyard/README.md`: install and update commands, the releases it holds.
- `CONTRIBUTING.md` Release step 3: publish from a checkout with every release tag fetched.
- `CHANGELOG.md` Unreleased, `### Added`: one line for #91.

## Risks / Trade-offs

- [A `VERSION` newer than the newest bundled release, from a stale package] → The updater refuses with `unknown base release vX; available releases: ...`, exit 2. The `@latest` docs keep this rare.
- [A `VERSION` older than 0.7.0] → Same refusal, where the in-repo updater would say to update to 0.7.0 first. 0.7.1 already stopped migrating those projects.
- [The bundle grows with every release] → About 2 KB per release at today's sizes, because git deltas the shared files. Revisit if it passes 1 MB.
- [Release headings and tags disagree] → The build fails loudly and names the tag.
