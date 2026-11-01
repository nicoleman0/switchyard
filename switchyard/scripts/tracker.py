#!/usr/bin/env python3
"""The only place that talks to the issue tracker. PRs stay on `gh pr`.

  tracker.py view <issue>
  tracker.py set-change <issue> <change-path>

The tracker comes from `switchyard/tracker.md`. Add a backend class and a BACKENDS entry.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TRACKER_FILE = Path(__file__).resolve().parents[1] / "tracker.md"
TRACKER_LINE = re.compile(r"^Tracker:\s*(\S+)\s*$", re.MULTILINE)


class TrackerError(Exception):
    def __init__(self, message: str, status: int = 1) -> None:
        super().__init__(message)
        self.status = status


class GitHub:
    def check_key(self, key: str) -> str:
        if not re.fullmatch(r"[0-9]+", key):
            raise TrackerError(f"tracker.py: GitHub issue keys are digits, got {key!r}", 2)
        return key

    def gh(self, *args: str, stdin: str | None = None) -> str:
        result = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True)
        if result.returncode != 0:
            sys.stderr.write(result.stderr)
            raise TrackerError("", result.returncode)
        return result.stdout

    def view(self, key: str) -> str:
        key = self.check_key(key)
        data = json.loads(self.gh("issue", "view", key, "--json", "number,title,state,body,comments"))
        lines = [f"#{data['number']} {data['title']}", f"State: {data['state']}", "", data["body"].strip(), "", "## Comments", ""]
        comments = data["comments"]
        if not comments:
            lines.append("No comments.")
        for comment in comments:
            author = (comment.get("author") or {}).get("login", "unknown")
            lines += [f"### {author}, {comment['createdAt']}", "", comment["body"].strip(), ""]
        return "\n".join(lines).rstrip("\n") + "\n"

    def set_change(self, key: str, path: str) -> None:
        key = self.check_key(key)
        body = json.loads(self.gh("issue", "view", key, "--json", "body"))["body"]
        first, _, rest = body.partition("\n")
        if first.startswith("Change:"):
            body = f"Change: {path}\n{rest}"
        else:
            body = f"Change: {path}\n\n{body}"
        self.gh("issue", "edit", key, "--body-file", "-", stdin=body)


BACKENDS = {"github": GitHub}


def load_tracker(path: Path = TRACKER_FILE):
    if not path.exists():
        sys.stderr.write(f"tracker.py: {path} is missing, assuming github. The updater adds it.\n")
        return BACKENDS["github"]()
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError) as error:
        raise TrackerError(f"tracker.py: cannot read {path}: {error}")
    names = TRACKER_LINE.findall(text)
    if len(names) != 1:
        raise TrackerError(f"tracker.py: {path} needs exactly one 'Tracker: <name>' line, found {len(names)}")
    if names[0] not in BACKENDS:
        raise TrackerError(f"tracker.py: unknown tracker {names[0]!r} in {path}. Known: {', '.join(sorted(BACKENDS))}")
    return BACKENDS[names[0]]()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Issue tracker operations.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("view", help="print an issue with its comments").add_argument("issue")
    change = sub.add_parser("set-change", help="make 'Change: <path>' the first line of the issue body")
    change.add_argument("issue")
    change.add_argument("path")
    args = parser.parse_args(argv)
    try:
        tracker = load_tracker()
        if args.command == "view":
            sys.stdout.write(tracker.view(args.issue))
        else:
            tracker.set_change(args.issue, args.path)
    except TrackerError as error:
        if str(error):
            sys.stderr.write(str(error) + "\n")
        return error.status
    return 0


if __name__ == "__main__":
    sys.exit(main())
