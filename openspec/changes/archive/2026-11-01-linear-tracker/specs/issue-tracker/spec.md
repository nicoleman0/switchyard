# Spec Delta

## Purpose

Defines how a project names its issue tracker, what every tracker backend does, which issue keys the workflow accepts, and how install and preflight handle the choice.

## ADDED Requirements

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
