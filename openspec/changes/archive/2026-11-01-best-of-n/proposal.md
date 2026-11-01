# Proposal

Delivers GitHub issue #120.

## Why

A large issue gets one implementer. When that attempt misses, the fix round stays on the same approach. Two implementers on different providers, building the same reviewed change, give the reviewer a choice. It costs about twice the implementer usage, so it runs only when the maintainer names it for an issue.

## What Changes

- Best-of-N: an opt-in flow for one issue. The default flow does not change.
- The issue's worktree, record, and branch are candidate a. Candidate b gets record key `<issue>b`, branch `<branch>-b`, and its own worktree off candidate a's branch.
- `state.py` accepts a key of digits with an optional `b` suffix. `status` sorts `120` before `120b` before `121`.
- `setup-worktree.sh <issue>b <branch>-b` requires the record `<issue>`. It branches from that record's branch, copies the open change under `openspec/changes/` and `.switchyard/answers/` from candidate a's worktree, copies `owned`, and records `candidate_of=<issue>`.
- `setup-worktree.sh`, `teardown-worktree.sh`, and `pre-review.sh` give project hooks `ISSUE` as digits only and a new `CANDIDATE` variable: `b` for candidate b, empty otherwise. Existing hooks see no change on ordinary issues.
- `switchyard/SKILL.md`: a new Best-of-N section, and one pointer from Per issue step 5.
- `switchyard/roles/reviewer.md`: one paragraph for a comparison review. The reviewer reads both diffs against the change, writes one review for the kept candidate, and names it on a `Keep:` line with reasons.
- After the pick, the loser is abandoned with `teardown-worktree.sh --abandon`. Fix rounds run on the kept candidate only, under its own key and branch.
- CHANGELOG: one line under Unreleased, Added.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty in this repo and every change sets `skip_specs: true`.

### Modified Capabilities

None.

## Impact

- `switchyard/scripts/state.py`, `setup-worktree.sh`, `teardown-worktree.sh`, `pre-review.sh`, with tests in `test_state.py` and `test_pre_review.py`.
- `switchyard/SKILL.md`: new Best-of-N section and one sentence in Per issue step 5.
- `switchyard/roles/reviewer.md`: one appended paragraph.
- `CHANGELOG.md`: one line.
- `switchyard/scripts/merge-queue.py` accepts `<issue>b` keys with `state.py`'s pattern.
- Shared, approved in answer 1: the shipped `switchyard/hooks/worktree-up.sh`, `worktree-down.sh`, and `checks.sh` headers, and the up hook's port line.
- Meets in-flight work: #114 (warm fix rounds, `end-worker.sh <issue> <role>`, reviewer split pane), #121 (`merge-queue.py` rejects non-digit keys), #124 (`state.py`), #118 (question queue). See design.md, Decision 10.
- Not changed: `roles/implementer.md`, `roles/planner.md`, `brief-template.md`, `routing.md`, `start-worker.sh`, `end-worker.sh`, README.
