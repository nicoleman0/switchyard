# Contributing

Switchyard is a template, so every file here is copied into new projects. Keep changes small and generic. Nothing should assume a stack.

## Report a problem or propose a change

Open an issue that states the problem. Keep it short. For a larger change, wait for a reply before you write code.

## Send a pull request

- One problem per PR.
- Follow the Writing section of `AGENTS.md` in commits, PR bodies, docs, and comments.
- CI must pass. The checks are the steps in `.github/workflows/ci.yml`, and each one runs locally as written.
- Add a line under Unreleased in `CHANGELOG.md` when someone using the template would notice the change.
- If you change `.claude/skills/work-issues/`, say how you tested it: which runner and which providers.

PRs are squash-merged.
