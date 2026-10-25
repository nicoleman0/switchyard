# Tasks

## 1. CI workflow

- [x] 1.1 In `.github/workflows/switchyard.yml`, after checkout, add `actions/setup-python@v7` with `python-version: '3.10'`, then a step `Compile Python scripts on Python 3.10` and a step `Test the scripts on Python 3.10` that run the same commands as the existing compile and test steps. Keep the header comment and the job name `check`. Verify the file parses with `ruby -ryaml -e 'YAML.load_file(ARGV[0])' .github/workflows/switchyard.yml` (PyYAML is not installed here).
- [x] 1.2 Add `actions/setup-python@v7` with `python-version: '3.x'` before `Lint shell scripts`, with a one-line comment that `3.x` is the newest stable release. Leave every existing step unchanged. Verify with `git diff` that the only changes are the added steps.
- [x] 1.3 Run the 3.10 commands locally: `uv run --no-project --python 3.10 python -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes (147 tests) and `git ls-files -z 'switchyard/*.py' | xargs -0 uv run --no-project --python 3.10 python -m py_compile` exits 0.

## 2. Docs

- [x] 2.1 In `README.md`, change the Requirements line to `git`, Python 3.10 or newer, and Node.js, and the CI sentence in the first Requirements bullet to say CI tests on Python 3.10 and the newest Python 3. Verify with `git grep -n 'Python 3' README.md`.
- [x] 2.2 In the `README.md` npm install paragraph, change "so it needs Python 3" to "so it needs Python 3.10 or newer". Verify with the same grep.
- [x] 2.3 Append under `## [Unreleased]` in `CHANGELOG.md`, in a `### Changed` heading: `- #104: CI tests the scripts on Python 3.10 and the newest Python 3. The README names 3.10 as the oldest supported Python.` Verify no other line in the file changed with `git diff CHANGELOG.md`.

  - [x] 2.4 In `create-switchyard/README.md:3`, change "It needs git, Python 3," to "It needs git, Python 3.10 or newer," (added by the plan answer). Verify with the same grep.

## 3. Repository checks

- [x] 3.1 `git ls-files -z 'switchyard/*.sh' | xargs -0 shellcheck` exits 0.
- [x] 3.2 `git ls-files -z 'switchyard/*.py' | xargs -0 python3 -m py_compile` exits 0.
- [x] 3.3 `git ls-files -z 'switchyard/*.mjs' | xargs -0 -n 1 node --check` exits 0.
- [x] 3.4 `python3 -m unittest discover -s switchyard/scripts -p 'test_*.py'` passes.
- [x] 3.5 `npm test --prefix create-switchyard` passes, with release tags present (`git tag -l 'v*'`).
- [x] 3.6 `npx @fission-ai/openspec validate --all --strict` passes.

## Workflow follow-up

- Archive the change in the PR that completes it.
- After push, confirm in the PR's Actions log that the 3.10 steps report Python 3.10.x and the later steps report the newest 3.x.
