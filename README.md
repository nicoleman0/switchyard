# Switchyard: an agent coordination framework

![A rail yard where switches sort one wagon onto each of three sidings, each ending at a signal](docs/switchyard.svg)

[![OpenSpec](https://img.shields.io/badge/OpenSpec-1F3A5F)](https://github.com/Fission-AI/OpenSpec)
[![Claude Code](https://img.shields.io/badge/Claude_Code-1F3A5F?logo=claude&logoColor=white)](https://claude.com/product/claude-code)
[![Codex](https://img.shields.io/badge/Codex-1F3A5F)](https://github.com/openai/codex)
[![opencode](https://img.shields.io/badge/opencode-1F3A5F?logo=opencode&logoColor=white)](https://opencode.ai)
[![Herdr](https://img.shields.io/badge/Herdr-1F3A5F)](https://herdr.dev)
[![GitHub CLI](https://img.shields.io/badge/GitHub_CLI-1F3A5F?logo=github&logoColor=white)](https://cli.github.com)

Switchyard is a template repository that was born out of my own personal AI development setup.

Start a new project from it, and the project begins with a delivery workflow for coding agents already in place: issues, specs, isolated worktrees, and review gates.

To adopt it, [start a new project](#start-a-new-project) from the template with one command, or [add the workflow to a repo you already have](#add-it-to-an-existing-repo) with one install command.

It does not depend on one AI provider. Use any agent CLI for the worker roles, and change a provider or a model by editing one file, `switchyard/routing.md`. The values it ships with are examples. The coordinator runs on any CLI that reads `AGENTS.md` and can run the skill's scripts.

It holds no application code. You add your stack on top.

One session coordinates. For each issue, a planner writes a spec change, an implementer builds it, and a reviewer checks it, in a git worktree of its own. The reviewer runs on another provider than the implementer when the project lists more than one. You answer the product questions and approve the merges.

## The workflow

Each piece covers a gap the others leave:

- **Issue, then spec, then code.** Every behaviour change starts as a short GitHub issue, becomes exactly one [OpenSpec](https://github.com/Fission-AI/OpenSpec) change, and ships as one PR. The PR archives the change into `openspec/specs/`, so the specs always describe what the code does.
- **Planning and building are separate sessions.** The planner and implementer can use different effort settings, and the planner stops at a plan. The implementer starts fresh and reads the plan from disk. Its session does not inherit the planner's context.
- **Two reviews, two reviewers.** The coordinator checks the plan before any code is written. A reviewer checks the diff against the change before anything is pushed, on another provider when one is available.
- **Files carry every handoff.** The brief, the answers, the change, and the review live in the worktree. Each session reads them from disk, so no stage works from another session's summary, and the coordinator holds verdicts, not diffs.
- **One worktree per issue.** Each issue gets its own branch, ports, and data. Issues that own different folders run in parallel.
- **Workers never push.** Each worktree's push URL is disabled, and a script lists any file changed outside the paths the issue owns. Nothing reaches the remote until the review passes, and nothing merges until you approve it.
- **Several providers share the load.** Worker roles run on any agent CLI the project lists in `routing.md`, and you choose the models there. Implementers rotate across the listed providers, so one usage window does not stall a batch.

### Who does what

| Role | Where it runs | Does | Never |
|---|---|---|---|
| You | GitHub and the coordinator's chat | Open issues, answer product questions, approve merges | |
| Coordinator | Your session on the main checkout, any CLI that reads `AGENTS.md` and can run the skill's scripts | Splits the work, writes briefs, reviews plans, acts on review verdicts, pushes, opens PRs, merges, cleans up | Implements |
| Planner | The issue's worktree, any provider | Reads the issue and the code, proposes the OpenSpec change, takes before screenshots, lists open questions | Writes code |
| Implementer | The same worktree, fresh session, any provider | Applies the change, runs every check, takes after screenshots, archives the change, commits, writes the PR body | Pushes |
| Reviewer | The same worktree, fresh session, another provider when available | Checks the diff against the change's scenarios and tasks, runs every check, writes a verdict file | Edits code |

### One issue, start to finish

![A sequence diagram drawn as rail tracks, one track per role. You hand the coordinator an issue and answer its questions. The coordinator briefs the planner and brings you the plan's decisions. Build and review repeat until the verdict is pass. You approve the pull request and the coordinator merges.](docs/workflow.svg)

1. **You open an issue.** State the problem. Pick a milestone if the project uses them. Keep it short: acceptance criteria belong in the change, not the issue.
2. **You ask the coordinator to work on it.** It reads the issue against the code and asks you about anything the issue does not settle. With several issues, it splits them by the folders each one owns and runs the independent ones in parallel.
3. **The coordinator sets up.** A script creates the worktree and runs your isolation hook. The coordinator writes a brief there: the issue, the paths it owns, its ports, and the decisions so far.
4. **The planner proposes the change.** It writes the proposal, optional design, and tasks under `openspec/changes/<name>`, plus a spec delta when the change has one. It links the change from the issue and stops with numbered questions, each with options and a recommendation. A change with `skip_specs: true` has no spec delta.
5. **The coordinator reviews the plan.** It checks the plan's claims against the code, answers what it can, and brings you the product decisions. The answers go into a file in the worktree.
6. **The implementer builds it.** A fresh session applies the tasks, runs every check, syncs the spec delta into `openspec/specs/`, archives the change, commits, and writes the PR body. It asks before it decides anything the plan does not cover.
7. **The reviewer checks the diff.** A fresh session, on another provider when available, reads the change and the diff. It checks each scenario and task, scope, tests, duplication, and the screenshots, runs every check, and writes a verdict to a file in the worktree.
8. **The coordinator acts on the verdict.** On a pass it pushes the branch and opens the PR. Otherwise a fresh implementer session reads the review and fixes it, and a new reviewer checks again. After two failed rounds the coordinator brings the findings to you.
9. **You approve.** The coordinator squash-merges, removes the worktree and its branch, and rebases the PRs still open.

You are asked something at three points: before work starts, after the plan, and at the merge.

## Requirements

- macOS or Linux. CI lints and tests the workflow's scripts on `ubuntu-latest`, and the maintainer develops on macOS. Windows is untested. WSL should behave like Linux, but nobody has run it.
- `git`, Python 3, and Node.js (OpenSpec runs through `npx`).
- The [GitHub CLI](https://cli.github.com), signed in.
- Any agent CLI with a worker row in `routing.md`. The coordinator can run on any CLI that reads `AGENTS.md` and can run the skill's scripts; see its note in `routing.md` for setup.
- With one provider, keep only that provider's rows in `routing.md`. The reviewer then runs on the implementer's provider, and the review is not independent.
- Recommended: [Herdr](https://herdr.dev), a terminal workspace manager for coding agents. See [Runners](#runners).
- For UI screenshots: Playwright in your project, and `sips` (macOS) or ImageMagick.
- Check them with `switchyard/scripts/preflight.sh <provider>...`, passing the providers in `routing.md`.

## Start a new project

Click **Use this template** on GitHub, or run:

```sh
gh repo create my-project --template nicoleman0/switchyard --private --clone
cd my-project
python3 switchyard/scripts/init-project.py
```

The new repo has every file here and none of this repo's history. Init moves this guide to `docs/WORKFLOW.md`, fixes its paths, and deletes Switchyard's own files: `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, the banner image, the social preview, and `docs/pixelart.py`. It keeps `docs/workflow.svg`, prints every move, deletion, and skip, and never commits. A committed copy of every moved and deleted file stays in git history: init refuses to run outside a git work tree and skips the listed paths with uncommitted changes. It ends by naming what to add next: your own `README.md` and `LICENSE`, for a start.

Then [make it yours](#make-it-yours) before the first issue.

## Add it to an existing repo

From the root of the repo:

```sh
git clone https://github.com/nicoleman0/switchyard.git ../switchyard
python3 ../switchyard/switchyard/scripts/update-switchyard.py --install
```

The clone beside the repo holds the updater; the default `--source` fetches the release. The command adds every workflow file the repo does not have and merges the ones it does. The merge keeps what the project owns:

- `AGENTS.md` gains the Workflow and Writing sections; a repo without an `AGENTS.md` gets the release's whole file, Project placeholder included.
- `.gitignore` gains the `.switchyard/` line when it is missing.
- `openspec/config.yaml` gains the Switchyard `rules` entries without replacing `context` or the project's own rules.
- `switchyard/routing.md` is added when it is missing and never replaced.

The report lists each file as `added`, `merged`, or `conflict`, then the totals, and writes `VERSION` naming the release. Conflict markers name the two sides. In `AGENTS.md`, `.gitignore`, and `openspec/config.yaml`, they stay inside the owned section or rule list. Any other existing workflow file that differs gets markers around the whole file. Resolve them, review the diff, and commit. To undo before committing: `git restore .`, remove files reported as `added`, and remove `VERSION`.

If the repo has no `openspec/` directory, install prints the next step, `npx @fission-ai/openspec init --tools claude,codex,opencode`; install writes `openspec/config.yaml` first, and init keeps it.

## Make it yours

Init removed the Switchyard-only files and moved the guide. What is left is your project's own files and settings:

| Edit | What goes there |
|---|---|
| `README.md`, `LICENSE` | Add your project's README and license. |
| `CHANGELOG.md`, `docs/workflow.svg` | Start your own changelog. Init kept the workflow chart next to the guide, which now reads it from `workflow.svg`. |
| `CONTRIBUTING.md` | Write your project's contributing guide, or leave it out. |
| `.github/workflows/` | `switchyard.yml` checks the workflow's own files and follows releases. Put your project's checks in a workflow of their own, such as `ci.yml`. |
| `AGENTS.md`, Project section | Your checks, shared services, and conventions. Every agent reads it. Preflight warns while the shipped placeholder is still there. |
| `openspec/config.yaml`, `context` | What the product is and what is out of scope. |
| `switchyard/hooks/worktree-up.sh` and `worktree-down.sh` | Per-issue isolation: ports, a database per issue, dependency install. What `worktree-up.sh` prints lands in each brief. |
| `switchyard/brief-template.md`, Isolation section | Rules every worker must follow, such as how to start a dev server on its own port. |
| `switchyard/scripts/shots.mjs` | The routes to screenshot, if the project has a UI. |
| `switchyard/routing.md` | The Providers table holds each provider's commands. The Workers table holds providers, models, effort, and flags. Shipped values are examples. This file belongs to your project. |

The coordinator's CLI setup belongs in the project's Coordinator notes in `routing.md`.

## Take a later release

Start from a clean checkout on a new branch, then run:

```sh
git switch -c update-switchyard
python3 switchyard/scripts/update-switchyard.py
```

The report lists files as `added`, `updated`, `removed`, `merged`, `conflict`, or `kept`. Review the diff and resolve conflict markers. The updater does not commit. To undo, restore changed and removed files with `git restore .`, remove files reported as added, and remove `VERSION` if the project did not have one before the update.

The updater adds `switchyard/routing.md` when it is missing, then leaves it unchanged in later updates. Review it after it is added.

The updater covers paths listed in its target release. It skips OpenSpec-generated files, which `npx @fission-ai/openspec update` refreshes, and Switchyard's README, license, changelog, contributing guide, and banner. See the [Switchyard releases](https://github.com/nicoleman0/switchyard/releases) for release notes.

The updater clones the release source, so a Codex session needs network access. Run it outside the sandbox if the session cannot access the network.

A repository that never had the workflow at all does not update from a release: it takes [install](#add-it-to-an-existing-repo), which needs no `--from`.

## Use it

1. Create an issue. Add `--milestone` if the project uses milestones:
   ```sh
   gh issue create --title "Password reset emails arrive twice" --body "..."
   ```
2. Start a CLI that reads `AGENTS.md` and can run the skill's scripts from the main checkout. Follow its Coordinator note in `routing.md` for writable worktree paths and session setup.
3. Tell it what to deliver:
   - "Work on issue #12."
   - "Work on #12, #14, and #15."
   - "Run the next steps of milestone M2."
   - "Put #14 on Codex."
4. See the batch with `python3 switchyard/scripts/state.py status`.
5. Answer its questions, review the PR it opens, and tell it to merge.

`AGENTS.md` tells any session asked to deliver issues to act as the coordinator and follow the skill, so there is nothing to invoke by name.

Not everything needs the crew:

- An idea that is still vague: `/opsx:explore`.
- One change you want to drive yourself: `/opsx:propose`, `/opsx:apply`, `/opsx:archive` in a single session.
- Work through the crew that changes no observable behaviour, such as tooling, refactors, or a bug where the code diverges from the spec: use a change with `skip_specs: true`. A hand-made PR outside the crew needs no change.

## Runners

The runner is how the coordinator starts a worker, prompts it, waits for it, and reads its report. The coordinator picks one by checking whether it runs inside Herdr.

| | Herdr (recommended) | Headless |
|---|---|---|
| Needs | Herdr | Nothing beyond the worker CLIs |
| Workers | Interactive agents, one pane per issue | One CLI command per turn, from the Providers table |
| Watching | Live. You can read a pane or type into it. | Each turn's output is logged to `.switchyard/turns/` in the worktree. |
| Worktrees | `~/.herdr/worktrees/<repo>` | `../<repo>.worktrees/<branch>` |

The commands are in `switchyard/runners/`.

## Layout

```
AGENTS.md                        rules every agent reads
CHANGELOG.md                     what changed in each release
CONTRIBUTING.md                  how to contribute to Switchyard
.github/
  workflows/switchyard.yml       checks on the workflow's own files
  ISSUE_TEMPLATE/                the short issue the workflow starts from
openspec/
  config.yaml                    project context and artifact rules
  specs/                         what the product does today
  changes/                       one folder per change in flight, plus archive/
.claude/
  agents/                        Claude role profiles
  skills/work-issues/SKILL.md    Claude Code entry point for the workflow
switchyard/
  SKILL.md                       the coordinator's playbook and routing rules
  routing.md                     project-owned providers, models, effort, flags, and commands
  roles/                         planner, implementer, and reviewer instructions, shared by every provider
  runners/                       Herdr and headless commands
  hooks/                         your per-issue isolation
  brief-template.md              what each worker is told
  scripts/                       batch state, worktree setup and teardown, screenshots, merge helpers
  VERSION                        Switchyard release the workflow files follow
  update-paths.txt               files brought forward by the release updater
.switchyard/                     ignored briefs, answers, reviews, turns, state, sessions, PR bodies, and screenshots
.claude/skills/openspec-*, commands/ generated by OpenSpec
.agents/, .opencode/             the same OpenSpec workflows for Codex and opencode
```

`npx @fission-ai/openspec update` refreshes the generated files.

## License

MIT. See [LICENSE](LICENSE).
