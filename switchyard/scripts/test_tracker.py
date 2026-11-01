"""Run tracker.py against a fake `gh` that logs its arguments and stdin."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
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


if __name__ == "__main__":
    unittest.main()
