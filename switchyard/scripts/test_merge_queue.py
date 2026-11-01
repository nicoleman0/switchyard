"""Exercise the queue with real rebases and pushes against a temporary origin."""

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parent.parent
REAL_GIT = shutil.which("git")
GH = r'''
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

fixture = Path(os.environ["QUEUE_FIXTURE"])
data = json.loads(fixture.read_text())
args = sys.argv[1:]
with open(os.environ["GH_LOG"], "a") as log:
    log.write(json.dumps(args) + "\n")

def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

def save():
    fixture.write_text(json.dumps(data))

def head(row):
    if row["state"] == "MERGED":
        return row["merged_head"]
    return git("--git-dir", data["origin"], "rev-parse", "refs/heads/" + row["branch"])

if args[:2] == ["pr", "list"]:
    branch = args[args.index("--head") + 1]
    rows = [dict(row, headRefOid=head(row)) for row in data["prs"].values() if row["branch"] == branch]
    print(json.dumps(rows))
    sys.exit(0)
row = data["prs"][args[2]]
if args[1] == "view":
    if args[-1] == "state":
        print(json.dumps({"state": row["state"]}))
    else:
        sequence = row.get("heads", [])
        value = sequence.pop(0) if sequence else head(row)
        save()
        print(json.dumps({"headRefOid": value}))
elif args[1] == "checks":
    sequence = row.get("checks", [{"checks": [{"name": "build", "bucket": "pass"}]}])
    result = sequence[0]
    if len(sequence) > 1:
        sequence.pop(0)
    save()
    if "checks" in result:
        print(json.dumps(result["checks"]))
    print(result.get("stderr", ""), file=sys.stderr)
    sys.exit(result.get("code", 0))
elif args[1] == "merge":
    sha = args[args.index("--match-head-commit") + 1]
    assert sha == head(row), "PR head moved"
    with tempfile.TemporaryDirectory(dir=fixture.parent) as folder:
        git("clone", "--no-hardlinks", "-q", "--branch", "main", data["origin"], folder)
        git("merge", "--squash", "origin/" + row["branch"], cwd=folder)
        git("-c", "user.name=Test", "-c", "user.email=test@example.test", "commit", "-qm", "squash", cwd=folder)
        git("push", "-q", "origin", "main", cwd=folder)
    if not row.get("unconfirmed_merge"):
        row["state"] = "MERGED"
        row["merged_head"] = sha
        save()
else:
    sys.exit("unexpected gh call")
'''


def git(repo, *args):
    return subprocess.run([REAL_GIT, "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


class MergeQueue(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.main = self.base / "main"
        self.main.mkdir()
        git(self.main, "init", "-q", "-b", "main")
        git(self.main, "config", "user.email", "test@example.test")
        git(self.main, "config", "user.name", "Test")
        shutil.copytree(SOURCE, self.main / "switchyard", ignore=shutil.ignore_patterns("__pycache__"))
        self.write(self.main, ".gitignore", ".switchyard/\n")
        self.write(self.main, "switchyard/hooks/checks.sh", "#!/bin/sh\necho project-ok\nexit \"${HOOK_EXIT:-0}\"\n")
        self.write(self.main, "switchyard/hooks/worktree-down.sh", "#!/bin/sh\nexit 0\n")
        self.write(self.main, "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n## [1.0.0]\n\n- old\n")
        self.write(self.main, "openspec/specs/queue/spec.md", "# Queue\n\n")
        self.write(self.main, "code.py", 'value = "base"\n')
        git(self.main, "add", ".")
        git(self.main, "commit", "-qm", "initial")
        self.origin = self.base / "origin.git"
        subprocess.run([REAL_GIT, "init", "--bare", "-q", str(self.origin)], check=True)
        git(self.origin, "symbolic-ref", "HEAD", "refs/heads/main")
        git(self.main, "remote", "add", "origin", str(self.origin))
        git(self.main, "push", "-q", "origin", "main")
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.stub("npx", 'import sys\nprint("OpenSpec stub")\nsys.exit(0)\n')
        self.stub("gh", GH)
        self.stub("git", f'''
import json
import os
import subprocess
import sys
with open(os.environ["GIT_LOG"], "a") as log:
    log.write(json.dumps({{"cwd": os.getcwd(), "args": sys.argv[1:]}}) + "\\n")
if os.environ.get("REJECT_PUSH") and any(arg.startswith("--force-with-lease=") for arg in sys.argv):
    sys.exit("push rejected by fixture")
sys.exit(subprocess.run([{REAL_GIT!r}, *sys.argv[1:]]).returncode)
''')
        self.env = {**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}", "SWITCHYARD_POLL_SECONDS": "0",
                    "QUEUE_FIXTURE": str(self.base / "fixture.json"), "GH_LOG": str(self.base / "gh.log"),
                    "GIT_LOG": str(self.base / "git.log")}
        self.env.pop("HERDR_ENV", None)
        self.trees = {}
        self.data = {"origin": str(self.origin), "prs": {}}

    def write(self, tree, name, text):
        path = tree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def stub(self, name, body):
        path = self.bin / name
        path.write_text(f"#!{sys.executable}\n" + body)
        path.chmod(0o755)

    def save(self):
        Path(self.env["QUEUE_FIXTURE"]).write_text(json.dumps(self.data))

    def issue(self, issue="1"):
        tree = self.base / f"tree-{issue}"
        branch = f"topic-{issue}"
        git(self.main, "worktree", "add", "-q", "-b", branch, str(tree))
        git(tree, "config", "extensions.worktreeConfig", "true")
        git(tree, "config", "--worktree", "remote.origin.pushurl", "disabled://push-from-main")
        self.write(tree, "CHANGELOG.md", f"# Changelog\n\n## [Unreleased]\n\n### Added\n\n- issue {issue}\n\n## [1.0.0]\n\n- old\n")
        self.write(tree, "openspec/specs/queue/spec.md", f"# Queue\n\n## Issue {issue}\n")
        git(tree, "add", ".")
        git(tree, "commit", "-qm", f"issue {issue}")
        git(self.main, "push", "-q", "origin", branch)
        state = self.main / ".switchyard/state" / f"{issue}.json"
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps({"issue": issue, "branch": branch, "path": str(tree),
                                     "owned": "CHANGELOG.md code.py"}))
        self.data["prs"][str(100 + int(issue))] = {"number": 100 + int(issue), "state": "OPEN", "branch": branch,
                                                  "url": f"https://example.test/pr/{issue}"}
        self.save()
        self.trees[issue] = tree
        return tree

    def upstream(self, code=False):
        self.write(self.main, "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- upstream\n\n## [1.0.0]\n\n- old\n")
        self.write(self.main, "openspec/specs/queue/spec.md", "# Queue\n\n## Upstream\n")
        if code:
            self.write(self.main, "code.py", 'value = "upstream"\n')
        git(self.main, "add", ".")
        git(self.main, "commit", "-qm", "advance main")
        git(self.main, "push", "-q", "origin", "main")

    def queue(self, *args, env=None):
        return subprocess.run([sys.executable, str(self.main / "switchyard/scripts/merge-queue.py"), *args],
                              cwd=self.main, env={**self.env, **(env or {})}, capture_output=True, text=True)

    def calls(self, kind="GH"):
        path = Path(self.env[kind + "_LOG"])
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def pushes(self):
        return [call for call in self.calls("GIT") if call["args"][0] == "push" and "--delete" not in call["args"]]

    def assert_status(self, result, code):
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)

    def assert_torn_down(self, issue):
        self.assertFalse(self.trees[issue].exists())
        self.assertFalse((self.main / f".switchyard/state/{issue}.json").exists())

    def test_default_and_resume_after_standalone_merge(self):
        first, second = self.issue("1"), self.issue("2")
        self.upstream()
        result = self.queue("1", "2")
        self.assert_status(result, 3)
        command = shlex.split(result.stdout.splitlines()[-1])
        head = git(first, "rev-parse", "HEAD")
        self.assertEqual(command, ["gh", "pr", "merge", "101", "--squash", "--match-head-commit", head])
        self.assertEqual((first / "CHANGELOG.md").read_text().count("### Added"), 1)
        self.assertEqual(len(self.pushes()), 1)
        self.assertEqual(self.pushes()[0]["cwd"], str(self.main))
        self.assertTrue(any(arg.startswith("--force-with-lease=topic-1:") for arg in self.pushes()[0]["args"]))
        subprocess.run(command, cwd=self.main, env=self.env, check=True, capture_output=True, text=True)
        result = self.queue("1", "2")
        self.assert_status(result, 3)
        self.assert_torn_down("1")
        text = (second / "CHANGELOG.md").read_text()
        self.assertEqual(text.count("### Added"), 1)
        for item in ("upstream", "issue 1", "issue 2"):
            self.assertIn(item, text)
        spec = (second / "openspec/specs/queue/spec.md").read_text()
        for item in ("Upstream", "Issue 1", "Issue 2"):
            self.assertIn(item, spec)

    def test_merge_batch_matches_pushed_heads_and_tears_down(self):
        self.issue("1")
        self.issue("2")
        self.upstream()
        result = self.queue("--merge", "1", "2")
        self.assert_status(result, 0)
        data = json.loads(Path(self.env["QUEUE_FIXTURE"]).read_text())
        merges = [call for call in self.calls() if call[:2] == ["pr", "merge"]]
        self.assertEqual(len(merges), 2)
        for issue, call in zip(("1", "2"), merges):
            self.assert_torn_down(issue)
            row = data["prs"][str(100 + int(issue))]
            self.assertEqual(row["state"], "MERGED")
            self.assertEqual(call[-2:], ["--match-head-commit", row["merged_head"]])

    def test_code_conflict_aborts_without_push(self):
        tree = self.issue()
        self.write(tree, "code.py", 'value = "feature"\n')
        git(tree, "add", ".")
        git(tree, "commit", "-qm", "code")
        git(self.main, "push", "-q", "origin", "topic-1")
        self.upstream(code=True)
        before = git(tree, "rev-parse", "HEAD")
        result = self.queue("--merge", "1")
        self.assert_status(result, 1)
        self.assertIn("code.py", result.stderr)
        self.assertEqual(git(tree, "rev-parse", "HEAD"), before)
        self.assertEqual(git(tree, "status", "--porcelain"), "")
        self.assertEqual((tree / "code.py").read_text(), 'value = "feature"\n')
        self.assertEqual(self.pushes(), [])

    def test_gate_failure_restores_head_and_can_retry(self):
        tree = self.issue()
        self.upstream()
        before = git(tree, "rev-parse", "HEAD")
        result = self.queue("1", env={"HOOK_EXIT": "1"})
        self.assert_status(result, 1)
        self.assertIn("pre-review.sh", result.stderr)
        self.assertIn("Log:", result.stdout)
        self.assertEqual(self.pushes(), [])
        self.assertEqual(git(tree, "rev-parse", "HEAD"), before)
        self.assert_status(self.queue("1"), 3)

    def test_local_remote_mismatch_stops_before_rebase(self):
        tree = self.issue()
        git(tree, "commit", "--allow-empty", "-qm", "local only")
        before = git(tree, "rev-parse", "HEAD")
        result = self.queue("1")
        self.assert_status(result, 1)
        self.assertIn("local head differs", result.stderr)
        self.assertEqual(git(tree, "rev-parse", "HEAD"), before)
        self.assertFalse(any("rebase" in call["args"] for call in self.calls("GIT")))

    def test_rejected_push_restores_head_for_retry(self):
        tree = self.issue()
        self.upstream()
        before = git(tree, "rev-parse", "HEAD")
        result = self.queue("1", env={"REJECT_PUSH": "1"})
        self.assert_status(result, 1)
        self.assertIn("push rejected", result.stderr)
        self.assertEqual(git(tree, "rev-parse", "HEAD"), before)
        self.assertEqual(git(tree, "status", "--porcelain"), "")
        self.assert_status(self.queue("1"), 3)

    def test_gate_edits_survive_restoring_original_head(self):
        tree = self.issue()
        self.upstream()
        before = git(tree, "rev-parse", "HEAD")
        self.write(self.main, "switchyard/hooks/checks.sh", "#!/bin/sh\necho hook-edit >code.py\nexit 1\n")
        result = self.queue("1")
        self.assert_status(result, 1)
        self.assertEqual(git(tree, "rev-parse", "HEAD"), before)
        self.assertEqual((tree / "code.py").read_text(), "hook-edit\n")
        self.assertEqual(self.pushes(), [])

    def test_checks_register_after_empty_and_pending_polls(self):
        self.issue()
        self.data["prs"]["101"]["heads"] = ["not-yet-visible"]
        self.data["prs"]["101"]["checks"] = [
            {"code": 1, "stderr": "no checks reported on the branch"},
            {"code": 1, "checks": []},
            {"code": 8, "checks": [{"name": "build", "bucket": "pending"}]},
            {"checks": [{"name": "build", "bucket": "pass"}, {"name": "optional", "bucket": "skipping"}]},
        ]
        self.save()
        self.assert_status(self.queue("1"), 3)
        self.assertEqual(len([call for call in self.calls() if call[:2] == ["pr", "checks"]]), 4)

    def test_failing_or_cancelled_check_stops_without_merge(self):
        self.issue()
        for bucket in ("fail", "cancel"):
            with self.subTest(bucket=bucket):
                self.data["prs"]["101"]["checks"] = [{"code": 1, "checks": [{"name": "build-broke", "bucket": bucket}]}]
                self.save()
                result = self.queue("--merge", "1")
                self.assert_status(result, 1)
                self.assertIn("build-broke", result.stderr)
                self.assertFalse(any(call[:2] == ["pr", "merge"] for call in self.calls()))

    def test_timeout_for_each_wait_phase(self):
        self.issue()
        for phase in ("head update", "check registration", "pending checks"):
            with self.subTest(phase=phase):
                self.data["prs"]["101"]["heads"] = ["old"] if phase == "head update" else []
                self.data["prs"]["101"]["checks"] = [{"checks": [] if phase == "check registration" else [{"name": "build", "bucket": "pending"}]}]
                self.save()
                result = self.queue("--timeout", "0", "1")
                self.assert_status(result, 1)
                self.assertIn(f"CI wait ran out during {phase}", result.stderr)

    def test_missing_record_validates_whole_batch_before_actions(self):
        self.issue()
        result = self.queue("1", "99")
        self.assert_status(result, 2)
        self.assertIn("99", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.pushes(), [])

    def test_unchanged_rebase_skips_push(self):
        tree = self.issue()
        before = git(tree, "rev-parse", "HEAD")
        self.assert_status(self.queue("1"), 3)
        self.assertEqual(self.pushes(), [])
        self.assertEqual(git(tree, "rev-parse", "HEAD"), before)

    def test_dirty_worktree_stops_before_rebase(self):
        tree = self.issue()
        self.write(tree, "code.py", "dirty\n")
        result = self.queue("1")
        self.assert_status(result, 1)
        self.assertIn("tracked changes", result.stderr)
        self.assertEqual((tree / "code.py").read_text(), "dirty\n")
        self.assertEqual(self.pushes(), [])

    def test_no_pr_or_closed_pr_stops(self):
        self.issue()
        for rows in ({}, {"101": {**self.data["prs"]["101"], "state": "CLOSED"}}):
            with self.subTest(rows=rows):
                self.data["prs"] = rows
                self.save()
                result = self.queue("1")
                self.assert_status(result, 1)
                self.assertEqual(self.pushes(), [])

    def test_invalid_timeout_and_poll_exit_2(self):
        self.issue()
        for value in ("-1", "nan", "inf", "bad"):
            with self.subTest(value=value):
                self.assert_status(self.queue("--timeout", value, "1"), 2)
                self.assert_status(self.queue("1", env={"SWITCHYARD_POLL_SECONDS": value}), 2)

    def test_multiple_conflicting_commits_ignore_diff3_and_rerere(self):
        tree = self.issue()
        path = tree / "openspec/specs/queue/spec.md"
        path.write_text(path.read_text() + "\n## Second commit\n")
        git(tree, "add", ".")
        git(tree, "commit", "-qm", "another append")
        git(self.main, "push", "-q", "origin", "topic-1")
        self.upstream()
        git(tree, "config", "merge.conflictStyle", "diff3")
        git(tree, "config", "rerere.enabled", "true")
        result = self.queue("1")
        self.assert_status(result, 3)
        for item in ("Upstream", "Issue 1", "Second commit"):
            self.assertIn(item, path.read_text())


if __name__ == "__main__":
    unittest.main()
