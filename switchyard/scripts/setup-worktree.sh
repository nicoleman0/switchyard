#!/usr/bin/env bash
# Create a worktree for one issue, then run the project's up hook to isolate it.
# Inside Herdr the worktree opens as a workspace; otherwise it is a plain git
# worktree beside the checkout.
# Usage: setup-worktree.sh [--parent <issue>] <issue-number> <branch>
set -euo pipefail

parent=
if [ "${1:-}" = --parent ]; then
  parent=${2:?parent issue number required}
  shift 2
fi
case ${1:-} in
  -*) echo "Unknown option $1." >&2; exit 2 ;;
esac
issue=${1:?issue number required}
branch=${2:?branch name required}
[ $# -eq 2 ] || { echo "Usage: setup-worktree.sh [--parent <issue>] <issue-number> <branch>" >&2; exit 2; }
repo=$(git rev-parse --show-toplevel)
cd "$repo"
base=$(git symbolic-ref --short HEAD)
hook=switchyard/hooks/worktree-up.sh
if [ -n "$parent" ]; then
  if [ "$parent" = "$issue" ]; then
    echo "Issue $issue cannot be its own parent." >&2
    exit 1
  fi
  parent_branch=$(python3 switchyard/scripts/state.py get "$parent" branch) || exit 1
  if python3 switchyard/scripts/state.py get "$parent" parent >/dev/null 2>&1; then
    echo "Issue $parent is itself stacked. Only one level is supported." >&2
    exit 1
  fi
  parent_head=$(git rev-parse --verify "refs/heads/$parent_branch^{commit}")
  base=$parent_head
fi

if [ "${HERDR_ENV:-}" = 1 ]; then
  created=$(herdr worktree create --cwd "$repo" --branch "$branch" --base "$base" \
    --label "#$issue $branch" --no-focus)
  read -r path pane workspace < <(python3 -c '
import json, sys
r = json.load(sys.stdin)["result"]["root_pane"]
print(r["cwd"], r["pane_id"], r["workspace_id"])' <<<"$created")
  printf 'path=%s\npane=%s\nworkspace=%s\n' "$path" "$pane" "$workspace"
else
  path="$(dirname "$repo")/$(basename "$repo").worktrees/$branch"
  git worktree add --quiet -b "$branch" "$path" "$base"
  printf 'path=%s\n' "$path"
fi

# Workers never push. Only the main checkout can reach the remote.
git config extensions.worktreeConfig true
git -C "$path" config --worktree remote.origin.pushurl workers-do-not-push

state_args=(init "$issue" "branch=$branch" "path=$path")
if [ -n "$parent" ]; then
  state_args+=("parent=$parent" "parent_branch=$parent_branch" "parent_head=$parent_head")
fi
if [ "${HERDR_ENV:-}" = 1 ]; then
  state_args+=(runner=herdr "pane=$pane")
else
  state_args+=(runner=headless)
fi
python3 switchyard/scripts/state.py "${state_args[@]}"

if [ -x "$hook" ]; then
  ISSUE=$issue BRANCH=$branch WORKTREE=$path MAIN_CHECKOUT=$repo "$hook"
fi
