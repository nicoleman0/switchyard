# Design

## Context

`update-switchyard.py` installs and updates every path in the target release's `switchyard/update-paths.txt`. The only `openspec/` path there is `openspec/config.yaml`. `run()` already records `openspec_existed` and uses it to print `INIT_COMMAND` after install. #82 made the main checkout's `openspec/` folder the mode switch (`SKILL.md`, Plans). create-switchyard spawns the bundled updater with inherited stdio and rejects any install argument today.

## Goals / Non-Goals

**Goals:** a project can install without OpenSpec and stay plain across updates. OpenSpec projects see no change.

**Non-Goals:** switching an installed project between modes; a plain choice in `init-project.py`; removing `openspec/` from projects that already have it.

## Decisions

1. **The question lives in the updater.** Both entry points (`npm init switchyard` and `python3 update-switchyard.py --install`) run it, so the rule has one home. create-switchyard only forwards the flag.
2. **Order of answers:** existing `openspec/` folder, then the flag, then the terminal prompt, then yes. Terminal means `sys.stdin.isatty()`. The prompt reads `Use OpenSpec for plans? [Y/n] `; empty means yes, `y`/`yes`/`n`/`no` in any case are accepted, anything else asks again, and EOF means yes. Yes is the default because it matches the release's current behaviour (decided in #82's plan review).
3. **Existing folder wins.** `--no-openspec` with an existing `openspec/` folder warns that the folder selects OpenSpec mode, then continues in that mode.
4. **One filter, applied to the path list.** When the project is plain, drop `openspec` roots from `paths` right after `read_update_paths`, before the target and base trees are built. The "listed path is missing" check and both the install and update loops then never see `openspec/` paths. Update mode reads plainness from the folder only.
5. **Flags choose install mode.** Updates accept either flag and ignore it, printing one line that the `openspec/` folder decides the mode after install. Passing both flags, or either with `--check`, is refused.
6. **Report.** Plain install prints `Plans: plain (no openspec/ folder); see SKILL.md, Plans.` where it would print the init step. A plain update prints nothing extra: skipped paths are not actions.
7. **npm's swallowed flag.** Without `--`, `npm init switchyard@latest --no-openspec` may set `npm_config_openspec=false` instead of passing the flag, as with `--dry-run`. create-switchyard maps `npm_config_openspec` `true`/`false` (or empty for false on npm 11.19.0) to the flag when no flag was given. Docs show the `--` form first.
8. **Tests feed no terminal.** `run_update` in the Python tests and `createIn` in the Node tests pass a non-terminal stdin, so a local run never blocks on the prompt. The prompt itself is tested with a pseudo-terminal (`pty` on macOS and Linux) or by running the prompt function with a fake stdin; the implementer picks whichever stays short.

## Risks / Trade-offs

- npm 11.19.0 consumes mode flags before `--` and exports `npm_config_openspec`. It warns that unknown CLI config will stop working in its next major version. Docs show flags after `--`.
- A plain project that later runs `openspec init` switches to OpenSpec mode, but its `openspec/config.yaml` lacks the Switchyard rules until a release changes that file. Switching modes is a non-goal; leave it undocumented, per the approved answer.
