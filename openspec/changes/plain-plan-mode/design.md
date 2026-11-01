# Design

## Context

See proposal.md, Why. OpenSpec is assumed in the roles, `SKILL.md`, `AGENTS.md`, `pre-review.sh` (archived and validate steps), `check-scope.sh` (`openspec/` always in scope), `merge-queue.py` (`openspec/specs/*/spec.md` append-only), the updater (`openspec/config.yaml`, the init hint), and the CI workflow. `openspec validate` exits 1 in a repo with no `openspec/` folder (checked: "No OpenSpec root found").

Installer work moves to #138 with its own change. This change does not edit the updater or `create-switchyard/`.

## Goals / Non-Goals

**Goals:** plain mode works end to end, fast path included. OpenSpec projects see no change in behaviour.

**Non-Goals:** switching a project between modes; a plain-mode choice in `init-project.py` (template path); installer questions, flags, config filtering, and init hints (#138); #130's doc fixes.

## Decisions

1. **Mode is the presence of `openspec/` in the main checkout.** It already decides whether OpenSpec can run at all, and the updater already reads it. A flag in `routing.md` could disagree with the tree and would need markdown parsing in three scripts; `routing.md` is about providers. AGENTS.md prose is not script-readable. Scripts test the folder directly; `SKILL.md` Plans is the one prose home of the rule.
2. **Plan file is `.switchyard/plan.md`, ignored.** It sits with the brief and answers, so every worker reads it from disk and nothing merges or archives. It is gone after teardown; the PR body carries the summary.
3. **Template `switchyard/plan-template.md`** has Why, What changes, Decisions, Impact, Scenarios (WHEN/THEN), Tasks (checkboxes, checks last). Impact, decisions, and tasks are what the coordinator's second sizing reads. "Scenarios: none" plays the role of `skip_specs: true`, and the coordinator checks it the same way.
4. **"The change" keeps its name.** One Plans section defines it for both modes, so most text stays as is and parallel SKILL.md edits do not conflict.
5. **Gate parity.** Plain mode replaces "change archived" and "openspec" with a "plan" step: file present, no `- [ ]` left. It mirrors archive refusing unfinished tasks.
6. **CI step guard** in the workflow's run line: skip with a message when `openspec/` is missing. Clearer in logs than a `hashFiles` condition.

## Risks / Trade-offs

- A plain branch that creates `openspec/` is reported out of scope, since mode reads the main checkout. Intended.
- Plain plans leave no record after teardown → PR body Changes and Decisions sections stay required.
- Large diff across files three in-flight issues touch → independent tasks start after #114 and #119; candidate-plan copying waits for #120; the installer work is split into #138.
