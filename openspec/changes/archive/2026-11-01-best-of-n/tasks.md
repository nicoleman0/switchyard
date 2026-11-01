# Tasks

## 1. Record keys

- [x] 1.1 In `switchyard/scripts/state.py`, a `valid_key` function holds the pattern and `issue_path` accepts `^[0-9]+b?$` (ASCII only) and rejects anything else with "issue key must be digits, optionally followed by b". `status` sorts by the number, then the suffix. Verify with 1.2.
- [x] 1.2 In `switchyard/scripts/test_state.py`, add cases: `120b` works for `init`, `set`, `get`, and `rm`; `120c`, `b`, `120bb`, and `12b0` fail; `status` lists `120`, `120b`, `121` in that order. Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`.
- [x] 1.3 In `switchyard/scripts/merge-queue.py`, check keys with `state.valid_key`. In `test_merge_queue.py`, a `<n>b` key runs and `<n>c` exits 2. Verify with the unittest command in 1.2.

## 2. Candidate setup and hook variables

- [x] 2.1 In `switchyard/scripts/setup-worktree.sh`, as design Decisions 2 and 3 give it: for a key ending in `b`, read record `<issue>` (exit 1 with a clear message when missing), use its branch as the base, copy each folder under its `openspec/changes/` except `archive`, copy its `.switchyard/answers/` when present, and record `owned` and `candidate_of`, plus candidate a's parent fields when it is stacked. Reject `--parent` with a `b` key. Pass the hook `ISSUE=<digits>` and `CANDIDATE=<b or empty>`. Update the usage line. Verify with 2.4.
- [x] 2.2 In `switchyard/scripts/teardown-worktree.sh`, pass the down hook `ISSUE=<digits>` and `CANDIDATE`. Add `--skip-hook`, accepted only with `--abandon`, which skips the down hook. Verify with 2.4.
- [x] 2.3 In `switchyard/scripts/pre-review.sh`, pass the checks hook `ISSUE=<digits>` and `CANDIDATE`. Verify with 2.4.
- [x] 2.4 Tests, in `test_state.py` and `test_pre_review.py`, using their existing temp-repo helpers:
  - `setup-worktree.sh 120b <branch>-b` with no record `120` exits 1 and creates no worktree or record.
  - With record `120` and an untracked change and answers file in its worktree: the new worktree's HEAD equals candidate a's branch head, the change folder and answers file are copied, `archive` is not, and record `120b` has `owned` and `candidate_of=120`.
  - The up hook, down hook, and checks hook see `ISSUE=120` and `CANDIDATE=b` for `120b`, and `ISSUE=120` and an empty `CANDIDATE` for `120`.
  - `teardown-worktree.sh --abandon 120b <branch>-b` removes only candidate b's worktree, branch, and record.
  - With a stacked candidate a, record `120b` has its parent fields, and `--parent` with `120b` exits 1.
  - With a down hook that removes shared state, `--abandon --skip-hook 120b topic-b` removes candidate b's worktree, branch, and record and leaves the state. `--skip-hook` without `--abandon` exits 2.
  Verify with `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'`.

- [x] 2.5 In `switchyard/hooks/worktree-up.sh`, print `port=4<nnn>` when `CANDIDATE` is `b`. Name `CANDIDATE` in the headers of `worktree-up.sh`, `worktree-down.sh`, and `checks.sh`. Verify by running the up hook with `ISSUE=120` and each `CANDIDATE`.

## 3. Coordinator and reviewer text

- [x] 3.1 In `switchyard/SKILL.md`, add a `## Best-of-N` section after Abandon an issue with Decisions 4 to 8 of `design.md` as short steps, and append to Per issue step 5: "When the maintainer named best-of-N for this issue, follow Best-of-N instead." Change no other text. Short imperative sentences, no em-dashes. Verify with `git diff switchyard/SKILL.md`: one appended sentence in step 5 and one new section.
- [x] 3.2 In `switchyard/roles/reviewer.md`, add one paragraph after the paragraph that follows section 9, holding Decision 6. Change no other text. Verify with `git diff switchyard/roles/reviewer.md`.
- [x] 3.3 Under Unreleased in `CHANGELOG.md`, in `### Added`, append this line. Append only.

  ```
  - #120: Best-of-N, opt-in per issue. Two implementers on different providers build the same reviewed change, the reviewer keeps one, and the other is abandoned. Hooks get a `CANDIDATE` variable.
  ```

## 4. Repository checks

- [x] 4.1 `switchyard/hooks/checks.sh` exits 0 from the worktree root.
- [x] 4.2 `npx --yes @fission-ai/openspec validate --all --strict` passes.
- [x] 4.3 `npm test --prefix create-switchyard` passes, after `git fetch --no-tags --depth=1 origin '+refs/tags/v*:refs/tags/v*'`.
