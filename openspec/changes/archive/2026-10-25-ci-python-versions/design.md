# Design

## Context

The workflow has one job, `check`, on `ubuntu-latest`. It calls `python3` from the runner image. The updater ships the file to every project, so it must keep working outside `nicoleman0/switchyard` and keep its header comment. Actions are pinned by major tag (`actions/checkout@v7`). The newest `actions/setup-python` release is v7.1.0 (2026-10-22); v7.0.0 came out 2026-07-20.

`union-resolve.py` has no tests, so only `py_compile` sees its syntax.

## Goals / Non-Goals

**Goals:**
- Tests run on the oldest supported Python and on the newest stable one.
- Steps that do not depend on the Python version run once.

**Non-Goals:**
- A preflight check of the Python version.
- Testing other operating systems.
- Changing the CLI error text in `create-switchyard/bin/create-switchyard.mjs`, which reports a missing binary, not a version. The plan answer added `create-switchyard/README.md:3` to the paths this change owns: it now says "Python 3.10 or newer".

## Decisions

### Two `setup-python` steps in one job, not a matrix

Order of steps:

1. `actions/checkout@v7`
2. `actions/setup-python@v7` with `python-version: '3.10'`
3. Compile Python scripts on Python 3.10
4. Test the scripts on Python 3.10
5. `actions/setup-python@v7` with `python-version: '3.x'`
6. The existing steps, unchanged, in their current order.

After each `setup-python` step, `python3` on `PATH` is the version just installed, so the existing `run:` lines need no edit.

Alternatives:
- A matrix over `['3.10', '3.x']`: every other step needs `if: matrix.python-version == '3.x'`, or the job splits in two. Splitting renames or adds a job, which can break a downstream branch rule that requires `check`.
- One `setup-python` step with a multi-line `python-version` (the last listed becomes the default) and `python3.10 -m unittest` for the old run: one step fewer, but it relies on the versioned binary name and hides which Python each step uses.

Trade-off: a 3.10 failure stops the job before the newest-Python steps run. The matrix would report both. The fix for one usually fixes the other, so this is acceptable.

### Newest Python is `'3.x'`

`setup-python` documents x-ranges as "the latest stable version of Python (for the specified major version)", and `allow-prereleases` defaults to `false`, so `3.x` never picks a pre-release. It moves to 3.15 on its own when 3.15 is released. A hard-coded `'3.14'` would go stale and need a release per Python version.

Source: `docs/advanced-usage.md` in `actions/setup-python`.

### Compile on 3.10 too

`py_compile` on 3.10 catches syntax newer than 3.10 in a script no test imports, such as `union-resolve.py`. It takes about a second.

### No preflight Python version check

All 147 tests pass on 3.9, so a 3.9 project is not known to break. A hard failure would be a refusal without a known cause. A version check is also more than one line: the `test_preflight.py` stub for `python3` answers every call the same way, so it cannot tell the version probe from the release check without new test plumbing.

## Risks / Trade-offs

- [`setup-python` cannot download 3.10 on a self-hosted or GHES runner without the tool cache] → The file already targets `ubuntu-latest`. A project on other runners owns its own workflow.
- [`3.x` moves to a new release that breaks a script] → That is the failure the issue wants CI to find.
- [`setup-python@v7` moves within the major tag] → Same pinning policy as `actions/checkout@v7`.
