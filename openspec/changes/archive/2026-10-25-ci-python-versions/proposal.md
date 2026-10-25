# Proposal

Delivers GitHub issue #104: CI tests the scripts on one Python version only.

## Why

The README asks for "Python 3" with no minimum, and CI tests on whatever `python3` `ubuntu-latest` ships (3.12 today). #101 passed locally on 3.15 and failed in CI on 3.12. A project on an older Python than CI's finds such failures itself.

## What Changes

- `.github/workflows/switchyard.yml` installs Python with `actions/setup-python`. It compiles and tests the scripts on 3.10, then on the newest stable Python 3. Every other step runs once, on the newest Python.
- `README.md` names Python 3.10 as the oldest supported version, in the Requirements list and the npm install paragraph, and says CI tests on 3.10 and the newest Python 3.
- `CHANGELOG.md` gains a `#104` line under Unreleased.
- No script changes. Preflight does not check the Python version.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is CI and docs only, so the change sets `skip_specs: true`.

## Impact

- `.github/workflows/switchyard.yml` ships to every project through `switchyard/update-paths.txt`. Downstream CI gains two `setup-python` steps and a 3.10 test run. The job name `check` stays, so required status checks keep matching.
- CI time grows by one extra test run (about a minute).
