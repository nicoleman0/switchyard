# Proposal

Delivers issue #114, "Fix rounds start a cold implementer session".

## Why

Each fix round starts a new implementer session. It re-reads the brief, the answers, the change, and the code to fix a few findings. On #34 three rounds each paid that cost. The fresh-session rule protects the reviewer's independence. The implementer has no such need, and its context is what a fix needs.

## What Changes

- Fix rounds and gate rounds resume the implementer session that built the change. The reviewer is always a fresh session.
- On Herdr the implementer agent stays running while the reviewer works. `start-worker.sh` starts a reviewer in a new pane split from the worktree's pane, so both agents live at once under distinct names, `implementer-<issue>` and `reviewer-<issue>`.
- The issue record keeps each role's worker, session, pane, and provider in role-prefixed fields, `<role>_worker`, `<role>_session`, `<role>_pane`, and `<role>_backend`. The unprefixed `role`, `backend`, `worker`, and `session` keep their meaning: the phase in progress. `pane` stays the worktree's root pane.
- `start-worker.sh <issue> <role> <provider> --resume` opens a new phase on the role's recorded session instead of starting one. It prints the same handles as a start. It exits 4 when there is nothing to resume, and the coordinator then starts a fresh session as today.
- `end-worker.sh <issue> [<role>]` ends one role's agent and closes the reviewer's split pane. Without a role it ends every live agent of the issue.
- Headless: Later turns resume the implementer's own session id, never the reviewer's. A provider whose First turn takes no `<session>`, such as Codex, makes its own id; the coordinator reads it from the first turn's log and records it. Codex resumes with `codex exec resume <id>` instead of `--last`.
- A provider that cannot resume falls back to a fresh session.
- Phase timings stay sequential. Starting the reviewer ends the implementer's phase even though its session lives on, and a resumed fix round opens a new implementer phase.
- Text: `SKILL.md` steps 5 to 7 and Act on the verdict, the Fix rounds paragraph of `roles/implementer.md`, both runner files, README lines that say fix rounds use a fresh implementer, and one CHANGELOG line.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change sets `skip_specs: true`. This repo keeps `openspec/specs/` empty, and the workflow's rules live in `SKILL.md`, the roles, and the runner files.

## Impact

- `switchyard/scripts/start-worker.sh`: per-role fields, `--resume`, the reviewer's split pane on Herdr.
- `switchyard/scripts/end-worker.sh`: optional role argument, ending every live agent, closing the split pane.
- `switchyard/scripts/test_state.py`: tests for the above.
- `switchyard/SKILL.md`: Per issue steps 5 to 7, Act on the verdict.
- `switchyard/roles/implementer.md`: Fix rounds paragraph.
- `switchyard/runners/herdr.md`, `switchyard/runners/headless.md`.
- `README.md`: the role table row and step 8, which say a fix round starts a fresh implementer.
- `CHANGELOG.md`: one line under Unreleased.
- Pending answers: `switchyard/routing.md` (codex Later turns) and the "Each phase starts a fresh session" paragraph in `SKILL.md`'s Size section are outside the owned paths.
- `switchyard/scripts/state.py`: no change expected. `state.py set` already accepts any field name.
