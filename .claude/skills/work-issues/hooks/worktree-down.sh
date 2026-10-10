#!/usr/bin/env bash
# Project hook: remove what worktree-up.sh created outside the worktree, such as
# databases, containers, and caches. Runs from the main checkout before the
# worktree is removed, with ISSUE, BRANCH, WORKTREE, and MAIN_CHECKOUT set.
set -euo pipefail
