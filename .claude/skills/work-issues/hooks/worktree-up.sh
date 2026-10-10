#!/usr/bin/env bash
# Project hook: give one issue's worktree its own state, so parallel issues share none.
# Runs from the main checkout with ISSUE, BRANCH, WORKTREE, and MAIN_CHECKOUT set.
# Print key=value lines on stdout for the brief. Send everything else to stderr.
set -euo pipefail

# Git-ignored config does not follow a worktree.
if [ -f .env ]; then
  cp .env "$WORKTREE/.env"
fi

# One port per issue, so dev servers and e2e runs never collide.
printf 'port=3%03d\n' $((ISSUE % 1000))

# Add what your stack needs here: a database per issue, dependency install, migrations.
