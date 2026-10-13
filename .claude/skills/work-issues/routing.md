# Project routing

This file belongs to the project. The updater adds it when missing and never changes it. Edit it to choose models, effort, providers, or flags. Row selection rules are in `SKILL.md`.

Supported worker providers are `claude`, `codex`, and `opencode`. Reviewers run on `claude` or `codex`.

## Workers

| Role | Provider | Flags | Use |
|---|---|---|---|
| Planner | claude | `--agent issue-planner --model opus --effort high --permission-mode auto` | |
| Planner | codex | `-m gpt-5.6-sol -c model_reasoning_effort=high --approve-for-me` | |
| Implementer | claude | `--agent issue-implementer --model sonnet --effort medium --permission-mode auto` | |
| Implementer | claude | `--agent issue-implementer --model opus --effort high --permission-mode auto` | escalation |
| Implementer | codex | `-m gpt-6-luna -c model_reasoning_effort=medium --approve-for-me` | |
| Implementer | opencode | `--model opencode-go/glm-5.3-flash --auto` | |
| Reviewer | claude | `--agent issue-reviewer --model opus --effort high --permission-mode auto` | |
| Reviewer | codex | `-m gpt-5.6-sol -c model_reasoning_effort=high --approve-for-me` | |

## Coordinator

| Provider | Model | Effort |
|---|---|---|
| claude | `opus` | high |
| codex | `gpt-5.6-sol` | medium |
