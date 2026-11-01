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

### Requirement: List a Linear project
With the Linear tracker, `tracker.py list <project>` SHALL print a header line naming the project and its slug id, then one line per open issue in the project, in delivery order. It SHALL read every page of the project's issues. A project with no open issues SHALL print the header and `No open issues.` and exit 0.

#### Scenario: Project over two pages
- **WHEN** the project `Onboarding` has 60 open issues and Linear returns them in two pages
- **THEN** `tracker.py list Onboarding` prints all 60 lines and exits 0

### Requirement: List line fields
Each issue line from `list` SHALL hold, separated by tabs: the issue key, its status name, its milestone name or `-`, its open blockers or `-`, and its title.

#### Scenario: Line for a blocked issue
- **WHEN** `ENG-2` is in Todo, in milestone `Setup`, and blocked by open `ENG-5`
- **THEN** its line is `ENG-2`, `Todo`, `Setup`, `ENG-5`, and its title, separated by tabs

### Requirement: Closed issues left out
`list` SHALL leave out issues whose status type is completed, canceled, or duplicate, and SHALL leave such issues out of every blockers field.

#### Scenario: Done issue left out
- **WHEN** the project has `ENG-1` in Done and `ENG-2` in Todo
- **THEN** the output has a line for `ENG-2` and none for `ENG-1`

#### Scenario: Closed blocker
- **WHEN** `ENG-2` is blocked by `ENG-1`, which is Done
- **THEN** `ENG-2`'s blockers field is `-`

### Requirement: Name the Linear project
`list` SHALL accept a project name, matched without regard to case, or a project slug id. When nothing matches, it SHALL exit 1 and list the visible project names close to the argument, or every visible project when none is close. When several projects match, it SHALL exit 1 and list each with its slug id.

#### Scenario: Name in another case
- **WHEN** the maintainer runs `tracker.py list onboarding` and the project is named `Onboarding`
- **THEN** it lists that project

#### Scenario: Unknown project
- **WHEN** no project is named `Onbording` and a project `Onboarding` exists
- **THEN** `list` exits 1 and names `Onboarding` as a close match

#### Scenario: Two projects with one name
- **WHEN** two projects are named `Onboarding`
- **THEN** `list` exits 1 and prints both with their slug ids

### Requirement: Base delivery order
`list` SHALL order issues by their milestone's order in the project, with issues that have no milestone after every milestone, then by Linear's manual issue order, then by key.

#### Scenario: No milestone last
- **WHEN** `ENG-3` has no milestone and `ENG-4` is in the project's last milestone
- **THEN** `ENG-4` is printed before `ENG-3`

### Requirement: Blocked issues follow their blockers
An issue blocked by an open issue in the list SHALL come after that issue; the order of the other issues SHALL be kept.

#### Scenario: Blocked issue moves after its blocker
- **WHEN** `ENG-2` comes before `ENG-5` in the base order and `ENG-2` is blocked by `ENG-5`
- **THEN** `ENG-5` is printed before `ENG-2`

### Requirement: Blockers outside the project
An open blocker outside the project SHALL be shown in the blockers field with the suffix ` (outside)` and SHALL NOT change the order.

#### Scenario: Blocker outside the project
- **WHEN** `ENG-2` is blocked by open issue `OPS-9` from another project
- **THEN** `ENG-2`'s blockers field is `OPS-9 (outside)` and its place is unchanged

### Requirement: Blocker cycles fail
A cycle among open blockers in the project SHALL make `list` exit 1, name the issues in the cycle, and print no issue lines.

#### Scenario: Cycle
- **WHEN** `ENG-2` is blocked by `ENG-3` and `ENG-3` is blocked by `ENG-2`
- **THEN** `list` exits 1, names `ENG-2` and `ENG-3`, and prints no issue lines

### Requirement: List on GitHub
With the GitHub tracker, `tracker.py list <project>` SHALL exit 2 without calling `gh`, and say that GitHub projects name their issues in the session.

#### Scenario: GitHub list
- **WHEN** the tracker is GitHub and the coordinator runs `tracker.py list Onboarding`
- **THEN** it exits 2, prints the message, and runs no `gh` command

### Requirement: Coordinator reads a Linear project's order
On Linear, when the maintainer names a project for the batch, the coordinator SHALL run `tracker.py list <project>` and take the issues in its order. When the maintainer names issues instead, and on GitHub, the order SHALL be the one the maintainer names, with milestones as today.

#### Scenario: Deliver a project
- **WHEN** the maintainer says "deliver project Onboarding" on Linear
- **THEN** the coordinator runs `tracker.py list Onboarding` and plans the batch in the printed order

### Requirement: Coordinator holds blocked issues
The coordinator SHALL start a listed issue only after each open blocker in the project has merged, unless the maintainer names the two issues to stack. It SHALL NOT start an issue with a blocker marked `outside`, and SHALL tell the maintainer which blocker it waits for.

#### Scenario: Outside blocker held
- **WHEN** an issue in the list shows `OPS-9 (outside)`
- **THEN** the coordinator does not start it and tells the maintainer it waits for `OPS-9`
