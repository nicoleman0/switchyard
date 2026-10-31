# Design

## 1. Exit status picks

The script's outcomes and statuses after this change:

| Outcome | Status |
|---|---|
| A watched agent needs the coordinator | `0` |
| Unknown name, or `herdr agent list` failed | the underlying status, `1` |
| Usage error: `--timeout` missing or not a positive number | `2` |
| Loop still working (no timeout set, or not reached yet) | `3` |
| Timeout reached: report printed, wait given up | `4` |

`3` stays as the loop's internal status and the status callers see only if the script is killed or the check is misused, as before. `4` is one clear branch condition for the coordinator. `2` is conventional usage-error status and keeps `4` meaning only one thing.

## 2. What elapsed time measures

`herdr agent list` returns no start timestamp (checked on 2026-10-31: the agent objects carry `agent_status`, `state_change_seq`, `completion_seq`, but no time fields). Options:

- Measure from when `wait-agents.sh` started. Simple, honest, under-reports if the coordinator starts the wait late.
- Track per agent the first poll that showed it working. Same or smaller span than script start, since the first poll happens seconds after start, and more code.

The script's only caller starts the wait right after starting the worker, and the fix-round flow reuses the script the same way, so option 1's span is within seconds of the agent's working time. Take option 1, and the report line says only the seconds. The proposal states the bound; the usage comment in the script repeats it in one clause.

## 3. Time range guard

A non-numeric or negative `--timeout` exits `2` with a one-line stderr message before any polling. Zero is rejected: a zero timeout would mean "never wait", which the coordinator has today by not calling the script. Shell arithmetic `date +%s` differences give whole seconds, so fractions are not accepted. That keeps the check `[ "$timeout" -gt 0 ] 2>/dev/null` and no float parsing.

## 4. Argument placement and empty names

Names are currently passed through as `"$@"`. The flag can appear anywhere without touching that contract:

- Parse known flags first, into `timeout` and an `agents` array, leaving names in `agents`.
- Rebuild the positional parameters with `set --` from `agents` so the embedded python keeps reading `"$@"` exactly as before. With no names this is an empty `"$@"`, which stays correct under `set -u` in the macOS-bundled bash 3.2, unlike an empty array expansion.
- Unknown flags fall into `agents` and surface as the existing `No such Herdr agent` error. That matches the current script, where any stray word is treated as a name.

## 5. CHANGELOG.md

`CONTRIBUTING.md` says to add a changelog line when a change would be noticed by a user of the template. This one would be. But the brief for this issue lists the owned paths exactly, and the implementer role forbids editing anything outside them without asking. The line is left out; the PR body records the decision under Decisions to review.
