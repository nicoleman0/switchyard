# Design

## Context

`build.mjs` writes a fresh bare repo in a temp dir, hashes each release's files into it, and runs `commit-tree` once per release with `env` (fixed names, `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null`, a private index). `env` spreads `process.env`, so a caller's `GIT_AUTHOR_DATE` or `GIT_COMMITTER_DATE` reaches `commit-tree` today. The commit dates are the only input that changes between runs. Blob and tree content come from tags or tracked files, and the bundle header lists refs in a fixed order.

Measured in a scratch clone (git 2.54.0, 10 CPUs, 110 objects):

- Unmodified script, two builds: bundles differ, 85131 vs 84990 bytes.
- With dates pinned, six builds: `cmp` finds no difference.
- With dates pinned, `pack.threads` set to 1, 2, 3, 4, 5, 8, and 64 (three runs each for 2 to 5): every bundle is byte-identical to the default build. Delta search threads do not change the pack today.

## Goals / Non-Goals

**Goals:**

- Same tag, same git version: byte-identical `dist/release.bundle`.

**Non-Goals:**

- Identical bytes across git versions. `pack-objects` and zlib output may differ between git releases; nothing in the build can pin that.
- `check-clean.mjs`, publishing, the updater.

## Decisions

- **Date source.** Older release: `git show -s --format=%cI v<release>^{commit}` in the source repo. Packed release: the same for `HEAD`. Both author and committer date get that value. `%cI` keeps the original offset, so the bundled commit's date reads exactly as the tag's. The maintainer chose this; a fixed epoch date was the alternative and loses the link to the tag.
- **Where.** Read the date in the release loop next to `commit-tree` and pass `{ ...env, GIT_AUTHOR_DATE: date, GIT_COMMITTER_DATE: date }` for that call only. `run`/`repo` take a fixed `env` today, so give `repo` an optional env override rather than calling `git` by hand. The spread order makes the dates win over the caller's environment.
- **No `pack.threads` pin.** Measured above: no effect at this size. Pinning is a one-line change if the test or a cross-machine check ever shows a difference. See question 1 in the plan summary.
- **Test.** In `install.test.mjs`, after `before()` has packed: run `node scripts/build.mjs` in `pkgDir` with `GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE` set to `2000-01-01T00:00:00Z`, then assert `dist/release.bundle` equals the tarball's `package/dist/release.bundle` byte for byte. The foreign date makes the test fail every time on the old script, rather than passing when both builds land in the same second. Also assert, from the existing `bundleGit` clone, that each bundled `v<release>` has the committer and author date (`%cI`, `%aI`) of the source repo's `v<release>^{commit}`, and the package version's tag has HEAD's. One extra build costs about 2 s, inside the suite's current runtime (it already packs once and runs npm exec many times).

## Risks / Trade-offs

- [Second build overwrites `pkgDir/dist`] → It writes the same bytes on success. On failure the test fails anyway, and `dist/` is git-ignored and rebuilt by every `prepack`.
- [Uncommitted working-tree edits get HEAD's date] → Accepted. A release build runs from a clean tag checkout, where HEAD is the tag.
- [A caller's `GIT_CONFIG_PARAMETERS` or `GIT_CONFIG_COUNT` still reaches git and could change pack settings] → Out of scope here. See question 2 in the plan summary.
