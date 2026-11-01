#!/usr/bin/env bash
# Project hook: give one issue's worktree its own state, so parallel issues share none.
# Runs from the main checkout with ISSUE, CANDIDATE, BRANCH, WORKTREE, and MAIN_CHECKOUT set.
# CANDIDATE is b for a best-of-N issue's second worktree, else empty. Give it its own values.
# Print key=value lines on stdout for the brief. Send everything else to stderr.
set -euo pipefail

# Git-ignored config does not follow a worktree.
if [ -f .env ]; then
  cp .env "$WORKTREE/.env"
fi

# One port per worktree, so dev servers and e2e runs never collide.
if [ "${CANDIDATE:-}" = b ]; then
  printf 'port=4%03d\n' $((ISSUE % 1000))
else
  printf 'port=3%03d\n' $((ISSUE % 1000))
fi

# Add what your stack needs here: a database per issue, dependency install, migrations.
