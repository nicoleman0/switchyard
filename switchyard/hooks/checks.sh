#!/usr/bin/env bash
# Project hook: the commands a branch must pass before a reviewer starts.
# Runs from pre-review.sh in the issue's worktree with ISSUE, CANDIDATE, BRANCH, WORKTREE, and MAIN_CHECKOUT
# set, as for worktree-up.sh.
# Exit non-zero to fail the gate. Every command runs, so one log lists every failure.
set -uo pipefail

status=0
run() {
  echo "-- $1"
  shift
  "$@" || status=1
}

run py_compile bash -c "git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile"
run unittest python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'
run shellcheck bash -c "git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck"
run node-check bash -c "git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check"

# Add your project's checks below, as: run <name> <command...>

exit "$status"
