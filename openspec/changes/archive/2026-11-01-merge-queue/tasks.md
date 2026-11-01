# Tasks

## 1. CHANGELOG-aware union

- [x] 1.1 In `switchyard/scripts/union-resolve.py`, after the union, merge the `## [Unreleased]` subsections as `design.md` describes: one `### <name>` per name, Keep a Changelog order (Added, Changed, Deprecated, Removed, Fixed, Security), unknown names after in first-seen order, items in their order with upstream first, text before the first `###` kept, released sections untouched. Files without `## [Unreleased]` keep today's output byte for byte. Update the docstring in one or two lines. Verify with 1.2.
- [x] 1.2 Add `switchyard/scripts/test_union_resolve.py`. Cases:
  - a spec file with one two-sided hunk: same output as before this change.
  - a CHANGELOG where both sides add `### Added` with one item each: one `### Added`, upstream item first.
  - both sides add items under Added and one side under Fixed: Added before Fixed, no duplicate heading.
  - an unknown subsection name stays, after the known ones.
  - a released `## [x.y.z]` section below Unreleased is unchanged.
  - a three-sided (`|||||||`) hunk exits non-zero and leaves the file unchanged.
  Verify with `python3 -m unittest switchyard/scripts/test_union_resolve.py` or the discover command in 4.4.

## 2. Merge queue

- [x] 2.1 Add executable `switchyard/scripts/merge-queue.py` as `design.md` describes: arguments `[--merge] [--timeout <seconds>] <issue>...`; records checked up front (exit 2 on a missing one); PR lookup by branch; merged PR torn down and skipped; fetch, clean-tree and head checks; rebase with `merge.conflictStyle=merge` and `rerere.enabled=false`; append-only conflicts resolved with `union-resolve.py`, anything else aborts the rebase and stops naming the files; `pre-review.sh`; lease push from the main checkout, skipped when the head did not change; CI wait in three phases under one timeout, with `SWITCHYARD_POLL_SECONDS`; print the merge command and exit 3, or with `--merge` merge with `--match-head-commit`, confirm `MERGED`, tear down, and continue. Exit codes 0, 1, 2, 3. Header of a few lines with the usage and exit codes, like `wait-agents.sh`. Python 3.10 syntax. Verify with 2.2.
- [x] 2.2 Add `switchyard/scripts/test_merge_queue.py`, built like `test_pre_review.py`: a temp main checkout with a copy of `switchyard/`, a bare origin, worktrees with records, a stub `npx`, a trivial `checks.sh`. Add a stub `gh` on `PATH` that reads PR state from a fixture file, reports `headRefOid` from the bare origin's branch, returns a scripted sequence of check results, logs every call, and on `pr merge` squash-merges the branch into origin `main` and marks the PR merged. Unset `HERDR_ENV`. Set `SWITCHYARD_POLL_SECONDS=0`. Cases:
  - two issues whose branches both append to `CHANGELOG.md` and a spec file, default mode: the first is rebased, pushed, and the run exits 3 with a `gh pr merge <n> --squash --match-head-commit <sha>` line. The CHANGELOG has one `### Added`.
  - run again after the stub merges the first: the first is torn down (no record, no worktree), the second is rebased on the new main and exits 3.
  - `--merge` with both: both merged and torn down, exit 0, and the stub log shows `--match-head-commit` with each pushed head.
  - a conflict in another file: exit 1, the stop names that file, the branch head and worktree are unchanged, nothing pushed.
  - `pre-review.sh` fails (hook exits 1): exit 1, nothing pushed.
  - a failed gate or rejected push after a completed rebase restores the old head for retry. Hook edits survive a failed gate.
  - local head differs from the PR's `headRefOid`: exit 1 before any rebase.
  - checks report none for the first polls, then pending, then pass: the run reaches exit 3.
  - a failing check: exit 1, names the check, no merge call.
  - `--timeout 0` with checks pending: exit 1, says the CI wait ran out.
  - an issue with no record: exit 2, nothing else runs.
  - a rebase that changes nothing: no push call.
  Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`.

## 3. Coordinator and docs

- [x] 3.1 In `switchyard/SKILL.md`, replace the body of the Several PRs section with the queue. Keep it short, imperative, no em-dashes. Cover: run `python3 scripts/merge-queue.py <issue>...` in merge order after ending each issue's worker sessions; what it does in one sentence; exit 3 prints the merge command, which you run on its own after the maintainer approves, then run the queue again with the issues not yet torn down; `--merge` only when the maintainer pre-approved merges for the batch; exit 1 names the file or step, fix it in the worktree, commit, and run the queue again; run it in the background when the CLI limits command time, and `--timeout` bounds the CI wait. Verify with `git diff switchyard/SKILL.md` showing changes in Several PRs only, plus 3.2.
- [x] 3.2 In the Merge and clean up section, replace the `For each PR still open:` line and its numbered list with one line: for each PR still open, run the queue as Several PRs says. Do not touch the paragraph above it. Verify with `git diff switchyard/SKILL.md` showing no other section changed.
- [x] 3.3 Under Unreleased in `CHANGELOG.md`, in `### Added`, append this line. Append only.

  ```
  - #121: `merge-queue.py <issue>...` rebases, checks, pushes, and waits for CI on each passing PR in order, then prints the merge command, or merges with `--merge`. `union-resolve.py` merges a CHANGELOG's Unreleased subsections instead of repeating their headings.
  ```

## 4. Repository checks

- [x] 4.1 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` passes.
- [x] 4.2 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 4.3 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 4.4 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 4.5 `npm test --prefix create-switchyard` passes, after `git fetch --no-tags --depth=1 origin '+refs/tags/v*:refs/tags/v*'`.
- [x] 4.6 `npx @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
