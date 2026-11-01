#!/usr/bin/env python3
"""Usage: merge-queue.py [--merge] [--timeout <seconds>] <issue>...
Exit 0: done; 1: stopped; 2: cannot run; 3: ready for a merge command.
"""

import argparse
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

from state import key_order, valid_key


SCRIPTS = Path(__file__).resolve().parent
# GitHub usually shows a pushed head within seconds.
HEAD_LAG = 60


class Stop(Exception):
    pass


def run(cwd, *args, check=True, env=None):
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    if check and result.returncode:
        detail = (result.stderr + result.stdout).strip()
        raise Stop(f"{shlex.join(str(arg) for arg in args)} failed ({result.returncode}): {detail}")
    return result


def payload(result):
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise Stop(f"invalid JSON from {shlex.join(result.args)}: {exc}") from exc


def number(value):
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError("must be a finite nonnegative number")
    return parsed


def append_only(name):
    parts = name.split("/")
    return name == "CHANGELOG.md" or (
        len(parts) == 4 and parts[:2] == ["openspec", "specs"] and parts[3] == "spec.md"
    )


def rebase_active(tree):
    return any((tree / run(tree, "git", "rev-parse", "--git-path", name).stdout.strip()).is_dir()
               for name in ("rebase-merge", "rebase-apply"))


def rebase(tree):
    command = ("git", "-c", "merge.conflictStyle=merge", "-c", "rerere.enabled=false", "rebase")
    resolved = set()
    try:
        result = run(tree, *command, "origin/main", check=False)
        while result.returncode:
            conflicts = run(tree, "git", "diff", "--name-only", "--diff-filter=U", "-z").stdout
            files = [name for name in conflicts.split("\0") if name]
            if not files:
                raise Stop(f"rebase failed: {(result.stderr + result.stdout).strip()}")
            outside = [name for name in files if not append_only(name)]
            if outside:
                raise Stop(f"rebase conflict outside append-only paths: {', '.join(outside)}")
            for name in files:
                run(tree, sys.executable, str(SCRIPTS / "union-resolve.py"), name)
                run(tree, "git", "add", "--", name)
                resolved.add(name)
            result = run(tree, *command, "--continue", check=False,
                         env={**os.environ, "GIT_EDITOR": "true"})
    except (Stop, OSError, KeyboardInterrupt):
        if rebase_active(tree):
            run(tree, "git", "rebase", "--abort")
        raise
    return sorted(resolved)


def wait_head(main, pr, branch, head, timeout, poll, progress):
    remote = run(main, "git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}").stdout.split()
    if not remote or remote[0] != head:
        raise Stop("local head differs from PR headRefOid; reconcile the branch before retrying")
    progress("PR head lags the pushed branch; waiting")
    bound = min(HEAD_LAG, timeout)
    deadline = time.monotonic() + bound
    while True:
        view = payload(run(main, "gh", "pr", "view", str(pr), "--json", "headRefOid"))
        if view["headRefOid"] == head:
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Stop(f"PR head did not reach {head} within {bound:g}s")
        time.sleep(min(poll, remaining))


def wait_ci(main, pr, head, timeout, poll, progress):
    deadline = time.monotonic() + timeout
    phase = "head update"
    while True:
        view = payload(run(main, "gh", "pr", "view", str(pr), "--json", "headRefOid"))
        if view["headRefOid"] == head:
            result = run(main, "gh", "pr", "checks", str(pr), "--json", "name,bucket", check=False)
            # gh exits 1 while the pushed commit has no registered checks.
            if result.returncode == 1 and ("no checks reported" in (result.stderr + result.stdout).lower()
                                           or result.stdout.strip() == "[]"):
                checks = []
            elif result.returncode in (0, 1, 8):
                checks = payload(result)
            else:
                raise Stop(f"CI checks failed ({result.returncode}): {(result.stderr + result.stdout).strip()}")
            if not isinstance(checks, list):
                raise Stop("CI checks returned a non-list result")
            failures = [check["name"] for check in checks if check["bucket"] in ("fail", "cancel")]
            if failures:
                raise Stop(f"CI failed: {', '.join(failures)}")
            unknown = [check for check in checks if check["bucket"] not in ("pending", "pass", "skipping")]
            if unknown:
                raise Stop(f"unknown CI check result: {unknown}")
            phase = "check registration" if not checks else "pending checks"
            if checks and all(check["bucket"] != "pending" for check in checks):
                current = payload(run(main, "gh", "pr", "view", str(pr), "--json", "headRefOid"))
                if current["headRefOid"] != head:
                    raise Stop("PR head moved while waiting for CI")
                progress(f"CI passed ({len(checks)} checks)")
                return
        else:
            phase = "head update"
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Stop(f"CI wait ran out during {phase} (timeout {timeout:g}s)")
        time.sleep(min(poll, remaining))


def record(main, issue):
    return json.loads((main / ".switchyard/state" / f"{issue}.json").read_text())


def restack_children(main, issue, progress):
    children = [path.stem for path in (main / ".switchyard/state").glob("*.json")
                if str(record(main, path.stem).get("parent", "")) == issue]
    for child in sorted(children, key=key_order):
        progress(f"restacking #{child}")
        result = run(main, "bash", str(SCRIPTS / "restack.sh"), child, check=False)
        print(result.stdout, end="", flush=True)
        if result.returncode:
            raise Stop(f"restack of #{child} failed ({result.returncode}): {result.stderr.strip()}")


def teardown(main, issue, branch):
    result = run(main, "bash", str(SCRIPTS / "teardown-worktree.sh"), issue, branch)
    print(result.stdout, end="", flush=True)


def process(main, issue, branch, tree, args):
    pr = "?"

    def progress(message):
        print(f"#{issue} PR #{pr}: {message}", flush=True)

    try:
        prs = payload(run(main, "gh", "pr", "list", "--head", branch, "--state", "all",
                          "--json", "number,state,headRefOid,url", "--limit", "1"))
        if not prs:
            raise Stop(f"no PR for branch {branch}")
        row = prs[0]
        pr = row["number"]
        if row["state"] == "MERGED":
            progress("already merged")
            restack_children(main, issue, progress)
            progress("tearing down")
            teardown(main, issue, branch)
            return 0
        if row["state"] != "OPEN":
            raise Stop("PR is closed without merging")
        progress("fetching origin")
        run(main, "git", "fetch", "origin")
        if not tree.is_dir() or tree == main:
            raise Stop(f"invalid issue worktree: {tree}")
        if run(tree, "git", "symbolic-ref", "--short", "HEAD").stdout.strip() != branch:
            raise Stop(f"worktree {tree} does not have branch {branch} checked out")
        if run(tree, "git", "status", "--porcelain", "--untracked-files=no").stdout:
            raise Stop(f"worktree has tracked changes: {tree}")
        if rebase_active(tree):
            raise Stop(f"worktree already has a rebase in progress: {tree}")
        old = run(tree, "git", "rev-parse", "HEAD").stdout.strip()
        if old != row["headRefOid"]:
            wait_head(main, pr, branch, old, args.timeout, args.poll, progress)
        progress("rebasing onto origin/main")
        files = rebase(tree)
        head = run(tree, "git", "rev-parse", "HEAD").stdout.strip()
        progress("rebased onto origin/main" + (f" (resolved {', '.join(files)})" if files else ""))
        try:
            progress("running pre-review.sh")
            gate = run(main, "bash", str(SCRIPTS / "pre-review.sh"), issue, check=False)
            print(gate.stdout, end="", flush=True)
            if gate.returncode:
                raise Stop(f"pre-review.sh failed ({gate.returncode}): {gate.stderr.strip()}")
            if run(tree, "git", "rev-parse", "HEAD").stdout.strip() != head:
                raise Stop("HEAD changed during pre-review.sh")
            if run(tree, "git", "status", "--porcelain", "--untracked-files=no").stdout:
                raise Stop("pre-review.sh left tracked changes")
        except (Stop, OSError, KeyboardInterrupt):
            # Keep hook edits; restore the old ref only while it is still our rebased head.
            if head != old and run(tree, "git", "rev-parse", "HEAD").stdout.strip() == head:
                run(tree, "git", "reset", "--keep", old)
            raise
        if head != old:
            progress("pushing with lease")
            try:
                run(main, "git", "push", f"--force-with-lease={branch}:{old}", "origin", branch)
            except (Stop, OSError, KeyboardInterrupt):
                remote = run(main, "git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}").stdout.split()
                # A lost response can follow a successful push; keep that published head.
                if remote and remote[0] == old and run(tree, "git", "rev-parse", "HEAD").stdout.strip() == head:
                    run(tree, "git", "reset", "--keep", old)
                raise
        else:
            progress("head unchanged; skipping push")
        progress("waiting for CI")
        wait_ci(main, pr, head, args.timeout, args.poll, progress)
        command = ["gh", "pr", "merge", str(pr), "--squash", "--match-head-commit", head]
        if not args.merge:
            progress("ready to merge; run this command after approval")
            print(shlex.join(command), flush=True)
            return 3
        progress("merging")
        run(main, *command)
        merged = payload(run(main, "gh", "pr", "view", str(pr), "--json", "state"))
        if merged["state"] != "MERGED":
            raise Stop("merge command returned but PR is not MERGED")
        progress("merged")
        restack_children(main, issue, progress)
        progress("tearing down")
        teardown(main, issue, branch)
        return 0
    except (Stop, OSError, ValueError, KeyError, TypeError, KeyboardInterrupt) as exc:
        print(f"STOP #{issue} PR #{pr}: {exc or 'interrupted'}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merge", action="store_true", help="merge a batch with prior maintainer approval")
    parser.add_argument("--timeout", type=number, default=1800, help="CI wait bound in seconds (default: 1800)")
    parser.add_argument("issues", nargs="+")
    args = parser.parse_args()
    try:
        args.poll = number(os.environ.get("SWITCHYARD_POLL_SECONDS", "10"))
        main = Path(run(SCRIPTS, "git", "worktree", "list", "--porcelain").stdout.splitlines()[0][9:]).resolve()
        records = []
        for issue in args.issues:
            if not valid_key(issue):
                raise Stop(f"invalid issue key: {issue}")
            values = [run(main, sys.executable, str(SCRIPTS / "state.py"), "get", issue, key).stdout.strip()
                      for key in ("branch", "path")]
            records.append((issue, values[0], Path(values[1]).resolve()))
            parent = str(record(main, issue).get("parent") or "")
            # A child rebased onto main before its parent merges would replay the parent's commits.
            if parent and parent not in args.issues[:len(records) - 1]:
                raise Stop(f"#{issue} is stacked on #{parent}; queue #{parent} before it")
    except (Stop, OSError, ValueError, argparse.ArgumentTypeError) as exc:
        print(f"Cannot run queue: {exc}", file=sys.stderr)
        return 2
    for issue, branch, tree in records:
        status = process(main, issue, branch, tree, args)
        if status:
            return status
    return 0


if __name__ == "__main__":
    sys.exit(main())
