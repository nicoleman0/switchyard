# Design

No behavioural decisions. Each fix is the smallest edit that removes the wrong claim, in the files' own style.

## Decisions

### 1. Rewrite the claim, not the structure

Each spot keeps its line and its neighbours. The edits:

- `roles/implementer.md` line 1: "You implement one change. Its plan and decisions are settled unless the fast path at the end applies." The rest of the paragraph stays. Fast-path readers land on the paragraph at the end, which tells them to plan first.
- `README.md` bullet "Planning and building are separate sessions": title gains "usually", and the body names the `small` exception with the same words step 6 already uses ("stops after the plan only when it has questions").
- `README.md` "at three points": "before work starts, after the plan when there is one, and at the merge". The pre-approval sentence stays, since step 9's ask stays optional.
- `SKILL.md` "Each phase starts a fresh session": "A phase starts a fresh session unless a rule says to resume one." The resume rules in the sentences after it stay.

### 2. Leave summaries that describe the full path alone

`README.md` line 26 ("a planner writes a spec change, an implementer builds it"), role table rows, and the skill's description describe the ordinary path, and README step 6 already carves out the `small` exception. #130 names only the two sentences above; widening would overlap #134's parallel SKILL.md edits and the "say nothing new" rule.

Alternative: reword every planner mention to "(on the ordinary path a planner)". Rejected: noisy, and the brief allows fixing wrong sentences only.

`skip_specs: true` (reasons in the proposal).
