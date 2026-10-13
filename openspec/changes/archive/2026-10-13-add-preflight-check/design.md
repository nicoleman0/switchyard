# Design

## Context

See proposal.md for the motivation. What the code needs today:

- Every entry-point script is bash and calls `python3` (`setup-worktree.sh`, `start-worker.sh`, `state.py`).
- OpenSpec runs through `npx`. Its package declares `engines.node >= 20.19.0` (`npm view @fission-ai/openspec engines`, version 1.14.1).
- `start-worker.sh` accepts the backends `claude`, `codex`, and `opencode`, and refuses a reviewer on `opencode`. The planner runs on the coordinator's backend, which is Claude or Codex.
- `shots.mjs` resolves `@playwright/test` from the package at `SHOTS_PACKAGE_DIR`, or the working directory.
- `compare.py` uses `sips`, then `magick`. It does not try ImageMagick 6's `convert`.
- `codex -p coordinator` layers `$CODEX_HOME/coordinator.config.toml` over the user config (`codex --help`). `CODEX_HOME` defaults to `~/.codex`.
- CI runs shellcheck on every `.sh` in the skill folder and `unittest` on `scripts/test_*.py`. The CI runner has none of the worker CLIs.
- Issues #24, #29, and #31 edit `SKILL.md` and `README.md` in parallel. #24 is moving the routing table and rewriting the Codex coordinator profile section.

## Goals / Non-Goals

**Goals:**
- One command that reports every missing requirement in one run, each with a fix.
- A non-zero exit only when a batch cannot run.
- Tests that pass on a machine with none of the checked tools.

**Non-Goals:**
- The placeholder check on the `AGENTS.md` Project section. That is issue #26.
- The one-provider setup (#27) and platform wording (#31).
- Installing anything, or checking usage windows.
- Checking that shared services are up. "Before starting" step 3 covers it.
- Reading the routing table to learn which providers the project uses.

## Decisions

**The script is bash: `scripts/preflight.sh`.**
Python 3 is one of the requirements, and a Python script cannot report that its own interpreter is missing. The other entry-point scripts are bash too. Alternative: `preflight.py`, with `shutil.which` and an injected PATH. Easier to test, but a missing `python3` would surface as the shell's "command not found".

**It uses only bash builtins and the tools it checks.**
`command -v`, `printf`, and `[ -f ]` do the work. No `grep`, `sed`, or `dirname`. This lets a test run it with a PATH that holds only stubs, so "git is missing" is testable on a machine that has git.

**Every check runs. Nothing exits early.**
The script collects a failure count and exits at the end. `set -u` is on; `set -e` is off, because a failed probe is a result, not an error.

**Output is one line per item on stdout, then a summary line.**

```
ok       git
ok       Python 3
MISSING  GitHub CLI: not signed in. Run: gh auth login
warn     Herdr: not installed. Workers will run headless. See https://herdr.dev
1 missing, 1 warning(s)
```

Each `MISSING` and `warn` line names the item, what is wrong, and one fix. Exit status is 1 when any line is `MISSING`, else 0. Alternative: failures on stderr. Rejected: the coordinator reads one stream, in order.

**Required checks.**

| Item | Probe | Fix printed |
|---|---|---|
| git | `command -v git` | Install Git with your system package manager. |
| Python 3 | `command -v python3` | Install Python 3 from python.org or your system package manager. |
| Node.js | `command -v node` and `command -v npx` | install Node.js, which brings `npx` |
| GitHub CLI | `command -v gh` | install from https://cli.github.com |
| GitHub CLI sign-in | `gh auth status` exits 0, run only when `gh` is found | `gh auth login` |
| Worker CLI | `command -v` on `claude`, `codex`, `opencode` | install Claude Code or Codex; the coordinator and reviewer need one |

The worker check passes when `claude` or `codex` is found. `opencode` alone fails, because the coordinator and reviewer need Claude Code or Codex. See answer 1.

`gh auth status` contacts GitHub, so it also fails with no network. A batch needs the network anyway. Alternative: `gh auth token`, which only checks that a token is stored. See question 2.

Node.js is checked for presence only, with `npx` also required for OpenSpec. No version check is needed. See answer 3.

**Optional checks.**

| Item | Probe | Warning says |
|---|---|---|
| Herdr | `command -v herdr` | workers will run headless |
| Playwright | `node` resolves `@playwright/test` from `SHOTS_PACKAGE_DIR` or the working directory | UI screenshots will not work |
| Image tool | `command -v sips` or `command -v magick` | the comparison page cannot be built |
| Second provider | at least two of `claude`, `codex`, `opencode` found | the reviewer will run on the implementer's provider, with `SWITCHYARD_SAME_PROVIDER=1` |
| Codex profile | `${CODEX_HOME:-$HOME/.codex}/coordinator.config.toml` exists, checked only when `codex` is found | a Codex coordinator needs it; see the skill |

The Playwright probe is skipped with a `warn` when `node` is missing. The image-tool probe does not need Node.js and still runs.

The Playwright probe repeats the resolution rule in `shots.mjs`. Both read `SHOTS_PACKAGE_DIR` and default to the working directory. A comment in each file names the other.

The coordinator runs the script from the main checkout. A project whose `worktree-up.sh` installs dependencies per worktree may have Playwright there and not in the main checkout. The line stays a warning for that reason.

The Codex profile warning names the profile file and points to the skill, without quoting a section heading. #24 is rewriting that section and may rename it.

**The skill gets one paragraph, above the numbered list in "Before starting".**

> Run `scripts/preflight.sh` first. It checks the requirements and says how to fix each missing one. Stop on a non-zero exit and tell the maintainer what is missing. Pass its warnings on. On Codex, run it outside the sandbox, because it calls GitHub.

A paragraph above the list leaves steps 1 to 3 untouched. A new step 1 would renumber three lines that parallel branches may edit.

**The README gets one line at the end of the Requirements list.**

> Check them with `.claude/skills/work-issues/scripts/preflight.sh`.

The Layout block already describes `scripts/` in general terms, and #24 owns it. It does not change.

**Tests live in `scripts/test_preflight.py`.**
Each test builds a temporary directory of stub commands, sets `PATH` to that directory alone, sets `HOME` and `CODEX_HOME` to temporary folders, and runs the script with bash by absolute path. Stubs are `#!/bin/sh` files that use only shell builtins. A stub `gh` and a stub `node` take their exit status from an environment variable. No test needs a real CLI or the network.

## Risks / Trade-offs

- A new requirement must be added in two places, the README and the script. → The README line that names the script sits in the Requirements list, next to the items.
- The script could call a tool that the stub PATH lacks, and pass locally where the real tool exists. → The tests run with a PATH of stubs only, so any such call fails them.
- `gh auth status` fails in a Codex sandbox with no network. → The skill paragraph tells a Codex coordinator to run the script outside the sandbox.
- The Playwright warning is noise for a project with no UI. → It is one line, and it says what it affects.
- #24 may move the Codex profile to another path. → The path is one variable in the script. The coordinator checks it when both branches merge.

## Resolved Answers

1. The worker check passes for `claude` or `codex`; `opencode` alone fails.
2. Use `gh auth status`.
3. Check Node.js for presence only, with `npx` required too.
4. Add one line under Unreleased in `CHANGELOG.md`.
