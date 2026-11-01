"""Run tracker.py against a fake `gh` or a fake Linear transport."""

import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, HTTPServer
import unittest

SCRIPT = Path(__file__).with_name("tracker.py").resolve()
sys.path.insert(0, str(SCRIPT.parent))
import tracker  # noqa: E402

GH = r'''
import json, os, sys
args = sys.argv[1:]
stdin = sys.stdin.read() if "-" in args else ""
with open(os.environ["GH_LOG"], "a") as log:
    log.write(json.dumps({"args": args, "stdin": stdin}) + "\n")
if os.environ.get("GH_FAIL"):
    sys.stderr.write("gh: boom\n")
    sys.exit(int(os.environ["GH_FAIL"]))
if args[:2] == ["issue", "view"]:
    sys.stdout.write(os.environ["GH_ISSUE"])
'''


class TrackerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        # Own skill folder, so the repo's tracker.md never decides these tests.
        scripts = root / "switchyard" / "scripts"
        scripts.mkdir(parents=True)
        (root / "switchyard" / "tracker.md").write_text("Tracker: github\n")
        self.script = scripts / "tracker.py"
        self.script.write_bytes(SCRIPT.read_bytes())
        bin_dir = root / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text("#!" + sys.executable + "\n" + GH)
        gh.chmod(0o755)
        self.log = root / "gh.log"
        self.env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "GH_LOG": str(self.log)}

    def issue(self, body: str, comments: list | None = None) -> None:
        self.env["GH_ISSUE"] = json.dumps(
            {"number": 148, "title": "Tie to gh", "state": "OPEN", "body": body, "comments": comments or []}
        )

    def run_tool(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(self.script), *args], env=self.env, capture_output=True, text=True)

    def calls(self) -> list:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_view_prints_title_state_body_and_comments(self) -> None:
        self.issue("The body.", [{"author": {"login": "ann"}, "createdAt": "2026-01-02", "body": "A note."}])
        result = self.run_tool("view", "148")
        self.assertEqual(result.returncode, 0, result.stderr)
        for text in ("#148 Tie to gh", "State: OPEN", "The body.", "### ann, 2026-01-02", "A note."):
            self.assertIn(text, result.stdout)
        self.assertNotIn("No comments.", result.stdout)

    def test_view_without_comments(self) -> None:
        self.issue("The body.")
        self.assertIn("No comments.", self.run_tool("view", "148").stdout)

    def test_set_change_prepends_line_and_blank_line(self) -> None:
        self.issue("Problem text.\n")
        self.assertEqual(self.run_tool("set-change", "148", "openspec/changes/x").returncode, 0)
        edit = self.calls()[-1]
        self.assertEqual(edit["args"], ["issue", "edit", "148", "--body-file", "-"])
        self.assertEqual(edit["stdin"], "Change: openspec/changes/x\n\nProblem text.\n")

    def test_set_change_replaces_existing_first_line(self) -> None:
        self.issue("Change: openspec/changes/old\n\nProblem \"quoted\"\nline two\n")
        self.assertEqual(self.run_tool("set-change", "148", "openspec/changes/new").returncode, 0)
        self.assertEqual(
            self.calls()[-1]["stdin"], "Change: openspec/changes/new\n\nProblem \"quoted\"\nline two\n"
        )

    def test_non_digit_key_fails_without_calling_gh(self) -> None:
        result = self.run_tool("view", "ENG-1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])

    def test_gh_failure_passes_status_and_stderr(self) -> None:
        self.env["GH_FAIL"] = "4"
        result = self.run_tool("view", "148")
        self.assertEqual(result.returncode, 4)
        self.assertIn("gh: boom", result.stderr)


class LoadTrackerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "tracker.md"

    def test_reads_github(self) -> None:
        self.path.write_text("# Project tracker\n\nTracker: github\n")
        self.assertIsInstance(tracker.load_tracker(self.path), tracker.GitHub)

    def test_unknown_name_lists_known(self) -> None:
        self.path.write_text("Tracker: jira\n")
        with self.assertRaises(tracker.TrackerError) as ctx:
            tracker.load_tracker(self.path)
        self.assertEqual(ctx.exception.status, 1)
        self.assertIn("github", str(ctx.exception))

    def test_name_on_next_line_is_not_a_tracker_line(self) -> None:
        self.path.write_text("Tracker:\ngithub\n")
        with self.assertRaises(tracker.TrackerError) as ctx:
            tracker.load_tracker(self.path)
        self.assertIn("found 0", str(ctx.exception))

    def test_no_tracker_line(self) -> None:
        self.path.write_text("# Project tracker\n")
        with self.assertRaises(tracker.TrackerError) as ctx:
            tracker.load_tracker(self.path)
        self.assertEqual(ctx.exception.status, 1)

    def test_two_tracker_lines(self) -> None:
        self.path.write_text("Tracker: github\nTracker: github\n")
        with self.assertRaises(tracker.TrackerError):
            tracker.load_tracker(self.path)

    def test_missing_file_uses_github_and_notes_on_stderr(self) -> None:
        from contextlib import redirect_stderr
        import io

        err = io.StringIO()
        with redirect_stderr(err):
            backend = tracker.load_tracker(self.path)
        self.assertIsInstance(backend, tracker.GitHub)
        self.assertIn("assuming github", err.getvalue())


def issue_page(nodes, has_next=False, end_cursor=None):
    return {"data": {
        "issue": {
            "identifier": "ENG-123", "title": "Fix login", "description": "Broken.\n",
            "state": {"name": "In Progress"},
            "comments": {"nodes": nodes, "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor}},
        }
    }}


def comment(author, created, body):
    return {"body": body, "createdAt": created, "user": None if author is None else {"name": author}}


class RecordingTransport:
    """Returns queued responses and records every query with its variables."""

    def __init__(self, responses) -> None:
        self.responses = list(responses)
        self.calls = []

    def __call__(self, query: str, variables: dict) -> dict:
        self.calls.append({"query": query, "variables": variables})
        if not self.responses:
            raise AssertionError("unexpected extra transport call")
        return self.responses.pop(0)


class LinearMain:
    """Runs tracker.main in the process against a patched load_tracker."""

    def setUp(self) -> None:
        self.saved_load = tracker.load_tracker
        self.addCleanup(setattr, tracker, "load_tracker", self.saved_load)
        self.saved_env = os.environ.pop("LINEAR_API_KEY", None)
        self.addCleanup(self.restore_env)
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

    def restore_env(self) -> None:
        os.environ.pop("LINEAR_API_KEY", None)
        if self.saved_env is not None:
            os.environ["LINEAR_API_KEY"] = self.saved_env

    def load(self, backend) -> None:
        tracker.load_tracker = lambda *args, **kwargs: backend
        self.backend = backend

    def run_tool(self, *args: str) -> int:
        with redirect_stdout(self.stdout), redirect_stderr(self.stderr):
            return tracker.main(list(args))


class LinearViewTest(LinearMain, unittest.TestCase):
    def test_view_prints_title_state_body_and_sorted_comments(self) -> None:
        transport = RecordingTransport([
            issue_page([comment("Bea", "2026-02-10", "Newer note.")], True, "cursor-1"),
            issue_page([comment("Ann", "2026-01-05", "Older note.")], False),
        ])
        self.load(tracker.Linear(transport))
        status = self.run_tool("view", "ENG-123")
        self.assertEqual(status, 0, self.stderr.getvalue())
        out = self.stdout.getvalue()
        for text in ("ENG-123 Fix login", "State: In Progress", "Broken.", "Ann", "2026-01-05",
                     "Older note.", "Bea", "Newer note."):
            self.assertIn(text, out)
        self.assertLess(out.index("Older note."), out.index("Newer note."))
        self.assertNotIn("No comments.", out)
        first_id = transport.calls[0]["variables"]["id"]
        second_id = transport.calls[1]["variables"]["id"]
        self.assertEqual((first_id, second_id), ("ENG-123", "ENG-123"))
        self.assertEqual(transport.calls[1]["variables"]["after"], "cursor-1")

    def test_view_prints_unknown_for_a_null_user(self) -> None:
        transport = RecordingTransport([issue_page([comment(None, "2026-01-05", "From a bot.")])])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("view", "ENG-123"), 0, self.stderr.getvalue())
        self.assertIn("### unknown, 2026-01-05", self.stdout.getvalue())

    def test_view_without_comments(self) -> None:
        transport = RecordingTransport([issue_page([])])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("view", "ENG-123"), 0, self.stderr.getvalue())
        self.assertIn("No comments.", self.stdout.getvalue())

    def test_view_with_no_description_prints_header_and_comments(self) -> None:
        page = issue_page([])
        page["data"]["issue"]["description"] = None
        transport = RecordingTransport([page])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("view", "ENG-123"), 0, self.stderr.getvalue())
        out = self.stdout.getvalue()
        self.assertIn("ENG-123 Fix login", out)
        self.assertLess(out.index("State: In Progress"), out.index("No comments."))

    def test_wrong_form_keys_exit_before_any_call(self) -> None:
        for key in ("149", "eng-123"):
            with self.subTest(key=key):
                transport = RecordingTransport([{}])
                self.load(tracker.Linear(transport))
                status = self.run_tool("view", key)
                self.assertEqual(status, 2, self.stderr.getvalue())
                self.assertIn("such as ENG-123", self.stderr.getvalue())
                self.assertEqual(transport.calls, [])


class LinearSetChangeTest(LinearMain, unittest.TestCase):
    def change(self, description: str) -> RecordingTransport:
        transport = RecordingTransport([
            {"data": {"issue": {"id": "uuid-1", "description": description}}},
            {"data": {"issueUpdate": {"success": True}}},
        ])
        self.load(tracker.Linear(transport))
        return transport

    def test_set_change_prepends_and_replaces_via_issue_update(self) -> None:
        cases = (
            ("Problem \"quoted\"\nline two", "Change: openspec/changes/x\n\nProblem \"quoted\"\nline two"),
            ("Change: openspec/changes/old\n\nProblem text", "Change: openspec/changes/x\n\nProblem text"),
        )
        for description, expected in cases:
            with self.subTest(description=description):
                transport = self.change(description)
                self.assertEqual(self.run_tool("set-change", "ENG-123", "openspec/changes/x"), 0, self.stderr.getvalue())
                calls = transport.calls
                self.assertIn("issue(id: $id) { id description }", calls[0]["query"])
                self.assertIn("issueUpdate", calls[1]["query"])
                self.assertEqual(calls[1]["variables"], {"id": "uuid-1", "input": {"description": expected}})

    def test_set_change_with_success_false_exits_one(self) -> None:
        transport = RecordingTransport([
            {"data": {"issue": {"id": "uuid-1", "description": "Problem."}}},
            {"data": {"issueUpdate": {"success": False}}},
        ])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("set-change", "ENG-123", "openspec/changes/x"), 1, self.stdout.getvalue())
        self.assertIn("success: false", self.stderr.getvalue())


class LinearErrorsTest(LinearMain, unittest.TestCase):
    def test_errors_in_a_response_list_every_message(self) -> None:
        transport = RecordingTransport([
            {"errors": [{"message": "Issue not found"}, {"message": "Team locked"}]},
        ])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("view", "ENG-123"), 1, self.stdout.getvalue())
        stderr = self.stderr.getvalue()
        self.assertIn("Issue not found", stderr)
        self.assertIn("Team locked", stderr)

    def test_missing_key_exits_before_any_call_and_names_the_variable(self) -> None:
        transport = RecordingTransport([{}])
        self.load(tracker.Linear())
        self.assertEqual(self.run_tool("view", "ENG-123"), 1, self.stdout.getvalue())
        self.assertIn("LINEAR_API_KEY", self.stderr.getvalue())
        self.assertEqual(transport.calls, [])


class CheckTest(LinearMain, unittest.TestCase):
    def test_check_on_github_prints_github_and_calls_nothing(self) -> None:
        self.load(tracker.GitHub())
        self.assertEqual(self.run_tool("check"), 0, self.stderr.getvalue())
        self.assertEqual(self.stdout.getvalue(), "github\n")

    def test_check_on_linear_asks_the_viewer(self) -> None:
        transport = RecordingTransport([{"data": {"viewer": {"id": "me"}}}])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("check"), 0, self.stderr.getvalue())
        self.assertEqual(self.stdout.getvalue(), "linear\n")
        self.assertIn("viewer", transport.calls[0]["query"])


class LinearHTTPTest(unittest.TestCase):
    """graphql_post against a local server: header, body, errors, and failures."""

    KEY = "lin_dev_attempt1847"

    def setUp(self) -> None:
        self.log = []
        server_log = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                server_log.log.append({"headers": dict(self.headers), "body": body})
                payload = server_log.payload or {"data": {}}
                status = server_log.status
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())

            def log_message(self, *args) -> None:
                pass

        self.status = 200
        self.payload = None
        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        url = f"http://127.0.0.1:{self.server.server_port}/graphql"
        self.post = tracker.graphql_post(url, self.KEY)

    def test_sends_key_query_and_variables(self) -> None:
        self.post("query { issue }", {"id": "ENG-123"})
        (request,) = self.log
        self.assertEqual(request["headers"].get("Authorization"), self.KEY)
        self.assertNotIn("Bearer", request["headers"].get("Authorization", ""))
        self.assertEqual(request["headers"].get("Content-Type"), "application/json")
        self.assertEqual(request["body"], {"query": "query { issue }", "variables": {"id": "ENG-123"}})

    def test_bad_status_with_errors_body_returns_the_errors(self) -> None:
        self.status = 400
        self.payload = {"errors": [{"message": "Validation failed"}]}
        payload = self.post("query { issue }", {})
        self.assertEqual(payload["errors"][0]["message"], "Validation failed")
        backend = tracker.Linear(transport=self.post)
        with self.assertRaises(tracker.TrackerError) as ctx:
            backend.query("query { issue }", {})
        self.assertIn("Validation failed", str(ctx.exception))

    def test_bad_status_without_json_names_the_status(self) -> None:
        self.status = 500
        self.payload = {"data": {}}  # a JSON body with no errors list still fails on the status
        with self.assertRaises(tracker.TrackerError) as ctx:
            self.post("query { issue }", {})
        self.assertIn("500", str(ctx.exception))

    def test_connection_refused_names_the_url(self) -> None:
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        closed_port = probe.getsockname()[1]
        probe.close()
        post = tracker.graphql_post(f"http://127.0.0.1:{closed_port}/graphql", self.KEY)
        with self.assertRaises(tracker.TrackerError) as ctx:
            post("query { issue }", {})
        self.assertIn(f"127.0.0.1:{closed_port}", str(ctx.exception))

    def test_messages_never_contain_the_key(self) -> None:
        self.status = 400
        self.payload = {"errors": [{"message": "Bad request"}]}
        backend = tracker.Linear(transport=self.post)
        with self.assertRaises(tracker.TrackerError) as ctx:
            backend.query("query { issue }", {})
        self.assertNotIn(self.KEY, str(ctx.exception))


class LoadTrackerLinearTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "tracker.md"

    def test_reads_linear(self) -> None:
        self.path.write_text("# Project tracker\n\nTracker: linear\n")
        self.assertIsInstance(tracker.load_tracker(self.path), tracker.Linear)

    def test_unknown_name_lists_known(self) -> None:
        self.path.write_text("Tracker: jira\n")
        with self.assertRaises(tracker.TrackerError) as ctx:
            tracker.load_tracker(self.path)
        self.assertEqual(ctx.exception.status, 1)
        self.assertIn("github", str(ctx.exception))
        self.assertIn("linear", str(ctx.exception))



def team_page(names, has_next=False):
    return {"data": {"issue": {"id": "uuid-1", "team": {"name": "Engineering", "states": {
        "nodes": [{"id": f"state-{name}", "name": name} for name in names],
        "pageInfo": {"hasNextPage": has_next},
    }}}}}


LINEAR_DEFAULTS = ["Backlog", "Todo", "In Progress", "In Review", "Done", "Canceled"]
UPDATED = {"data": {"issueUpdate": {"success": True}}}


class LinearSetPhaseTest(LinearMain, unittest.TestCase):
    def test_building_sends_the_in_progress_state(self) -> None:
        transport = RecordingTransport([team_page(LINEAR_DEFAULTS), UPDATED])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("set-phase", "ENG-123", "building"), 0, self.stderr.getvalue())
        self.assertEqual(transport.calls[0]["variables"], {"id": "ENG-123"})
        self.assertIn("states(first: 250)", transport.calls[0]["query"])
        self.assertIn("issueUpdate", transport.calls[1]["query"])
        self.assertEqual(transport.calls[1]["variables"], {"id": "uuid-1", "input": {"stateId": "state-In Progress"}})
        self.assertEqual(self.stdout.getvalue(), "")

    def test_override_changes_the_state_sent(self) -> None:
        transport = RecordingTransport([team_page(LINEAR_DEFAULTS), UPDATED])
        self.load(tracker.Linear(transport, statuses={"needs-input": "Todo"}))
        self.assertEqual(self.run_tool("set-phase", "ENG-123", "needs-input"), 0, self.stderr.getvalue())
        self.assertEqual(transport.calls[1]["variables"]["input"], {"stateId": "state-Todo"})

    def test_missing_status_lists_the_team_and_sends_no_update(self) -> None:
        transport = RecordingTransport([team_page(LINEAR_DEFAULTS)])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("set-phase", "ENG-123", "needs-input"), 1)
        stderr = self.stderr.getvalue()
        for text in ("'Needs input'", "Engineering", "Backlog, Todo, In Progress, In Review, Done, Canceled"):
            self.assertIn(text, stderr)
        self.assertEqual(len(transport.calls), 1)

    def test_names_match_exactly(self) -> None:
        transport = RecordingTransport([team_page(["in progress"])])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("set-phase", "ENG-123", "building"), 1)
        self.assertEqual(len(transport.calls), 1)

    def test_more_than_one_page_of_statuses_fails(self) -> None:
        transport = RecordingTransport([team_page(LINEAR_DEFAULTS, has_next=True)])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("set-phase", "ENG-123", "building"), 1)
        self.assertIn("more than 250 statuses", self.stderr.getvalue())
        self.assertEqual(len(transport.calls), 1)

    def test_success_false_exits_one(self) -> None:
        transport = RecordingTransport([team_page(LINEAR_DEFAULTS), {"data": {"issueUpdate": {"success": False}}}])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("set-phase", "ENG-123", "building"), 1)
        self.assertIn("success: false", self.stderr.getvalue())

    def test_unknown_issue_exits_one(self) -> None:
        transport = RecordingTransport([{"data": {"issue": None}}])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("set-phase", "ENG-123", "building"), 1)
        self.assertIn("Linear has no issue ENG-123", self.stderr.getvalue())

    def test_unknown_phase_exits_two_and_calls_nothing(self) -> None:
        transport = RecordingTransport([])
        self.load(tracker.Linear(transport))
        with self.assertRaises(SystemExit) as ctx:
            self.run_tool("set-phase", "ENG-123", "done")
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("needs-input", self.stderr.getvalue())
        self.assertEqual(transport.calls, [])

    def test_github_key_on_linear_exits_two(self) -> None:
        transport = RecordingTransport([])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("set-phase", "149", "building"), 2)
        self.assertEqual(transport.calls, [])


class LinearCommentTest(LinearMain, unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.file = Path(tmp.name) / "q.md"

    def test_comment_sends_the_uuid_and_exact_body(self) -> None:
        body = "Questions from Switchyard\n\n1. \"Which\" status?\n"
        self.file.write_text(body)
        transport = RecordingTransport([{"data": {"issue": {"id": "uuid-1"}}},
                                        {"data": {"commentCreate": {"success": True}}}])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("comment", "ENG-123", str(self.file)), 0, self.stderr.getvalue())
        self.assertIn("commentCreate", transport.calls[1]["query"])
        self.assertEqual(transport.calls[1]["variables"], {"input": {"issueId": "uuid-1", "body": body}})

    def test_comment_success_false_exits_one(self) -> None:
        self.file.write_text("text")
        transport = RecordingTransport([{"data": {"issue": {"id": "uuid-1"}}},
                                        {"data": {"commentCreate": {"success": False}}}])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("comment", "ENG-123", str(self.file)), 1)
        self.assertIn("commentCreate returned success: false", self.stderr.getvalue())

    def test_blank_or_missing_file_exits_one_without_a_call(self) -> None:
        self.file.write_text(" \n\t\n")
        for path in (self.file, self.file.with_name("missing.md")):
            with self.subTest(path=path.name):
                transport = RecordingTransport([])
                self.load(tracker.Linear(transport))
                self.assertEqual(self.run_tool("comment", "ENG-123", str(path)), 1)
                self.assertIn(path.name, self.stderr.getvalue())
                self.assertEqual(transport.calls, [])

    def test_missing_key_names_the_variable_for_new_commands(self) -> None:
        self.file.write_text("text")
        for args in (("set-phase", "ENG-123", "building"), ("comment", "ENG-123", str(self.file))):
            with self.subTest(command=args[0]):
                self.stderr = io.StringIO()
                self.load(tracker.Linear())
                self.assertEqual(self.run_tool(*args), 1)
                self.assertIn("LINEAR_API_KEY is not set", self.stderr.getvalue())


class GitHubPhaseAndCommentTest(TrackerTest):
    def test_set_phase_does_nothing(self) -> None:
        result = self.run_tool("set-phase", "150", "building")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertEqual(self.calls(), [])

    def test_set_phase_checks_the_key(self) -> None:
        self.assertEqual(self.run_tool("set-phase", "ENG-1", "building").returncode, 2)
        self.assertEqual(self.calls(), [])

    def test_comment_posts_the_file(self) -> None:
        path = Path(self.tmp.name) / "q.md"
        path.write_text("Questions from Switchyard\n\n1. Which?\n")
        result = self.run_tool("comment", "150", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        (call,) = self.calls()
        self.assertEqual(call["args"], ["issue", "comment", "150", "--body-file", "-"])
        self.assertEqual(call["stdin"], "Questions from Switchyard\n\n1. Which?\n")

    def test_comment_with_a_blank_file_calls_nothing(self) -> None:
        path = Path(self.tmp.name) / "q.md"
        path.write_text("\n")
        self.assertEqual(self.run_tool("comment", "150", str(path)).returncode, 1)
        self.assertEqual(self.calls(), [])


class StatusTableTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "tracker.md"

    def write(self, *rows: str) -> None:
        self.path.write_text("# Project tracker\n\nTracker: linear\n\n| Phase | Status |\n| --- | --- |\n"
                             + "".join(row + "\n" for row in rows))

    def test_a_row_overrides_one_phase_and_keeps_the_rest(self) -> None:
        self.write("| needs-input | Blocked |")
        backend = tracker.load_tracker(self.path)
        self.assertEqual(backend.statuses, {**tracker.PHASES, "needs-input": "Blocked"})

    def test_no_table_keeps_the_defaults(self) -> None:
        self.path.write_text("# Project tracker\n\nTracker: linear\n")
        self.assertEqual(tracker.load_tracker(self.path).statuses, tracker.PHASES)

    def test_github_checks_the_table_too(self) -> None:
        self.path.write_text("Tracker: github\n\n| Phase | Status |\n|:---|---:|\n| building | Doing |\n")
        self.assertIsInstance(tracker.load_tracker(self.path), tracker.GitHub)
        self.path.write_text("Tracker: github\n\n| shipping | Done |\n")
        with self.assertRaises(tracker.TrackerError):
            tracker.load_tracker(self.path)

    def test_bad_rows_exit_one_on_view_naming_the_row(self) -> None:
        cases = {
            "| shipping | Done |": "unknown phase",
            "| building | Doing |\n| building | Again |": "repeats a phase",
            "| needs-input |  |": "empty status",
            "| needs-input | Blocked | extra |": "two cells",
        }
        for rows, problem in cases.items():
            with self.subTest(rows=rows):
                self.write(rows)
                bad_row = rows.splitlines()[-1]
                stderr = io.StringIO()
                saved = tracker.load_tracker
                tracker.load_tracker = lambda: saved(self.path)
                try:
                    with redirect_stderr(stderr):
                        status = tracker.main(["view", "ENG-123"])
                finally:
                    tracker.load_tracker = saved
                self.assertEqual(status, 1, stderr.getvalue())
                self.assertIn(bad_row, stderr.getvalue())
                self.assertIn(problem, stderr.getvalue())
                self.assertIn("planning, plan-review, building, in-review, needs-input", stderr.getvalue())


def project_find(*nodes) -> dict:
    return {"data": {"projects": {"nodes": list(nodes)}}}


def project_list(names, has_next=False) -> dict:
    return {"data": {"projects": {
        "nodes": [{"name": name, "slugId": f"slug-{name}"} for name in names],
        "pageInfo": {"hasNextPage": has_next},
    }}}


def project_issues_page(nodes, has_next=False, end_cursor=None) -> dict:
    return {"data": {"project": {"issues": {
        "nodes": nodes, "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor}}}}}


def relations_page(nodes, has_next=False, end_cursor=None) -> dict:
    return {"data": {"issue": {"inverseRelations": {
        "nodes": nodes, "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor}}}}}


def relation(blocker: str, kind="blocks", state_type="unstarted") -> dict:
    return {"type": kind, "issue": {"identifier": blocker, "state": {"type": state_type}, "project": {"id": "other"}}}


def issue_node(key, title="Fix it", sort=0.0, milestone=None, status="Todo", status_type="unstarted", relations=()):
    return {"identifier": key, "title": title, "sortOrder": sort,
            "state": {"name": status, "type": status_type},
            "projectMilestone": milestone,
            "inverseRelations": {"nodes": list(relations), "pageInfo": {"hasNextPage": False, "endCursor": None}}}


ONBOARDING = {"id": "pid-1", "name": "Onboarding", "slugId": "onboard-a"}


def flat_node(key, title="Fix it", sort=0.0, milestone=None, status_type="unstarted", relations=()):
    """A node shaped for delivery_order: relations flattened to a list."""
    return {"identifier": key, "title": title, "sortOrder": sort,
            "state": {"name": "Todo", "type": status_type},
            "projectMilestone": milestone, "inverseRelations": list(relations)}


class DeliveryOrderTest(unittest.TestCase):
    """The ordering rule as a pure function over plain dicts."""

    def test_milestones_first_in_their_order_and_no_milestone_last(self) -> None:
        setup = {"name": "Setup", "sortOrder": 10.0}
        first = {"name": "First", "sortOrder": 0.0}
        issues = [
            flat_node("ENG-3", milestone=setup),
            flat_node("ENG-2", milestone=first),
            flat_node("ENG-4"),
        ]
        self.assertEqual([n["identifier"] for n in tracker.delivery_order(issues)], ["ENG-2", "ENG-3", "ENG-4"])

    def test_key_number_ties_compare_as_numbers(self) -> None:
        issues = [flat_node("ENG-10"), flat_node("ENG-9")]
        self.assertEqual([n["identifier"] for n in tracker.delivery_order(issues)], ["ENG-9", "ENG-10"])

    def test_a_blocked_issue_lands_after_its_blocker_keeping_relative_order(self) -> None:
        issues = [flat_node("ENG-2", relations=[relation("ENG-5")]), flat_node("ENG-3"),
                  flat_node("ENG-5"), flat_node("ENG-6")]
        self.assertEqual([n["identifier"] for n in tracker.delivery_order(issues)], ["ENG-3", "ENG-5", "ENG-2", "ENG-6"])

    def test_a_blocked_issue_does_not_fall_behind_later_milestones(self) -> None:
        first = {"name": "First", "sortOrder": 0.0}
        second = {"name": "Second", "sortOrder": 1.0}
        third = {"name": "Third", "sortOrder": 2.0}
        issues = [
            flat_node("ENG-1", sort=0.0, milestone=first, relations=[relation("ENG-3")]),
            flat_node("ENG-2", sort=1.0, milestone=first),
            flat_node("ENG-3", sort=2.0, milestone=first),
            flat_node("ENG-4", milestone=second),
            flat_node("ENG-5", milestone=third),
        ]
        self.assertEqual([n["identifier"] for n in tracker.delivery_order(issues)],
                         ["ENG-2", "ENG-3", "ENG-1", "ENG-4", "ENG-5"])

    def test_an_outside_blocker_is_shown_and_moves_nothing(self) -> None:
        issues = [flat_node("ENG-2", relations=[relation("OPS-9")]), flat_node("ENG-3")]
        ordered = tracker.delivery_order(issues)
        self.assertEqual([n["identifier"] for n in ordered], ["ENG-2", "ENG-3"])
        self.assertEqual(ordered[0]["blockers"], ["OPS-9 (outside)"])

    def test_a_closed_blocker_is_left_out_of_the_field_and_the_order(self) -> None:
        issues = [flat_node("ENG-2", relations=[relation("ENG-1", state_type="completed")]),
                  flat_node("ENG-1")]
        ordered = tracker.delivery_order(issues)
        self.assertEqual([n["identifier"] for n in ordered], ["ENG-1", "ENG-2"])
        self.assertEqual(ordered[1]["blockers"], [])

    def test_a_related_relation_is_not_a_blocker(self) -> None:
        issues = [flat_node("ENG-2", relations=[relation("ENG-5", kind="related")]), flat_node("ENG-5")]
        ordered = tracker.delivery_order(issues)
        self.assertEqual([n["identifier"] for n in ordered], ["ENG-2", "ENG-5"])
        self.assertEqual(ordered[0]["blockers"], [])

    def test_cycles_raise_and_name_every_member(self) -> None:
        two = [flat_node("ENG-2", relations=[relation("ENG-3")]), flat_node("ENG-3", relations=[relation("ENG-2")])]
        with self.assertRaises(tracker.TrackerError) as ctx:
            tracker.delivery_order(two)
        self.assertIn("ENG-2", str(ctx.exception))
        self.assertIn("ENG-3", str(ctx.exception))
        self.assertIn("cycle", str(ctx.exception))
        three = [flat_node("ENG-2", relations=[relation("ENG-3")]),
                 flat_node("ENG-3", relations=[relation("ENG-7")]),
                 flat_node("ENG-7", relations=[relation("ENG-2")])]
        with self.assertRaises(tracker.TrackerError) as ctx:
            tracker.delivery_order(three)
        for member in ("ENG-2", "ENG-3", "ENG-7"):
            self.assertIn(member, str(ctx.exception))


class LinearFindProjectTest(LinearMain, unittest.TestCase):
    def test_name_without_case_lists_the_project(self) -> None:
        transport = RecordingTransport([
            project_find(ONBOARDING),
            project_issues_page([issue_node("ENG-5", "Seed the database")]),
        ])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("list", "onboarding"), 0, self.stderr.getvalue())
        out = self.stdout.getvalue()
        self.assertIn("Project Onboarding (onboard-a)", out)
        self.assertIn("ENG-5\tTodo\t-\t-\tSeed the database", out)
        first = transport.calls[0]
        # One `or` filter carries both the case-free name and the slug id.
        self.assertIn("or: [{ name: { eqIgnoreCase: $name } }, { slugId: { eq: $name } }]", first["query"])
        self.assertEqual(first["variables"], {"name": "onboarding"})

    def test_an_unknown_project_lists_close_names(self) -> None:
        transport = RecordingTransport([project_find(), project_list(["Onboarding"])])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("list", "Onbording"), 1, self.stdout.getvalue())
        self.assertIn("Onboarding", self.stderr.getvalue())

    def test_an_unrelated_name_lists_every_name_and_more_on_a_full_page(self) -> None:
        transport = RecordingTransport([project_find(), project_list(["Alpha", "Beta", "Gamma"], True)])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("list", "Delivery invoices"), 1)
        stderr = self.stderr.getvalue()
        self.assertIn("Alpha, Beta, Gamma", stderr)
        self.assertIn("and more", stderr)

    def test_two_matches_exit_one_with_both_slug_ids(self) -> None:
        transport = RecordingTransport([
            project_find({"id": "pid-1", "name": "Onboarding", "slugId": "onboard-a"},
                         {"id": "pid-2", "name": "Onboarding", "slugId": "onboard-b"}),
        ])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("list", "Onboarding"), 1)
        stderr = self.stderr.getvalue()
        self.assertIn("onboard-a", stderr)
        self.assertIn("onboard-b", stderr)
        self.assertIn("slug id", stderr)
        self.assertEqual(len(transport.calls), 1)


class LinearProjectIssuesTest(LinearMain, unittest.TestCase):
    def block_paged(self, extra_nodes=()) -> list:
        blocked = issue_node("ENG-2", relations=[])
        blocked["inverseRelations"] = {"nodes": [], "pageInfo": {"hasNextPage": True, "endCursor": "rel-cur-1"}}
        return [
            project_find(ONBOARDING),
            project_issues_page([blocked, *extra_nodes]),
            relations_page([relation("ENG-5")]),
        ]

    def test_two_issue_pages_are_both_read(self) -> None:
        transport = RecordingTransport([
            project_find(ONBOARDING),
            project_issues_page([issue_node("ENG-5")], True, "iss-cur-1"),
            project_issues_page([issue_node("ENG-6")]),
        ])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("list", "Onboarding"), 0, self.stderr.getvalue())
        out = self.stdout.getvalue()
        self.assertLess(out.index("ENG-5"), out.index("ENG-6"))
        self.assertEqual(transport.calls[1]["variables"], {"id": "pid-1", "after": None})
        self.assertEqual(transport.calls[2]["variables"], {"id": "pid-1", "after": "iss-cur-1"})
        self.assertEqual(transport.calls[1]["query"], transport.calls[2]["query"])

    def test_an_issue_with_more_relations_follows_up_and_the_blocker_counts(self) -> None:
        transport = RecordingTransport(self.block_paged(extra_nodes=[issue_node("ENG-5")]))
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("list", "Onboarding"), 0, self.stderr.getvalue())
        follow = transport.calls[2]
        self.assertIn("issue(id: $id)", follow["query"])
        self.assertIn("inverseRelations(first: 100", follow["query"])
        self.assertEqual(follow["variables"], {"id": "ENG-2", "after": "rel-cur-1"})
        second = self.stdout.getvalue().strip().splitlines()
        self.assertEqual(second[1], "ENG-5\tTodo\t-\t-\tFix it")
        self.assertEqual(second[2], "ENG-2\tTodo\t-\tENG-5\tFix it")

    def test_the_issue_query_text_is_pinned(self) -> None:
        transport = RecordingTransport([project_find(ONBOARDING), project_issues_page([])])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("list", "Onboarding"), 0, self.stderr.getvalue())
        query = transport.calls[1]["query"]
        for text in ("project(id: $id)", "issues(first: 50, after: $after",
                     'nin: ["completed", "canceled", "duplicate"]', "inverseRelations(first: 20)",
                     "projectMilestone { name sortOrder }", "state { name type }"):
            self.assertIn(text, query)


class LinearListTest(LinearMain, unittest.TestCase):
    def test_list_prints_the_header_and_lines_in_order(self) -> None:
        setup = {"name": "Setup", "sortOrder": 0.0}
        transport = RecordingTransport([
            project_find(ONBOARDING),
            project_issues_page([
                issue_node("ENG-2", "Add the login form", 1.0, setup, "In Progress", "started",
                           [relation("ENG-5")]),
                issue_node("ENG-5", "Seed the database", 0.0, setup, "Todo", "unstarted"),
            ]),
        ])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("list", "Onboarding"), 0, self.stderr.getvalue())
        self.assertEqual(self.stdout.getvalue(), (
            "Project Onboarding (onboard-a)\n"
            "ENG-5\tTodo\tSetup\t-\tSeed the database\n"
            "ENG-2\tIn Progress\tSetup\tENG-5\tAdd the login form\n"
        ))

    def test_an_empty_project_prints_no_open_issues(self) -> None:
        transport = RecordingTransport([project_find(ONBOARDING), project_issues_page([])])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("list", "Onboarding"), 0, self.stderr.getvalue())
        self.assertEqual(self.stdout.getvalue(), "Project Onboarding (onboard-a)\nNo open issues.\n")

    def test_an_outside_blocker_is_marked(self) -> None:
        transport = RecordingTransport([
            project_find(ONBOARDING),
            project_issues_page([issue_node("ENG-7", "Write the docs", relations=[relation("OPS-9")])]),
        ])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("list", "Onboarding"), 0, self.stderr.getvalue())
        self.assertIn("OPS-9 (outside)", self.stdout.getvalue())

    def test_a_cycle_exits_one_with_nothing_on_stdout(self) -> None:
        transport = RecordingTransport([
            project_find(ONBOARDING),
            project_issues_page([
                issue_node("ENG-2", relations=[relation("ENG-3")]),
                issue_node("ENG-3", relations=[relation("ENG-2")]),
            ]),
        ])
        self.load(tracker.Linear(transport))
        self.assertEqual(self.run_tool("list", "Onboarding"), 1, self.stdout.getvalue())
        self.assertEqual(self.stdout.getvalue(), "")
        stderr = self.stderr.getvalue()
        self.assertIn("ENG-2", stderr)
        self.assertIn("ENG-3", stderr)

    def test_a_missing_key_fails_before_any_call(self) -> None:
        self.load(tracker.Linear())
        self.assertEqual(self.run_tool("list", "Onboarding"), 1, self.stdout.getvalue())
        self.assertIn("LINEAR_API_KEY is not set", self.stderr.getvalue())


class GitHubListTest(TrackerTest):
    def test_list_exits_two_without_calling_gh(self) -> None:
        result = self.run_tool("list", "Onboarding")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("On GitHub", result.stderr)
        self.assertEqual(self.calls(), [])


class KeyAgreementTest(unittest.TestCase):
    """state.py and tracker.py check Linear keys separately; pin that they agree."""

    KEYS = ("ENG-123", "A1-7", "ENG-1234567", "eng-123", "ENG-", "ENG-12a", "-12", "E-1", "1ENG-2")

    def test_state_and_linear_accept_the_same_keys(self) -> None:
        import state

        linear = tracker.Linear()
        for key in self.KEYS:
            if key.isdigit():
                continue
            with self.subTest(key=key):
                try:
                    linear.check_key(key)
                    linear_accepts = True
                except tracker.TrackerError:
                    linear_accepts = False
                self.assertEqual(state.valid_key(key), linear_accepts)


if __name__ == "__main__":
    unittest.main()
