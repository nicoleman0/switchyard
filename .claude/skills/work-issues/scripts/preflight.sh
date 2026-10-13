#!/usr/bin/env bash
# Check batch requirements before creating a worktree.
set -u

missing=0
warnings=0

required() {
  local name=$1
  local command=$2
  local fix=$3
  if command -v "$command" >/dev/null 2>&1; then
    printf 'ok       %s\n' "$name"
  else
    printf 'MISSING  %s: not installed. %s\n' "$name" "$fix"
    missing=$((missing + 1))
  fi
}

warning() {
  printf 'warn     %s\n' "$1"
  warnings=$((warnings + 1))
}

required git git 'Install Git with your system package manager.'
required 'Python 3' python3 'Install Python 3 from python.org or your system package manager.'

if command -v node >/dev/null 2>&1 && command -v npx >/dev/null 2>&1; then
  printf 'ok       Node.js\n'
else
  printf 'MISSING  Node.js: node and npx are required. Install Node.js.\n'
  missing=$((missing + 1))
fi

if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then
    printf 'ok       GitHub CLI\n'
  else
    printf 'MISSING  GitHub CLI: not signed in. Run: gh auth login\n'
    missing=$((missing + 1))
  fi
else
  printf 'MISSING  GitHub CLI: not installed. Install from https://cli.github.com\n'
  missing=$((missing + 1))
fi

worker_count=0
for cli in claude codex opencode; do
  if command -v "$cli" >/dev/null 2>&1; then
    worker_count=$((worker_count + 1))
  fi
done
if command -v claude >/dev/null 2>&1 || command -v codex >/dev/null 2>&1; then
  printf 'ok       Worker CLI\n'
else
  printf 'MISSING  Worker CLI: Claude Code or Codex is required because the coordinator and reviewer need one. Install Claude Code or Codex.\n'
  missing=$((missing + 1))
fi

if command -v herdr >/dev/null 2>&1; then
  printf 'ok       Herdr\n'
else
  warning 'Herdr: not installed. Workers will run headless. See https://herdr.dev'
fi

if command -v node >/dev/null 2>&1; then
  # Match the package lookup used by shots.mjs.
  if node -e 'require.resolve("@playwright/test", { paths: [process.env.SHOTS_PACKAGE_DIR || "."] })' >/dev/null 2>&1; then
    printf 'ok       Playwright\n'
  else
    warning 'Playwright: @playwright/test not found. UI screenshots will not work.'
  fi
else
  warning 'Playwright: skipped because Node.js is missing. UI screenshots will not work.'
fi

if command -v sips >/dev/null 2>&1 || command -v magick >/dev/null 2>&1; then
  printf 'ok       Image tool\n'
else
  warning 'Image tool: install sips or ImageMagick. The comparison page cannot be built.'
fi

if [ "$worker_count" -ge 2 ]; then
  printf 'ok       Second provider\n'
else
  warning 'Second provider: unavailable. The reviewer will run on the implementer provider with SWITCHYARD_SAME_PROVIDER=1.'
fi

if command -v codex >/dev/null 2>&1; then
  codex_home=${CODEX_HOME:-$HOME/.codex}
  if [ -f "$codex_home/coordinator.config.toml" ]; then
    printf 'ok       Codex coordinator profile\n'
  else
    warning "Codex coordinator profile: missing $codex_home/coordinator.config.toml. See the work-issues skill."
  fi
fi

printf '%s missing, %s warning(s)\n' "$missing" "$warnings"
[ "$missing" -eq 0 ]
