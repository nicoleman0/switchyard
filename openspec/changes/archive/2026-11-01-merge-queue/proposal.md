# Proposal

Delivers GitHub issue #121.

## Why

With several PRs open, the coordinator merges them one at a time by hand: rebase onto `origin/main`, resolve the append-only conflicts, run the checks, force-push, wait for CI, merge, tear down. Each step is mechanical, and each merge makes the next PR conflict on `CHANGELOG.md`.

## What Changes

- New `switchyard/scripts/merge-queue.py [--merge] [--timeout <seconds>] <issue>...`. For each issue, in the order given, it:
  1. finds the issue's PR by its recorded branch;
  2. tears the issue down and moves on when the PR is already merged;
  3. rebases the worktree onto `origin/main`;
  4. resolves conflicts in `CHANGELOG.md` and `openspec/specs/*/spec.md` with `union-resolve.py`;
  5. runs `pre-review.sh <issue>`;
  6. force-pushes from the main checkout with a lease on the PR's old head;
  7. waits for the PR's checks to appear on the new head, then for them to finish.
- When a PR is ready, it prints the merge command and exits 3. With `--merge`, it merges with `--match-head-commit`, tears the issue down, and goes on to the next.
- It stops on the first conflict or failure it cannot resolve and names the issue, the PR, and the file or step. A stopped rebase is aborted, so the branch is as it was.
- `union-resolve.py`: after the union, a file with a `## [Unreleased]` heading gets its Unreleased subsections merged into one of each, in Keep a Changelog order. This removes the duplicate `### Added` headers a plain union leaves.
- `SKILL.md`: the Several PRs section and the rebase list under Merge and clean up point at the queue.
- CHANGELOG: one line under Unreleased, Added.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty in this repo and every change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- New: `switchyard/scripts/merge-queue.py`, `switchyard/scripts/test_merge_queue.py`, `switchyard/scripts/test_union_resolve.py`.
- `switchyard/scripts/union-resolve.py`: the CHANGELOG step. Plain union behaviour is unchanged for other files.
- `switchyard/SKILL.md`: the Several PRs section and the numbered list under Merge and clean up only. #113 edits the approval wording of Merge and clean up in parallel.
- `CHANGELOG.md`: one line.
- Not changed: `pre-review.sh`, `teardown-worktree.sh`, `README.md` (its line about rebasing the PRs still open stays true), `routing.md`.
