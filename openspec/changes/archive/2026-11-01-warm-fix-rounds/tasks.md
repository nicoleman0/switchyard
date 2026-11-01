# Tasks

## 1. Worker scripts

- [x] 1.1 In `switchyard/scripts/start-worker.sh`, write `<role>_worker`, `<role>_session`, `<role>_backend`, and on Herdr `<role>_pane` with the existing `state.py set` call (design decision 1). Keep the unprefixed fields as they are. Verify: a test starts a planner, then an implementer, and reads both roles' fields from the record.
- [x] 1.2 Add `--resume` to `start-worker.sh` as design decision 2 describes, including the exit 4 and exit 1 cases, the `phase-start`, and the printed handles. Update the usage line. Verify: tests cover a live Herdr agent, `agent_not_found`, a working agent, a headless session, a missing session, and a provider mismatch.
- [x] 1.3 On Herdr, start the reviewer in a split pane (design decision 3), for agent and turns reviewers. Verify: with the stubbed `herdr`, a test sees `pane split <pane> --direction down --cwd <path>`, `reviewer_pane` recorded, `agent start reviewer-<n> ... --pane <new pane>`, and the new pane printed.
- [x] 1.4 In `switchyard/scripts/end-worker.sh`, take an optional role, end every live worker when it is absent, close and clear the reviewer's pane, and run `phase-end` once (design decision 4). Update the usage line. Verify: tests end the reviewer alone while the implementer stays recorded, end both with no role, and keep the existing lifecycle and refusal cases passing.
- [x] 1.5 Confirm `#79` timing still holds: a test runs implementer start, reviewer start, reviewer end, implementer `--resume`, and checks `phases` has four closed or open entries in that order with one open at a time.
- [x] 1.6 Run one real `codex exec` turn in a scratch folder and confirm the output shows the session id and that `codex exec resume <id>` resumes it. Record the exact line in design decision 6. If the id is not printed, use `codex exec --json` and its first event instead, and update the design.

## 2. Workflow text

- [x] 2.1 `switchyard/SKILL.md` step 5: no change unless needed for the role fields. Step 6: the fast path's "prompt the same session" stays. Step 7: when the implementer reports its commit, leave its session running; a gate failure resumes it with `start-worker.sh ... --resume` and the existing prompt, falling back to a fresh session on exit 4. Edit only session wording.
- [x] 2.2 `switchyard/SKILL.md` Act on the verdict: on `changes requested`, end the reviewer with `end-worker.sh <issue> reviewer`, resume the implementer, and fall back to a fresh one on exit 4. Keep the prompt.
- [x] 2.3 `switchyard/roles/implementer.md` Fix rounds: say the change is already built, by this session or an earlier one. Keep the rest.
- [x] 2.4 `switchyard/runners/herdr.md`: the End row takes `[<role>]`; replace the sentence on reused names with the two live names and the reviewer's split pane; add `--resume` to the start rows.
- [x] 2.5 `switchyard/runners/headless.md`: Later turns resume the role's own recorded session; a provider whose First turn has no `<session>` has its id read from the first turn's log and recorded with `state.py set <issue> <role>_session=<id>`; replace the End row's "so does each fix round".
- [x] 2.6 `README.md`: fix the Implementer row in the role table and step 8, which say a fix round uses a fresh implementer. Touch no other line.
- [x] 2.7 `CHANGELOG.md`: one line under Unreleased, Changed, for #114. Tell existing projects to change Codex's Later turns to resume by id.
- [x] 2.8 Apply the answers to questions 1 and 2 (`routing.md` codex row, the Size paragraph in `SKILL.md`) only as answered.

## 3. Checks

- [x] 3.1 Run `switchyard/hooks/checks.sh` from the worktree root and record each check's result and the unittest counts.
- [x] 3.2 Run `npx --yes @fission-ai/openspec validate --all --strict` and confirm it exits 0.

## Workflow follow-up

- [x] `Change: openspec/changes/warm-fix-rounds` added as the first line of issue #114 at plan time.
- [x] Archive the change under `openspec/changes/archive/<date>-warm-fix-rounds` in the PR that completes it.
