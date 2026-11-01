#!/usr/bin/env bash
# End Herdr agents and leave their panes ready for the next command.
# Usage: end-worker.sh <issue> [<role>]
# With no role, end every recorded agent of the issue, reviewer first.
set -euo pipefail

issue=${1:?issue number required}
only_role=${2:-}
script_dir=$(cd "$(dirname "$0")" && pwd)
skill_dir=$(cd "$script_dir/.." && pwd)
state="$script_dir/state.py"
if [ -n "$only_role" ] && [ ! -f "$skill_dir/roles/$only_role.md" ]; then
  echo "Unknown role: $only_role" >&2
  exit 1
fi
runner=$(python3 "$state" get "$issue" runner)
[ "$runner" = herdr ] || { echo "Issue $issue: End is only available on the Herdr runner" >&2; exit 1; }
root_pane=$(python3 "$state" get "$issue" pane)

field() {
  python3 "$state" get "$issue" "$1" 2>/dev/null || true
}

agent_status() {
  python3 -c 'import json,sys; r=json.load(sys.stdin).get("result", {}); a=r.get("agent", r); print(a.get("agent_status", "unknown"))' <<<"$1"
}

end_value() {
  python3 - "$skill_dir/routing.md" "$1" <<'PY' 2>&1
from pathlib import Path
import sys

path, provider = Path(sys.argv[1]), sys.argv[2]
if not path.is_file():
    raise SystemExit(f"routing file is missing: {path}")
lines = path.read_text().splitlines()
table = False
header = None
for line in lines:
    cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
    if not table:
        if "Provider" in cells and "End" in cells:
            header = cells
            table = True
        continue
    if line.lstrip().startswith("|"):
        if all(set(cell) <= set(":- ") for cell in cells):
            continue
        if len(cells) != len(header):
            continue
        row = dict(zip(header, cells))
        if row.get("Provider") == provider:
            value = row.get("End", "").strip()
            if value:
                print(value)
                raise SystemExit(0)
            raise SystemExit(f"End value is empty for provider {provider} in routing.md")
    elif table:
        break
raise SystemExit(f"provider {provider} or Providers table End column is missing in routing.md")
PY
}

# end_agent <name> <provider> <pane>: exits 1 when the agent cannot be ended.
end_agent() {
  local worker=$1 backend=$2 pane=$3 agent_result status="" rc=0 value prompt_result
  agent_result=$(herdr agent get "$worker" 2>&1) || rc=$?
  if [ "$rc" -ne 0 ]; then
    [[ "$agent_result" == *agent_not_found* ]] || { echo "$agent_result" >&2; exit 1; }
  else
    status=$(agent_status "$agent_result")
    case "$status" in
      working|blocked) echo "Issue $issue: $worker is $status; wait for or read the agent before ending it" >&2; exit 1 ;;
    esac
    value=$(end_value "$backend") || { echo "Issue $issue: $value" >&2; exit 1; }
    rc=0
    prompt_result=$(herdr agent prompt "$worker" "$value" 2>&1 >/dev/null) || rc=$?
    if [ "$rc" -ne 0 ] && [[ "$prompt_result" != *agent_not_found* ]]; then
      echo "$prompt_result" >&2
      exit 1
    fi
  fi

  local timeout=${END_WORKER_TIMEOUT_SECONDS:-30} elapsed last_state=${status:-agent_not_found} pane_result shell_pid foreground_pid
  [[ "$timeout" =~ ^[1-9][0-9]*$ ]] || { echo "Issue $issue: END_WORKER_TIMEOUT_SECONDS must be a positive integer" >&2; exit 1; }
  for ((elapsed=0; elapsed<timeout; elapsed++)); do
    rc=0
    agent_result=$(herdr agent get "$worker" 2>&1) || rc=$?
    if [ "$rc" -eq 0 ]; then
      last_state=$(agent_status "$agent_result")
    elif [[ "$agent_result" == *agent_not_found* ]]; then
      pane_result=$(herdr pane process-info --pane "$pane") || { echo "$pane_result" >&2; exit 1; }
      read -r shell_pid foreground_pid < <(python3 -c 'import json,sys; d=json.load(sys.stdin); r=d.get("result", d); r=r.get("process_info", r); print(r["shell_pid"], r["foreground_process_group_id"])' <<<"$pane_result")
      last_state=agent_not_found
      if [ "$shell_pid" = "$foreground_pid" ]; then
        herdr pane send-keys "$pane" ctrl+u >/dev/null 2>&1
        printf 'ended=%s\n' "$worker"
        return 0
      fi
    else
      echo "$agent_result" >&2
      exit 1
    fi
    sleep 1
  done
  echo "Issue $issue: timed out ending $worker; last state: $last_state" >&2
  exit 1
}

if [ -n "$only_role" ]; then roles=("$only_role"); else roles=(reviewer implementer planner); fi
ended=0
if [ -z "$(field planner_pane)" ] && [ -z "$(field implementer_pane)" ]; then
  # Records from before per-role fields name one worker in the root pane.
  worker=$(field worker)
  if [ -n "$worker" ] && { [ -z "$only_role" ] || [ "$only_role" = "$(field role)" ]; }; then
    end_agent "$worker" "$(python3 "$state" get "$issue" backend)" "$root_pane"
    ended=1
  fi
else
  for role in "${roles[@]}"; do
    worker=$(field "${role}_worker")
    pane=$(field "${role}_pane")
    if [ -n "$worker" ]; then
      end_agent "$worker" "$(python3 "$state" get "$issue" "${role}_backend")" "${pane:-$root_pane}"
      ended=1
    fi
    if [ "$role" = reviewer ] && [ -n "$pane" ]; then
      close_result=$(herdr pane close "$pane" 2>&1) \
        || [[ "$close_result" == *pane_not_found* ]] || { echo "$close_result" >&2; exit 1; }
      python3 "$state" set "$issue" reviewer_pane= reviewer_worker=
      printf 'closed=%s\n' "$pane"
      ended=1
    fi
  done
fi
python3 "$state" phase-end "$issue"
[ "$ended" = 1 ] || echo "Issue $issue: there is no agent to end"
