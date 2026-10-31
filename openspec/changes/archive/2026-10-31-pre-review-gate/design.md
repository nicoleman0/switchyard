# Design

## Context

- Check commands live as prose today: the Project section of `AGENTS.md` (still the placeholder in this repo) and the brief. A script cannot run prose. This repo's real list is the steps in `.github/workflows/switchyard.yml`.
- `check-scope.sh <issue>` reads the record with `state.py`, diffs `origin/main...HEAD` in the worktree, and exits 1 when a file falls outside `owned`. The coordinator runs it again in Open the PR, step 1, and rules on each listed file there.
- `state.py` finds the main checkout as the first entry of `git worktree list`. Records live there.
- Hooks under `switchyard/hooks/` run from the main checkout with `ISSUE`, `BRANCH`, `WORKTREE`, and `MAIN_CHECKOUT` set. `setup-worktree.sh` runs `worktree-up.sh` only when it is executable.
- The updater treats only `switchyard/routing.md` as project-owned. The hooks are 3-way merged like any other file.
- The implementer role's Fix rounds paragraph is keyed on `.switchyard/reviews/` existing. A gate failure on the first round has no review file.

## Goals / Non-Goals

**Goals:**
- One command the coordinator runs before every review, with one exit code to act on.
- A failure report an implementer reads from disk.
- One project-owned file that holds the check commands.

**Non-Goals:**
- Changing the reviewer role or its verdict rules (#115).
- Resuming the implementer session for fix rounds (#114). The gate fix round starts a fresh session, as review fix rounds do today.
- Pointing `AGENTS.md`, the brief template, or the roles at the hook. That is a follow-up once the hook exists.
- Timeouts for hung checks (#123 covers stuck workers, not this).

## Decisions

### The hook is `switchyard/hooks/checks.sh`, project-owned

Alternatives: parse a command list from `AGENTS.md` (fragile, prose); a list in `routing.md` (that file is about providers, and mixing concerns makes both harder to change); a non-owned hook merged by the updater (a project edit would conflict on every release that touches it).

The hook joins `PROJECT_OWNED`. Install adds it when missing. Update adds it to a project that lacks it and never touches an existing copy.

The shipped hook runs the Switchyard file checks from `switchyard.yml`: `py_compile`, the `unittest` suite, `shellcheck`, and `node --check`. These hold in every project that has `switchyard/`, so the shipped default is useful, not a stub. It leaves out OpenSpec validation (the gate runs it) and the release-only steps (`if: github.repository == ...` in CI). A short comment says to add the project's own checks below.

The hook runs every command, prints a header line before each, and exits 1 if any failed. It does not use `set -e` for the check lines, so one failure does not hide the next.

### The gate runs the main checkout's hook, in the worktree

Same as `worktree-up.sh`: the hook comes from the main checkout, at `<main>/switchyard/hooks/checks.sh`. Its working directory is the worktree, with `ISSUE`, `BRANCH`, `WORKTREE`, and `MAIN_CHECKOUT` set.

A branch cannot weaken its own gate this way. The cost: an issue that changes `checks.sh` is gated by the old copy until it merges. The reviewer still runs every check.

Missing hook: the step prints `SKIP project checks: no switchyard/hooks/checks.sh` and does not fail. A stated default over a refusal. A hook that exists but is not executable is a `FAIL`, since that is almost always a mistake.

### Step order and what each step checks

1. Clean tree: `git -C <worktree> status --porcelain` is empty. `.switchyard/` is ignored, so it does not count. The review reads the commit, so the gate must test the commit and nothing else.
2. Scope: `check-scope.sh <issue>`.
3. OpenSpec: `npx --yes @fission-ai/openspec validate --all --strict` in the worktree. `--yes` keeps `npx` from prompting.
4. Project checks: the hook.

Cheap steps first. Every step runs even after one fails, so one log lists every failure and the fix round fixes them together.

### Output and exit codes

- Log: `<worktree>/.switchyard/checks/<n>.log`, where `<n>` is one more than the highest number there, starting at 1. Same rule as `.switchyard/reviews/`. Each step's full stdout and stderr follow a `== <step>` header, then its exit status.
- Stdout: one `PASS <step>`, `FAIL <step>`, or `SKIP <step>: <reason>` line per step, then `Log: <path>`.
- Exit 0: no step failed. Exit 1: at least one step failed. Exit 2: the gate could not run (no issue argument, no record, worktree path missing). The coordinator sends exit 1 to the implementer and handles exit 2 itself.

The main checkout and the record come from `state.py`, so the script runs from the main checkout or any worktree, as `check-scope.sh` does.

### SKILL.md step 7

Append to step 7, before the reviewer starts:

- Run `scripts/pre-review.sh <issue>`.
- Exit 1 with only the scope step failed: rule on each listed file as in Open the PR, step 1. Accept a file by adding it to `owned` with `state.py set` and run the gate again. Send anything else back as below.
- Any other exit 1: start a new implementer session on the same row, record `implementer_row`, and prompt: `Read switchyard/roles/implementer.md, then .switchyard/brief.md, .switchyard/answers/, and the newest file in .switchyard/checks/, and fix the failed checks for issue #<issue>. The change is already built: follow the Fix rounds paragraph with that log in place of a review.` Then run step 7 again.
- Two failed gate runs in a row: stop and bring the log to the maintainer.
- Gate rounds do not count toward the two `changes requested` rounds in Act on the verdict.

The prompt carries the Fix rounds pointer because the implementer role is shared and keyed on `.switchyard/reviews/`. Editing the role would collide with #114.

### Updater

One line: add `"switchyard/hooks/checks.sh"` to the `PROJECT_OWNED` set. The install and update paths already handle every member the same way, and existing tests cover that for `routing.md`.

## Risks / Trade-offs

- [#122 edits the same `PROJECT_OWNED` line] → The second branch to merge resolves a one-line conflict by keeping both entries. `union-resolve.py` does not apply to Python; the coordinator resolves it by hand.
- [Shipped hook needs `shellcheck`, which preflight does not check] → A missing tool fails the hook with `command not found` in the log. The coordinator reads the summary before starting a fix round and fixes the environment instead. Adding `shellcheck` to preflight is out of scope.
- [Two homes for check commands: `AGENTS.md` prose and the hook] → The hook becomes the runnable one. Pointing `AGENTS.md` and the brief at it is a follow-up.
- [The reviewer reruns the same checks] → Kept. #115 owns the reviewer role; it can read the passing log later.
- [Adding accepted files to `owned` changes what the record says the issue owns] → That is what the coordinator ruled, and Open the PR step 1 then passes without asking twice.
