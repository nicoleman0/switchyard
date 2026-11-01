# Proposal

After #116, #114, #115, #117, #113, and #82 a `small` issue plans and builds in one session, fix rounds resume the implementer, and the maintainer can pre-approve merges. Some docs still say every issue stops at a plan and every phase starts fresh.

Issue: #130, milestone Faster delivery.

## Impact

Only doc text changes. No behaviour, no code.

- `switchyard/roles/implementer.md`: line 1 says the plan and its decisions are settled. On the fast path nothing is settled before the implementer plans it.
- `README.md`: "the planner stops at a plan" and "at three points" describe only the full path. A `small` issue is one session, and it has no plan-stop request.
- `switchyard/SKILL.md`: "Each phase starts a fresh session" contradicts the resume rule in its own next sentence.

#130 names these spots. The brief adds: say nothing new, edit only wrong sentences, leave `switchyard/SKILL.md`'s Several PRs and Stacked issues sections to #134.

`skip_specs: true`: docs only, no observable behaviour, and the repo keeps `openspec/specs/` empty.
