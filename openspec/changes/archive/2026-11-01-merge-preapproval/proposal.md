# Proposal

Delivers GitHub issue #113.

## Why

Each merge waits for a per-PR approval in the coordinator conversation. On #106 to #109 a PR spent 2 to 5 hours open to merge, longer than the agent work that produced it. A maintainer who trusts a batch has no way to approve it once, up front.

## What Changes

- The maintainer may pre-approve a batch's merges in the coordinator conversation by naming the condition, for example reviewer pass and green CI.
- The pre-approval is explicit, covers that batch only, and the maintainer can withdraw it. Without one, every merge still waits for explicit per-PR approval.
- With a pre-approval, when the repo allows auto-merge (`gh api repos/{owner}/{repo} --jq .allow_auto_merge`), the coordinator merges with `gh pr merge <pr> --squash --auto`, so the merge lands when CI finishes. When the repo does not allow auto-merge, the coordinator waits for CI and merges.
- Each `gh pr merge` runs as its own command, not chained with a CI wait or another merge.
- The Coordinator section's approval sentence and the approval wording in Merge and clean up change. `CHANGELOG.md` and `README.md` get one line each.

## Capabilities

### New Capabilities

None. `openspec/specs/` is empty and this repo sets `skip_specs: true` on every change.

### Modified Capabilities

None.

## Impact

- `switchyard/SKILL.md`: the Coordinator section's approval sentence, and the approval wording at the start of Merge and clean up plus one added mechanics paragraph there.
- `CHANGELOG.md`: one line under Unreleased, in `### Changed`.
- `README.md`: one appended sentence where pre-approval makes the flow's text incomplete.
- No script, test, routing, or spec change. The Several PRs section and the rebase list under Merge and clean up stay untouched: #121 edits those in parallel.
