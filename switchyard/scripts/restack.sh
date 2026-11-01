#!/usr/bin/env bash
# Replay a child's commits after its parent merges, then retarget its PR.
# Run from the main checkout. Usage: restack.sh <issue>
set -euo pipefail

issue=${1:?issue key required}
[ $# -eq 1 ] || { echo "Usage: restack.sh <issue>" >&2; exit 2; }
repo=$(git rev-parse --show-toplevel)
cd "$repo"
state=switchyard/scripts/state.py
if ! parent_head=$(python3 "$state" get "$issue" parent_head); then
  echo "Issue $issue has no parent_head to restack." >&2
  exit 2
fi
path=$(python3 "$state" get "$issue" path)
branch=$(python3 "$state" get "$issue" branch)
parent_branch=$(python3 "$state" get "$issue" parent_branch)
if [ "$(git -C "$path" symbolic-ref --short HEAD)" != "$branch" ]; then
  echo "Worktree $path must have $branch checked out." >&2
  exit 1
fi
if [ -n "$(git -C "$path" status --porcelain)" ]; then
  echo "Worktree $path has uncommitted changes." >&2
  exit 1
fi
if [ -d "$(git -C "$path" rev-parse --git-path rebase-merge)" ] ||
   [ -d "$(git -C "$path" rev-parse --git-path rebase-apply)" ]; then
  echo "Worktree $path already has a rebase in progress." >&2
  exit 1
fi

if ! git -C "$path" merge-base --is-ancestor "$parent_head" HEAD; then
  echo "Issue $issue no longer descends from parent_head. If already rebased, finish the push, PR retarget, and parent field update manually." >&2
  exit 1
fi

git fetch origin
if ! git -C "$path" rebase --onto origin/main "$parent_head"; then
  echo "Restack from $parent_branch failed. Conflicted files:" >&2
  git -C "$path" diff --name-only --diff-filter=U >&2
  git -C "$path" rebase --abort
  echo "Rebase aborted. Resolve the restack manually, then push, retarget the PR, and clear the parent fields." >&2
  exit 1
fi
if git ls-remote --exit-code --heads origin "refs/heads/$branch" >/dev/null; then
  git push --force-with-lease origin "$branch"
else
  status=$?
  [ "$status" -eq 2 ] || exit "$status"
fi
pr=$(gh pr list --head "$branch" --state open --json number --limit 1 --jq '.[0].number // empty')
if [ -n "$pr" ]; then
  gh pr edit "$branch" --base main
fi
python3 "$state" set "$issue" parent= parent_branch= parent_head=
