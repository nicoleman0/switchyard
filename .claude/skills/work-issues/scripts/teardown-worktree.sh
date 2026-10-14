#!/usr/bin/env bash
# Run the project's down hook, then remove an issue's worktree and its branch.
# Usage: teardown-worktree.sh <issue-number> <branch>
set -euo pipefail

issue=${1:?issue number required}
branch=${2:?branch name required}
repo=$(git rev-parse --show-toplevel)
cd "$repo"
hook=.claude/skills/work-issues/hooks/worktree-down.sh

path=$(git worktree list --porcelain | awk -v ref="branch refs/heads/$branch" '
  /^worktree / { path = substr($0, 10) }
  $0 == ref { print path }')
[ -n "$path" ] || { echo "No worktree has branch $branch checked out." >&2; exit 1; }

if [ -x "$hook" ]; then
  ISSUE=$issue BRANCH=$branch WORKTREE=$path MAIN_CHECKOUT=$repo "$hook"
fi

workspace=""
if [ "${HERDR_ENV:-}" = 1 ]; then
  workspace=$(herdr worktree list --cwd "$repo" | python3 -c '
import json, sys
rows = json.load(sys.stdin)["result"]["worktrees"]
print(next((r.get("open_workspace_id") or "" for r in rows if r["branch"] == sys.argv[1]), ""))' "$branch")
fi
if [ -n "$workspace" ]; then
  herdr worktree remove --workspace "$workspace" >/dev/null
else
  git worktree remove "$path"
fi

git branch -D "$branch"

# ls-remote --exit-code: 0 when the ref exists, 2 when it is already gone.
remote_branch_state() {
  git ls-remote --exit-code --heads origin "$1" >/dev/null
}

push_failed=
if remote_branch_state "$branch"; then
  if ! git push origin --delete "$branch"; then
    # GitHub may delete the branch between the check and the push, so a
    # rejected push only means failure while the branch is still there.
    if remote_branch_state "$branch"; then
      push_failed=exists
    elif [ $? -ne 2 ]; then
      push_failed=unknown
    fi
  fi
else
  status=$?
  [ "$status" -eq 2 ] || exit "$status"
fi
python3 .claude/skills/work-issues/scripts/state.py rm "$issue"
if [ -n "$push_failed" ]; then
  if [ "$push_failed" = exists ]; then
    echo "Failed to delete remote branch $branch on origin: it still exists." >&2
  else
    echo "Failed to delete remote branch $branch on origin: could not confirm it is gone." >&2
  fi
  exit 1
fi
echo "Removed worktree $path and branch $branch (local and remote)."
