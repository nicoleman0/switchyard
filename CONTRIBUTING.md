# Contributing

Switchyard is a template, so every file here is copied into new projects. Keep changes small and generic. Nothing should assume a stack.

## Design principles

Judge a change by these.

- Anyone can adopt it. A stranger with another provider, operating system, or repository can use the change without editing a file the updater owns.
- No provider is special. Planner, implementer, and reviewer run on any provider the project lists. The skill and the scripts do not name a provider where a project-owned file can.
- The project chooses its models. Shipped values are examples, not recommendations. The maintainer's word comes first. The order of choice is in the Routing section of `switchyard/SKILL.md`.
- Prefer a stated default over a refusal. Fail hard only when a batch cannot run at all, such as a missing `git` or a signed-out `gh`.
- What a project changes lives in files the project owns. The updater never replaces them.

## Report a problem or propose a change

Open an issue that states the problem. Keep it short. For a larger change, wait for a reply before you write code.

## Send a pull request

- One problem per PR.
- Follow the Writing section of `AGENTS.md` in commits, PR bodies, docs, and comments.
- CI must pass. The checks are the steps in `.github/workflows/switchyard.yml`, and each one runs locally as written.
- Add a line under Unreleased in `CHANGELOG.md` when someone using the template would notice the change.
- If you change `switchyard/`, say how you tested it: which runner and which providers.

PRs are squash-merged.
