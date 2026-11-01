#!/usr/bin/env python3
"""The only place that talks to the issue tracker. PRs stay on `gh pr`.

  tracker.py view <issue>
  tracker.py list <project>
  tracker.py set-change <issue> <change-path>
  tracker.py set-phase <issue> <phase>
  tracker.py comment <issue> <file>
  tracker.py check

`list` prints a Linear project's open issues in delivery order; on GitHub
it exits 2 and asks for named issues. The tracker comes from
`switchyard/tracker.md`, which may also hold a `Phase | Status` table of
Linear status names. set-phase does nothing on GitHub. Add a backend class
and a BACKENDS entry.
"""

from __future__ import annotations

import argparse
import difflib
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

# Default Linear status for each phase; tracker.md can override any of them.
PHASES = {
    "planning": "Planning",
    "plan-review": "Plan review",
    "building": "In Progress",
    "in-review": "In Review",
    "needs-input": "Needs input",
}

LINEAR_URL = "https://api.linear.app/graphql"
LINEAR_KEY_ENV = "LINEAR_API_KEY"

# Ordered out ("completed" and friends) so the closed rule has one home:
# Linear's issues filter and the blocker check both read this tuple.
CLOSED_TYPES = ("completed", "canceled", "duplicate")

PROJECT_QUERY = (
    "query Project($name: String!) {\n"
    "  projects(first: 50, filter: { or: [{ name: { eqIgnoreCase: $name } }, { slugId: { eq: $name } }] }) {\n"
    "    nodes { id name slugId }\n"
    "  }\n"
    "}"
)

PROJECTS_QUERY = (
    "query Projects {\n"
    "  projects(first: 250) { nodes { name slugId } pageInfo { hasNextPage } }\n"
    "}"
)

# Each connection multiplies its children by `first` in Linear's complexity
# budget, so issue relations are paged apart from the issues (about 90 points
# per issue; `first: 50` on relations alone would go over the 10,000 limit).
RELATION_FIELDS = (
    "nodes { type issue { identifier state { type } } }"
    " pageInfo { hasNextPage endCursor }"
)

PROJECT_ISSUES_QUERY = (
    "query ProjectIssues($id: String!, $after: String) {\n"
    "  project(id: $id) {\n"
    "    issues(first: 50, after: $after, filter: { state: { type: { nin: "
    + json.dumps(list(CLOSED_TYPES)) + " } } }) {\n"
    "      nodes { identifier title sortOrder state { name type } projectMilestone { name sortOrder }\n"
    "        inverseRelations(first: 20) {\n"
    "          " + RELATION_FIELDS + "\n"
    "        }\n"
    "      }\n"
    "      pageInfo { hasNextPage endCursor }\n"
    "    }\n"
    "  }\n"
    "}"
)

RELATIONS_QUERY = (
    "query Relations($id: String!, $after: String) {\n"
    "  issue(id: $id) {\n"
    "    inverseRelations(first: 100, after: $after) {\n"
    "      " + RELATION_FIELDS + "\n"
    "    }\n"
    "  }\n"
    "}"
)

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


def key_parts(identifier: str) -> tuple:
    """ENG-10 sorts after ENG-9, so the number compares as a number."""
    team, dash, number = identifier.partition("-")
    return (team, int(number) if dash and number.isdigit() else 0)


def blocker_key_parts(identifier: str) -> tuple:
    """Ordering for key-shaped blocker text; non-key text goes last."""
    parts = key_parts(identifier)
    return (0, *parts) if "-" in identifier else (1, identifier, 0)


def base_key(node: dict) -> tuple:
    """Milestone order (no milestone last), then manual order, then the key."""
    milestone = node.get("projectMilestone")
    return (
        float("inf") if milestone is None else milestone["sortOrder"],
        node["sortOrder"],
        *key_parts(node["identifier"]),
    )


def edges(node: dict, open_keys: set) -> tuple:
    """`blocks` relations as in-list blocker keys and outside blocker keys.

    A source the key cannot read comes back without an `issue`; not shown.
    """
    in_list, outside = [], []
    for relation in node.get("inverseRelations", []):
        if relation.get("type") != "blocks":
            continue
        blocker = relation.get("issue")
        if not blocker or blocker["state"]["type"] in CLOSED_TYPES:
            continue
        key = blocker["identifier"]
        (in_list if key in open_keys else outside).append(key)
    return in_list, outside


def delivery_order(nodes: list) -> list:
    """Order a Linear project's open issues for delivery.

    Base order is the milestone's order in the project (none last), then
    Linear's manual `sortOrder`, then the key. Each issue's blockers come
    from its `blocks` relations: an open blocker in the list is an edge, one
    outside the list is shown as `<key> (outside)` and changes nothing, one
    closed is ignored. Each step emits the first issue in base order whose
    in-list blockers are all emitted (Kahn's algorithm with the base index
    as priority), so a blocked issue lands after its blockers and the
    relative order of the others is kept. A cycle raises and names members.

    Takes the project's issue nodes as plain dicts shaped like the GraphQL
    query's `nodes`, with `inverseRelations` flattened to a node list.
    Returns new dicts in delivery order with a `blockers` display list.
    """
    base = [node for node in nodes if node["state"]["type"] not in CLOSED_TYPES]
    base.sort(key=base_key)
    open_keys = {node["identifier"] for node in base}
    position = {node["identifier"]: index for index, node in enumerate(base)}

    depends_on, blocker_lists = {}, {}
    for node in base:
        in_list, outside = edges(node, open_keys)
        in_list.sort(key=position.__getitem__)
        outside.sort(key=blocker_key_parts)
        depends_on[node["identifier"]] = set(in_list)
        blocker_lists[node["identifier"]] = [*in_list, *(f"{key} (outside)" for key in outside)]

    emitted, ordered, left = set(), [], list(base)
    while left:
        for node in left:
            if depends_on[node["identifier"]] <= emitted:
                ordered.append({**node, "blockers": blocker_lists[node["identifier"]]})
                emitted.add(node["identifier"])
                left.remove(node)
                break
        else:
            members = cycle_members(left, depends_on, emitted)
            raise TrackerError(f"tracker.py: blocked-by cycle: {' -> '.join([*members, members[0]])}")
    return ordered


def cycle_members(left: list, depends_on: dict, emitted: set) -> list:
    """Walk one left issue's unemitted blockers until a key repeats.

    Every left issue has an unemitted in-list blocker (else the loop would
    have emitted it), so the walk only visits left keys and stops.
    """
    start = next(node["identifier"] for node in left if depends_on[node["identifier"]] - emitted)
    seen, current = [], start
    while current not in seen:
        seen.append(current)
        current = sorted(depends_on[current] - emitted, key=blocker_key_parts)[0]
    return seen[seen.index(current):]


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

    def set_phase(self, key: str, phase: str) -> None:
        # GitHub issues have no workflow status; checking the key keeps typos loud.
        self.check_key(key)

    def comment(self, key: str, body: str) -> None:
        key = self.check_key(key)
        self.gh("issue", "comment", key, "--body-file", "-", stdin=body)

    def list(self, name: str) -> str:
        # A second way to order GitHub batches is spec work the issue does
        # not ask for; the maintainer names issues and milestones.
        raise TrackerError(
            "tracker.py: list reads a Linear project. On GitHub, name the issues; milestones set the order.",
            2,
        )


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

    def __init__(self, transport=None, statuses: dict | None = None) -> None:
        self._transport = transport
        self.statuses = {**PHASES, **(statuses or {})}

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

    def set_phase(self, key: str, phase: str) -> None:
        key = self.check_key(key)
        wanted = self.statuses[phase]
        issue = self.lookup(key, "id team { name states(first: 250) { nodes { id name } pageInfo { hasNextPage } } }")
        team = issue["team"]
        states = team["states"]
        if states["pageInfo"]["hasNextPage"]:
            # Paging for a team this large is not worth it; a silent miss would be worse.
            raise TrackerError(f"Linear team {team['name']} has more than 250 statuses; tracker.py reads only 250")
        ids = [state["id"] for state in states["nodes"] if state["name"] == wanted]
        if not ids:
            names = ", ".join(state["name"] for state in states["nodes"])
            raise TrackerError(
                f"Linear team {team['name']} has no status {wanted!r} for phase {phase}. Its statuses: {names}. "
                f"Add the status in Linear, or name another in the Phase | Status table in switchyard/tracker.md."
            )
        self.update(issue["id"], {"stateId": ids[0]})

    def comment(self, key: str, body: str) -> None:
        key = self.check_key(key)
        issue = self.lookup(key, "id")
        self.mutate(
            "commentCreate",
            "mutation Comment($input: CommentCreateInput!) { commentCreate(input: $input) { success } }",
            {"input": {"issueId": issue["id"], "body": body}},
        )

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

    def find_project(self, name: str) -> dict:
        """Return the project by name without case or slug id.

        No match exits 1 with close project names (every name when none is
        close); several matches exit 1 with each one's slug id to pass.
        """
        projects = self.query(PROJECT_QUERY, {"name": name})["projects"]["nodes"]
        if len(projects) == 1:
            return projects[0]
        if projects:
            listing = "\n  ".join(f"{project['name']} ({project['slugId']})" for project in projects)
            raise TrackerError(
                f"tracker.py: several Linear projects are called {name!r}:\n  {listing}\n"
                f"Pass one project's slug id, such as `tracker.py list {projects[0]['slugId']}`."
            )
        page = self.query(PROJECTS_QUERY, {})["projects"]
        lowered = name.lower()
        named = [project["name"] for project in page["nodes"]]
        close = sorted(set(difflib.get_close_matches(name, named)))
        close += sorted(set(n for n in named if lowered in n.lower()) - set(close))
        shown = close or named
        more = ", and more" if page["pageInfo"]["hasNextPage"] else ""
        raise TrackerError(f"tracker.py: Linear has no project {name!r}. Projects: {', '.join(shown)}{more}")

    def project_issues(self, project_id: str) -> list:
        """Every open issue in the project, with `inverseRelations` flattened."""
        nodes, after = [], None
        while True:
            connection = self.query(PROJECT_ISSUES_QUERY, {"id": project_id, "after": after})["project"]["issues"]
            for node in connection["nodes"]:
                related = node["inverseRelations"]
                flat = list(related["nodes"])
                while related["pageInfo"]["hasNextPage"]:
                    related = self.query(
                        RELATIONS_QUERY,
                        {"id": node["identifier"], "after": related["pageInfo"]["endCursor"]},
                    )["issue"]["inverseRelations"]
                    flat += related["nodes"]
                nodes.append({**node, "inverseRelations": flat})
            if not connection["pageInfo"]["hasNextPage"]:
                return nodes
            after = connection["pageInfo"]["endCursor"]

    def list(self, name: str) -> str:
        project = self.find_project(name)
        ordered = delivery_order(self.project_issues(project["id"]))
        if not ordered:
            return f"Project {project['name']} ({project['slugId']})\nNo open issues.\n"
        lines = [f"Project {project['name']} ({project['slugId']})"]
        for node in ordered:
            milestone = (node.get("projectMilestone") or {}).get("name") or "-"
            blockers = ", ".join(node["blockers"]) or "-"
            lines.append("\t".join([node["identifier"], node["state"]["name"], milestone, blockers, node["title"]]))
        return "\n".join(lines) + "\n"


BACKENDS = {"github": GitHub, "linear": Linear}


def read_statuses(text: str, path: Path) -> dict:
    """Read the optional `| Phase | Status |` table; every other line is ignored."""
    statuses = {}
    for line in text.splitlines():
        row = line.strip()
        if not row.startswith("|"):
            continue
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if cells[0] == "Phase" or all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        problem = None
        if len(cells) != 2:
            problem = "needs two cells, a phase and a status"
        elif cells[0] not in PHASES:
            problem = "names an unknown phase"
        elif cells[0] in statuses:
            problem = "repeats a phase"
        elif not cells[1]:
            problem = "has an empty status"
        if problem:
            raise TrackerError(f"tracker.py: the row {row!r} in {path} {problem}. Phases: {', '.join(PHASES)}")
        statuses[cells[0]] = cells[1]
    return statuses


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
    statuses = read_statuses(text, path)
    backend = BACKENDS[names[0]]
    return backend(statuses=statuses) if backend is Linear else backend()


def read_body(path: str) -> str:
    try:
        body = Path(path).read_text()
    except (OSError, UnicodeDecodeError) as error:
        raise TrackerError(f"tracker.py: cannot read {path}: {error}")
    if not body.strip():
        raise TrackerError(f"tracker.py: {path} is blank; there is nothing to post")
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Issue tracker operations.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("view", help="print an issue with its comments").add_argument("issue")
    change = sub.add_parser("set-change", help="make 'Change: <path>' the first line of the issue body")
    change.add_argument("issue")
    change.add_argument("path")
    phase = sub.add_parser("set-phase", help="move the issue to the status for a phase (nothing on GitHub)")
    phase.add_argument("issue")
    phase.add_argument("phase", choices=PHASES)
    comment = sub.add_parser("comment", help="post a file as an issue comment")
    comment.add_argument("issue")
    comment.add_argument("file")
    listing = sub.add_parser("list", help="print a Linear project's open issues in delivery order")
    listing.add_argument("project")
    sub.add_parser("check", help="confirm the configured tracker is usable and print its name")
    args = parser.parse_args(argv)
    try:
        tracker = load_tracker()
        if args.command == "view":
            sys.stdout.write(tracker.view(args.issue))
        elif args.command == "list":
            sys.stdout.write(tracker.list(args.project))
        elif args.command == "set-change":
            tracker.set_change(args.issue, args.path)
        elif args.command == "set-phase":
            tracker.set_phase(args.issue, args.phase)
        elif args.command == "comment":
            tracker.comment(args.issue, read_body(args.file))
        else:
            sys.stdout.write(tracker.check() + "\n")
    except TrackerError as error:
        if str(error):
            sys.stderr.write(str(error) + "\n")
        return error.status
    return 0


if __name__ == "__main__":
    sys.exit(main())
