# Design

## Context

`tracker.py` has `view`, `set-change`, `set-phase`, `comment`, and `check` on GitHub and Linear (#148 to #150). `Linear.query` sends GraphQL through an injectable transport, and `test_tracker.py` pins queries with `RecordingTransport`. `SKILL.md` Before starting takes the issues the maintainer names; `AGENTS.md` says milestones set the order when the project uses them. No `LINEAR_API_KEY` is available, so nothing here is checked against live Linear.

## Goals / Non-Goals

**Goals:**
- One read-only command prints a Linear project's open issues in a ready-to-run order.
- The mechanical part (paging, filtering, sorting, blockers, cycles) lives in the script, with tests.
- GitHub projects see no change.

**Non-Goals:**
- Listing a GitHub milestone. GitHub keeps "the maintainer names the issues".
- Sub-issue structure. A sub-issue in the project is listed as an issue like any other.
- Checking that the project's teams have the #150 statuses. It needs a states query per team; the first worker start already fails with the team's status list. Left for a later issue if it costs time.
- Accepting a project URL. The maintainer can pass the slug id from it.

## Decisions

### Linear API

From Linear's SDK schema (https://raw.githubusercontent.com/linear/linear/master/packages/sdk/src/schema.graphql, read 2026-11-01):
- `projects(first, after, filter: ProjectFilter): ProjectConnection!`. `ProjectFilter.name` and `slugId` are `StringComparator`, which has `eqIgnoreCase` and `eq`. `ProjectFilter.or` takes a list.
- `project(id: String!): Project!`, documented as "by its identifier or URL slug". `Project.id`, `name`, `slugId`.
- `Project.issues(first, after, filter: IssueFilter): IssueConnection!`. No sort argument; the default page order is `createdAt`.
- `Issue.identifier`, `title`, `sortOrder: Float!` ("Used for manual sorting in list views"), `state: WorkflowState!`, `projectMilestone: ProjectMilestone` (null when the issue has no milestone).
- `ProjectMilestone.name`, `sortOrder: Float!` ("The order of the milestone in relation to other milestones within a project").
- `WorkflowState.name`, `type`: one of `triage`, `backlog`, `unstarted`, `started`, `completed`, `canceled`, `duplicate`.
- `Issue.inverseRelations(first, after): IssueRelationConnection!`. `IssueRelation.issue` is the source, `relatedIssue` the target, and `type` "describes how the source issue relates to" the target: `blocks`, `duplicate`, `related`, `similar`. So the blockers of issue X are X's `inverseRelations` nodes with `type == "blocks"`, and each blocker is the node's `issue`.

Linear limits one query to 10,000 complexity points: 0.1 per property, 1 per object, and each connection multiplies its children by `first` (https://linear.app/developers/rate-limiting).

### Queries

1. Find the project:
   `projects(first: 50, filter: { or: [{ name: { eqIgnoreCase: $name } }, { slugId: { eq: $name } }] }) { nodes { id name slugId } }`.
   - One node: use it.
   - Several: exit 1, one line each `<name> (<slugId>)`, and say to pass the slug id.
   - None: run `projects(first: 250) { nodes { name slugId } pageInfo { hasNextPage } }`. Pick close names with `difflib.get_close_matches` plus names that contain the argument without case. Print them, or every name when none is close, and `and more` when `hasNextPage`. Exit 1.
2. Issues, paged by `$after` until `hasNextPage` is false:
   ```
   project(id: $id) { issues(first: 50, after: $after,
     filter: { state: { type: { nin: ["completed", "canceled", "duplicate"] } } }) {
     nodes { identifier title sortOrder state { name type } projectMilestone { name sortOrder }
       inverseRelations(first: 20) {
         nodes { type issue { identifier state { type } project { id } } }
         pageInfo { hasNextPage endCursor } } }
     pageInfo { hasNextPage endCursor } } }
   ```
   About 93 points per issue, 4,700 per page. `first: 50` on relations would pass 10,000.
3. An issue whose `inverseRelations.pageInfo.hasNextPage` is true gets its remaining relations by `issue(id: $key) { inverseRelations(first: 100, after: $after) { ... } }`, paged the same way `fetch` pages comments.

The state filter runs in Linear, so closed issues cost no pages. The script still treats a returned issue as open only when its state type is not closed, so the filter and the rule have one home: a `CLOSED_TYPES` tuple used in both.

### Order

1. Base order: milestone `sortOrder`, with no milestone last; then issue `sortOrder`; then team key and number, so ties are stable.
2. Blockers per issue: `blocks` relations whose source is not closed. One in the list is an edge; one not in the list is shown as `<key> (outside)`.
3. Emit the first issue in base order whose in-list blockers are all emitted (Kahn's algorithm with the base index as priority). A blocked issue moves after its blocker and nothing else moves.
4. Issues left when none can be emitted are in a cycle or blocked by one. Find a cycle by walking blockers from one left issue and name its members, such as `blocked-by cycle: ENG-2 -> ENG-3 -> ENG-2`. Exit 1 before printing any line.

A blocked issue can end up after issues of a later milestone. Its milestone field still shows its own milestone.

Why `Issue.sortOrder`: it is the only issue order field outside sub-issues and priority. The schema calls it the manual order "in list views". Whether a project view's manual order uses it is not documented; see Risks.

Alternative: print the fields and let the coordinator order them in `SKILL.md`. That puts a graph sort in prose, untested, and each coordinator could do it differently. The coordinator still splits by owned folders and decides when to start each issue.

### Output

```
Project Onboarding (3f2a1b9c8d7e)
ENG-5	Todo	Setup	-	Seed the database
ENG-2	In Progress	Setup	ENG-5	Add the login form
ENG-7	Backlog	-	OPS-9 (outside)	Write the docs
```

Tab-separated with the title last, so a title with any text cannot shift a field. Blockers are comma-separated in base order. One line per issue reads well in a terminal and is easy to parse.

### GitHub

`GitHub.list` raises `TrackerError(..., 2)`: "tracker.py: list reads a Linear project. On GitHub, name the issues; milestones set the order." Exit 2 matches other usage errors that fail before any call. Listing a GitHub milestone would add a second way to order GitHub batches, which the issue does not ask for.

### Key and status

`list` makes calls only after `LINEAR_API_KEY` is read, through the existing `transport()`, so `LINEAR_API_KEY is not set` stays the message on that path.

### SKILL.md

Before starting:
- Step 1: on Linear, when the maintainer names a project, run `python3 scripts/tracker.py list <project>` and read each listed issue with `view`. The batch is the listed issues unless the maintainer narrows it.
- Step 2: take issues in the list's order. An issue with an open blocker in the list starts after that blocker merges, unless the maintainer names the two to stack (Stacked issues). An issue with an `(outside)` blocker waits; tell the maintainer which blocker it waits for. The split by owned folders still applies.

`AGENTS.md` Workflow, delivery-order line: add "On Linear, a named Linear project sets the order." README "Use Linear": one paragraph on `list`. CHANGELOG: one line under Unreleased, Added.

## Risks / Trade-offs

- [No live Linear call] → Queries follow the published schema and are pinned with the fake transport. The PR body says it is untested and lists the fields above.
- [`Issue.sortOrder` may not be the order a project view shows] → The schema has no per-project issue order. If live use shows a different order, the fix is the sort key in one function.
- [Complexity estimate is by hand] → A test pins `first: 50` and `first: 20`. A query over the limit fails with Linear's error message, which `query` already prints.
- [A blocker's project is hidden or the blocker is in a team the key cannot read] → Linear omits what the key cannot see; such a blocker is not shown. Not handled.
- [Many projects with no close match] → The fallback lists up to 250 names and says when there are more.
