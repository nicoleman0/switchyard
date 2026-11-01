## ADDED Requirements

### Requirement: Set an issue's phase
`tracker.py set-phase <key> <phase>` SHALL accept the phases `planning`, `plan-review`, `building`, `in-review`, and `needs-input`. An unknown phase or a key of the wrong form SHALL exit 2 before any tracker call. On GitHub, `set-phase` SHALL exit 0 and make no call.

#### Scenario: Unknown phase
- **WHEN** the coordinator runs `tracker.py set-phase ENG-123 done` with the Linear tracker
- **THEN** it exits 2, lists the known phases, and calls nothing

#### Scenario: GitHub does nothing
- **WHEN** the tracker is GitHub and the coordinator runs `tracker.py set-phase 150 building`
- **THEN** it exits 0, prints nothing, and runs no `gh` command

### Requirement: Linear phase statuses
With the Linear tracker, `set-phase` SHALL move the issue to the workflow status named for the phase, in the issue's own team. The default names SHALL be `Planning` for `planning`, `Plan review` for `plan-review`, `In Progress` for `building`, `In Review` for `in-review`, and `Needs input` for `needs-input`. Status names SHALL match exactly.

#### Scenario: Default status
- **WHEN** `tracker.md` has no status table and the coordinator runs `set-phase ENG-123 building`
- **THEN** `ENG-123` moves to its team's `In Progress` status

#### Scenario: Status missing from the team
- **WHEN** the issue's team has no status named `Needs input` and the coordinator runs `set-phase ENG-123 needs-input`
- **THEN** `tracker.py` exits 1, names `Needs input` and the team, lists the team's status names, and changes nothing

### Requirement: Status names from tracker.md
`tracker.md` MAY hold a table with a `Phase` column and a `Status` column. Each row SHALL replace the default status for its phase; phases without a row keep their default. A row naming an unknown phase, a phase twice, or an empty status SHALL fail every `tracker.py` command with a message naming the row.

#### Scenario: Override one phase
- **WHEN** `tracker.md` has a row `| needs-input | Blocked |` and the coordinator runs `set-phase ENG-123 needs-input`
- **THEN** the issue moves to `Blocked`, and `set-phase ENG-123 building` still uses `In Progress`

#### Scenario: Bad row
- **WHEN** `tracker.md` has a row `| shipping | Done |`
- **THEN** `tracker.py view ENG-123` exits 1 and names the row and the known phases

### Requirement: Post an issue comment
`tracker.py comment <key> <file>` SHALL post the file's text as one comment on the issue, on GitHub and on Linear. A missing, unreadable, or blank file SHALL exit 1 before any tracker call.

#### Scenario: Comment on Linear
- **WHEN** the tracker is Linear and the coordinator runs `tracker.py comment ENG-123 q.md`
- **THEN** one comment with the text of `q.md` is added to `ENG-123`

#### Scenario: Blank file
- **WHEN** `q.md` is empty or holds only whitespace
- **THEN** `tracker.py comment` exits 1 and calls nothing

### Requirement: Workers set their phase
`start-worker.sh` SHALL set the issue's phase before it starts or resumes a worker: `planning` for a planner, `building` for an implementer, and `in-review` for a reviewer. A best-of-N candidate key SHALL set the phase of its issue. When `set-phase` fails, `start-worker.sh` SHALL exit non-zero with the tracker's message and start no worker and change no record.

#### Scenario: Implementer start on Linear
- **WHEN** the coordinator runs `start-worker.sh ENG-123b implementer codex`
- **THEN** `ENG-123` is set to `building` before the worker starts

#### Scenario: Tracker fails
- **WHEN** the tracker is Linear, `LINEAR_API_KEY` is unset, and the coordinator runs `start-worker.sh ENG-123 planner claude`
- **THEN** it exits 1, prints `LINEAR_API_KEY is not set`, and the issue's record has no planner fields

### Requirement: Coordinator sets review and input phases
The coordinator SHALL set `plan-review` when a planner stops and `needs-input` when it asks the maintainer about an issue. After the answers arrive, it SHALL set the phase the issue was in before `needs-input`. Done SHALL be left to Linear's GitHub integration.

#### Scenario: Planner stops
- **WHEN** the planner for `ENG-123` stops with its plan
- **THEN** the coordinator runs `tracker.py set-phase ENG-123 plan-review` before it reviews the change

### Requirement: Questions on Linear
With the Linear tracker, the coordinator SHALL post an issue's open questions as one comment whose first line is `Questions from Switchyard`, and SHALL read as answers the comments posted after the newest such comment, or answers given in the chat. It SHALL copy the answers to the issue's answers file. GitHub projects SHALL keep the queue in `.switchyard/questions.md`.

#### Scenario: Questions posted
- **WHEN** the plan for `ENG-123` raises two questions for the maintainer
- **THEN** `ENG-123` gets one comment starting `Questions from Switchyard` with both questions, and moves to `needs-input`

#### Scenario: Answer by reply
- **WHEN** the maintainer replies to that comment in Linear and the coordinator's next wait returns
- **THEN** the coordinator reads the reply with `tracker.py view`, writes it to the answers file, and sets `ENG-123` back to `plan-review`

#### Scenario: GitHub queue unchanged
- **WHEN** the tracker is GitHub and an issue has questions
- **THEN** they go to `.switchyard/questions.md` and no comment is posted
