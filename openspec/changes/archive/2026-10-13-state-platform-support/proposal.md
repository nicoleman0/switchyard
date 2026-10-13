# Proposal

Delivers issue #31, "Platform support is not stated".

## Why

The scripts are bash and Python. The README's Requirements section names no operating system, so a Windows user finds out by failing.

## What Changes

- Add one bullet at the top of the Requirements list in `README.md`:

  ```markdown
  - macOS or Linux. CI lints and tests the workflow's scripts on `ubuntu-latest`, and the maintainer develops on macOS. Windows is untested. WSL should behave like Linux, but nobody has run it.
  ```

- Nothing else in `README.md` changes. No script changes.

## Decisions

- The bullet states three facts and no more: where CI lints and tests, where the maintainer works, and that Windows and WSL are untested. It says "untested", not "unsupported".
- The bullet goes first in the list, on its own line, so issue #28 can add a line to the same section without a conflict.
- No design document. The change is one line of prose.
- Portability problems found in the scripts are reported to the coordinator, not fixed here.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`. It is documentation, and no observable behaviour changes.

## Impact

- `README.md`: one new bullet in Requirements.
