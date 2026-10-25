# Design

## Helper

```python
def find_project_root() -> Path:
    result = git("rev-parse", "--show-toplevel", check=False)
    if result.returncode:
        raise Refusal("run this command inside a git work tree")
    return Path(os.fsdecode(result.stdout.strip()))
```

- Lives next to `git()`. It takes no `cwd`, as both callers run from the current directory.
- Keeps `check=False` so the refusal text stays ours, not git's stderr.

## Order of checks

- `--check`: argument conflicts, then `find_project_root()`, then `read_version`. Unchanged.
- Update/install: `--install` with `--from` refusal, then `find_project_root()`, then the clean-tree check. Unchanged.

## Comparison of the two copies

Identical in the git call, the returncode test, the message, and the decoding. Nothing to reconcile.
