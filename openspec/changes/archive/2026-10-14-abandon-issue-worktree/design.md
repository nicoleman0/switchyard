# Design

## Context

`teardown-worktree.sh` currently runs the down hook before removing the checkout. Git refuses normal removal when a worktree contains modified or untracked files. The script supports both `git worktree remove` and Herdr's `herdr worktree remove --workspace` paths.

The coordinator ran the Herdr scratch check from the main checkout on Herdr 2026-10-14, on a worktree holding an untracked file and a modified tracked file:

- `herdr worktree remove --workspace <id>` exits 1 with `{"error":{"code":"dirty_worktree_requires_force","message":"fatal: '<path>' contains modified or untracked files, use --force to delete it"}}`.
- `herdr worktree remove --workspace <id> --force` exits 0, prints `{"result":{"forced":true,...,"type":"worktree_removed"}}`, removes the checkout, and keeps the local branch. `git branch -D` is still needed afterwards, which the script already does.

## Goals / Non-Goals

**Goals:**

- Refuse ordinary teardown before side effects when the checkout has uncommitted files.
- Make abandonment report all discarded files and local-only commits, then complete teardown on both runners.

**Non-Goals:**

- Change normal teardown behavior for clean worktrees or the existing remote-delete failure handling.

## Decisions

- Resolve the worktree and inspect it before running the down hook. This keeps a refused teardown side-effect free.
- In `--abandon` mode, print `git status --short` and `git log --oneline <branch> --not --remotes` before invoking the hook. This includes untracked files and commits absent from all remote refs.
- Use forced removal only for explicit abandonment. Pass `--force` to Herdr's remove command and `--force` to `git worktree remove` so both runners discard the checkout. The scratch check above confirms both work on a dirty worktree.
- Treat `--abandon` as non-interactive consent, as required by the coordinator's headless use.
- Parse options before the positionals and accept only `--abandon`; any other option gets a clear usage message and a non-zero exit.
- Herdr worktrees are not created from the worker checkout, so the Herdr removal path is tested with a stub, as the other Herdr tests do.

## Behaviour

The tests in `scripts/test_state.py` are the acceptance check.

1. Ordinary teardown preserves dirty work. The script detects modified, staged, and untracked files before running the down hook or making any other teardown change. When the worktree is dirty it stops with a message that directs the coordinator to `--abandon`.
2. Abandonment reports discarded work. With `--abandon` the script prints the worktree's `git status --short` output, including untracked files, and the commits on the issue branch no remote branch reaches, before it runs the down hook or removes anything. It never prompts; passing the flag is the consent.
3. Abandonment removes issue resources. After reporting and running the down hook, it removes the worktree with `--force` on both runners, the local branch, the remote branch when present, and the issue state record. The existing remote-delete failure handling and the record removal stay as they are.

## Risks / Trade-offs

- [A long branch history can produce a large report] → Print only commits reachable from the local issue branch but absent from all remote refs.

## Migration Plan

No migration is needed. Existing clean worktrees keep the ordinary teardown path; coordinators use `--abandon` only when they intend to discard local work.
