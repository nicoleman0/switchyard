# Proposal

Delivers issue #149, "Linear cannot be the issue tracker".

## Why

A team that keeps its issues in Linear cannot use Switchyard: `tracker.py` knows only GitHub, and every script assumes issue keys are digits. #148 put tracker calls behind one script so a second backend is one class and one table entry. #150 and #151 build on this backend.

## What Changes

- `tracker.py` gets a `linear` backend with the same `view` and `set-change` operations. It calls Linear's GraphQL API with `LINEAR_API_KEY`, through the Python standard library.
- `tracker.py check` is a new operation: it confirms the configured tracker is usable. GitHub has nothing extra to check; Linear checks that the key is set and accepted.
- Issue keys may be Linear identifiers such as `ENG-123`, as well as digits, each with the best-of-N `b` suffix. `state.py`, `setup-worktree.sh`, `merge-queue.py` ordering, Herdr agent names, and the shipped `worktree-up.sh` hook accept both forms.
- On Linear, branch names start with the lowercased issue key so Linear's GitHub integration links the PR. `SKILL.md` says so.
- Install takes `--tracker <name>` (default `github`). It writes `Tracker: <name>` into `switchyard/tracker.md` when the file is missing.
- Preflight runs `tracker.py check` and reports a missing or rejected Linear key with the fix. `gh` stays required.
- README gets a short "Use Linear" section; CHANGELOG gets an Unreleased line.

PRs stay on GitHub. Status changes, comments, and delivery order from Linear are #150 and #151.

## Capabilities

### New Capabilities

- `issue-tracker`: which tracker a project uses, how it is chosen at install, the operations every backend provides, the issue key forms, and the preflight check.

### Modified Capabilities

None. `openspec/specs/` is empty.

## Impact

- `switchyard/scripts/tracker.py`, `test_tracker.py`: Linear backend, `check`.
- `switchyard/scripts/state.py`, `test_state.py`: key forms, ordering, `check-key`.
- `switchyard/scripts/setup-worktree.sh`, `start-worker.sh`: key validation, lowercase agent names.
- `switchyard/hooks/worktree-up.sh`: port from the key's number.
- `switchyard/scripts/preflight.sh`, `test_preflight.py`: tracker check.
- `switchyard/scripts/update-switchyard.py`, `test_update_switchyard.py`: `--tracker`.
- `create-switchyard/bin/create-switchyard.mjs`, `test/install.test.mjs`: pass `--tracker` through.
- `switchyard/SKILL.md`, `switchyard/runners/herdr.md`, `README.md`, `CHANGELOG.md`: docs.
- No new dependency. Untested against live Linear: no API key in this environment.
