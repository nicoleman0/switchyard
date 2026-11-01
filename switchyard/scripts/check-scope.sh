#!/usr/bin/env bash
# List files an issue's branch changed outside the paths it owns. Exits 1 if any.
# The change's own files under openspec/ are always in scope.
# Usage: check-scope.sh <issue-number>
set -euo pipefail

issue=${1:?issue number required}
state="$(cd "$(dirname "$0")" && pwd)/state.py"
path=$(python3 "$state" get "$issue" path)
owned=$(python3 "$state" get "$issue" owned)
read -r -a prefixes <<<"$owned"

base=$(python3 "$state" get "$issue" parent_head 2>/dev/null) || base=origin/main
changed=$(git -C "$path" diff --name-only "$base...HEAD")

outside=()
while IFS= read -r file; do
  [ -n "$file" ] || continue
  inside=0
  for prefix in openspec/ ${prefixes[@]+"${prefixes[@]}"}; do
    case "$file" in "$prefix"*) inside=1 ;; esac
  done
  [ "$inside" = 1 ] || outside+=("$file")
done <<<"$changed"

if [ "${#outside[@]}" -gt 0 ]; then
  echo "Issue $issue changed files outside its owned paths ($owned):" >&2
  printf '%s\n' "${outside[@]}"
  exit 1
fi
echo "Issue $issue: every changed file is in scope."
