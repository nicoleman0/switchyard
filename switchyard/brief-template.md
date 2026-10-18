# Brief: issue #{issue}

You work on one issue in your own git worktree. A coordinator session reviews the plan and relays questions to the maintainer. A reviewer session checks the commit against the change, on another provider when the project has one. Answers to your questions arrive as files in `.switchyard/answers/`.

- Issue: #{issue}, {title}. Read it with `gh issue view {issue} --comments`.
- Worktree: `{path}`, branch `{branch}`.
- Isolation values: {values}.
- You own: {owned_paths}. Anything else is shared: ask before you change it.
- Milestone for the PR: {milestone, or "none"}.

## Issue notes from the coordinator

{notes}

## Isolation (required)

Shared services run from the main checkout and are already up. Use only the isolation values above for ports, databases, and other per-issue state.
- Never start or stop a shared service. Never touch the main checkout, another worktree, or a port you were not given.
- Stop any dev server you start when you finish.
- Checks: run every check `AGENTS.md` lists, on your own ports.

## Screenshots (UI changes only)

From the worktree root, with the dev server running, run `SHOTS_BASE=http://127.0.0.1:<port> node switchyard/scripts/shots.mjs .switchyard/shots/<before|after>`. The planner takes the before shots and the implementer takes the after shots. `.switchyard/shots/` is git-ignored, and both sessions can read it. Build the comparison page with `switchyard/scripts/compare.py` into `.switchyard/shots/compare.html`; its usage is in the file header.

## Shared files

The `openspec/specs/` files may change in parallel branches. Add your own requirement and never reword existing text, so merges stay trivial.

## PR

Use plain, short sentences. The sections are Changes, Decisions to review, Checks (with real numbers), Review, and Screenshots. Leave Review and Screenshots as "Pending": the coordinator fills them in. Follow the writing rules in `AGENTS.md`.
