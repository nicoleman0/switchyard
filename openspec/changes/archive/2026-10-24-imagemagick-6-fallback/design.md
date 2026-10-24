# Design

## Context

See proposal.md for why and for the Ubuntu versions. The maintainer set the order (`sips`, `magick`, `convert`) and ruled out requiring ImageMagick 7.

## Goals / Non-Goals

**Goals:**
- `compare.py` works with ImageMagick 6 alone.
- `preflight.sh` reports ok exactly when `compare.py` would find a tool.

**Non-Goals:**
- Checking that `magick` is ImageMagick. No other common tool ships that name.
- Naming the chosen tool in the preflight output.
- Restructuring `compare.py` beyond the tool choice.

## Decisions

- **Accept `convert` only when `convert -version` prints "ImageMagick" on stdout.** Windows ships a `convert.exe` that converts FAT volumes to NTFS. Run it with `-version` only, with output captured and the exit status ignored. ImageMagick 6 and 7 both print `Version: ImageMagick ...` on the first line. Alternative: trust any `convert`. Rejected per the maintainer's trap list.
- **Prefer `magick` over `convert`.** ImageMagick 7 keeps `convert` as a deprecated alias that prints a warning. Checking `magick` first means `convert` is only used on ImageMagick 6.
- **Choose the tool once per run, before any image work.** Today `img()` calls `shutil.which` per screenshot. With a `convert -version` probe, once is cheaper, and a missing tool fails before any work. A small `image_tool()` function returns the command name or exits with the message.
- **Same arguments for `convert` and `magick`.** `convert src -resize WIDTHx -quality 62 out.jpg` is valid in ImageMagick 6. Only the command name changes.
- **Two implementations, one agreement test.** `compare.py` is Python and `preflight.sh` is bash. Sharing code would mean preflight calling `compare.py`, and the preflight tests stub `python3`. Instead, a table in `test_preflight.py` runs both scripts against the same stub `PATH` and asserts preflight says ok exactly when `compare.py` succeeds, and that `compare.py` used the expected tool. The table is the one home for the rule's cases.
- **Test `compare.py` as a black box.** The test runs the real `compare.py` with `sys.executable`, a one-screen spec, and stub tools that log their own name and write the output file. No import, so no refactor of the module's top-level code.

## Risks / Trade-offs

- [A `convert -version` that hangs] → Not seen on any known `convert`. No timeout, to keep it simple.
- [The rule drifts between the two scripts] → The agreement table fails when one script changes and the other does not.
