#!/usr/bin/env python3
"""The only place that talks to the issue tracker. PRs stay on `gh pr`.

  tracker.py view <issue>
  tracker.py set-change <issue> <change-path>
  tracker.py check

The tracker comes from `switchyard/tracker.md`. Add a backend class and a
BACKENDS entry.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

TRACKER_FILE = Path(__file__).resolve().parents[1] / "tracker.md"
TRACKER_LINE = re.compile(r"^Tracker:\s*(\S+)\s*$", re.MULTILINE)

LINEAR_URL = "https://api.linear.app/graphql"
LINEAR_KEY_ENV = "LINEAR_API_KEY"
ISSUE_QUERY = (
    "query Issue($id: String!, $after: String) {\n"
    "  issue(id: $id) {\n"
    "    identifier\n"
    "    title\n"
    "    description\n"
    "    state { name }\n"
    "    comments(first: 100, after: $after) {\n"
    "      nodes { body createdAt user { name } }\n"
    "      pageInfo { hasNextPage endCursor }\n"
    "    }\n"
    "  }\n"
    "}"
)


class TrackerError(Exception):
    def __init__(self, message: str, status: int = 1) -> None:
        super().__init__(message)
        self.status = status


def with_change_line(body: str, path: str) -> str:
    """Make `Change: <path>` the first line, replacing one that is already there."""
    first, _, rest = body.partition("\n")
    if first.startswith("Change:"):
        return f"Change: {path}\n{rest}"
    return f"Change: {path}\n\n{body}"


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

    def check(self) -> str:
        # Preflight already runs `gh auth status`; there is nothing to ask here.
        return "github"

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
        self.gh("issue", "edit", key, "--body-file", "-", stdin=with_change_line(body, path))


def graphql_post(url: str, key: str):
    """Return transport(query, variables) -> dict for Linear's GraphQL endpoint."""
    def post(query: str, variables: dict) -> dict:
        request = urllib.request.Request(
            url,
            data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
            headers={"Authorization": key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            try:
                payload = json.loads(error.read())
            except ValueError:
                payload = None
            if isinstance(payload, dict) and "errors" in payload:
                # Linear reports failures in a GraphQL errors list, which can
                # arrive with a 200 or an error status.
                return payload
            raise TrackerError(f"Linear API returned HTTP {error.code} from {url}") from error
        except (urllib.error.URLError, TimeoutError) as error:
            raise TrackerError(f"cannot reach {url}: {error}") from error
    return post


class Linear:
    # Team-key length rules are not published; an uppercase letter leads,
    # letters or digits follow, then a dash and a number.
    KEY_PATTERN = r"[A-Z][A-Z0-9]*-[0-9]+"

    def __init__(self, transport=None) -> None:
        self._transport = transport

    def transport(self):
        # Read at call time so a bad key still parses arguments and validates keys.
        if self._transport is None:
            key = os.environ.get(LINEAR_KEY_ENV)
            if not key:
                raise TrackerError(
                    f"{LINEAR_KEY_ENV} is not set. Create a personal API key in your Linear settings and export it."
                )
            self._transport = graphql_post(LINEAR_URL, key)
        return self._transport

    def query(self, query: str, variables: dict) -> dict:
        payload = self.transport()(query, variables)
        errors = payload.get("errors")
        if errors:
            messages = "; ".join(str(error.get("message", error)) for error in errors)
            raise TrackerError(f"Linear API error: {messages}")
        return payload["data"]

    def check_key(self, key: str) -> str:
        if not re.fullmatch(self.KEY_PATTERN, key):
            raise TrackerError(
                f"tracker.py: Linear issue keys are an uppercase team key, a dash, and a number, "
                f"such as ENG-123, got {key!r}",
                2,
            )
        return key

    def check(self) -> str:
        self.transport()
        try:
            self.query("query Viewer { viewer { id } }", {})
        except TrackerError as error:
            raise TrackerError(f"Linear check failed: {error}. If {LINEAR_KEY_ENV} was rejected, create a new personal API key in your Linear settings.") from None
        return "linear"

    def fetch(self, identifier: str) -> dict:
        issue = self.query(ISSUE_QUERY, {"id": identifier, "after": None})["issue"]
        if issue is None:
            raise TrackerError(f"Linear has no issue {identifier}")
        comments = issue["comments"]
        nodes = comments["nodes"]
        while comments["pageInfo"]["hasNextPage"]:
            comments = self.query(
                ISSUE_QUERY, {"id": identifier, "after": comments["pageInfo"]["endCursor"]}
            )["issue"]["comments"]
            nodes += comments["nodes"]
        return issue

    def view(self, key: str) -> str:
        key = self.check_key(key)
        issue = self.fetch(key)
        lines = [f"{issue['identifier']} {issue['title']}", f"State: {issue['state']['name']}", "",
                 (issue["description"] or "").strip(), "", "## Comments", ""]
        comments = issue["comments"]["nodes"]
        if not comments:
            lines.append("No comments.")
        else:
            # Linear does not promise comment order; ask for the oldest first.
            for comment in sorted(comments, key=lambda comment: comment["createdAt"]):
                author = (comment.get("user") or {}).get("name") or "unknown"
                lines += [f"### {author}, {comment['createdAt']}", "", comment["body"].strip(), ""]
        return "\n".join(lines).rstrip("\n") + "\n"

    def lookup(self, key: str, fields: str) -> dict:
        """Return the issue's `fields` by identifier; mutations need its UUID `id`."""
        issue = self.query(
            f"query IssueId($id: String!) {{ issue(id: $id) {{ {fields} }} }}",
            {"id": key},
        )["issue"]
        if issue is None:
            raise TrackerError(f"Linear has no issue {key}")
        return issue

    def set_change(self, key: str, path: str) -> None:
        key = self.check_key(key)
        issue = self.lookup(key, "id description")
        self.update(issue["id"], {"description": with_change_line(issue["description"] or "", path)})

    def mutate(self, name: str, query: str, variables: dict) -> None:
        if not self.query(query, variables)[name]["success"]:
            # The schema can return a false success without an errors entry.
            raise TrackerError(f"Linear API error: {name} returned success: false")

    def update(self, issue_id: str, fields: dict) -> None:
        self.mutate(
            "issueUpdate",
            "mutation Update($id: String!, $input: IssueUpdateInput!) {"
            " issueUpdate(id: $id, input: $input) { success } }",
            {"id": issue_id, "input": fields},
        )


BACKENDS = {"github": GitHub, "linear": Linear}


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
    sub.add_parser("check", help="confirm the configured tracker is usable and print its name")
    args = parser.parse_args(argv)
    try:
        tracker = load_tracker()
        if args.command == "view":
            sys.stdout.write(tracker.view(args.issue))
        elif args.command == "set-change":
            tracker.set_change(args.issue, args.path)
        else:
            sys.stdout.write(tracker.check() + "\n")
    except TrackerError as error:
        if str(error):
            sys.stderr.write(str(error) + "\n")
        return error.status
    return 0


if __name__ == "__main__":
    sys.exit(main())
