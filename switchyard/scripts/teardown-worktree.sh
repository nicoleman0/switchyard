#!/usr/bin/env bash
# Run the down hook, then remove an issue's worktree and branches.
# Ordinary teardown refuses a dirty worktree; --abandon reports what it discards.
# Usage: teardown-worktree.sh [--abandon] <issue-number> <branch>
set -euo pipefail

abandon=
while [ "${1:-}" = --abandon ]; do
  abandon=1
  shift
done
case ${1:-} in
  -*)
    echo "Unknown option $1. Usage: teardown-worktree.sh [--abandon] <issue-number> <branch>" >&2
    exit 2
    ;;
esac

issue=${1:?issue number required}
branch=${2:?branch name required}
[ $# -eq 2 ] || { echo "Usage: teardown-worktree.sh [--abandon] <issue-number> <branch>" >&2; exit 2; }
repo=$(git rev-parse --show-toplevel)
cd "$repo"
hook=switchyard/hooks/worktree-down.sh
record="$repo/.switchyard/state/$issue.json"

if [ -f "$record" ]; then
  recorded_branch=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("branch", ""))' "$record")
  if [ "$recorded_branch" != "$branch" ]; then
    echo "Issue $issue records branch $recorded_branch, not $branch." >&2
    exit 1
  fi
  record_path=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("path", ""))' "$record")
else
  record_path=
fi

entry_path=$(git worktree list --porcelain | awk -v ref="branch refs/heads/$branch" '
  /^worktree / { path = substr($0, 10) }
  $0 == ref { print path }')
path=${entry_path:-$record_path}
worktree_present=
if [ -n "$entry_path" ] && [ -d "$entry_path" ]; then
  worktree_present=1
else
  echo "Skipped: worktree for $branch is already gone."
fi

local_present=
if git show-ref --verify --quiet "refs/heads/$branch"; then
  local_present=1
else
  echo "Skipped: local branch $branch is already gone."
fi

if [ -n "$worktree_present" ] && [ -z "$abandon" ] && [ -n "$(git -C "$path" status --porcelain)" ]; then
  git -C "$path" status --short >&2
  echo "Worktree $path has uncommitted changes. Use --abandon to discard them." >&2
  exit 1
fi

if [ -n "$abandon" ]; then
  echo "Abandoning issue $issue. About to discard:"
  if [ -n "$worktree_present" ]; then
    echo "Uncommitted files in $path:"
    git -C "$path" status --short
  else
    echo "Worktree folder is gone."
  fi
  if [ -n "$local_present" ]; then
    echo "Commits on $branch that no remote branch has:"
    git log --oneline "$branch" --not --remotes
  else
    echo "Local branch is gone."
  fi
fi

if [ -x "$hook" ]; then
  ISSUE=$issue BRANCH=$branch WORKTREE=$path MAIN_CHECKOUT=$repo "$hook"
fi

removed=()
if [ -n "$worktree_present" ]; then
  workspace=
  if [ "${HERDR_ENV:-}" = 1 ]; then
    workspace=$(herdr worktree list --cwd "$repo" | python3 -c '
import json, sys
rows = json.load(sys.stdin)["result"]["worktrees"]
print(next((r.get("open_workspace_id") or "" for r in rows if r["branch"] == sys.argv[1]), ""))' "$branch")
  fi
  if [ -n "$workspace" ]; then
    if [ -n "$abandon" ]; then
      herdr worktree remove --workspace "$workspace" --force >/dev/null
    else
      herdr worktree remove --workspace "$workspace" >/dev/null
    fi
  elif [ -n "$abandon" ]; then
    git worktree remove --force "$path"
  else
    git worktree remove "$path"
  fi
  removed+=("worktree $path")
elif [ -n "$entry_path" ]; then
  git worktree remove "$entry_path"
  removed+=("stale worktree entry $entry_path")
fi

if [ -n "$local_present" ]; then
  git branch -D "$branch"
  removed+=("local branch $branch")
fi

remote_branch_state() {
  git ls-remote --exit-code --heads origin "$1" >/dev/null
}

push_failed=
if remote_branch_state "$branch"; then
  if ! git push origin --delete "$branch"; then
    if remote_branch_state "$branch"; then
      push_failed=exists
    elif [ $? -ne 2 ]; then
      push_failed=unknown
    fi
  else
    removed+=("remote branch $branch")
  fi
else
  status=$?
  if [ "$status" -eq 2 ]; then
    echo "Skipped: remote branch $branch is already gone."
  else
    exit "$status"
  fi
fi

python3 switchyard/scripts/state.py rm "$issue"
if [ -n "$push_failed" ]; then
  if [ "$push_failed" = exists ]; then
    echo "Failed to delete remote branch $branch on origin: it still exists." >&2
  else
    echo "Failed to delete remote branch $branch on origin: could not confirm it is gone." >&2
  fi
  exit 1
fi
if [ "${#removed[@]}" -gt 0 ]; then
  printf 'Removed %s.\n' "$(IFS=', '; echo "${removed[*]}")"
else
  echo "Removed issue $issue record."
fi
