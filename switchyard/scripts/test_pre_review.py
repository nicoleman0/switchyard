#!/usr/bin/env python3
"""Exercise pre-review.sh against a temporary main checkout and worktree."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SOURCE_SKILL = Path(__file__).resolve().parent.parent


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


class PreReview(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name).resolve()
        self.main = base / "main"
        self.main.mkdir()
        git(self.main, "init", "-q", "-b", "main")
        git(self.main, "config", "user.email", "test@example.test")
        git(self.main, "config", "user.name", "Test")
        shutil.copytree(SOURCE_SKILL, self.main / "switchyard", ignore=shutil.ignore_patterns("__pycache__"))
        git(self.main, "add", ".")
        git(self.main, "commit", "-qm", "initial")
        origin = base / "origin.git"
        subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True)
        git(self.main, "remote", "add", "origin", str(origin))
        git(self.main, "push", "-q", "origin", "main")
        self.tree = base / "tree"
        git(self.main, "worktree", "add", "-q", "-b", "topic", str(self.tree))
        self.bin = base / "bin"
        self.bin.mkdir()
        self.stub("npx", 'echo "npx $*"\nexit "${NPX_EXIT:-0}"')
        self.env = os.environ.copy()
        self.env["PATH"] = f"{self.bin}:{self.env['PATH']}"
        self.state("init", "1", "branch=topic", f"path={self.tree}", "owned=src/")
        self.commit_file("src/a.txt")
        self.hook(self.main / "switchyard/hooks/checks.sh", "echo project-ok")

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(0o755)

    def hook(self, path, body, mode=0o755):
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(mode)

    def state(self, *args):
        return subprocess.run(
            ["python3", str(self.main / "switchyard/scripts/state.py"), *args],
            cwd=self.main, env=self.env, check=True, capture_output=True, text=True,
        )

    def commit_file(self, name, text="x"):
        (self.tree / name).parent.mkdir(parents=True, exist_ok=True)
        (self.tree / name).write_text(text)
        git(self.tree, "add", name)
        git(self.tree, "commit", "-qm", f"add {name}")

    def gate(self, *args, env=None):
        args = args or ("1",)
        return subprocess.run(
            ["bash", str(self.main / "switchyard/scripts/pre-review.sh"), *args],
            cwd=self.main, env={**self.env, **(env or {})}, capture_output=True, text=True,
        )

    def logs(self):
        return sorted((self.tree / ".switchyard/checks").glob("*.log"))

    def test_all_pass(self):
        result = self.gate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for step in ("clean tree", "scope", "openspec", "project checks"):
            self.assertIn(f"PASS {step}", result.stdout)
        log = self.tree / ".switchyard/checks/1.log"
        self.assertIn(f"Log: {log}", result.stdout)
        text = log.read_text()
        for step in ("clean tree", "scope", "openspec", "project checks"):
            self.assertIn(f"== {step}", text)
        self.assertIn("npx --yes @fission-ai/openspec validate --all --strict", text)

    def test_second_run_writes_next_log(self):
        self.gate()
        self.gate()
        self.assertEqual([p.name for p in self.logs()], ["1.log", "2.log"])

    def test_hook_failure(self):
        self.hook(self.main / "switchyard/hooks/checks.sh", "echo hook-broke\nexit 1")
        result = self.gate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL project checks", result.stdout)
        for step in ("clean tree", "scope", "openspec"):
            self.assertIn(f"PASS {step}", result.stdout)
        self.assertIn("hook-broke", self.logs()[0].read_text())

    def test_hook_comes_from_main_checkout_in_worktree(self):
        self.hook(
            self.main / "switchyard/hooks/checks.sh",
            'echo "main-copy $ISSUE $BRANCH $WORKTREE $MAIN_CHECKOUT"\npwd',
        )
        result = self.gate()
        self.assertEqual(result.returncode, 0, result.stdout)
        text = self.logs()[0].read_text()
        self.assertIn(f"main-copy 1 topic {self.tree} {self.main}", text)
        self.assertIn(str(self.tree), text.split("main-copy", 1)[1])
        self.assertNotIn("Add your project's checks", text)

    def test_candidate_key_splits_issue_and_candidate(self):
        self.hook(self.main / "switchyard/hooks/checks.sh", 'echo "vars [$ISSUE] [$CANDIDATE]"')
        self.state("init", "1b", "branch=topic", f"path={self.tree}", "owned=src/")
        for key, expected in (("1", "vars [1] []"), ("1b", "vars [1] [b]")):
            result = self.gate(key)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(expected, self.logs()[-1].read_text())

    def test_no_hook_skips(self):
        (self.main / "switchyard/hooks/checks.sh").unlink()
        result = self.gate()
        self.assertEqual(result.returncode, 0)
        self.assertIn("SKIP project checks: no switchyard/hooks/checks.sh", result.stdout)

    def test_hook_not_executable_fails(self):
        self.hook(self.main / "switchyard/hooks/checks.sh", "exit 0", mode=0o644)
        result = self.gate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL project checks", result.stdout)

    def test_scope_failure_still_runs_later_steps(self):
        self.commit_file("other/b.txt")
        result = self.gate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL scope", result.stdout)
        self.assertIn("PASS openspec", result.stdout)
        self.assertIn("PASS project checks", result.stdout)
        self.assertIn("other/b.txt", self.logs()[0].read_text())

    def test_openspec_failure(self):
        result = self.gate(env={"NPX_EXIT": "1"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL openspec", result.stdout)

    def test_uncommitted_tracked_change_fails(self):
        (self.tree / "src/a.txt").write_text("changed")
        result = self.gate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL clean tree", result.stdout)

    def test_files_under_switchyard_dir_do_not_fail_clean_tree(self):
        (self.tree / ".gitignore").write_text(".switchyard/\n")
        git(self.tree, "add", ".gitignore")
        git(self.tree, "commit", "-qm", "ignore")
        (self.tree / ".switchyard/notes.md").parent.mkdir(parents=True, exist_ok=True)
        (self.tree / ".switchyard/notes.md").write_text("n")
        result = self.gate()
        self.assertIn("PASS clean tree", result.stdout)

    def test_no_record_exits_2_without_log(self):
        result = self.gate("9")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.logs(), [])

    def test_no_argument_exits_2(self):
        self.assertEqual(subprocess.run(
            ["bash", str(self.main / "switchyard/scripts/pre-review.sh")],
            cwd=self.main, env=self.env, capture_output=True, text=True,
        ).returncode, 2)


if __name__ == "__main__":
    unittest.main()
