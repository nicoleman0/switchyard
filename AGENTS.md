# Working in this repository

## Workflow

- Use the GitHub issues as the source of truth for implementation breakdown. Milestones are optional. With them, they set the delivery order. Without them, the order is the one the maintainer names the issues in.
- Product behaviour lives in `openspec/specs/`. Change it through an OpenSpec change in `openspec/changes/` (`/opsx:propose`, `/opsx:apply`, `/opsx:archive`), exactly one change per GitHub issue. If work is too big for one PR, split the issue, not the change. Archive the change in the PR that completes it.
- New work: open a short GitHub issue (the problem, and a milestone if the project uses them) first, then propose a change that names it. After proposing, add `Change: openspec/changes/<name>` as the first line of the issue body with `gh issue edit`. Use `/opsx:explore` while an idea is still vague. Acceptance criteria live in the change's scenarios and tasks; the issue links to the change instead of repeating them.
- Deliver issues with the `work-issues` skill (`switchyard/`). The coordinator session plans the work and reviews it. A planner agent proposes each change and an implementer agent builds it, in its own worktree. The skill holds the roles and routing rules. `switchyard/routing.md` is the project's file for providers, models, effort, flags, and commands.
- A session asked to deliver issues is the coordinator when it can read `AGENTS.md` and run the skill's scripts: read `switchyard/SKILL.md` and follow it.
- For issues delivered through `work-issues`, always make an OpenSpec change. When no observable behaviour changes, such as bugs where code diverges from the spec, tooling, infrastructure, or refactors, set `skip_specs: true` in its `.openspec.yaml`. A hand-made PR outside the skill may use an issue and PR with no change.
- Run `npx @fission-ai/openspec validate --all --strict` when specs or changes are edited.

## Project

Replace this section with your project's rules. Agents read it on every task.

- Checks: list every command that must pass before a PR, such as lint, typecheck, tests, and build.
- Shared services: name what must be running in the main checkout, and the command that starts it.
- Conventions: package managers, lockfiles, migrations, module boundaries.
- Never commit: `.env`, credentials, real customer data.

## Writing

These apply to commits, PR bodies, issues, docs, and code comments.

- Use plain, short sentences.
- No AI attribution: no "Generated with" footers and no co-author trailers for an assistant.
- No em-dashes.
- Comments say why, not what.
