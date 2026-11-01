## ADDED Requirements

### Requirement: Added tracker file names GitHub by default
When the updater adds a missing `switchyard/tracker.md`, on install without `--tracker` or on an update, it SHALL write the release's file with its `Tracker:` line set to `github`, whatever tracker the release's file names. The rest of the release's file SHALL be kept.

#### Scenario: Install without a tracker flag
- **WHEN** the release's `tracker.md` says `Tracker: linear` and install runs with no `--tracker` in a repo with no `tracker.md`
- **THEN** `switchyard/tracker.md` is added and says `Tracker: github`

#### Scenario: Update adds the file
- **WHEN** a project updates from a release with no `tracker.md` to a release whose `tracker.md` says `Tracker: linear`
- **THEN** `switchyard/tracker.md` is added and says `Tracker: github`

#### Scenario: Install keeps an existing file without a flag
- **WHEN** install runs with no `--tracker` and the repo's `tracker.md` says `Tracker: linear`
- **THEN** the file is unchanged and install prints nothing about the tracker

### Requirement: Template init resets the tracker
`init-project.py` SHALL set the `Tracker:` line of `switchyard/tracker.md` to `github` and print one line for the file: `reset` when it changed the line, `kept` when the line already said `github`, and `skipped` with the reason when the file is absent, has uncommitted changes, or does not hold exactly one `Tracker:` line. The rest of the file SHALL be kept.

#### Scenario: Template names Linear
- **WHEN** a project made from the template has a committed `tracker.md` with `Tracker: linear` and the maintainer runs init
- **THEN** the file says `Tracker: github` and init prints `reset     switchyard/tracker.md (Tracker: github)`

#### Scenario: Template names GitHub
- **WHEN** the committed `tracker.md` already says `Tracker: github`
- **THEN** the file is unchanged and init prints `kept      switchyard/tracker.md (Tracker: github)`

#### Scenario: Uncommitted tracker edit
- **WHEN** `tracker.md` has uncommitted changes
- **THEN** init leaves it unchanged and prints `skipped   switchyard/tracker.md (uncommitted changes)`

### Requirement: Tracker line stays on one line
A `Tracker:` line in `switchyard/tracker.md` SHALL hold its name on the same line. `tracker.py` SHALL NOT read a name from the next line.

#### Scenario: Name on the next line
- **WHEN** `tracker.md` holds `Tracker:` and `github` on separate lines
- **THEN** `tracker.py` reports that it found no `Tracker:` line
