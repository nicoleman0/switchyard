# Tasks

## 1. Lessons file

- [x] 1.1 Create `switchyard/lessons.md` with the header from the Format section of `design.md`, word for word, and the seed lines below, as the answer to plan question 1 fixed them.

  ```markdown
  ## Claude Code

  - 2026-10-29: Folder trust is per folder. Trusting a parent folder did not cover a new folder under it, so a worker in a new worktree can stop at the trust prompt before its first turn. Enter alone picks "No, exit"; answer with Down then Enter, or start the worker from a trusted folder.

  ## zsh coordinator

  - 2026-10-31: An unquoted `$FLAGS` in zsh is not word-split, so `start-worker.sh ... -- $FLAGS` passes all flags as one argument and the CLI exits. Run multi-flag starts under bash, or use `${=FLAGS}` in zsh.

  ## Herdr

  - 2026-10-31: Each `herdr agent start` waits for readiness, about 30 s on a failure. Start several workers in parallel subshells, not one after another.
  ```

  No em-dashes. Verify the file has no `<...>` or `{...}` placeholders left; `${=FLAGS}` is shell syntax, not a placeholder.

## 2. Updater

- [x] 2.1 In `switchyard/scripts/update-switchyard.py`, set `PROJECT_OWNED = {"switchyard/routing.md", "switchyard/lessons.md"}`. No other change to the script.
- [x] 2.2 In `switchyard/scripts/test_update_switchyard.py`, add a `LESSONS = "switchyard/lessons.md"` constant and four tests modelled on the routing ones:
  - update: a local edit to the lessons file survives an upstream change to it, and the report has no `updated:` or `added:` line for it;
  - update: a project without the file gets the release's copy, reported `added:`;
  - install: an existing lessons file is kept byte for byte and not named in the report;
  - install: a missing lessons file is added with the release's content.
  Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`.

## 3. SKILL

- [x] 3.1 In `switchyard/SKILL.md`, Per issue step 2, replace the bullet `- any known traps.` with `- any known traps, with the lines from \`switchyard/lessons.md\` that apply to this issue.` Change no other line in the step.
- [x] 3.2 Append this section at the end of `switchyard/SKILL.md`, after Abandon an issue. The last sentence follows the answer to plan question 2:

  ```markdown
  ## Record lessons

  After each teardown, merged or abandoned, update `switchyard/lessons.md` in the main checkout. Add a line for each trap that cost time on that issue, such as a flag a CLI rejected, a check that needed a service, or a review finding that came back. Follow the format in its header. Delete lines that no longer apply. At the end of the batch, commit the file on its own small PR.
  ```

## 4. Shared docs (approved by the answer to plan question 3, lines added only)

- [x] 4.1 `README.md`: next to each place that names `switchyard/routing.md` as project-owned (the install list, Take a later release, the tree), add `switchyard/lessons.md` the same way. Append lines; do not reword existing ones.
- [x] 4.2 `CHANGELOG.md`: under Unreleased, in an `### Added` section, append `- #122: \`switchyard/lessons.md\` carries traps from one batch to the next. The updater adds it when missing and never changes it.`

## 5. Repository checks

- [x] 5.1 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 5.2 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 5.3 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` passes.
- [x] 5.4 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 5.5 `npm test --prefix create-switchyard` passes.
- [x] 5.6 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
