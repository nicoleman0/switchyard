# Tasks

Start after #93 merges and this branch is rebased on `main`.

## 1. Undo commands

- [x] 1.1 Before the write loop in `update-switchyard.py`, plan the undo entries in loop order, then `VERSION`, as design.md describes. Tracked paths come from one `git --literal-pathspecs ls-files -z` call. Keep every write under the `args.dry_run` guard; verify with `git diff` that no new write sits outside it.
- [x] 1.2 Add one function that turns the started entries into output, filtered by what is on disk now: the `Not undone:` lines, then the blank line, header, and `git restore --`, `rm --`, `rmdir --` lines, paths quoted with `shlex.quote`. Print it after the release notes and `Next:` lines on a real run only. Verify `Already at X` and `--dry-run` print no header.
- [x] 1.3 Put the write loop and the `VERSION` write in a `try` that catches `OSError`, prints the block for the entries started so far (the failing one included), and re-raises, so the existing handler prints the error and returns 2. Verify with the test in 1.6.
- [x] 1.4 Add tests that run the printed commands with `sh -c` and check `git status --porcelain --untracked-files=all` and the directory list match the pre-run state, for: an update with updated, removed, and added files; an `--install` into an empty repo (no directory left behind, and a second `--install` prints the `openspec init` line again); an `--install` over a tracked `AGENTS.md`; an update with `--from` and no `VERSION` (`VERSION` is deleted); and an added path with a space and a single quote. Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`.
- [x] 1.5 Add tests that a conflict run still prints the block and exits 1, and that an untracked file the run merges gets a `Not undone:` line before the header and no command. Verify with the same unittest command.
- [x] 1.6 Add a partial-failure test, skipped when `os.geteuid() == 0`. The release adds `switchyard/a/new.txt` (a new directory), updates tracked `switchyard/b.txt`, and adds `switchyard/z/locked.txt` into an existing tracked directory `switchyard/z/` that the test sets to `0o555` (and restores in cleanup). Assert exit 2, `update-switchyard:` on stderr, `VERSION` unchanged, and a block naming `switchyard/b.txt`, `switchyard/a/new.txt`, and `switchyard/a`, but no `rm` of `switchyard/z/locked.txt`. Run the block with `sh -c`, which must succeed, and check the pre-run state comes back. Verify with the same unittest command.
- [x] 1.7 Update #92's dry-run tests that compare `dry_run.stdout` with `real_run.stdout + b"Dry run: nothing was written.\n"`: compare against the real output cut at the undo header, and assert the dry run has no header. Verify the same files are still reported by running the unittest command.

## 2. Docs

- [x] 2.1 In `README.md`, replace the undo recipe at the end of the install report paragraph ("Add it to an existing repo") and the one in "Take a later release" with one sentence each saying the updater ends by printing the commands that undo the run. Verify with `grep -n "git restore" README.md` returning nothing.
- [x] 2.2 Add `- #95: The updater ends by printing the commands that undo that run.` under Unreleased, Added in `CHANGELOG.md`. Verify the line sits with #93's.

## 3. Repository checks

- [x] 3.1 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` passes.
- [x] 3.2 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 3.3 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 3.4 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 3.5 `npm test --prefix create-switchyard` passes.
- [x] 3.6 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
