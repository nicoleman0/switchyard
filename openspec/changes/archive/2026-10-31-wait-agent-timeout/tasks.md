# Tasks

## 1. The wait script

- [x] 1.1 In `switchyard/scripts/wait-agents.sh`, parse `--timeout <seconds>` and `--timeout=<seconds>` out of the arguments into an `agents` array, rebuild the positional parameters as design.md decision 4 describes, and reject a non-positive or non-numeric timeout with status `2`. Without the flag the loop is unchanged. Verify: `wait-agents.sh --timeout` alone exits `2` with the usage line on stderr, and `wait-agents.sh` with no arguments loops as before on a real `herdr agent list`.
- [x] 1.2 Add the timeout check in the loop's still-working branch: when the wait has reached the timeout, print one `name status elapsed` line per watched agent still working, elapsed in seconds from script start as design.md decision 2 describes, and exit `4`. Verify: against a scratch `herdr agent list` with a stubbed `herdr`, or by running with `--timeout 1` against a busy real agent, the run prints the report line and exits `4`.
- [x] 1.3 Update the script's usage comment for the flag, the statuses table it implies, and the one-clause bound on the elapsed number. Verify: shellcheck exits `0`, and the comment keeps its current brevity.
- [x] 1.4 Run the whole script once with no `--timeout` against real Herdr agents whose states include one that has finished, and confirm the pre-change behaviour: same print format, same statuses.

## 2. Runner and skill text

- [x] 2.1 In `switchyard/runners/herdr.md`, add the flag to the Wait row and add one sentence to the `wait-agents.sh` paragraph naming status `4` and the report line format. Verify: no existing sentence is reworded.
- [x] 2.2 In `switchyard/SKILL.md`, extend step 6, Watch, with two or three lines in the existing style: on timeout, read each still-working agent's pane, then nudge, end, or reassign it. Verify: no other step or section is touched.

## 3. Repository checks

- [x] 3.1 Run `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` and confirm it exits `0`.
- [x] 3.2 Run `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` and record the counts.
- [x] 3.3 Run `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` and confirm it exits `0`.
- [x] 3.4 Run `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` and confirm it exits `0`.
- [x] 3.5 Run `npx --yes @fission-ai/openspec validate --all --strict` and confirm it exits `0`.

## Workflow follow-up

- [x] `Change: openspec/changes/wait-agent-timeout` added as the first line of issue #123 at plan time, before implementation.
- [x] Archive the change under `openspec/changes/archive/2026-10-31-wait-agent-timeout` in the PR that completes it.
