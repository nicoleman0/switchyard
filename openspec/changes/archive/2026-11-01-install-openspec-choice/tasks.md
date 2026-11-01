# Tasks

## 1. Updater

- [x] 1.1 `update-switchyard.py`: add `--openspec` and `--no-openspec` (mutually exclusive), accepted and ignored on update with a mode reminder, refused with `--check` (design Decision 5). Verify with refusal tests: both flags and a flag with `--check` exit 2 and write nothing; each flag on update prints the reminder and leaves folder-based mode unchanged.
- [x] 1.2 Decide the mode on install in the order of Decision 2, with the prompt read from stdin only when it is a terminal. Warn and continue in OpenSpec mode for `--no-openspec` when `openspec/` exists (Decision 3). Verify with tests: no flag and no terminal adds `openspec/config.yaml`; `--openspec` adds it; `--no-openspec` skips it; `--no-openspec` with an existing `openspec/` warns and installs in OpenSpec mode; the prompt answers `n`, `yes`, empty, and EOF give no, yes, yes, yes.
- [x] 1.3 Drop `openspec` roots from `paths` when the project is plain (Decision 4), for install and update. Verify with tests: plain install reports no `openspec/` path and creates no `openspec/` folder; an update from a base whose `openspec/config.yaml` differs from the target, in a project without `openspec/`, reports no `openspec/` path and exits 0; the same update with `openspec/` present still merges the file.
- [x] 1.4 After a plain install print the plain-plans line instead of the init step (Decision 6). Verify: the existing `INIT_COMMAND` test still passes for yes; a plain install's output has the plain-plans line and no `openspec init`.
- [x] 1.5 `test_update_switchyard.py`: `run_update` passes `stdin=subprocess.DEVNULL` so existing tests never prompt (Decision 8). Verify by running the suite from an interactive terminal.

## 2. create-switchyard

- [x] 2.1 `create-switchyard.mjs`: install accepts at most one of `--openspec` or `--no-openspec` and forwards it as `updater(["--install", "--source", bundle, flag])`. Any other install argument, or both flags, still prints usage and exits 2. With no flag, map `npm_config_openspec` `true`/`false` (or empty for false on npm 11.19.0) to the flag (Decision 7). Add both flags to `usage`. `update` forwarding is unchanged; the updater accepts and ignores the flags there.
- [x] 2.2 `install.test.mjs`: `createIn` passes `input: ""` (or `stdio` with ignored stdin). Add tests: `--no-openspec` installs with no `openspec/` folder; `npm_config_openspec=false` does the same; both flags exit 2 with usage. Verify with `npm test --prefix create-switchyard`.
- [x] 2.3 Check real npm once, in a scratch repo with the packed tarball: `npm exec --package=<tarball> create-switchyard --no-openspec` and `npm init`-style use without `--`. Record in the PR whether npm passed the flag or set `npm_config_openspec`.

## 3. Docs

- [x] 3.1 `README.md` install section: after the command block, one sentence on the OpenSpec question, its default, and `npm init switchyard@latest -- --no-openspec`. The `openspec/config.yaml` merge bullet and the init-step paragraph say they apply when the project uses OpenSpec. No other README text changes.
- [x] 3.2 `create-switchyard/README.md`: one bullet for `-- --no-openspec`.
- [x] 3.3 `CHANGELOG.md` Unreleased, Added: one line for #138.

## 4. Repository checks

- [x] 4.1 `switchyard/hooks/checks.sh` exits 0.
- [x] 4.2 `npx --yes @fission-ai/openspec validate --all --strict` passes.
- [x] 4.3 `npm test --prefix create-switchyard` passes, after `git fetch --no-tags --depth=1 origin '+refs/tags/v*:refs/tags/v*'`.
