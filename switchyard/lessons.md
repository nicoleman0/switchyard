# Lessons

This file belongs to the project. The updater adds it when missing and never changes it.

Traps that cost time in a batch, so the next batch does not find them again. The coordinator adds a line after each issue and copies the lines that apply into each brief's coordinator notes.

- One line per trap: the date found, the trap, and what to do instead.
- Group lines under an area heading, such as a provider, a check, or a review finding.
- Delete a line when it no longer applies. This file is not a history.
- When a trap becomes a lasting fact about a provider or a check, move it to `routing.md` or `AGENTS.md` and delete it here.

## Claude Code

- 2026-10-29: Folder trust is per folder. Trusting a parent folder did not cover a new folder under it, so a worker in a new worktree can stop at the trust prompt before its first turn. Enter alone picks "No, exit"; answer with Down then Enter, or start the worker from a trusted folder.

## zsh coordinator

- 2026-10-31: An unquoted `$FLAGS` in zsh is not word-split, so `start-worker.sh ... -- $FLAGS` passes all flags as one argument and the CLI exits. Run multi-flag starts under bash, or use `${=FLAGS}` in zsh.

## Herdr

- 2026-10-31: Each `herdr agent start` waits for readiness, about 30 s on a failure. Start several workers in parallel subshells, not one after another.
