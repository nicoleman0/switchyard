# Design

## Context

See `proposal.md` for motivation and scope. `routing.md` already gives Claude worker rows `--model` and `--effort` flags. Claude Code 2.1.300 `--help` confirms `--model <model>` and `--effort <level>` for the current session. It does not document interactive slash commands, so this change will document the verified startup flags only.

The headless runner already directs each turn's output to `.claude/turns/<role>-<n>.log`. The Claude coordinator note currently waits for a foreground command; Claude Code stops a foreground shell command after 10 minutes, and an implementer turn can run longer. Claude Code's Bash tool has a background mode (`run_in_background`) that re-invokes the session when the background command exits. PR #48 records the #41 OpenCode proof and its `--auto` worktree result.

## Goals / Non-Goals

**Goals:**

- Keep provider-specific behavior in the Claude coordinator note and generic long-command guidance in the headless runner.
- Reuse the runner's per-turn logs and existing routing table values.
- Link the archived proof description to durable PR evidence.

**Non-Goals:**

- Change runner scripts, updater behavior, README content, or shared skill behavior.
- Add a product spec for project-owned workflow documentation.

## Decisions

- Have Claude coordinators run each headless worker turn in the background with the Bash tool's background mode (`run_in_background`), and when Claude Code reports that the command exited, read the newest log in that worktree's `.claude/turns/` directory. Do not tell the coordinator to poll with follow-up commands. This addresses the 10-minute foreground timeout while preserving the per-turn log convention. Do not add a runner script for this documentation fix.
- Add one provider-neutral headless instruction: if the coordinator harness stops long foreground commands, run the turn in the background and read its log when it exits. Keep waiting mechanics specific to each coordinator note.
- Tell Claude coordinators to set the values from the `claude` row of the Coordinator table at startup with `claude --model <model> --effort <level>`, in one sentence. These exact options and value forms appear in the installed `claude --help`; the help does not establish slash-command syntax.
- Update the OpenCode note with the #41 result: the proof's `--auto` session set up the worktree, wrote the brief, and started the planner, so with `--auto` the worktrees needed no extra setup. Keep the claim scoped to the proof and keep the note's `Not tried` lines.
- Replace the ignored `.claude/answers/proof.md` reference in the archived design with PR #48, which records the proof.
- Declare `skip_specs: true`. The issue changes copied workflow documentation and its examples, and no existing capability spec describes this documentation. Adding a spec would invent a product requirement.
- Add the changelog line under `### Fixed` in Unreleased, keeping the Added, Changed, Fixed order. It tells existing projects to update their own Claude coordinator note because the updater does not change `routing.md`.

## Risks / Trade-offs

- [A background turn may outlive the coordinator's shell command] → Claude Code re-invokes the session when a background command exits, so the coordinator reads the per-turn log then; do not poll with follow-up commands.
- [A future Claude Code release may change model or effort options] → The notes use the CLI's documented flags and project-selected table values; verify them with `claude --help` when updating the note.
- [The worktree proof may be generalized beyond its scope] → State only the observed `--auto` result from PR #48.

## Migration Plan

No runtime migration. Existing projects must update their own `routing.md` Claude note, because the updater does not replace that project-owned file. The changelog will call this out.

## Open Questions

None. The maintainer's decisions in issue #47 settle the four requested changes.
