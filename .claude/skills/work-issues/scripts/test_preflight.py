from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("preflight.sh").resolve()


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        self.codex_home = self.root / "codex"
        self.codex_home.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def add(self, name, body="exit 0\n"):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + body)
        path.chmod(0o755)
        return path

    def run_check(self, extra_env=None):
        env = {
            "PATH": str(self.bin),
            "HOME": str(self.home),
            "CODEX_HOME": str(self.codex_home),
            "SHOTS_PACKAGE_DIR": str(self.root),
        }
        if extra_env:
            for key, value in extra_env.items():
                if value is None:
                    env.pop(key, None)
                else:
                    env[key] = value
        return subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def add_base(self, *extra):
        for name in ("git", "python3", "node", "npx", "gh", *extra):
            if name == "node":
                self.add(name, 'exit "${NODE_PLAYWRIGHT_STATUS:-0}"\n')
            elif name == "gh":
                self.add(name, 'exit "${GH_AUTH_STATUS:-0}"\n')
            else:
                self.add(name)

    def test_git_passes_and_missing_git_fails(self):
        self.add_base("claude", "magick", "herdr")
        self.add("sips")
        result = self.run_check()
        self.assertEqual(result.returncode, 0)
        self.assertIn("ok       git", result.stdout)

        (self.bin / "git").unlink()
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING  git: not installed. Install Git with your system package manager.", result.stdout)

    def test_each_required_tool_has_a_fix_message(self):
        cases = (
            ("python3", "Python 3", "Install Python 3"),
            ("node", "Node.js", "Install Node.js"),
            ("npx", "Node.js", "Install Node.js"),
            ("gh", "GitHub CLI", "cli.github.com"),
        )
        for command, name, fix in cases:
            with self.subTest(command=command):
                self.add_base("claude", "magick", "herdr")
                (self.bin / command).unlink()
                result = self.run_check()
                self.assertEqual(result.returncode, 1)
                line = next(line for line in result.stdout.splitlines() if line.startswith("MISSING") and name in line)
                self.assertIn(fix, line)
                for path in self.bin.iterdir():
                    path.unlink()

    def test_gh_auth_status_and_missing_cli_report_once(self):
        self.add_base("claude", "magick", "herdr")
        self.assertEqual(self.run_check().returncode, 0)
        result = self.run_check({"GH_AUTH_STATUS": "1"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("gh auth login", result.stdout)
        self.assertEqual(sum("GitHub CLI" in line for line in result.stdout.splitlines()), 1)

        (self.bin / "gh").unlink()
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(sum("GitHub CLI" in line for line in result.stdout.splitlines()), 1)

    def test_worker_cli_rules(self):
        for clis, expected in ((["claude"], 0), (["codex"], 0), (["opencode"], 1), ([], 1)):
            with self.subTest(clis=clis):
                self.add_base(*clis, "magick", "herdr")
                result = self.run_check()
                self.assertEqual(result.returncode, expected)
                if expected:
                    self.assertIn("MISSING  Worker CLI", result.stdout)
                    if clis == ["opencode"]:
                        self.assertIn("coordinator and reviewer need one", result.stdout)
                else:
                    self.assertIn("ok       Worker CLI", result.stdout)
                for path in self.bin.iterdir():
                    path.unlink()

    def test_all_required_items_are_reported_and_counted(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        for item in ("git", "Python 3", "Node.js", "GitHub CLI", "Worker CLI"):
            self.assertTrue(any(line.startswith("MISSING") and item in line for line in result.stdout.splitlines()), item)
        self.assertIn("5 missing,", result.stdout)

    def test_optional_herdr_and_image_tool_warn_without_failing(self):
        self.add_base("claude")
        result = self.run_check()
        self.assertEqual(result.returncode, 0)
        self.assertIn("warn     Herdr:", result.stdout)
        self.assertIn("warn     Image tool:", result.stdout)
        for image_tool in ("magick", "sips"):
            with self.subTest(image_tool=image_tool):
                self.add(image_tool)
                result = self.run_check()
                self.assertNotIn("warn     Image tool:", result.stdout)
                (self.bin / image_tool).unlink()

    def test_playwright_probe_and_missing_node_warning(self):
        self.add_base("claude", "magick", "herdr")
        result = self.run_check()
        self.assertIn("ok       Playwright", result.stdout)
        result = self.run_check({"NODE_PLAYWRIGHT_STATUS": "1"})
        self.assertIn("warn     Playwright:", result.stdout)
        (self.bin / "node").unlink()
        result = self.run_check()
        self.assertIn("MISSING  Node.js", result.stdout)
        self.assertIn("warn     Playwright: skipped", result.stdout)
        self.assertEqual(sum(line.startswith("MISSING  Node.js") for line in result.stdout.splitlines()), 1)

    def test_second_provider_warning(self):
        self.add_base("claude", "magick", "herdr")
        result = self.run_check()
        self.assertIn("warn     Second provider:", result.stdout)
        self.add("codex")
        result = self.run_check()
        self.assertIn("ok       Second provider", result.stdout)
        self.assertNotIn("warn     Second provider:", result.stdout)

    def test_codex_profile_path_and_absence(self):
        self.add_base("codex", "magick", "herdr")
        result = self.run_check()
        self.assertIn("warn     Codex coordinator profile:", result.stdout)
        (self.codex_home / "coordinator.config.toml").write_text("profile = true\n")
        result = self.run_check()
        self.assertIn("ok       Codex coordinator profile", result.stdout)

        (self.bin / "codex").unlink()
        result = self.run_check()
        self.assertNotIn("Codex coordinator profile", result.stdout)

        (self.codex_home / "coordinator.config.toml").unlink()
        (self.home / ".codex").mkdir()
        (self.home / ".codex" / "coordinator.config.toml").write_text("profile = true\n")
        self.add("codex")
        env = {"CODEX_HOME": None}
        result = self.run_check(env)
        self.assertIn("ok       Codex coordinator profile", result.stdout)

    def test_full_pass_has_no_missing_or_warnings(self):
        self.add_base("claude", "codex", "herdr", "magick")
        (self.codex_home / "coordinator.config.toml").write_text("profile = true\n")
        result = self.run_check()
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("MISSING", result.stdout)
        self.assertFalse(any(line.startswith("warn ") for line in result.stdout.splitlines()))


if __name__ == "__main__":
    unittest.main()
