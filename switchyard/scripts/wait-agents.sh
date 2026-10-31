#!/usr/bin/env bash
# Herdr runner only. Block until an agent needs the coordinator, then print its
# name and state.
# Usage: wait-agents.sh [--timeout <seconds>] [agent-name ...]
#      (no names: every named agent)
# Statuses: 0 an agent needs the coordinator, 1 unknown name or failed herdr,
# 2 bad --timeout, 3 not yet, 4 timeout reached.
# With --timeout, the wait ends there and prints each agent still working with
# the seconds since the wait started; a lower bound, because the watch can
# start after the agent did.
set -euo pipefail

timeout=""
agents=()
while [ $# -gt 0 ]; do
  case "$1" in
    --timeout)
      [ $# -ge 2 ] || { echo "$0: --timeout needs a positive number of seconds" >&2; exit 2; }
      timeout="$2"
      shift 2 ;;
    --timeout=*)
      timeout="${1#--timeout=}"
      shift ;;
    *)
      agents+=("$1")
      shift ;;
  esac
done
if [ -n "$timeout" ] && ! [ "$timeout" -gt 0 ] 2>/dev/null; then
  echo "$0: --timeout needs a positive number of seconds" >&2
  exit 2
fi
# Set the names back as positional parameters so the embedded check keeps
# reading "$@"; under set -u on bash 3.2 an empty "$@" is safe, an empty array
# is not.
if [ "${#agents[@]}" -gt 0 ]; then
  set -- "${agents[@]}"
else
  set --
fi
start=$(date +%s)

check='
import json, os, sys

names = set(sys.argv[1:])
agents = [a for a in json.load(sys.stdin)["result"]["agents"] if a.get("name")]
missing = names - {a["name"] for a in agents}
if missing:
    sys.exit(f"No such Herdr agent: {sorted(missing)}")
stopped = [a for a in agents
           if (not names or a["name"] in names)
           and a["agent_status"] in ("idle", "done", "blocked", "unknown")]
for a in stopped:
    print(a["name"], a["agent_status"])
if os.environ.get("WAIT_TIMED_OUT"):
    # A report only exists when the wait timed out; it ends the script.
    if stopped:
        sys.exit(0)
    elapsed = os.environ["WAIT_ELAPSED"]
    working = [a for a in agents
               if (not names or a["name"] in names)
               and a["agent_status"] not in ("idle", "done", "blocked", "unknown")]
    for a in working:
        print(a["name"], a["agent_status"], f"{elapsed}s")
    sys.exit(4)
sys.exit(0 if stopped else 3)'

while true; do
  if herdr agent list | python3 -c "$check" "$@"; then
    exit 0
  else
    status=$?
    # 3: no watched agent needs the coordinator yet.
    [ "$status" -eq 3 ] || exit "$status"
  fi
  if [ -n "$timeout" ]; then
    now=$(date +%s)
    if [ "$((now - start))" -ge "$timeout" ]; then
      export WAIT_TIMED_OUT=1 WAIT_ELAPSED=$((now - start))
      # The result ends the script: 4, or 0 when an agent needs it now.
      herdr agent list | python3 -c "$check" "$@"
      exit 0
    fi
  fi
  sleep 15
done