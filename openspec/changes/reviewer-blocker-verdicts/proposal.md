# Proposal

Delivers GitHub issue #115.

## Why

The reviewer's verdict is `changes requested` when any line in sections 1 to 7 fails, Writing included. A typo in the PR body costs the same fix round as an unmet task: a new implementer session and a new reviewer session. The coordinator may not fix anything itself, so even a one-word fix takes both sessions.

## What Changes

- The reviewer marks each failing line in sections 1 to 7 `Blocker:` or `Note:`. Passing lines say met or pass, with no mark. The sections and their numbers stay as they are.
- A blocker is one of: a scenario or task not met, a check that fails, a scope breach, a security or data-loss problem. Everything else is a note: writing, style, code quality.
- The verdict is `changes requested` only when a line is a blocker. Notes alone give `Verdict: pass`. The first line stays `Verdict: pass` or `Verdict: changes requested`.
- On a later round the reviewer checks that each earlier blocker is fixed.
- The coordinator still never builds an issue. After review it may fix notes and blockers itself when all its fixes together are about 10 changed lines or fewer, code included. It commits them in the worktree, reruns every check in the brief, and records each fix in the PR body's Review section. When it fixes every blocker this way, it opens the PR without another review round.
- Anything larger, or a fix that fails a check, goes to a fix round as today.
- CHANGELOG: one line under Unreleased, Changed (shared file, pending approval).

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty in this repo and every change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- `switchyard/roles/reviewer.md`: the opening paragraph's later-round sentence, section 4, and the verdict rule.
- `switchyard/SKILL.md`: the Coordinator paragraph (opening of Work issues) and the Act on the verdict section only.
- Shared, pending approval: `CHANGELOG.md`, and possibly one sentence of `switchyard/roles/implementer.md`.
- No scripts change. Nothing parses the review file beyond its first line by hand.
