# Tasks

One commit. Plain, short sentences, no em-dashes, per the Writing section of `AGENTS.md`. Comments say why, not what.

## 1. compare.py

- [x] 1.1 Add `image_tool()` that returns `"sips"`, `"magick"`, or `"convert"` in that order. Accept `convert` only when `subprocess.run(["convert", "-version"], capture_output=True, text=True, check=False).stdout` contains `ImageMagick`. Otherwise exit with: `compare.py needs sips (macOS) or ImageMagick (magick or convert) to shrink the screenshots`. Verify: read the function.
- [x] 1.2 Call `image_tool()` once at the top, after the spec loads and before any `img()` call. `img()` uses its result: the `sips` command as today, otherwise `[tool, src, "-resize", f"{width}x", "-quality", "62", out]`. Verify: `git diff` shows no other change to the page output.

## 2. preflight.sh

- [x] 2.1 The Image tool check passes when `sips` or `magick` is on `PATH`, or when `convert -version 2>/dev/null` output contains `ImageMagick`. Keep the ok and warn lines as they are. Verify: `shellcheck switchyard/scripts/preflight.sh` passes.

## 3. Tests (`switchyard/scripts/test_preflight.py`)

- [x] 3.1 Extend `test_optional_herdr_and_image_tool_warn_without_failing`: an ImageMagick `convert` stub (prints `Version: ImageMagick 6.9.12-98 Q16 x86_64` for `-version`) clears the warning; a `convert` stub that prints something else and exits 4 does not.
- [x] 3.2 Add an agreement test with one table of cases: {sips, magick, IM convert} → sips; {magick, IM convert} → magick; {IM convert} → convert; {non-IM convert} → none; {} → none. For each case, run `preflight.sh` and the real `compare.py` (via `sys.executable`, `PATH` set to the stub bin only) on a one-screen spec with empty `before` and `after` PNG files. Stubs append their name to a log and create their last argument. Assert: preflight prints `ok       Image tool` exactly when `compare.py` exits 0, and the log names the expected tool. Use `subTest` per case.
- [x] 3.3 Verify: `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes, and the new test fails if `convert` is removed from either script.

## 4. Changelog

- [x] 4.1 `CHANGELOG.md`: under `## [Unreleased]`, add `### Fixed` with `- #38: compare.py and the preflight check fall back to ImageMagick 6's convert, the version Ubuntu 24.04 ships.` No version bump. Verify: `switchyard/VERSION` is unchanged.

## 5. Checks

- [x] 5.1 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` passes.
- [x] 5.2 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 5.3 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 5.4 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes. Record the test count.
- [x] 5.5 The release version check from `.github/workflows/switchyard.yml` prints "VERSION matches newest release".
- [x] 5.6 `npx @fission-ai/openspec validate --all --strict` passes.
- [x] 5.7 `git grep -nP '\x{2014}' -- switchyard/scripts CHANGELOG.md` prints nothing (no em-dashes).

## Workflow follow-up

- Archive the change to `openspec/changes/archive/<date>-imagemagick-6-fallback` in the same commit. There is no spec delta to sync.
