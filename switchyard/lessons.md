# Lessons

This file belongs to the project. The updater adds it when missing and never changes it.

Traps that cost time in a batch, so the next batch does not find them again. The coordinator adds a line after each issue and copies the lines that apply into each brief's coordinator notes.

- One line per trap: the date found, the trap, and what to do instead.
- Group lines under an area heading, such as a provider, a check, or a review finding.
- Delete a line when it no longer applies. This file is not a history.
- When a trap becomes a lasting fact about a provider or a check, move it to `routing.md` or `AGENTS.md` and delete it here.

## Claude Code

- 2026-10-31: The auto-mode classifier refused a background command that chained CI waits and merges, and allowed each `gh pr merge` run as its own command. Run merges one per command.
- 2026-10-29: Folder trust is per folder. Trusting a parent folder did not cover a new folder under it, so a worker in a new worktree can stop at the trust prompt before its first turn. Enter alone picks "No, exit"; answer with Down then Enter, or start the worker from a trusted folder.

## zsh coordinator

- 2026-10-31: An unquoted `$FLAGS` in zsh is not word-split, so `start-worker.sh ... -- $FLAGS` passes all flags as one argument and the CLI exits. Run multi-flag starts under bash, or use `${=FLAGS}` in zsh.

## Herdr

- 2026-11-01: `herdr agent stop` does not end an agent, and a leftover name makes the next start fail with `agent_name_taken`. End agents with `end-worker.sh`.
- 2026-10-31: Each `herdr agent start` waits for readiness, about 30 s on a failure. Start several workers in parallel subshells, not one after another.

## Implementers

- 2026-10-31: Sonnet implementers at low or medium effort twice reported an archive they had not made. `pre-review.sh` catches it; read the gate result, not the report.

## Checks

- 2026-10-31: CI runs an older shellcheck at info severity. Functions called indirectly need `# shellcheck disable=SC2317,SC2329`, and `A && B || C` fails as SC2015. Run `shellcheck -S info` locally.

## Merge queue

- 2026-11-01: Right after a push, GitHub's PR head can lag, so `merge-queue.py` stops on "local head differs". #134 makes it wait; on older copies rerun after a few seconds.
- 2026-11-01: A local commit not yet pushed also stops the queue at the head check. Push first, then run the queue.
