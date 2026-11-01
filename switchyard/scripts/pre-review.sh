#!/usr/bin/env bash
# Run the cheap checks on an issue's worktree before a reviewer starts.
# Check the tree, scope, plan or OpenSpec archive, and project checks. All run.
# Exit 0 if none failed, 1 if one did, 2 if the gate cannot run. Log: <worktree>/.switchyard/checks/<n>.log
# Usage: pre-review.sh <issue>
set -uo pipefail

issue=${1:-}
[ -n "$issue" ] || { echo "usage: pre-review.sh <issue>" >&2; exit 2; }
scripts="$(cd "$(dirname "$0")" && pwd)"
main=$(git -C "$scripts" worktree list --porcelain | sed -n '1s/^worktree //p')
[ -n "$main" ] || { echo "Issue $issue: cannot find the main checkout" >&2; exit 2; }
state() { (cd "$main" && python3 "$scripts/state.py" get "$issue" "$1"); }
path=$(state path) || exit 2
branch=$(state branch) || exit 2
[ -d "$path" ] || { echo "Issue $issue: worktree $path is missing" >&2; exit 2; }

dir="$path/.switchyard/checks"
mkdir -p "$dir"
n=1
for f in "$dir"/*.log; do
  [ -e "$f" ] || continue
  num=$(basename "$f" .log)
  case "$num" in '' | *[!0-9]*) continue ;; esac
  [ "$num" -ge "$n" ] && n=$((num + 1))
done
log="$dir/$n.log"
: >"$log"

failed=0
# step <name> <command...>: run in the worktree, log everything, print one status line.
step() {
  local name=$1 code
  shift
  printf '== %s\n' "$name" >>"$log"
  (cd "$path" && "$@") >>"$log" 2>&1
  code=$?
  printf 'exit %s\n\n' "$code" >>"$log"
  if [ "$code" -eq 0 ]; then
    echo "PASS $name"
  else
    echo "FAIL $name"
    failed=1
  fi
}
skip() {
  printf '== %s\nskipped: %s\n\n' "$1" "$2" >>"$log"
  echo "SKIP $1: $2"
}

# shellcheck disable=SC2317,SC2329 # called through step
clean_tree() {
  local dirty
  dirty=$(git status --porcelain --untracked-files=no)
  [ -z "$dirty" ] || { echo "Uncommitted tracked changes:"; echo "$dirty"; return 1; }
}
step "clean tree" clean_tree
step scope "$scripts/check-scope.sh" "$issue"
# shellcheck disable=SC2317,SC2329 # called through step
archived() {
  local open
  open=$(find openspec/changes -mindepth 1 -maxdepth 1 -type d ! -name archive 2>/dev/null)
  [ -z "$open" ] || { echo "Changes not archived:"; echo "$open"; return 1; }
}
# shellcheck disable=SC2317,SC2329 # called through step
plan_complete() {
  python3 - <<'PY'
from pathlib import Path
import re
import sys

plan = Path(".switchyard/plan.md")
if not plan.is_file():
    sys.exit("Missing .switchyard/plan.md")
pending = [f"{number}: {line}" for number, line in enumerate(plan.read_text().splitlines(), 1)
           if re.match(r"^\s*- \[ \]", line)]
if pending:
    sys.exit("Unfinished plan tasks:\n" + "\n".join(pending))
PY
}
if [ -d "$main/openspec" ]; then
  step "change archived" archived
  step openspec npx --yes @fission-ai/openspec validate --all --strict
else
  skip "change archived" "plain mode: no openspec/ in main checkout"
  skip openspec "plain mode: no openspec/ in main checkout"
  step plan plan_complete
fi

hook="$main/switchyard/hooks/checks.sh"
if [ ! -e "$hook" ]; then
  skip "project checks" "no switchyard/hooks/checks.sh"
elif [ ! -x "$hook" ]; then
  printf '== project checks\n%s is not executable\nexit 1\n\n' "$hook" >>"$log"
  echo "FAIL project checks"
  failed=1
else
  digits=${issue%b}
  step "project checks" env ISSUE="$digits" CANDIDATE="${issue#"$digits"}" BRANCH="$branch" WORKTREE="$path" MAIN_CHECKOUT="$main" "$hook"
fi

echo "Log: $log"
exit "$failed"
