## ADDED Requirements

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
