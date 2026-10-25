# Proposal

Delivers GitHub issue #103.

## Why

`create-switchyard/scripts/build.mjs` makes one synthetic commit per release with `git commit-tree`. It fixes the author and committer names but not the dates, so each commit takes the build time. Two builds of the same tag give different commit IDs and a different `dist/release.bundle`. Nobody can check a published tarball against the tag it came from.

## What Changes

- Each synthetic commit for an older release takes the committer date of `v<release>^{commit}` as both its author and committer date.
- The commit for the packed release (the working tree) takes HEAD's committer date the same way.
- A dated build ignores `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` from the caller's environment.
- A test builds a second time with a foreign date in the environment and checks the bundle is byte-identical to the one `npm pack` built. It also checks each bundled commit carries its tag's date.
- No change to which releases are bundled, the tag names, the commit messages, the tree contents, or the bundle format. The updater is untouched.
- CHANGELOG: one line under Unreleased, Fixed.

## Capabilities

### New Capabilities

None. No observable behaviour changes for users, so the change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- `create-switchyard/scripts/build.mjs`: dates on `commit-tree`.
- `create-switchyard/test/install.test.mjs`: one new test, about one extra build (2 s locally).
- `CHANGELOG.md`: one appended line.
