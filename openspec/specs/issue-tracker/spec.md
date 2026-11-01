# Issue Tracker Specification

## Purpose

Defines how a project names its issue tracker, what every tracker backend does, which issue keys the workflow accepts, and how install and preflight handle the choice.

## Requirements

### Requirement: Project names its tracker
The project SHALL name its issue tracker in `switchyard/tracker.md` with one `Tracker: <name>` line. The known names SHALL be `github` and `linear`. Every issue read and issue edit SHALL go through `switchyard/scripts/tracker.py`. Pull requests SHALL stay on GitHub for every tracker.

#### Scenario: Linear named
- **WHEN** `tracker.md` has `Tracker: linear`
- **THEN** `tracker.py` uses Linear for `view`, `set-change`, and `check`

#### Scenario: Unknown name
- **WHEN** `tracker.md` names a tracker that is not known
- **THEN** `tracker.py` exits 1 and lists the known names

### Requirement: Linear issue read
With the Linear tracker, `tracker.py view <key>` SHALL print the issue's identifier and title, its status name, its description, and every comment with author and time, oldest first. With no comments it SHALL print `No comments.`

#### Scenario: Issue with comments
- **WHEN** the maintainer runs `tracker.py view ENG-123` and the issue has two comments
- **THEN** the output shows `ENG-123 <title>`, `State: <status name>`, the description, and both comments in creation order

#### Scenario: Issue with no description
- **WHEN** the Linear issue has no description
- **THEN** `view` prints the header and comments with an empty body and exits 0

### Requirement: Linear Change line
With the Linear tracker, `tracker.py set-change <key> <path>` SHALL make `Change: <path>` the first line of the issue description. It SHALL replace an existing `Change:` first line, and otherwise prepend the line and a blank line. The rest of the description SHALL be unchanged.

#### Scenario: Prepend
- **WHEN** the description is `Problem text.` and the planner runs `set-change ENG-123 openspec/changes/x`
- **THEN** the description becomes `Change: openspec/changes/x`, a blank line, and `Problem text.`

#### Scenario: Replace
- **WHEN** the description starts with `Change: openspec/changes/old`
- **THEN** only that first line is replaced

### Requirement: Linear API key
The Linear tracker SHALL authenticate with the personal API key in `LINEAR_API_KEY`. When the key is missing, or Linear rejects a request, `tracker.py` SHALL exit non-zero and print what failed and how to fix it, without printing the key.

#### Scenario: Key missing
- **WHEN** `LINEAR_API_KEY` is unset and the maintainer runs `tracker.py view ENG-123`
- **THEN** it exits 1 and says to set `LINEAR_API_KEY` to a Linear personal API key, before any network call

#### Scenario: Linear returns errors
- **WHEN** Linear answers with a GraphQL `errors` list, with any HTTP status
- **THEN** `tracker.py` exits 1 and prints each error message

### Requirement: Keys checked per tracker
Each tracker SHALL accept only its own key form: GitHub takes digits, Linear takes an uppercase team key, a dash, and a number, such as `ENG-123`. A key of the wrong form SHALL fail before any tracker call.

#### Scenario: Digits on Linear
- **WHEN** the tracker is Linear and the key is `149`
- **THEN** `tracker.py` exits 2 and names the Linear key form, without calling Linear

### Requirement: Workflow accepts both key forms
The worktree, state, worker, and merge-queue scripts SHALL accept issue keys that are digits or a Linear identifier, each optionally followed by `b` for a best-of-N candidate. They SHALL reject any other key before creating a worktree. Lists of issues SHALL sort numeric keys by number, and Linear keys by team key and then number.

#### Scenario: Linear key set up
- **WHEN** the coordinator runs `setup-worktree.sh ENG-123 eng-123-fix-login`
- **THEN** the worktree and record are created for `ENG-123`

#### Scenario: Linear best-of-N candidate
- **WHEN** the coordinator runs `setup-worktree.sh ENG-123b eng-123-fix-login-b` after candidate a exists
- **THEN** candidate b is set up from `ENG-123`'s record

#### Scenario: Bad key rejected early
- **WHEN** the coordinator runs `setup-worktree.sh eng-123 topic`
- **THEN** the script exits non-zero naming the accepted forms, and no worktree or branch is created

#### Scenario: Herdr agent name
- **WHEN** a planner starts on Herdr for issue `ENG-123`
- **THEN** its agent is named `planner-eng-123`

#### Scenario: Hook port
- **WHEN** the shipped `worktree-up.sh` runs for `ENG-123`
- **THEN** it prints `port=3123`, and `port=4123` for candidate b

### Requirement: Linear branch names
On Linear, the coordinator SHALL start each issue's branch name with the lowercased issue key, so Linear's GitHub integration links the pull request to the issue.

#### Scenario: Branch for a Linear issue
- **WHEN** the coordinator sets up `ENG-123`
- **THEN** the branch name starts with `eng-123`

### Requirement: Install chooses the tracker
Install SHALL take `--tracker <name>`, default `github`. When `switchyard/tracker.md` is missing, install SHALL write it with `Tracker: <name>`. When the file exists, install SHALL keep it and say so if it names another tracker. An unknown name SHALL fail before any file is written. Updates SHALL never change `tracker.md`.

#### Scenario: Install with Linear
- **WHEN** the maintainer runs `npm init switchyard@latest -- --tracker linear` in a repo with no Switchyard
- **THEN** `switchyard/tracker.md` contains `Tracker: linear`

#### Scenario: Existing tracker file
- **WHEN** install runs with `--tracker linear` and `tracker.md` already says `Tracker: github`
- **THEN** the file is unchanged and install prints that it kept the existing tracker

#### Scenario: Unknown tracker name
- **WHEN** install runs with `--tracker jira`
- **THEN** it exits 2, lists the known names, and writes nothing

### Requirement: Preflight checks the tracker
Preflight SHALL run the tracker check. On Linear it SHALL report `MISSING` when `LINEAR_API_KEY` is unset or rejected, with the fix, and `ok` when one cheap query succeeds. On GitHub the existing `gh` check SHALL stay the only tracker check. `gh` SHALL stay required for every tracker.

#### Scenario: Linear key missing
- **WHEN** the tracker is Linear and `LINEAR_API_KEY` is unset
- **THEN** preflight prints a `MISSING` line naming `LINEAR_API_KEY` and how to create a key, and exits non-zero

#### Scenario: Linear key works
- **WHEN** the tracker is Linear and the key is accepted
- **THEN** preflight prints `ok       Linear`

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
