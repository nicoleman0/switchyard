# Tasks

## 1. list in tracker.py

- [x] 1.1 Add `CLOSED_TYPES = ("completed", "canceled", "duplicate")` and `Linear.find_project(name)` with the two queries from design.md: exact name without case or slug id; on none, close names or every name, with `and more` on `hasNextPage`; on several, each with its slug id. Verify: `test_tracker.py` tests that `onboarding` finds `Onboarding` and sends `eqIgnoreCase` and the slug id in one `or` filter; that `Onbording` exits 1 naming `Onboarding`; that an unrelated name exits 1 listing every name and `and more` when the page has more; that two matches exit 1 with both slug ids.
- [x] 1.2 Add `Linear.project_issues(project_id)`: the paged issues query from design.md with the state filter built from `CLOSED_TYPES`, and per-issue paging of `inverseRelations` when `hasNextPage`. Verify: tests that two issue pages are both read with the second page's `after` set to the first's `endCursor`; that an issue with more relations gets a follow-up `issue(id:)` query and its later blockers count; that the query text holds `first: 50`, `inverseRelations(first: 20)`, and the `nin` list.
- [x] 1.3 Add `delivery_order(issues)` as a pure function: base order, blockers from `blocks` relations whose source is open, `(outside)` blockers, Kahn's order by base index, and a cycle error naming its members. Verify: unit tests with plain dicts: milestones by `sortOrder` and no milestone last; ties by key number (`ENG-10` after `ENG-9`); a blocked issue moves after its blocker and nothing else moves; an outside blocker is shown and does not move the issue; a closed blocker is left out; a `related` relation is ignored; a two-issue cycle and a three-issue cycle each raise `TrackerError` naming every member.
- [x] 1.4 Add `Linear.list(name)` that prints the header, the tab-separated lines from design.md, or `No open issues.`. Add `GitHub.list` that raises the exit-2 error. Add the `list` subcommand and update the module docstring. Verify: `main(["list", "Onboarding"])` with the recording transport prints the header and lines in order; an empty project prints `No open issues.` and exits 0; a cycle exits 1 with nothing on stdout; GitHub `list Onboarding` exits 2 with the message and an empty `gh` log; Linear `list` with `LINEAR_API_KEY` unset exits 1 with `LINEAR_API_KEY is not set` before any call.

## 2. Docs

- [x] 2.1 `switchyard/SKILL.md` Before starting, steps 1 and 2: the Linear text from design.md. GitHub steps unchanged in meaning. Verify: read both steps.
- [x] 2.2 `AGENTS.md` Workflow, delivery-order line: add that on Linear a named project sets the order. Verify: read it.
- [x] 2.3 `README.md` "Use Linear": one short paragraph on "deliver project <name>", `tracker.py list`, how blockers order and hold issues, and the `(outside)` mark. Verify: read it against the Writing rules in `AGENTS.md`.
- [x] 2.4 `CHANGELOG.md` Unreleased, `### Added`: one line for #151 that says it is untested against live Linear. Verify: read it.

## 3. Checks

- [x] 3.1 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` passes.
- [x] 3.2 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 3.3 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck -S info` passes.
- [x] 3.4 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` passes.
- [x] 3.5 `git fetch --no-tags --depth=1 origin '+refs/tags/v*:refs/tags/v*' && npm test --prefix create-switchyard` passes.
- [x] 3.6 `npx --yes @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it, and check the archive folder and the updated `openspec/specs/issue-tracker/spec.md` exist before reporting.
- PR body: say it is untested against live Linear, and list the schema fields from design.md with the schema URL.
