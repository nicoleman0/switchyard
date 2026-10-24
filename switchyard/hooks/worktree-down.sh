#!/usr/bin/env bash
# Project hook: remove what worktree-up.sh created outside the worktree, such as
# databases, containers, and caches. Runs from the main checkout; the worktree
# folder may already be gone. ISSUE, BRANCH, WORKTREE, and MAIN_CHECKOUT are set.
set -euo pipefail
