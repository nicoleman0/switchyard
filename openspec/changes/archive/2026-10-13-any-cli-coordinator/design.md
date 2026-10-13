# Design

## Context

See `proposal.md` for the problem. The current skill describes a Codex-only coordinator profile, preflight requires `claude` or `codex`, and both runner guides name Codex-specific writable paths. `AGENTS.md` and several README sections also restrict the coordinator to Claude Code or Codex. The existing OpenSpec archive and `CONTRIBUTING.md` establish the project's preference for provider-neutral instructions and project-owned routing.

## Goals / Non-Goals

**Goals:**

- State generic coordinator capabilities in the skill, with CLI-specific setup in `routing.md`.
- Keep maintainer approval as an explicit workflow rule on every CLI.
- Remove provider-specific coordinator gates from preflight.
- Demonstrate the path with an OpenCode coordinator session.

**Non-Goals:**

- Change worker routing or the runner commands used to start workers.
- Change setup, teardown, or scope-check behavior owned by issues #37 and #39.
- Claim support for a coordinator CLI that has not completed the proof.

## What must hold

- Any CLI that reads `AGENTS.md` and can run the skill's scripts can coordinate an issue.
- The skill states the coordinator capabilities; CLI setup lives in the project's `routing.md`.
- The maintainer explicitly approves every merge, regardless of CLI permission prompts.
- Preflight does not require Claude Code or Codex as the coordinator.

## Decisions

### Put generic requirements in the skill and CLI details in routing.md

The skill will say a coordinator must read `AGENTS.md`, run the skill scripts, write to issue worktrees, push from the main checkout, and ask the maintainer before a merge. It will use generic verbs for starting, waiting for, reading, and ending workers. CLI-specific launch, writable-path, permission, and wait behavior will live in the project's `routing.md`, next to the worker provider notes.

The shared skill will say to read the skill path that `AGENTS.md` names; it will not assume the CLI auto-loads `.claude/skills/`. The `AGENTS.md` coordinator sentence will no longer name Claude Code or Codex.

**Alternative considered:** Keep setup in the skill and add an exception for each new CLI. Rejected because every new CLI would require changing shared template instructions.

### Remove the coordinator CLI preflight check

The coordinator is already running when it invokes preflight. Remove the required `claude`/`codex` check and the optional Codex profile warning. Do not parse `routing.md` to discover the coordinator. Keep checks for general tools and named worker providers.

Update `test_preflight.py` so an environment with the general requirements and OpenCode, but no Claude Code or Codex, passes. Remove assertions for the coordinator check and Codex profile check, and update the missing-item count.

**Alternative considered:** Parse the Coordinator table in `routing.md`. Rejected because the running CLI is already known and parsing project-authored Markdown would add a second source of truth.

### Keep merge approval independent of permission prompts

The skill's merge step will state that the coordinator waits for explicit maintainer approval before invoking the merge command. This rule applies even when the CLI can run shell commands without prompting. CLI permission settings are not an approval record.

**Alternative considered:** Rely on each CLI's confirmation prompt. Rejected because some CLIs, including pi, do not provide one.

### Keep the README claims tied to the proof

Change only the approved intro sentence to: “The coordinator runs on any CLI that reads `AGENTS.md` and can run the skill's scripts.” Put that wording in this design for review. Update the other Claude Code/Codex-only claims in “Who does what”, “Requirements”, and “Use it” to use the same eligibility rule. Where documentation lists coordinator CLIs tried, name Claude Code and Codex, and opencode only as “tried in the proof for #41”. The proof task records the coordinator CLI and model that actually ran; it does not make a broader verified-support claim.

### Prove the shortest end-to-end coordinator path

The coordinator of this issue batch runs one real OpenCode coordinator session, using OpenCode's default model on this machine. Use a temporary GitHub scratch issue and a disposable branch. The session must read `AGENTS.md` and the skill, run preflight, create a worktree, write its brief, start one real worker turn, end that worker, and tear down the worktree. Record the OpenCode version/model, worker provider, and the observed results in the PR body. Do not open or merge a PR for the scratch issue. The planner and implementer do not start Herdr agents.

This is the smallest proof that exercises the handoff to a worker and cleanup as well as reading the instructions and running preflight. A scripted imitation would not show that OpenCode can interpret the files and carry out the coordinator steps.

## Risks / Trade-offs

- [A new CLI may need permissions or shell behavior not covered by shipped notes] → Its project can add notes to `routing.md`; the capability statement and proof define the requirements.
- [A CLI may perform merges without prompting] → The skill requires explicit maintainer approval before the merge command on every CLI.
- [A scratch issue or worktree may be left behind if the proof stops early] → Record cleanup as part of the proof, and close the scratch issue after teardown.
- [One OpenCode proof could be read as proof for every CLI] → Name only the CLI actually tried and keep the generic statement conditional on the stated capabilities.

## Migration Plan

No migration is needed. The `routing.md` coordinator table has not shipped in a release. Projects that copy this version can add coordinator notes in their project-owned routing file.

## Open Questions

None. The brief sets the scope, proof CLI, default-model choice, and merge approval rule.
