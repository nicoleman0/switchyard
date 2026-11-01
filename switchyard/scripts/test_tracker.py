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
        return subprocess.run([sys.executable, str(SCRIPT), *args], env=self.env, capture_output=True, text=True)

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


if __name__ == "__main__":
    unittest.main()
