# Proposal

## Why

Delivers GitHub issue #38. `compare.py` shrinks screenshots with `sips`, then `magick`. `preflight.sh` checks for the same two commands. ImageMagick 6 has no `magick` command, only `convert`, so both scripts miss it.

Checked on 2026-10-24 against the Ubuntu archive:
- Ubuntu 24.04 LTS (noble) ships `imagemagick` 8:6.9.12.98+dfsg1-5.2build2. Its `postinst` registers `convert` and the other IM6 tools with update-alternatives. There is no `magick`.
- Ubuntu 26.04 LTS (resolute) ships 8:7.1.2.18+dfsg1-1. Its `postinst` registers `magick` as well as `convert`.
- Sources: Launchpad `getPublishedSources` for `imagemagick` in each series (`https://api.launchpad.net/1.0/ubuntu/+archive/primary?ws.op=getPublishedSources&source_name=imagemagick&exact_match=true&status=Published&distro_series=https://api.launchpad.net/1.0/ubuntu/<series>`), and the `imagemagick-6.q16` and `imagemagick-7.q16` amd64 debs in `http://archive.ubuntu.com/ubuntu/pool/universe/i/imagemagick/`. packages.ubuntu.com returned an Internal Server Error.

So the current LTS works today, but 24.04 and 22.04 are still supported and fail. The maintainer chose a fallback over requiring ImageMagick 7.

## What Changes

- `switchyard/scripts/compare.py`: pick the image tool once, in this order: `sips`, `magick`, then `convert` only when `convert -version` says ImageMagick. `convert` takes the same arguments as `magick` here. The error names both ImageMagick commands.
- `switchyard/scripts/preflight.sh`: the Image tool check uses the same order and the same `convert -version` test.
- `switchyard/scripts/test_preflight.py`: cases for ImageMagick `convert`, a `convert` that is not ImageMagick, and one table that runs both scripts on the same stub `PATH` and checks they agree.
- `CHANGELOG.md`: one line under Unreleased.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty and this change sets `skip_specs: true`: it is tooling.

### Modified Capabilities

None.

## Impact

- `switchyard/scripts/compare.py`, `switchyard/scripts/preflight.sh`, `switchyard/scripts/test_preflight.py`, `CHANGELOG.md`.
- The README Requirements line already says "`sips` (macOS) or ImageMagick". After this change it is true for ImageMagick 6 too, so it stays as is.
- Out of scope: the README install sections (#74).
