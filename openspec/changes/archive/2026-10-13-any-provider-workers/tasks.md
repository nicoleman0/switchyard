# Tasks

Read `.claude/answers/` first. The design follows the recommended option of each open question. If an answer picks another option, update design.md and these tasks before you start.

## 1. start-worker.sh

- [x] 1.1 In `scripts/test_state.py`, add stub commands `claude`, `codex`, `opencode`, and `pi` to the harness bin folder, so the tests do not depend on installed CLIs. Verify: the suite still passes before any script change, on a `PATH` without the real CLIs.
- [x] 1.2 Change the tests to the new behaviour, and watch them fail:
  - a provider that is not a command on `PATH` fails, names the provider on stderr, and leaves the record unchanged;
  - a name with an uppercase letter or a slash fails the same way;
  - headless starts on `claude`, `codex`, `opencode`, and `pi` each record a 36-character lowercase UUID as `session` and an empty `worker`;
  - two starts on one provider record different sessions;
  - on Herdr, a start without `--turns` calls `herdr agent start <role>-<issue> --kind <provider> --pane <pane> -- <flags>` for `pi` as it does for `claude`;
  - on Herdr, a start with `--turns` calls no `herdr agent start`, records a session, and prints `pane=` and `session=`;
  - `--turns` on the headless runner succeeds;
  - a reviewer on `opencode` after an implementer on `claude` succeeds;
  - a reviewer on `opencode` after an implementer on `opencode` fails without `SWITCHYARD_SAME_PROVIDER=1` and succeeds with it;
  - a start with no `routing.md` succeeds. Remove `test_start_without_routing_file_fails_without_mutating_record`.
- [x] 1.3 Change `scripts/start-worker.sh` as design.md describes: the provider check, `--turns`, one session id per turns start, and the three removals. Update the usage comment. Keep the order of checks, so no failure changes the record. Verify: the tests from 1.2 pass, and `grep -n "claude\|codex\|opencode\|routing.md" scripts/start-worker.sh` prints nothing.

## 2. preflight.sh

- [x] 2.1 Change `scripts/test_preflight.py` first:
  - `Coordinator CLI` passes with `claude` or `codex` and is `MISSING` with neither, including when only `opencode` or `pi` is installed;
  - with no arguments, the output has the `Worker providers: none named` warning and no `Second provider` line;
  - a named provider that is installed prints `ok       Provider <name>`, and one that is not prints a `warn` line;
  - names given and none installed prints the `Worker providers` warning and still exits 0 when the coordinator CLI is found;
  - one installed prints the `Second provider` warning with "not independent", and two print `ok       Second provider`;
  - a fifth name, such as `aider`, is checked like the others;
  - the count test still expects 5 missing with nothing installed;
  - the full-pass test passes `claude codex` and expects no warning.
- [x] 2.2 Change `scripts/preflight.sh` to match design.md. Use only builtins. Verify: the tests pass, and running it here with `claude codex opencode pi` exits 0.

## 3. routing.md

- [x] 3.1 Rewrite the header as in design.md. Remove the "Supported worker providers" sentence. Verify: the header says the values are examples and that the maintainer's word wins.
- [x] 3.2 Remove only the versioned model IDs from the Codex and opencode Workers rows; keep all other flags, effort values, and Claude aliases. Add the three empty pi rows last in each role's group with `when named`. Do not reorder the existing rows.
- [x] 3.3 Add the Providers section with the table from design.md and the provider notes, including how to pin a model for each CLI. Move the Codex notes from `runners/headless.md` and `runners/herdr.md`; phrase later-turn guidance so it covers rows without a pinned model. Move the usage facts from `SKILL.md`. Verify: every fact in the removed runner sections appears once in `routing.md`.
- [x] 3.4 Leave the Codex Coordinator Model cell empty and say under the table that an empty Model cell means the CLI's own default. Change the closing line so it does not say "recommends".

## 4. SKILL.md and the runners

- [x] 4.1 Rewrite the Routing section as design.md describes: the order of precedence once, then the row rules. Keep the fresh-session paragraph, the no-push paragraph, and the escalation paragraph's last sentence. Verify: `grep -n -i "never choose\|opencode\|codex's\|claude's" SKILL.md` shows no line in Routing, and the section no longer tells the coordinator to stop for a missing file or row.
- [x] 4.2 Change the frontmatter description and the preflight paragraph. In the Codex coordinator profile instructions, omit the `model` TOML line when the Coordinator Model cell is empty. Verify: the description names no provider as the implementer's.
- [x] 4.3 Rewrite `runners/headless.md` as design.md describes. Verify: it names no worker CLI command, and it says where `<flags>`, `<session>`, and `<prompt>` come from for every provider.
- [x] 4.4 Rewrite `runners/herdr.md` as design.md describes. Verify: it has both Start commands, the End cell, the "Providers that run as turns" section with the `TURN-DONE-<issue>-<turn>` marker, and no provider section.
- [x] 4.5 Walk the Routing rules against four copies of `routing.md`: as shipped, only `claude` rows, only `pi` rows with the Use cells cleared, and no file. For each, write down the planner, the implementer, the reviewer, and whether the override is set. Verify: each rule gives one answer with no edit to the skill. Put the four walk-throughs in the PR body under Decisions to review.
- [x] 4.6 Change the one line in each of `roles/reviewer.md`, `roles/implementer.md`, and `brief-template.md` that says the reviewer or the implementer is on another provider. Do not touch `.claude/agents/`.
- [x] 4.7 Add "`CONTRIBUTING.md` if the repo has one" to the reading list in `roles/planner.md` and `roles/reviewer.md`. Verify: neither file names a Switchyard principle.

## 5. Docs

- [x] 5.1 Update `README.md` at the places design.md lists. Use the intro and the "Several providers share the load" wording from design.md as reviewed, and keep line 12 word for word. Then "Who does what", Requirements with the one-provider bullet, Runners, "Planning and building are separate sessions", "Make it yours", and Layout. Add no new section. Leave the badges. Verify: `grep -n -i "claude, codex, \(and\|or\) opencode\|recommend" README.md` shows no line that limits workers to three providers or recommends a model. The Herdr "(recommended)" label stays.
- [x] 5.2 Update the `routing.md` line in `AGENTS.md`.
- [x] 5.3 Add the "Design principles" section to `CONTRIBUTING.md` after the opening paragraph, with the wording from design.md as reviewed. Leave the opening paragraph and the other sections as they are. Verify: the order of precedence is spelled out in `SKILL.md` only, and `CONTRIBUTING.md` points to it.
- [x] 5.4 Correct the Unreleased #36 sentence about the opencode example model. Add lines under Unreleased for the provider workflow and for projects updating from 0.5.0: Codex and opencode rows use CLI defaults until a project pins a model using the syntax in `routing.md`. Keep all other existing entries unchanged and do not change `VERSION`.
- [x] 5.5 Verify no versioned model IDs remain in `routing.md`, `SKILL.md`, runner files, `README.md`, or `AGENTS.md`, and released changelog history keeps its model names.

## 6. End to end

- [x] 6.1 Run one real headless pi turn from the worktree using `--model ollama/qwen3.5:9b-32k` on the command line, not in the shipped row. Use a read-only prompt that asks which file `planner.md` tells it to read first, then ask a later turn to repeat its answer. Verify: the second turn shows the first turn's context, and the session file is under `.claude/sessions/`. Quote both turns and say the proof model is not in the shipped row in the PR body. Remove the scratch record afterwards.
- [x] 6.2 Run two OpenCode turns in separate sessions using `--model opencode-go/glm-5.3-flash` on the command line. Verify: the second session does not recall the first. Record the default model's exact failure and both turn results in the PR body. Do not retry another model if either GLM turn fails.
- [x] 6.3 Record the coordinator's successful pi Herdr smoke test in the PR body. Do not start another Herdr agent.
- [x] 6.4 List under Decisions to review in the PR body: the removed `routing.md` check, the removed opencode reviewer refusal, the `command -v` rule and what a typo does, the empty shipped model defaults and unshipped pi proof model, the revised planning/building wording, and the stale description in `.claude/agents/issue-reviewer.md`.

## 7. Repository checks

- [x] 7.1 `git ls-files -z '.claude/skills/work-issues/*.sh' | xargs -0 shellcheck` passes.
- [x] 7.2 `git ls-files -z '.claude/skills/work-issues/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 7.3 `git ls-files -z '.claude/skills/work-issues/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 7.4 `python3 -m unittest discover -s .claude/skills/work-issues/scripts -p 'test_*.py'` passes, with the test count in the PR body.
- [x] 7.5 `npx @fission-ai/openspec validate --all --strict` passes.
