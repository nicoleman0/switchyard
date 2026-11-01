# Design

## Context

#148 added `tracker.py` with `BACKENDS = {"github": GitHub}`. Each backend validates its own keys and has `view(key)` and `set_change(key, path)`. `tracker.md` is project-owned and found next to the scripts.

Keys are assumed to be digits in:
- `state.py`: `valid_key` (`[0-9]+b?`) and `key_order` (`int(issue.rstrip("b"))`). `merge-queue.py` imports both.
- `setup-worktree.sh`: a `case` that rejects non-digit candidate keys. Non-candidate keys are first checked by `state.py init`, after the worktree exists.
- `start-worker.sh`: Herdr agent name `$role-$issue`.
- `hooks/worktree-up.sh`: `$((ISSUE % 1000))`. With `ISSUE=ENG-123` and `set -u`, bash reads `ENG` as an unset variable and the hook fails.

Other key uses are opaque strings and need no change: `end-worker.sh` reads the stored agent name, `pre-review.sh`, `teardown-worktree.sh`, and `setup-worktree.sh` strip `b` with `${issue%b}`, which works for `ENG-123b`. `state.py review_result` reads review round numbers, not keys.

Herdr 0.9.5, probed locally with a nonexistent pane: `planner-ENG-123` fails with `invalid_agent_name`, "agent name must start with a lowercase letter and contain only lowercase letters, digits, '-' or '_' (1-32 characters)". `planner-eng-123` passes the name check.

## Goals / Non-Goals

**Goals:**
- A Linear project can run every step GitHub projects run today, with PRs on GitHub.
- GitHub projects see no change.

**Non-Goals:**
- Status moves, posting questions, reading answers from comments (#150).
- Delivery order from a Linear project (#151).
- Phase-to-status names in `tracker.md` (#150).

## Decisions

### Linear API

Sources:
- Linear developers, GraphQL page (https://linear.app/developers/graphql): endpoint `https://api.linear.app/graphql`; personal API keys use "header: `Authorization: <API_KEY>`", with no `Bearer` (that form is for OAuth tokens); `issue(id: "BLA-123")` takes the human identifier; errors come in a GraphQL `errors` array and "queries can partially succeed with a 200 HTTP status".
- Linear SDK schema (https://raw.githubusercontent.com/linear/linear/master/packages/sdk/src/schema.graphql): `Issue.identifier`, `title`, `description` (nullable, markdown), `state: WorkflowState!`, `branchName`, `comments(first, after, ...)` returning a connection with `pageInfo { hasNextPage endCursor }`; `Comment.body`, `createdAt`, `user` (nullable for bots and integrations); `IssueUpdateInput.description`; `Query.issue(id: String!)`.

Queries, all with GraphQL variables, never string interpolation:
- view: `issue(id: $id) { identifier title description state { name } comments(first: 100, after: $after) { nodes { body createdAt user { name } } pageInfo { hasNextPage endCursor } } }`. Page until `hasNextPage` is false, then sort comments by `createdAt`. A null `user` prints as `unknown`, like GitHub's missing author.
- set-change: read `issue(id) { id description }`, compute the new description with the same rule as GitHub, then `issueUpdate(id: $id, input: { description: $description }) { success }`. `success: false` exits 1.
- check: `viewer { id }`.

### Shared Change-line rule

The rule that turns a body into one with `Change: <path>` first is the same knowledge for both backends. Move it to one module-level function, `with_change_line(body, path)`, and call it from both. This is a refactor of GitHub's code; do it as its own task, before the Linear backend, with the GitHub tests passing unchanged.

### HTTP transport

`Linear(transport=None)`. The default transport is `graphql_post(url, key)`, a closure over `urllib.request` that POSTs JSON with `Authorization: <key>` and `Content-Type: application/json`, a 30 second timeout, and returns the decoded JSON. On `HTTPError` it reads the body: if it is JSON with `errors`, it returns it so the caller reports the messages; otherwise it raises `TrackerError` with the status. `URLError` and timeouts raise `TrackerError` naming the endpoint. The backend raises `TrackerError` on any `errors` in the response, joining their `message` fields.

Tests inject a fake transport to test the backend's queries and formatting, and run `graphql_post` against a local `http.server` on `127.0.0.1` to test the header, JSON body, error bodies, and a closed port. No endpoint environment variable: the URL is a constant, and the test passes its own URL to `graphql_post`.

`LINEAR_API_KEY` is read when a Linear operation runs, not at load, so `tracker.py` with a bad key still parses arguments and validates keys first. A missing key raises `TrackerError` (exit 1): "LINEAR_API_KEY is not set. Create a personal API key in your Linear settings and export it." The settings path is not named: I could not confirm it from the docs. The key never appears in messages.

### `tracker.py check`

A third subcommand. GitHub's `check` returns at once: preflight already checks `gh auth status`. Linear's runs `viewer { id }`. Exit 0 prints nothing; failure prints the reason on stderr and exits 1.

Alternative: put the Linear call in `preflight.sh` with `curl`. That would put Linear knowledge (endpoint, header form) in a second file, and `curl` is not otherwise required.

Preflight reads the tracker name with `tracker.py` too: `check` prints `<name>` on stdout when it succeeds (`github` or `linear`), so preflight can print `ok       Linear` or stay silent for GitHub. On failure preflight prints `MISSING  Tracker: <stderr>` and counts it as missing. GitHub's `check` succeeding prints `github` and preflight prints nothing new, so GitHub output is unchanged.

### Key forms

| Where | Accepts |
| --- | --- |
| `tracker.py` GitHub | `[0-9]+` |
| `tracker.py` Linear | `[A-Z][A-Z0-9]*-[0-9]+` |
| `state.py valid_key` | `([0-9]+\|[A-Z][A-Z0-9]*-[0-9]+)b?` |

`state.py` accepts both forms whatever the tracker. It guards file names and ordering, not tracker semantics, and reading `tracker.md` there would couple two scripts that are orthogonal today. A wrong-tracker key still fails at `tracker.py view`, which the coordinator runs in Before starting, before any worktree.

Linear's team key rules (length, digits allowed) are not in the docs I found. The pattern allows letters and digits after a leading letter. Lowercase is rejected rather than folded: Linear prints identifiers in uppercase, and one spelling keeps one state file per issue on case-insensitive file systems.

`key_order` returns `(team, number, key)`, with `team = ""` for digits, so numeric keys sort first and by number, as today.

### Early key check in `setup-worktree.sh`

Add `state.py check-key <key>`: exit 0 when valid, else the existing `fail` message and exit 1. `setup-worktree.sh` calls it first, for the issue and for `--parent`, and drops its own digits `case`. One regex, in `state.py`. This also fixes the existing gap where a bad non-candidate key creates a worktree and then fails at `state.py init`.

### Herdr agent names

`start-worker.sh` lowercases the key: `worker="$role-$(printf '%s' "$issue" | tr '[:upper:]' '[:lower:]')"`. Bash 3.2 on macOS has no `${var,,}`. The name is stored in the record as today, so `end-worker.sh` and `--resume` read it back unchanged. Herdr's 32-character limit leaves 20 characters of key after `implementer-`; Herdr's own `invalid_agent_name` error covers a longer key, so no extra check.

### Hook port

`worktree-up.sh` takes the number after the last dash: `number=${ISSUE##*-}`, then `$((10#$number % 1000))`. For digits `${ISSUE##*-}` is the key itself, so GitHub ports do not change. `ENG-123` and `OPS-123` get the same port; a comment in the hook says so. `ISSUE` keeps its meaning, so hooks and `checks.sh` callers need no new variable.

### Branch names

`SKILL.md`, Per issue step 1, gets one sentence: on Linear, start the branch with the lowercased key, such as `eng-123-fix-login`. Linear links a PR whose branch name contains the issue ID (Linear GitHub docs, https://linear.app/docs/github, as summarised in search results; the page itself would not load here). Linear's own generated branch names use the lowercase identifier.

Alternative: a `tracker.py branch <key>` operation printing Linear's `branchName`. Linear's default `branchName` is `<user>/eng-123-title`, which does not start with the key, and it adds an API call per issue. The sentence is smaller.

### Install flag

`update-switchyard.py` gets `--tracker` with `choices=("github", "linear")`, default `None`. A test asserts the choices equal `tracker.BACKENDS` keys, so the two lists cannot drift without a failing test.

On `--install`:
- The target release has no `switchyard/tracker.md`: with `--tracker`, refuse before writing: "`<target>` has no switchyard/tracker.md; --tracker needs a later release."
- `tracker.md` is missing locally: add it with the target's content, the `Tracker:` line replaced by `Tracker: <name>`. Without `--tracker`, the target's content as today.
- `tracker.md` exists locally and names another tracker: keep it and print "Keeping switchyard/tracker.md (Tracker: <old>); edit it to change the tracker."

Without `--install`, `--tracker` prints "Ignoring --tracker: switchyard/tracker.md decides after install.", as `--openspec` does. `--check` refuses `--tracker` like the other install flags.

`create-switchyard.mjs` accepts at most one OpenSpec flag plus `--tracker <name>` or `--tracker=<name>`, in any order, and forwards them. It does not validate the name: the updater's `choices` is the one place. npm swallows `--tracker=linear` given without `--` into `npm_config_tracker`, so use that when no `--tracker` argument is present, as `npm_config_openspec` is used. `npm init switchyard@latest --tracker linear` with a space and no `--` fails inside npm before our code runs (npm 11.19.0, tested locally with `npm exec`), so the README shows the `--` form.

### Docs

- README: a short "Use Linear" section: install flag, `LINEAR_API_KEY`, branch names, PRs on GitHub, Linear's GitHub integration must be connected for PR links.
- `runners/herdr.md`: agent names use the lowercased key.
- CHANGELOG Unreleased, `### Added`: one line for #149.

## Risks / Trade-offs

- [No live Linear call was possible] → Queries follow the published schema and are pinned by tests with a fake transport and a local HTTP server. The PR body says it is untested against live Linear.
- [Two Linear teams' issues with the same number share a hook port] → Comment in the hook; a project with several teams edits its hook.
- [Comment page size or ordering differ from the schema] → Paging and client-side sort by `createdAt` do not depend on the default order.
- [`create-switchyard` tests run against released tags, and no release has `tracker.md` with `linear` yet] → The package test checks forwarding with an invalid name, which fails in the updater's argparse with "invalid choice". The updater's own tests cover writing `Tracker: linear`.

## Migration Plan

No migration. Existing projects keep `Tracker: github` and digit keys. A project switches by editing `tracker.md` and exporting `LINEAR_API_KEY`. A project that changed `worktree-up.sh` keeps its own port line through the updater's merge; it only matters once it switches to Linear.
