#!/usr/bin/env python3
"""Exercise batch-state commands in isolated temporary git repositories."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
import unittest


SCRIPTS = Path(__file__).parent
SOURCE_SKILL = SCRIPTS.parent


class Harness(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.test"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Test"], check=True)
        (self.repo / ".keep").write_text("x")
        subprocess.run(["git", "-C", str(self.repo), "add", ".keep"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "initial"], check=True)
        self.origin = self.base / "origin.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self.origin)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin", str(self.origin)], check=True)
        self.skill = self.repo / "switchyard"
        shutil.copytree(SOURCE_SKILL, self.skill)
        (self.skill / "routing.md").write_text("# Routing\n")
        (self.skill / "roles/planner.md").write_text("role")
        self.up_hook = self.skill / "hooks/worktree-up.sh"
        self.up_hook.write_text("#!/bin/sh\necho hook-output\n[ \"${FAIL_HOOK:-}\" != 1 ]\n")
        self.up_hook.chmod(0o755)
        self.down_hook = self.skill / "hooks/worktree-down.sh"
        self.down_hook.write_text("#!/bin/sh\n[ \"${FAIL_HOOK:-}\" != 1 ]\n")
        self.down_hook.chmod(0o755)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        for cli in ("claude", "codex", "opencode", "pi"):
            self.stub(cli, "exit 0")
        self.log = self.base / "calls.jsonl"
        self.stub("gh", 'echo "$*" >> "$CALL_LOG"\n[ "$1 $2" = "pr list" ] && [ "$3" = "--head" ] && [ "$5" = "--state" ] && [ "$6" = all ] && [ "$7" = "--json" ] && [ "$8" = "number,state" ] && [ "$9" = "--limit" ] && [ "${10}" = 1 ] || exit 23\n[ "${FAIL_GH:-}" != 1 ] || exit 2\nprintf \'%s\\n\' "${GH_RESULT:-[]}"')
        self.stub("herdr", 'echo "$*" >> "$CALL_LOG"\n[ "${FAIL_HERDR:-}" != 1 ] || exit 2\nif [ "$1 $2" = "agent list" ] && [ "$#" = 2 ]; then printf \'%s\\n\' "$HERDR_RESULT"; elif [ "$1 $2" = "agent start" ]; then [ "${FAIL_START:-}" != 1 ] || exit 2; case "$3" in planner-10|planner-8|implementer-10|reviewer-10) ;; *) exit 23 ;; esac; echo "agent start output"; elif [ "$1 $2" = "worktree create" ]; then printf \'%s\\n\' "$HERDR_CREATE_RESULT"; elif [ "$1 $2" = "pane split" ]; then printf \'{"result":{"pane":{"pane_id":"w1:p2"}}}\\n\'; elif [ "$1 $2" = "pane close" ]; then echo ok; else exit 23; fi')
        self.env = os.environ.copy()
        self.env.update(PATH=f"{self.bin}:{self.env['PATH']}", CALL_LOG=str(self.log), TEST_WORKTREE=str(self.repo))
        self.env["HERDR_RESULT"] = '{"result":{"agents":[]}}'
        self.env["HERDR_CREATE_RESULT"] = '{"result":{"root_pane":{"cwd":"' + str(self.repo) + '","pane_id":"w1:p1","workspace_id":"ws1"}}}'
        self.env.pop("HERDR_ENV", None)

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(0o755)

    def run_cmd(self, *args, cwd=None, env=None, bash=False):
        command = [os.environ.get("TEST_BASH", "bash"), *args] if bash else ["python3", str(self.skill / "scripts/state.py"), *args]
        return subprocess.run(command, cwd=cwd or self.repo, env=env or self.env, capture_output=True, text=True)

    def state(self, *args):
        return self.run_cmd(*args)

    def get(self, issue, field):
        return self.state("get", issue, field).stdout.strip()

    def init(self, issue="8", **values):
        self.state("init", issue, *(f"{k}={v}" for k, v in values.items()))

    def script(self, name, *args, env=None):
        return self.run_cmd(str(self.skill / "scripts" / name), *args, env=env, bash=True)

    def record(self, issue="8"):
        return json.loads((self.repo / f".switchyard/state/{issue}.json").read_text())

    def write_record(self, record):
        (self.repo / f".switchyard/state/{record['issue']}.json").write_text(json.dumps(record))

    def test_phase_commands_and_headless_starts(self):
        self.init(path=str(self.repo), runner="headless", planner_row="claude --model opus")
        before = self.record()
        self.assertEqual(self.state("phase-end", "8").returncode, 0)
        self.assertEqual(self.record(), before)
        self.assertEqual(self.state("phase-start", "8").returncode, 1)
        for role, provider in (("planner", "claude"), ("implementer", "codex")):
            result = self.script("start-worker.sh", "8", role, provider)
            self.assertEqual(result.returncode, 0, result.stderr)
        phases = self.record()["phases"]
        self.assertEqual(len(phases), 2)
        self.assertEqual(phases[0]["row"], "claude --model opus")
        self.assertEqual(phases[0]["role"], "planner")
        self.assertEqual(phases[0]["provider"], "claude")
        self.assertEqual(phases[0]["ended"], phases[1]["started"])
        self.assertRegex(phases[0]["started"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertNotIn("ended", phases[1])
        self.assertEqual(self.state("phase-end", "8").returncode, 0)
        before = self.record()
        self.assertEqual(self.state("phase-end", "8").returncode, 0)
        self.assertEqual(self.record(), before)
        self.state("set", "8", "backend=")
        self.assertEqual(self.state("phase-start", "8").returncode, 1)

    def test_archive_teardown_reviews_and_retry(self):
        self.assertEqual(self.script("setup-worktree.sh", "8", "topic").returncode, 0)
        record = self.record()
        reviews = Path(record["path"]) / ".switchyard/reviews"
        (self.repo / ".git/info/exclude").write_text(".switchyard/\n")
        reviews.mkdir(parents=True)
        (reviews / "2.md").write_text("Verdict: changes requested\n")
        (reviews / "10.md").write_text("Verdict: pass\nMore text\n")
        (reviews / "notes.md").write_text("Ignore this\n")
        self.state("set", "8", "role=planner", "backend=claude", "size=medium", "plan_size=small")
        self.state("phase-start", "8")
        env = self.env.copy(); env["FAIL_HOOK"] = "1"
        self.assertNotEqual(self.script("teardown-worktree.sh", "8", "topic", env=env).returncode, 0)
        history_path = self.repo / ".switchyard/history.jsonl"
        first = history_path.read_text()
        summary = json.loads(first)
        self.assertEqual(summary["rounds"], 2)
        self.assertEqual(summary["verdict"], "pass")
        self.assertEqual(summary["size"], "medium")
        self.assertEqual(summary["plan_size"], "small")
        self.assertFalse(summary["abandoned"])
        self.assertIn("ended", summary["phases"][0])
        report = self.state("timings")
        self.assertEqual(sum(line.split()[:1] == ["8"] for line in report.stdout.splitlines()), 1)
        self.assertEqual(self.script("teardown-worktree.sh", "8", "topic").returncode, 0)
        self.assertEqual(history_path.read_text(), first)
        self.assertFalse((self.repo / ".switchyard/state/8.json").exists())
        self.assertIn("Verdict: pass", self.state("timings", "8").stdout)

    def test_timings_fixed_times_models_and_totals(self):
        self.init(size="medium")
        phases = []
        for role, row, start, end in (
            ("planner", "claude --model opus", "10:00:00", "10:00:45"),
            ("implementer", "codex -m mini", "10:01:00", "10:43:00"),
            ("reviewer", "claude --model=sonnet", "11:00:00", "12:10:00"),
            ("reviewer", "claude", "12:10:00", "12:10:45"),
            ("planner", "", "12:11:00", "12:11:45"),
        ):
            phases.append(dict(role=role, provider=row.split()[0] if row else "claude", row=row,
                               started="2026-10-31T" + start + "Z", ended="2026-10-31T" + end + "Z"))
        record = self.record(); record.update(phases=phases, rounds=2, verdict="pass")
        self.write_record(record)
        result = self.state("timings", "8")
        self.assertEqual(result.returncode, 0, result.stderr)
        for value in ("opus", "mini", "sonnet", "default", "45s", "42m", "1h10m", "Rounds: 2", "Verdict: pass", "Total: 2h11m"):
            self.assertIn(value, result.stdout)
        self.assertRegex(result.stdout, r"planner\s+claude\s+-\s+2026")
        history = dict(record, issue="7", archived="2026-10-31T13:00:00Z", abandoned=True)
        (self.repo / ".switchyard/history.jsonl").write_text("broken\n" + json.dumps(history) + "\n")
        report = self.state("timings")
        self.assertIn("Cannot read history line 1:", report.stderr)
        self.assertEqual(sum(line.split()[:1] == ["7"] for line in report.stdout.splitlines()), 1)
        self.assertEqual(sum(line.split()[:1] == ["8"] for line in report.stdout.splitlines()), 1)
        self.assertIn("abandoned", report.stdout)
        self.assertRegex(report.stdout, r"claude\s+opus\s+planner\s+2\s+1m")
        self.assertRegex(report.stdout, r"codex\s+mini\s+implementer\s+2\s+1h24m")
        self.assertIn("Verdict: abandoned", self.state("timings", "7").stdout)
        record["phases"][-1].pop("ended")
        self.write_record(record)
        self.assertIn("running", self.state("timings", "8").stdout)
        # Open phases are excluded from aggregate durations.
        self.assertRegex(self.state("timings").stdout, r"claude\s+-\s+planner\s+1\s+45s")

    def test_turn_commands_record_turns(self):
        self.init(path=str(self.repo), runner="headless", planner_row="claude --model opus")
        result = self.script("start-worker.sh", "8", "planner", "claude")
        self.assertEqual(result.returncode, 0, result.stderr)
        phase = self.record()["phases"][0]
        self.assertEqual(phase["turns"], [{"started": phase["started"]}])
        self.assertEqual(self.state("turn-end", "8").returncode, 0)
        turn = self.record()["phases"][0]["turns"][0]
        self.assertRegex(turn["ended"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        before = self.record()
        self.assertEqual(self.state("turn-end", "8").returncode, 0)
        self.assertEqual(self.record(), before)
        self.assertEqual(self.state("turn-start", "8").returncode, 0)
        phase = self.record()["phases"][0]
        self.assertEqual(len(phase["turns"]), 2)
        self.assertEqual(set(phase["turns"][1]), {"started"})
        # An open turn is a no-op.
        before = self.record()
        self.assertEqual(self.state("turn-start", "8").returncode, 0)
        self.assertEqual(self.record(), before)
        # A second start-worker.sh closes the old open turn at the phase's ended time.
        result = self.script("start-worker.sh", "8", "implementer", "codex")
        self.assertEqual(result.returncode, 0, result.stderr)
        phases = self.record()["phases"]
        self.assertEqual(phases[0]["turns"][-1]["ended"], phases[0]["ended"])
        self.assertEqual(phases[0]["ended"], phases[1]["started"])
        self.assertEqual(phases[1]["turns"], [{"started": phases[1]["started"]}])
        # phase-end closes the open turn too.
        self.assertEqual(self.state("phase-end", "8").returncode, 0)
        phases = self.record()["phases"]
        self.assertEqual(phases[1]["turns"][0]["ended"], phases[1]["ended"])
        result = self.state("turn-start", "8")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(result.stderr.strip().splitlines()), 1)
        before = self.record()
        self.assertEqual(self.state("turn-end", "8").returncode, 0)
        self.assertEqual(self.record(), before)

    def test_timings_busy_wait_and_turns(self):
        self.init(size="medium")
        record = self.record()
        record["rounds"] = 1
        record["verdict"] = "pass"
        record["phases"] = [
            {"role": "planner", "provider": "claude", "row": "claude --model opus",
             "started": "2026-10-31T10:00:00Z", "ended": "2026-10-31T10:42:00Z",
             "turns": [{"started": "2026-10-31T10:00:00Z", "ended": "2026-10-31T10:10:00Z"},
                       {"started": "2026-10-31T10:12:00Z", "ended": "2026-10-31T10:20:00Z"}]},
            {"role": "implementer", "provider": "codex", "row": "",
             "started": "2026-10-31T10:42:00Z", "ended": "2026-10-31T11:24:00Z"},
        ]
        self.write_record(record)
        result = self.state("timings", "8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout,
                         r"planner\s+claude\s+opus\s+2026-10-31T10:00:00Z\s+42m\s+18m\s+24m\n")
        self.assertRegex(result.stdout, r"implementer\s+codex\s+-\s+\S+\s+42m\s+-\s+-\n")
        self.assertIn("Rounds: 1  Verdict: pass  Busy: 18m  Total: 1h24m", result.stdout)
        # An open turn counts to now and the phase prints running.
        recent = (datetime.now(timezone.utc) - timedelta(seconds=130)).strftime("%Y-%m-%dT%H:%M:%SZ")
        record["phases"].append({"role": "reviewer", "provider": "codex", "row": "codex",
                                 "started": recent, "turns": [{"started": recent}]})
        self.write_record(record)
        result = self.state("timings", "8")
        self.assertRegex(result.stdout, r"reviewer\s+codex\s+default\s+\S+\s+running 2m\s+2m\s+0s\n")
        self.assertIn("Busy: 20m", result.stdout)

    def test_timings_no_issue_busy_column(self):
        self.init(size="medium")
        record = self.record()
        record["rounds"] = 1
        record["verdict"] = "pass"
        record["phases"] = [
            {"role": "planner", "provider": "claude", "row": "claude --model opus",
             "started": "2026-10-31T10:00:00Z", "ended": "2026-10-31T10:42:00Z",
             "turns": [{"started": "2026-10-31T10:00:00Z", "ended": "2026-10-31T10:10:00Z"},
                       {"started": "2026-10-31T10:12:00Z", "ended": "2026-10-31T10:20:00Z"}]},
            {"role": "implementer", "provider": "codex", "row": "",
             "started": "2026-10-31T10:42:00Z", "ended": "2026-10-31T11:24:00Z"},
        ]
        self.write_record(record)
        history = {"issue": "7", "size": "small", "archived": "2026-10-31T11:30:00Z",
                   "abandoned": False,
                   "phases": [{"role": "planner", "provider": "claude", "row": "claude",
                               "started": "2026-10-31T09:00:00Z", "ended": "2026-10-31T09:10:00Z"}]}
        (self.repo / ".switchyard/history.jsonl").write_text(json.dumps(history) + "\n")
        result = self.state("timings")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"\b8\s+medium\s+1\s+pass\s+1h24m\s+18m\n")
        # A record whose phases have no turns shows - and adds nothing.
        self.assertRegex(result.stdout, r"\b7\s+small\s+-\s+-\s+10m\s+-\n")
        self.assertRegex(result.stdout, r"claude\s+opus\s+planner\s+1\s+42m\s+18m\n")
        self.assertRegex(result.stdout, r"codex\s+-\s+implementer\s+1\s+42m\s+-\n")

    def test_timings_empty(self):
        result = self.state("timings")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "No timings recorded.\n")

    def test_commands_and_validation(self):
        self.init(branch="old")
        self.init(branch="new")
        self.assertEqual(self.get("8", "branch"), "new")
        self.assertEqual(self.state("set", "8", "path=/tmp").returncode, 0)
        self.assertEqual(self.get("8", "branch"), "new")
        for args in [("set", "99", "a=b"), ("get", "8", "missing"), ("init", "x", "a=b")]:
            result = self.state(*args)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(len(result.stderr.strip().splitlines()), 1)
        self.state("init", "8", "empty=")
        self.assertNotEqual(self.state("get", "8", "empty").returncode, 0)
        self.assertEqual(len(self.state("get", "8", "empty").stderr.strip().splitlines()), 1)
        for action in ("init", "set"):
            for key in ("phases", "archived"):
                result = self.state(action, "8", f"{key}=x")
                self.assertEqual(result.returncode, 1)
                self.assertEqual(len(result.stderr.splitlines()), 1)
        invalid = self.state("set", "8", "issue=9")
        self.assertNotEqual(invalid.returncode, 0)
        self.assertEqual(len(invalid.stderr.strip().splitlines()), 1)
        self.assertEqual(self.state("rm", "500").returncode, 0)

    def test_candidate_keys(self):
        self.init("120b", branch="old")
        self.assertEqual(self.state("set", "120b", "branch=b120").returncode, 0)
        self.assertEqual(self.get("120b", "branch"), "b120")
        for key in ("120c", "b", "120bb", "12b0"):
            result = self.state("init", key, "a=b")
            self.assertEqual(result.returncode, 1, key)
            self.assertIn("issue key must be digits, optionally followed by b", result.stderr)
        self.init("121", branch="b121")
        self.init("120", branch="b120a")
        rows = [line.split()[0] for line in self.state("status").stdout.splitlines()[1:]]
        self.assertEqual(rows, ["120", "120b", "121"])
        self.assertEqual(self.state("rm", "120b").returncode, 0)
        self.assertFalse((self.repo / ".switchyard/state/120b.json").exists())

    def test_get_missing_record_has_distinct_exit_code(self):
        result = self.state("get", "500", "branch")
        self.assertEqual(result.returncode, 3)
        self.assertIn("no record", result.stderr)

    def test_get_corrupt_record_keeps_failure_exit_code(self):
        path = self.repo / ".switchyard/state/56.json"
        path.parent.mkdir(parents=True)
        path.write_text("{not json")
        result = self.script("teardown-worktree.sh", "56", "topic")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot read record", result.stderr)
        self.assertTrue(path.exists())

    def test_teardown_record_without_branch_fails_and_keeps_record(self):
        self.init("56", path=str(self.base / "missing"))
        result = self.script("teardown-worktree.sh", "56", "topic")
        self.assertEqual(result.returncode, 1)
        self.assertIn("field branch is missing or empty", result.stderr)
        self.assertTrue((self.repo / ".switchyard/state/56.json").exists())

    def test_record_uses_main_checkout_from_linked_worktree(self):
        branch = self.base / "linked"
        subprocess.run(["git", "-C", str(self.repo), "worktree", "add", "-qb", "linked", str(branch)], check=True)
        result = subprocess.run(["python3", str(self.skill / "scripts/state.py"), "init", "42", "x=y"], cwd=branch, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.repo / ".switchyard/state/42.json").exists())

    def test_status_table_and_live_lookups(self):
        self.init("2", branch="b2", path=str(self.repo), runner="herdr", worker="planner-2", pane="p2", role="planner")
        self.init("10", branch="b10", path=str(self.repo), runner="headless", session="ses_issue10")
        self.env["HERDR_RESULT"] = '{"result":{"agents":[{"name":"planner-2","agent_status":"working"}]}}'
        self.env["GH_RESULT"] = '[{"number":12,"state":"OPEN"}]'
        result = self.state("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(result.stdout.index("2  "), result.stdout.index("10"))
        self.assertIn("working", result.stdout)
        self.assertIn("ses_issue10", result.stdout)
        self.assertIn("#12 open", result.stdout)

    def test_status_shows_waiting(self):
        self.init("2", branch="b2", path=str(self.repo), role="planner", waiting="questions")
        self.assertIn("planner, waiting", self.state("status").stdout)
        self.state("set", "2", "waiting=")
        out = self.state("status").stdout
        self.assertIn("planner", out)
        self.assertNotIn("waiting", out)

    def test_status_agent_ended_and_missing_worktree(self):
        self.init("2", branch="b2", path=str(self.repo), runner="herdr", worker="gone")
        self.init("3", branch="b3", path=str(self.base / "missing"), runner="headless")
        self.env["HERDR_RESULT"] = '{"result":{"agents":[]}}'
        result = self.state("status")
        self.assertIn("ended", result.stdout)
        self.assertIn("no worktree", result.stdout)
        self.assertIn("pr list", self.log.read_text())

    def test_setup_records_before_hook_and_teardown_removes_record(self):
        result = self.script("setup-worktree.sh", "8", "topic")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("hook-output", result.stdout)
        self.assertEqual(self.get("8", "runner"), "headless")
        self.assertEqual(Path(self.record()["path"]), (self.base / "repo.worktrees/topic").resolve())
        down = self.script("teardown-worktree.sh", "8", "topic")
        self.assertEqual(down.returncode, 0, down.stderr)
        self.assertFalse((self.repo / ".switchyard/state/8.json").exists())

    def test_setup_hook_failure_keeps_record_and_teardown_failure_keeps_record(self):
        env = self.env.copy(); env["FAIL_HOOK"] = "1"
        result = self.script("setup-worktree.sh", "8", "topic", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.get("8", "runner"), "headless")
        down = self.script("teardown-worktree.sh", "8", "topic", env=env)
        self.assertNotEqual(down.returncode, 0)
        self.assertTrue((self.repo / ".switchyard/state/8.json").exists())

    def hook_log(self):
        for hook, name in ((self.up_hook, "up"), (self.down_hook, "down")):
            hook.write_text(f'#!/bin/sh\necho "{name} [$ISSUE] [$CANDIDATE]" >> "$MAIN_CHECKOUT/hooks.log"\n')
        return self.repo / "hooks.log"

    def test_setup_candidate_requires_first_record(self):
        result = self.script("setup-worktree.sh", "120b", "topic-b")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no record", result.stderr)
        self.assertFalse((self.base / "repo.worktrees/topic-b").exists())
        self.assertNotIn("refs/heads/topic-b", self.run_cmd("-c", "git show-ref", bash=True).stdout)
        self.assertFalse((self.repo / ".switchyard/state/120b.json").exists())

    def test_setup_candidate_copies_change_and_isolates_hooks(self):
        log = self.hook_log()
        self.assertEqual(self.script("setup-worktree.sh", "120", "topic").returncode, 0)
        first = Path(self.record("120")["path"])
        self.state("set", "120", "owned=src/ CHANGELOG.md")
        (first / "a.txt").write_text("a")
        subprocess.run(["git", "-C", str(first), "add", "a.txt"], check=True)
        subprocess.run(["git", "-C", str(first), "commit", "-qm", "a"], check=True)
        for name in ("openspec/changes/best/tasks.md", "openspec/changes/best/.openspec.yaml",
                     "openspec/changes/archive/old/tasks.md", ".switchyard/answers/plan.md"):
            (first / name).parent.mkdir(parents=True, exist_ok=True)
            (first / name).write_text(name)
        result = self.script("setup-worktree.sh", "120b", "topic-b")
        self.assertEqual(result.returncode, 0, result.stderr)
        second = Path(self.record("120b")["path"])
        head = lambda tree: subprocess.run(["git", "-C", str(tree), "rev-parse", "HEAD"],
                                           capture_output=True, text=True, check=True).stdout
        self.assertEqual(head(second), head(first))
        for name in ("openspec/changes/best/tasks.md", "openspec/changes/best/.openspec.yaml",
                     ".switchyard/answers/plan.md"):
            self.assertEqual((second / name).read_text(), name)
        self.assertFalse((second / "openspec/changes/archive").exists())
        self.assertFalse((second / ".switchyard/plan.md").exists())
        self.assertEqual(self.record("120b")["owned"], "src/ CHANGELOG.md")
        self.assertEqual(self.record("120b")["candidate_of"], "120")
        self.assertEqual(self.record("120b")["branch"], "topic-b")
        down = self.script("teardown-worktree.sh", "--abandon", "120b", "topic-b")
        self.assertEqual(down.returncode, 0, down.stderr)
        self.assertFalse(second.exists())
        self.assertTrue(first.exists())
        self.assertFalse((self.repo / ".switchyard/state/120b.json").exists())
        self.assertEqual(self.record("120")["branch"], "topic")
        refs = self.run_cmd("-c", "git show-ref", bash=True).stdout
        self.assertNotIn("refs/heads/topic-b", refs)
        self.assertIn("refs/heads/topic", refs)
        self.assertEqual(self.script("teardown-worktree.sh", "--abandon", "120", "topic").returncode, 0)
        self.assertEqual(log.read_text().splitlines(),
                         ["up [120] []", "up [120] [b]", "down [120] [b]", "down [120] []"])

    def test_setup_candidate_copies_plain_plan(self):
        first_setup = self.script("setup-worktree.sh", "82", "topic")
        self.assertEqual(first_setup.returncode, 0, first_setup.stderr)
        first = Path(self.record("82")["path"])
        plan = first / ".switchyard/plan.md"
        plan.parent.mkdir(parents=True, exist_ok=True)
        content = b"# Plan: issue #82\n\n## Tasks\n\n- [ ] Implement\n"
        plan.write_bytes(content)

        second_setup = self.script("setup-worktree.sh", "82b", "topic-b")
        self.assertEqual(second_setup.returncode, 0, second_setup.stderr)
        second = Path(self.record("82b")["path"])
        copied = second / ".switchyard/plan.md"
        self.assertTrue(copied.is_file())
        self.assertEqual(copied.read_bytes(), content)
        self.assertFalse((second / "openspec").exists())
        copied.write_bytes(content.replace(b"[ ]", b"[x]"))
        self.assertEqual(plan.read_bytes(), content)

    def test_abandon_skip_hook_keeps_shared_state(self):
        # A hook that ignores CANDIDATE gives both candidates one database.
        self.up_hook.write_text("#!/bin/sh\necho database=shared\n")
        self.down_hook.write_text('#!/bin/sh\nrm -f "$MAIN_CHECKOUT/shared-db"\n')
        shared = self.repo / "shared-db"
        shared.write_text("data")
        self.assertEqual(self.script("setup-worktree.sh", "120", "topic").returncode, 0)
        result = self.script("setup-worktree.sh", "120b", "topic-b")
        self.assertEqual(result.returncode, 0, result.stderr)
        second = Path(self.record("120b")["path"])
        down = self.script("teardown-worktree.sh", "--skip-hook", "120b", "topic-b")
        self.assertEqual(down.returncode, 2)
        self.assertIn("--skip-hook needs --abandon", down.stderr)
        self.assertTrue(second.exists())
        down = self.script("teardown-worktree.sh", "--abandon", "--skip-hook", "120b", "topic-b")
        self.assertEqual(down.returncode, 0, down.stderr)
        self.assertIn("by --skip-hook", down.stdout)
        self.assertEqual(shared.read_text(), "data")
        self.assertFalse(second.exists())
        self.assertFalse((self.repo / ".switchyard/state/120b.json").exists())
        self.assertNotIn("refs/heads/topic-b", self.run_cmd("-c", "git show-ref", bash=True).stdout)
        self.assertTrue(Path(self.record("120")["path"]).exists())

    def test_setup_candidate_of_stacked_issue(self):
        _, child, head = self.make_stack()
        result = self.script("setup-worktree.sh", "--parent", "8", "9b", "child-b")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Drop --parent", result.stderr)
        self.assertFalse((self.repo / ".switchyard/state/9b.json").exists())
        result = self.script("setup-worktree.sh", "9b", "child-b")
        self.assertEqual(result.returncode, 0, result.stderr)
        for field, value in (("parent", "8"), ("parent_branch", "parent"), ("parent_head", head)):
            self.assertEqual(self.record("9b")[field], value)
        result = self.script("teardown-worktree.sh", "8", "parent")
        self.assertEqual(result.returncode, 1)
        self.assertIn("restack.sh 9b", result.stderr)

    def test_teardown_without_record_succeeds(self):
        path = self.base / "repo.worktrees/topic"
        subprocess.run(["git", "-C", str(self.repo), "worktree", "add", "-qb", "topic", str(path)], check=True)
        result = self.script("teardown-worktree.sh", "77", "topic")
        self.assertEqual(result.returncode, 0, result.stderr)

        self.assertFalse((self.repo / ".switchyard/history.jsonl").exists())

    def test_teardown_no_record_and_nothing_to_remove_fails(self):
        marker = self.base / "down-ran"
        self.down_hook.write_text(f"#!/bin/sh\ntouch {marker}\n")
        for args in (("77", "topic"), ("--abandon", "77", "topic")):
            result = self.script("teardown-worktree.sh", *args)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("Issue 77: no record, and nothing to remove for branch topic.", result.stderr)
            self.assertNotIn("setup-worktree.sh", result.stderr)
            self.assertNotIn("Removed", result.stdout)
            self.assertFalse(marker.exists())

    def test_teardown_no_record_removes_lone_local_branch(self):
        subprocess.run(["git", "-C", str(self.repo), "branch", "topic"], check=True)
        result = self.script("teardown-worktree.sh", "77", "topic")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(subprocess.run(["git", "-C", str(self.repo), "show-ref", "--verify", "--quiet", "refs/heads/topic"]).returncode, 0)

    def test_teardown_no_record_removes_lone_remote_branch(self):
        subprocess.run(["git", "-C", str(self.repo), "push", "-q", "origin", "HEAD:refs/heads/topic"], check=True)
        result = self.script("teardown-worktree.sh", "77", "topic")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(subprocess.run(["git", "-C", str(self.origin), "branch", "--list", "topic"], capture_output=True, text=True).stdout, "")

    def test_teardown_missing_entry_removes_record_and_reports_skips(self):
        self.state("init", "56", "branch=topic", f"path={self.base / 'missing'}")
        result = self.script("teardown-worktree.sh", "56", "topic")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("Skipped:"), 3)
        self.assertIn("Removed issue 56 record.", result.stdout)
        self.assertFalse((self.repo / ".switchyard/state/56.json").exists())

    def test_teardown_stale_entry_runs_hook_and_skips_herdr(self):
        self.assertEqual(self.script("setup-worktree.sh", "56", "topic").returncode, 0)
        record_path = self.record("56")["path"]
        self.down_hook.write_text('#!/bin/sh\nprintf "%s" "$WORKTREE" > "$MAIN_CHECKOUT/hook-worktree"\n')
        tree = Path(record_path)
        shutil.rmtree(tree)
        env = self.env.copy()
        env["HERDR_ENV"] = "1"
        result = self.script("teardown-worktree.sh", "56", "topic", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / "hook-worktree").read_text(), record_path)
        self.assertNotIn("worktree remove", self.log.read_text() if self.log.exists() else "")
        worktrees = subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "list", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertNotIn(record_path, worktrees)
        self.assertFalse((self.repo / ".switchyard/state/56.json").exists())

    def test_teardown_refuses_existing_detached_worktree(self):
        self.assertEqual(self.script("setup-worktree.sh", "56", "topic").returncode, 0)
        tree = Path(self.record("56")["path"])
        subprocess.run(["git", "-C", str(tree), "checkout", "--detach", "-q"], check=True)
        marker = tree / "untracked.txt"
        marker.write_text("keep me")
        result = self.script("teardown-worktree.sh", "56", "topic")
        self.assertEqual(result.returncode, 1)
        self.assertIn("recorded path exists", result.stderr)
        self.assertTrue(marker.exists())
        self.assertTrue((self.repo / ".switchyard/state/56.json").exists())

    def test_teardown_lists_removed_parts_with_comma_and_space(self):
        self.assertEqual(self.script("setup-worktree.sh", "56", "topic").returncode, 0)
        record_path = self.record("56")["path"]
        result = self.script("teardown-worktree.sh", "56", "topic")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip().splitlines()[-1],
            f"Removed worktree {record_path}, local branch topic.",
        )

    def test_teardown_branch_mismatch_changes_nothing(self):
        self.assertEqual(self.script("setup-worktree.sh", "56", "topic").returncode, 0)
        result = self.script("teardown-worktree.sh", "56", "wrong")
        self.assertEqual(result.returncode, 1)
        self.assertTrue((self.repo / ".switchyard/state/56.json").exists())
        self.assertTrue(Path(self.record("56")["path"]).exists())

    def test_abandon_teardown_with_gone_folder_removes_record(self):
        self.assertEqual(self.script("setup-worktree.sh", "56", "topic").returncode, 0)
        tree = Path(self.record("56")["path"])
        shutil.rmtree(tree)
        result = self.script("teardown-worktree.sh", "--abandon", "56", "topic")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Worktree folder is gone.", result.stdout)
        self.assertFalse((self.repo / ".switchyard/state/56.json").exists())

    def stub_teardown_git(self, branch, on_delete):
        real = shutil.which("git")
        origin = str(self.origin)
        self.stub("git", f'''if [ "$1 $2 $3" = "push origin --delete" ] && [ "$4" = "{branch}" ]; then
  {on_delete}
fi
exec "{real}" "$@"''')

    def test_teardown_tolerates_branch_deleted_between_check_and_push(self):
        self.assertEqual(self.script("setup-worktree.sh", "39", "race").returncode, 0)
        subprocess.run(["git", "-C", str(self.repo), "push", "-q", "origin", "race"], capture_output=True)
        # The wrapper deletes the ref right before its own push --delete runs,
        # so the push is rejected the way the bare repo rejects a missing ref.
        self.stub_teardown_git("race", f'"{shutil.which("git")}" -C "{self.origin}" update-ref -d refs/heads/race')
        down = self.script("teardown-worktree.sh", "39", "race")
        self.assertEqual(down.returncode, 0, down.stderr)
        self.assertEqual(subprocess.run(["git", "ls-remote", "--heads", str(self.origin), "race"], capture_output=True, text=True).stdout, "")
        self.assertFalse((self.repo / ".switchyard/state/39.json").exists())

    def test_teardown_reports_failed_remote_delete_and_removes_record(self):
        self.assertEqual(self.script("setup-worktree.sh", "39", "race").returncode, 0)
        subprocess.run(["git", "-C", str(self.repo), "push", "-q", "origin", "race"], capture_output=True)
        self.stub_teardown_git("race", 'echo "push failed" >&2; exit 1')
        down = self.script("teardown-worktree.sh", "39", "race")
        self.assertNotEqual(down.returncode, 0)
        self.assertIn("race", down.stderr)
        self.assertIn("still exists", down.stderr)
        hinted = subprocess.run(["git", "ls-remote", "--heads", str(self.origin), "race"], capture_output=True, text=True).stdout
        self.assertIn("refs/heads/race", hinted)
        self.assertFalse((self.repo / ".switchyard/state/39.json").exists())

    def make_dirty(self, tree):
        # Modified, staged, and untracked files, as git's plain removal refuses.
        (tree / ".keep").write_text("changed\n")
        (tree / "staged.txt").write_text("x\n")
        (tree / "untracked.txt").write_text("x\n")
        subprocess.run(["git", "-C", str(tree), "add", "staged.txt"], check=True)

    def test_teardown_refuses_dirty_worktree_before_the_hook(self):
        self.down_hook.write_text('#!/bin/sh\necho down >> "$MAIN_CHECKOUT/hook-log"\n')
        self.assertEqual(self.script("setup-worktree.sh", "8", "topic").returncode, 0)
        tree = Path(self.record()["path"])
        self.make_dirty(tree)
        down = self.script("teardown-worktree.sh", "8", "topic")
        self.assertNotEqual(down.returncode, 0)
        self.assertIn("--abandon", down.stderr)
        self.assertIn("untracked.txt", down.stderr)
        self.assertIn(" M .keep", down.stderr)
        self.assertTrue((self.repo / ".switchyard/state/8.json").exists())
        self.assertTrue(tree.exists())
        self.assertEqual(subprocess.run(["git", "-C", str(self.repo), "branch", "--list", "topic"], capture_output=True, text=True).stdout.count("topic"), 1)
        self.assertFalse((self.repo / "hook-log").exists())

    def test_teardown_rejects_unknown_options(self):
        self.assertEqual(self.script("setup-worktree.sh", "8", "topic").returncode, 0)
        tree = Path(self.record()["path"])
        self.make_dirty(tree)
        down = self.script("teardown-worktree.sh", "--force", "8", "topic")
        self.assertEqual(down.returncode, 2)
        self.assertIn("Usage: teardown-worktree.sh", down.stderr)
        self.assertTrue((self.repo / ".switchyard/state/8.json").exists())
        self.assertTrue(tree.exists())

    def test_abandon_reports_and_discards_dirty_worktree(self):
        self.down_hook.write_text('#!/bin/sh\necho down >> "$MAIN_CHECKOUT/hook-log"\n')
        self.assertEqual(self.script("setup-worktree.sh", "8", "topic").returncode, 0)
        tree = Path(self.record()["path"])
        self.make_dirty(tree)
        draft = subprocess.run(["git", "-C", str(tree), "commit", "-qm", "draft change", "staged.txt"], capture_output=True, text=True)
        self.assertEqual(draft.returncode, 0, draft.stderr)
        down = self.script("teardown-worktree.sh", "--abandon", "8", "topic")
        self.assertEqual(down.returncode, 0, down.stderr)
        self.assertEqual(down.stderr, "")
        self.assertIn("?? untracked.txt", down.stdout)
        self.assertIn(" M .keep", down.stdout)
        self.assertIn("draft change", down.stdout)
        history = json.loads((self.repo / ".switchyard/history.jsonl").read_text())
        self.assertTrue(history["abandoned"])
        self.assertTrue((self.repo / "hook-log").exists())
        self.assertFalse((self.repo / ".switchyard/state/8.json").exists())
        self.assertFalse(tree.exists())
        self.assertEqual(subprocess.run(["git", "-C", str(self.repo), "branch", "--list", "topic"], capture_output=True, text=True).stdout, "")
        self.assertEqual(subprocess.run(["git", "ls-remote", "--heads", str(self.origin), "topic"], capture_output=True, text=True).stdout, "")

    def test_abandon_deletes_the_remote_branch(self):
        self.assertEqual(self.script("setup-worktree.sh", "39", "race").returncode, 0)
        subprocess.run(["git", "-C", str(self.repo), "push", "-q", "origin", "race"], capture_output=True)
        down = self.script("teardown-worktree.sh", "--abandon", "39", "race")
        self.assertEqual(down.returncode, 0, down.stderr)
        self.assertEqual(subprocess.run(["git", "ls-remote", "--heads", str(self.origin), "race"], capture_output=True, text=True).stdout, "")
        self.assertFalse((self.repo / ".switchyard/state/39.json").exists())

    def stub_teardown_herdr(self, workspace, tree):
        # Stands in for `herdr worktree remove`, which takes the checkout with
        # it and leaves the local branch for `git branch -D`.
        self.stub("herdr", 'echo "$*" >> "$CALL_LOG"\nif [ "$1 $2" = "worktree list" ]; then printf \'%s\\n\' "$HERDR_LIST_RESULT"\nelif [ "$1 $2" = "worktree remove" ]; then git worktree remove --force "$HERDR_TREE"\nelse exit 23\nfi')
        env = self.env.copy()
        env["HERDR_ENV"] = "1"
        env["HERDR_LIST_RESULT"] = json.dumps({"result": {"worktrees": [{"branch": "topic", "open_workspace_id": workspace}]}})
        env["HERDR_TREE"] = str(tree)
        return env

    def test_abandon_forces_herdr_removal_on_dirty_worktree(self):
        self.assertEqual(self.script("setup-worktree.sh", "8", "topic").returncode, 0)
        tree = Path(self.record()["path"])
        self.make_dirty(tree)
        env = self.stub_teardown_herdr("ws-open", tree)
        down = self.script("teardown-worktree.sh", "--abandon", "8", "topic", env=env)
        self.assertEqual(down.returncode, 0, down.stderr)
        self.assertIn("worktree remove --workspace ws-open --force", self.log.read_text())
        self.assertFalse(tree.exists())
        self.assertFalse((self.repo / ".switchyard/state/8.json").exists())
        self.assertEqual(subprocess.run(["git", "-C", str(self.repo), "branch", "--list", "topic"], capture_output=True, text=True).stdout, "")

    def test_plain_teardown_refuses_dirty_herdr_worktree_before_removal(self):
        self.assertEqual(self.script("setup-worktree.sh", "8", "topic").returncode, 0)
        tree = Path(self.record()["path"])
        self.make_dirty(tree)
        env = self.stub_teardown_herdr("ws-open", tree)
        down = self.script("teardown-worktree.sh", "8", "topic", env=env)
        self.assertNotEqual(down.returncode, 0)
        self.assertIn("--abandon", down.stderr)
        # The stub logs every herdr call, so nothing means teardown stopped first.
        self.assertNotIn("worktree remove", self.log.read_text() if self.log.exists() else "")
        self.assertTrue((self.repo / ".switchyard/state/8.json").exists())
        self.assertTrue(tree.exists())



    def stack_git(self, *args, cwd=None):
        return subprocess.run(["git", "-C", str(cwd or self.repo), *args],
                              env=self.env, capture_output=True, text=True, check=True).stdout.strip()

    def stack_commit(self, tree, name, text):
        (tree / name).write_text(text)
        self.stack_git("add", name, cwd=tree)
        self.stack_git("commit", "-qm", name, cwd=tree)
        return self.stack_git("rev-parse", "HEAD", cwd=tree)

    def make_stack(self, herdr=False):
        self.stack_git("branch", "-M", "main")
        self.stack_git("push", "-q", "origin", "main")
        result = self.script("setup-worktree.sh", "8", "parent")
        self.assertEqual(result.returncode, 0, result.stderr)
        parent = Path(self.record()["path"])
        head = self.stack_commit(parent, "parent.txt", "parent\n")
        env = self.env.copy()
        if herdr:
            tree = self.base / "herdr-child"
            self.stack_git("worktree", "add", "-qb", "child", str(tree), "parent")
            env.update(HERDR_ENV="1", HERDR_CREATE_RESULT=json.dumps({"result": {"root_pane": {
                "cwd": str(tree), "pane_id": "w1:p2", "workspace_id": "ws1"}}}))
        result = self.script("setup-worktree.sh", "--parent", "8", "9", "child", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        child = Path(self.record("9")["path"])
        self.assertEqual(self.stack_git("rev-parse", "HEAD", cwd=child), head)
        for field, value in (("parent", "8"), ("parent_branch", "parent"), ("parent_head", head)):
            self.assertEqual(self.record("9")[field], value)
        if herdr:
            self.assertIn(f"--base {head}", self.log.read_text())
        return parent, child, head

    def test_setup_stacked_git_and_herdr(self):
        # Each runner uses the captured parent head, not the checkout's HEAD.
        self.make_stack()

    def test_setup_stacked_herdr(self):
        self.make_stack(herdr=True)

    def test_setup_refuses_missing_or_stacked_parent(self):
        for existing in (False, True):
            with self.subTest(existing=existing):
                if existing:
                    self.init(branch="parent", parent="7")
                result = self.script("setup-worktree.sh", "--parent", "8", "9", "child")
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("itself stacked" if existing else "no record", result.stderr)
                self.assertFalse((self.base / "repo.worktrees/child").exists())
                self.assertNotIn("refs/heads/child", self.stack_git("show-ref"))
                self.assertEqual(self.state("get", "9", "path").returncode, 3)

    def test_teardown_refuses_parent_until_all_children_clear(self):
        parent, child, _ = self.make_stack()
        self.init("10", parent="8")
        self.stack_git("push", "-q", "origin", "parent")
        before = self.record()
        self.down_hook.write_text('#!/bin/sh\ntouch "$MAIN_CHECKOUT/down-called"\n')
        for options in ((), ("--abandon",)):
            result = self.script("teardown-worktree.sh", *options, "8", "parent")
            self.assertEqual(result.returncode, 1, result.stderr)
            for number in ("9", "10"):
                self.assertIn(f"restack.sh {number}", result.stderr)
            self.assertTrue(parent.exists())
            self.assertTrue(child.exists())
            self.assertEqual(self.record(), before)
            self.assertFalse((self.repo / "down-called").exists())
            self.assertFalse((self.repo / ".switchyard/history.jsonl").exists())
            self.assertIn("refs/heads/parent", self.stack_git("ls-remote", "--heads", "origin", "parent"))
        for number in ("9", "10"):
            self.assertEqual(self.state("set", number, "parent=").returncode, 0)
        result = self.script("teardown-worktree.sh", "8", "parent")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(parent.exists())
        self.assertEqual(self.stack_git("ls-remote", "--heads", "origin", "parent"), "")

    def prepare_restack(self, conflict=False, pushed=True):
        parent, child, head = self.make_stack()
        self.stack_commit(child, "parent.txt" if conflict else "child.txt", "child\n")
        # The parent can gain fixes after the child branches.
        self.stack_commit(parent, "parent.txt", "parent fix\n")
        self.stack_git("push", "-q", "origin", "parent")
        if pushed:
            self.stack_git("push", "-q", "origin", "child")
        self.stack_git("merge", "--squash", "parent")
        self.stack_git("commit", "-qm", "squashed parent")
        self.stack_git("push", "-q", "origin", "main")
        self.stub("gh", 'echo "$*" >> "$CALL_LOG"\nif [ "$1 $2" = "pr list" ]; then printf "%s\\n" "${OPEN_PR:-42}"; elif [ "$1 $2" = "pr edit" ]; then [ "${FAIL_EDIT:-}" != 1 ]; else exit 23; fi')
        return child, head

    def test_restack_squash_replays_only_child_pushes_and_retargets(self):
        child, head = self.prepare_restack()
        result = self.script("restack.sh", "9")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.stack_git("rev-list", "--count", "origin/main..child"), "1")
        self.assertEqual(self.stack_git("diff", "--name-only", "origin/main...child"), "child.txt")
        self.assertEqual((child / "parent.txt").read_text(), "parent fix\n")
        self.assertNotEqual(self.stack_git("rev-parse", "child^"), head)
        self.assertEqual(self.stack_git("rev-parse", "child^"), self.stack_git("rev-parse", "origin/main"))
        self.assertEqual(self.stack_git("rev-parse", "child"), self.stack_git("rev-parse", "origin/child"))
        self.assertIn("pr edit child --base main", self.log.read_text())
        for field in ("parent", "parent_branch", "parent_head"):
            self.assertEqual(self.record("9")[field], "")

    def test_restack_conflict_aborts_and_preserves_record_and_remote(self):
        child, _ = self.prepare_restack(conflict=True)
        before = self.record("9")
        head = self.stack_git("rev-parse", "child")
        result = self.script("restack.sh", "9")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("parent.txt", result.stderr)
        self.assertEqual(self.stack_git("rev-parse", "child"), head)
        self.assertEqual(self.stack_git("rev-parse", "origin/child"), head)
        self.assertEqual(self.record("9"), before)
        self.assertEqual(self.stack_git("status", "--porcelain", cwd=child), "")
        for name in ("rebase-merge", "rebase-apply"):
            self.assertFalse(Path(self.stack_git("rev-parse", "--git-path", name, cwd=child)).exists())
        self.assertFalse(self.log.exists())

    def test_restack_without_remote_or_open_pr(self):
        child, _ = self.prepare_restack(pushed=False)
        # Match gh's empty output when no PR is open.
        self.stub("gh", 'echo "$*" >> "$CALL_LOG"\n[ "$1 $2" = "pr list" ]')
        result = self.script("restack.sh", "9")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.stack_git("ls-remote", "--heads", "origin", "child"), "")
        self.assertNotIn("pr edit", self.log.read_text())
        self.assertEqual(self.record("9")["parent"], "")
        self.assertEqual((child / "child.txt").read_text(), "child\n")

    def test_restack_failed_retarget_keeps_parent_fields(self):
        self.prepare_restack()
        before = self.record("9")
        env = self.env.copy(); env["FAIL_EDIT"] = "1"
        result = self.script("restack.sh", "9", env=env)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(self.record("9"), before)
        head = self.stack_git("rev-parse", "child")
        retry = self.script("restack.sh", "9")
        self.assertEqual(retry.returncode, 1, retry.stderr)
        self.assertIn("finish the push", retry.stderr)
        self.assertEqual(self.stack_git("rev-parse", "child"), head)
        self.assertEqual(self.record("9"), before)

    def test_restack_requires_parent_head(self):
        self.init(path=str(self.repo), branch="main")
        result = self.script("restack.sh", "8")
        self.assertEqual(result.returncode, 2)
        self.assertIn("parent_head", result.stderr)
        self.assertFalse(self.log.exists())

    def test_stacked_scope_ignores_parent_changes(self):
        _, child, _ = self.make_stack()
        self.state("set", "9", "owned=child.txt")
        self.stack_commit(child, "child.txt", "child\n")
        result = self.script("check-scope.sh", "9")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.stack_commit(child, "outside.txt", "outside\n")
        result = self.script("check-scope.sh", "9")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout.strip(), "outside.txt")
        self.state("set", "9", "parent_head=missing-ref")
        result = self.script("check-scope.sh", "9")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("every changed file is in scope", result.stdout)

    def test_setup_herdr_records_pane(self):
        env = self.env.copy(); env["HERDR_ENV"] = "1"
        env["HERDR_CREATE_RESULT"] = '{"result":{"root_pane":{"cwd":"' + str(self.base / "herdr-tree") + '","pane_id":"w9:p2","workspace_id":"ws9"}}}'
        self.stub("herdr", 'echo "$*" >> "$CALL_LOG"\nprintf \'%s\\n\' "$HERDR_CREATE_RESULT"')
        # Herdr is stubbed, so make the worktree it would have created.
        subprocess.run(["git", "-C", str(self.repo), "worktree", "add", "-qb", "topic", str(self.base / "herdr-tree")], check=True)
        result = self.script("setup-worktree.sh", "8", "topic", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        pushurl = subprocess.run(["git", "-C", str(self.base / "herdr-tree"), "config", "--worktree", "remote.origin.pushurl"], capture_output=True, text=True)
        self.assertEqual(pushurl.stdout.strip(), "workers-do-not-push")
        self.assertEqual(self.get("8", "runner"), "herdr")
        self.assertEqual(self.get("8", "pane"), "w9:p2")

    def test_status_empty_and_failed_lookups(self):
        self.assertIn("No issues in flight.", self.state("status").stdout)
        self.assertNotIn("agent list", self.log.read_text() if self.log.exists() else "")
        self.init(branch="b", path=str(self.repo), runner="herdr", worker="x")
        for failing in ("FAIL_GH", "FAIL_HERDR"):
            self.env.pop("FAIL_GH", None)
            self.env.pop("FAIL_HERDR", None)
            self.env[failing] = "1"
            result = self.state("status")
            self.assertEqual(result.returncode, 0)
            self.assertIn("?", result.stdout)
            self.assertTrue(result.stderr.strip())

    def test_start_worker_modes(self):
        self.init(branch="b", path=str(self.repo), runner="headless")
        sessions = []
        for provider in ("claude", "codex", "opencode", "pi"):
            issue = str(8 + len(sessions))
            self.init(issue, branch="b", path=str(self.repo), runner="headless")
            result = self.script("start-worker.sh", issue, "planner", provider)
            self.assertEqual(result.returncode, 0, result.stderr)
            record = self.record(issue)
            self.assertEqual(record["worker"], "")
            self.assertRegex(record["session"], r"^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
            sessions.append(record["session"])
        self.assertEqual(len(sessions), len(set(sessions)))
        self.init("20", branch="b", path=str(self.repo), runner="headless")
        first = self.script("start-worker.sh", "20", "planner", "pi")
        first_session = self.get("20", "session")
        second = self.script("start-worker.sh", "20", "implementer", "pi")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertNotEqual(first_session, self.get("20", "session"))
        self.init("10", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1")
        herdr_env = self.env.copy(); herdr_env["HERDR_ENV"] = "1"
        result = self.script("start-worker.sh", "10", "planner", "pi", "--", "--agent", "x", env=herdr_env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [f"path={self.repo}", "pane=w1:p1", "name=planner-10"])
        self.assertEqual(self.get("10", "worker"), "planner-10")
        self.assertIn("agent start planner-10 --kind pi --pane w1:p1 -- --agent x", self.log.read_text())
        result = self.script("start-worker.sh", "10", "planner", "pi", "--turns", env=herdr_env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(self.get("10", "session"), r"^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
        self.assertEqual(self.record("10")["worker"], "")
        self.assertEqual(self.record("10")["role"], "planner")
        self.assertIn("pane=w1:p1", result.stdout)
        self.assertIn("session=", result.stdout)
        calls = self.log.read_text()
        self.assertEqual(calls.count("agent start"), 1)
        self.init("21", branch="b", path=str(self.repo), runner="headless")
        self.assertEqual(self.script("start-worker.sh", "21", "planner", "pi", "--turns").returncode, 0)
        before = self.record("10")
        fail_env = herdr_env.copy(); fail_env["FAIL_START"] = "1"
        failed = self.script("start-worker.sh", "10", "planner", "claude", env=fail_env)
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(self.record("10"), before)

    def test_start_failures_do_not_mutate(self):
        self.init(branch="b", path=str(self.repo), runner="headless", role="planner", backend="codex", session="old")
        before = self.record()
        for args in [("8", "unknown", "claude"), ("8", "planner", "bad"), ("8", "planner", "ClaUde"), ("8", "planner", "foo/bar"), ("8", "planner", "eval"), ("99", "planner", "claude")]:
            result = self.script("start-worker.sh", *args)
            self.assertNotEqual(result.returncode, 0)
            if args[2] != "claude":
                self.assertIn(args[2], result.stderr)
        self.assertEqual(self.record(), before)

    def test_start_worker_records_agent_blocked_at_startup(self):
        self.init("10", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1")
        self.stub("herdr", 'echo "$*" >> "$CALL_LOG"\nif [ "$1 $2" = "agent start" ]; then echo \'{"error":{"code":"agent_not_ready","message":"blocked during startup"}}\' >&2; exit 1; fi\nexit 23')
        env = self.env.copy(); env["HERDR_ENV"] = "1"
        result = self.script("start-worker.sh", "10", "implementer", "codex", env=env)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(self.record("10")["role"], "implementer")
        self.assertEqual(self.record("10")["worker"], "implementer-10")
        self.assertEqual(self.record("10")["implementer_backend"], "codex")
        self.assertTrue(result.stdout.endswith("status=blocked\n"))
        self.assertIn("blocked at startup", result.stderr)
        self.assertEqual(self.record("10")["phases"][0]["provider"], "codex")
        self.assertNotIn("ended", self.record("10")["phases"][0])

    def stub_end_worker(self, status="idle"):
        gone = self.base / "agent-gone"
        body = '''echo "$*" >> "$CALL_LOG"
if [ "$1 $2" = "agent get" ]; then
  if [ -f "$AGENT_GONE" ]; then echo '{"error":{"code":"agent_not_found"}}' >&2; exit 1; fi
  printf '{"result":{"agent":{"agent_status":"%s"}}}\\n' "$AGENT_STATE"
elif [ "$1 $2" = "agent prompt" ]; then
  if [ "${RACE_GONE:-}" = 1 ]; then
    touch "$AGENT_GONE"
    echo '{"error":{"code":"agent_not_found"}}' >&2
    exit 1
  fi
  if [ "${PROMPT_BLOCKED:-}" = 1 ]; then
    echo '{"error":{"code":"agent_blocked"}}' >&2
    exit 1
  fi
  printf '{"result":{"prompted":true}}\\n'
  if [ "${NO_END:-}" != 1 ]; then touch "$AGENT_GONE"; fi
elif [ "$1 $2" = "pane process-info" ]; then
  printf '{"result":{"process_info":{"shell_pid":123,"foreground_process_group_id":123}}}\\n'
elif [ "$1 $2" = "pane send-keys" ]; then printf '{"result":{"sent":true}}\\n'
else exit 23
fi'''
        self.stub("herdr", body.replace('"%s"', f'"{status}"'))
        env = self.env.copy()
        env.update(HERDR_ENV="1", AGENT_GONE=str(gone), AGENT_STATE=status)
        return env

    def test_end_worker_lifecycle_cases(self):
        self.init("8", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1", worker="implementer-8", backend="claude")
        (self.skill / "routing.md").write_text("| Provider | On Herdr | End |\n|---|---|---|\n| claude | agent | `/exit` |\n")
        self.state("set", "8", "role=implementer")
        self.assertEqual(self.state("phase-start", "8").returncode, 0)
        live_env = self.stub_end_worker()
        ended = self.script("end-worker.sh", "8", env=live_env)
        self.assertEqual(ended.returncode, 0, ended.stderr)
        self.assertEqual(ended.stdout, "ended=implementer-8\n")
        self.assertIn("ended", self.record()["phases"][0])
        calls = self.log.read_text()
        self.assertIn("agent prompt implementer-8 /exit", calls)
        self.assertIn("pane send-keys w1:p1 ctrl+u", calls)

        self.log.write_text("")
        gone_env = self.stub_end_worker()
        (Path(gone_env["AGENT_GONE"])).write_text("gone")
        already = self.script("end-worker.sh", "8", env=gone_env)
        self.assertEqual(already.returncode, 0, already.stderr)
        self.assertNotIn("agent prompt", self.log.read_text())
        self.assertIn("pane send-keys w1:p1 ctrl+u", self.log.read_text())

        self.log.write_text("")
        race_env = self.stub_end_worker(); race_env["RACE_GONE"] = "1"
        Path(race_env["AGENT_GONE"]).unlink(missing_ok=True)
        raced = self.script("end-worker.sh", "8", env=race_env)
        self.assertEqual(raced.returncode, 0, raced.stderr)
        self.assertEqual(raced.stdout, "ended=implementer-8\n")
        self.assertIn("agent prompt implementer-8 /exit", self.log.read_text())
        self.assertIn("pane send-keys w1:p1 ctrl+u", self.log.read_text())

        self.log.write_text("")
        blocked_env = self.stub_end_worker(); blocked_env["PROMPT_BLOCKED"] = "1"
        Path(blocked_env["AGENT_GONE"]).unlink(missing_ok=True)
        blocked = self.script("end-worker.sh", "8", env=blocked_env)
        self.assertEqual(blocked.returncode, 1)
        self.assertIn("agent_blocked", blocked.stderr)
        self.assertNotIn("ended=", blocked.stdout)

    def test_end_worker_refuses_active_agents_and_bad_routing(self):
        self.init("8", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1", worker="implementer-8", backend="claude")
        (self.skill / "routing.md").write_text("| Provider | On Herdr | End |\n|---|---|---|\n| claude | agent | `/exit` |\n")
        self.state("set", "8", "role=implementer")
        self.state("phase-start", "8")
        for state in ("working", "blocked"):
            self.log.write_text("")
            result = self.script("end-worker.sh", "8", env=self.stub_end_worker(state))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(state, result.stderr)
            self.assertNotIn("ended", self.record()["phases"][0])
            self.assertNotIn("agent prompt", self.log.read_text())
        (self.skill / "routing.md").write_text("| Provider | On Herdr | End |\n|---|---|---|\n| claude | agent | |\n")
        result = self.script("end-worker.sh", "8", env=self.stub_end_worker())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("claude", result.stderr)

    def test_end_worker_empty_worker_headless_and_timeout(self):
        self.init("8", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1", worker="", backend="opencode")
        self.state("set", "8", "role=implementer")
        self.state("phase-start", "8")
        empty = self.script("end-worker.sh", "8")
        self.assertEqual(empty.returncode, 0, empty.stderr)
        self.assertFalse(self.log.exists())
        self.assertIn("ended", self.record()["phases"][0])
        self.init("9", branch="b", path=str(self.repo), runner="headless", worker="x", backend="claude")
        headless = self.script("end-worker.sh", "9")
        self.assertNotEqual(headless.returncode, 0)
        self.assertIn("Herdr", headless.stderr)
        self.init("10", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1", worker="implementer-10", backend="claude")
        (self.skill / "routing.md").write_text("| Provider | On Herdr | End |\n|---|---|---|\n| claude | agent | `/exit` |\n")
        self.state("set", "10", "role=implementer")
        self.state("phase-start", "10")
        env = self.stub_end_worker(); env["NO_END"] = "1"; env["END_WORKER_TIMEOUT_SECONDS"] = "1"
        timed = self.script("end-worker.sh", "10", env=env)
        self.assertNotEqual(timed.returncode, 0)
        self.assertIn("last state", timed.stderr)
        self.assertNotIn("ended", self.record("10")["phases"][0])

    def test_start_without_routing_file_succeeds(self):
        self.init(branch="b", path=str(self.repo), runner="headless", role="planner", backend="codex", session="old")
        (self.skill / "routing.md").unlink()
        result = self.script("start-worker.sh", "8", "planner", "claude")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.get("8", "backend"), "claude")

    def test_worktree_cannot_push_and_scope_is_checked(self):
        (self.repo / "openspec").mkdir()
        git = lambda *args, cwd=self.repo: subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
        self.assertEqual(git("push", "-q", "origin", "HEAD:main").returncode, 0)
        git("fetch", "-q", "origin")
        self.assertEqual(self.script("setup-worktree.sh", "8", "topic").returncode, 0)
        tree = Path(self.record()["path"])
        missing = self.script("check-scope.sh", "8")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("owned", missing.stderr)
        self.state("set", "8", "owned=src/ docs/guide.md")
        for name in ["src/a.py", "docs/guide.md", "openspec/changes/x/tasks.md"]:
            (tree / name).parent.mkdir(parents=True, exist_ok=True)
            (tree / name).write_text("x")
        git("add", "-A", cwd=tree); git("commit", "-qm", "in scope", cwd=tree)
        result = self.script("check-scope.sh", "8")
        self.assertEqual(result.returncode, 0, result.stderr)
        (tree / "README.md").write_text("x"); (tree / "srcs.py").write_text("x")
        git("add", "-A", cwd=tree); git("commit", "-qm", "out of scope", cwd=tree)
        result = self.script("check-scope.sh", "8")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.split(), ["README.md", "srcs.py"])

        blocked = git("push", "origin", "topic", cwd=tree)
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("workers-do-not-push", blocked.stderr)
        self.assertEqual(git("ls-remote", "--heads", "origin", "topic").stdout, "")
        self.assertEqual(git("push", "-q", "origin", "topic").returncode, 0)
        self.assertIn("refs/heads/topic", git("ls-remote", "--heads", "origin", "topic").stdout)
        self.assertEqual(self.script("teardown-worktree.sh", "8", "topic").returncode, 0)

    def test_scope_uses_main_checkout_mode(self):
        git = lambda *args, cwd=self.repo: subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True)
        git("push", "-q", "origin", "HEAD:main")
        git("fetch", "-q", "origin")
        setup = self.script("setup-worktree.sh", "8", "topic")
        self.assertEqual(setup.returncode, 0, setup.stderr)
        tree = Path(self.record()["path"])
        self.state("set", "8", "owned=src/")
        plan = tree / "openspec/changes/x/tasks.md"
        plan.parent.mkdir(parents=True)
        plan.write_text("- [x] Done\n")
        git("add", "openspec", cwd=tree)
        git("commit", "-qm", "add change", cwd=tree)

        plain = self.script("check-scope.sh", "8")
        self.assertEqual(plain.returncode, 1, plain.stderr)
        self.assertEqual(plain.stdout.splitlines(), ["openspec/changes/x/tasks.md"])
        (self.repo / "openspec").mkdir()
        spec = self.script("check-scope.sh", "8")
        self.assertEqual(spec.returncode, 0, spec.stderr)

    def test_check_scope_reports_all_files_when_owned_is_blank(self):
        bash = "/bin/bash"
        version = subprocess.run([bash, "-c", "echo $BASH_VERSION"], capture_output=True, text=True).stdout.strip()
        if not version.startswith("3."):
            self.skipTest(f"test needs bash 3; /bin/bash is {version or 'unknown'}")
        git = lambda *args, cwd=self.repo: subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
        self.assertEqual(git("push", "-q", "origin", "HEAD:main").returncode, 0)
        git("fetch", "-q", "origin")
        self.assertEqual(self.script("setup-worktree.sh", "8", "topic").returncode, 0)
        tree = Path(self.record()["path"])
        self.state("set", "8", "owned= ")
        (tree / "README.md").write_text("x")
        added = git("add", "-A", cwd=tree)
        committed = git("commit", "-qm", "out of scope", cwd=tree)
        result = subprocess.run([bash, str(self.skill / "scripts/check-scope.sh"), "8"], cwd=self.repo, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout + added.stderr + committed.stderr)
        self.assertEqual(result.stdout.split(), ["README.md"])
        self.assertNotIn("unbound variable", result.stderr)

    def test_reviewer_runs_on_another_provider(self):
        self.init(branch="b", path=str(self.repo), runner="headless")
        self.assertEqual(self.script("start-worker.sh", "8", "planner", "claude").returncode, 0)
        before = self.record()
        failed = self.script("start-worker.sh", "8", "reviewer", "codex")
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("no implementer has run", failed.stderr)
        self.assertEqual(self.record(), before)

        self.assertEqual(self.script("start-worker.sh", "8", "implementer", "claude").returncode, 0)
        self.assertEqual(self.get("8", "implementer_backend"), "claude")
        before = self.record()
        for backend, reason in [("claude", "another provider")]:
            failed = self.script("start-worker.sh", "8", "reviewer", backend)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn(reason, failed.stderr)
            self.assertEqual(self.record(), before)

        self.assertEqual(self.script("start-worker.sh", "8", "reviewer", "codex").returncode, 0)
        self.assertEqual(self.record()["role"], "reviewer")
        self.assertEqual(self.record()["backend"], "codex")
        self.assertEqual(self.get("8", "implementer_backend"), "claude")
        status = self.state("status")
        self.assertRegex(status.stdout, r"8\s+b\s+reviewer\s+codex")

        same = self.env.copy(); same["SWITCHYARD_SAME_PROVIDER"] = "1"
        result = self.script("start-worker.sh", "8", "reviewer", "claude", env=same)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.record()["backend"], "claude")
        self.assertEqual(self.script("start-worker.sh", "8", "reviewer", "opencode", env=same).returncode, 0)

    def test_opencode_same_provider_reviewer_needs_override(self):
        self.init(branch="b", path=str(self.repo), runner="headless")
        self.assertEqual(self.script("start-worker.sh", "8", "implementer", "opencode").returncode, 0)

        result = self.script("start-worker.sh", "8", "reviewer", "opencode")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("another provider", result.stderr)

        same = self.env.copy()
        same["SWITCHYARD_SAME_PROVIDER"] = "1"
        result = self.script("start-worker.sh", "8", "reviewer", "opencode", env=same)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.record()["backend"], "opencode")

    def test_opencode_reviewer_after_claude_needs_no_override(self):
        self.init(branch="b", path=str(self.repo), runner="headless")
        self.assertEqual(self.script("start-worker.sh", "8", "implementer", "claude").returncode, 0)

        result = self.script("start-worker.sh", "8", "reviewer", "opencode")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.record()["backend"], "opencode")

    def test_reviewer_starts_in_split_herdr_pane(self):
        self.init("10", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1")
        herdr_env = self.env.copy(); herdr_env["HERDR_ENV"] = "1"
        self.assertEqual(self.script("start-worker.sh", "10", "implementer", "codex", env=herdr_env).returncode, 0)
        result = self.script("start-worker.sh", "10", "reviewer", "claude", "--", "--agent", "issue-reviewer", env=herdr_env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [f"path={self.repo}", "pane=w1:p2", "name=reviewer-10"])
        calls = self.log.read_text()
        self.assertIn(f"pane split w1:p1 --direction down --cwd {self.repo}", calls)
        self.assertIn("agent start reviewer-10 --kind claude --pane w1:p2 -- --agent issue-reviewer", calls)
        record = self.record("10")
        self.assertEqual((record["worker"], record["reviewer_worker"], record["reviewer_pane"]), ("reviewer-10", "reviewer-10", "w1:p2"))
        self.assertEqual((record["implementer_worker"], record["implementer_pane"], record["pane"]), ("implementer-10", "w1:p1", "w1:p1"))

        self.log.write_text("")
        turns = self.script("start-worker.sh", "10", "reviewer", "claude", "--turns", env=herdr_env)
        self.assertEqual(turns.returncode, 0, turns.stderr)
        self.assertIn("pane=w1:p2", turns.stdout)
        self.assertIn("pane split w1:p1", self.log.read_text())
        self.assertEqual(self.record("10")["reviewer_worker"], "")

        before = self.record("10")
        fail_env = herdr_env.copy(); fail_env["FAIL_START"] = "1"
        failed = self.script("start-worker.sh", "10", "reviewer", "claude", env=fail_env)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("pane close w1:p2", self.log.read_text())
        self.assertEqual(self.record("10"), before)

    def test_start_records_each_role_fields(self):
        self.init(branch="b", path=str(self.repo), runner="headless")
        self.assertEqual(self.script("start-worker.sh", "8", "planner", "claude").returncode, 0)
        self.assertEqual(self.script("start-worker.sh", "8", "implementer", "codex").returncode, 0)
        record = self.record()
        self.assertEqual((record["planner_backend"], record["implementer_backend"]), ("claude", "codex"))
        self.assertNotEqual(record["planner_session"], record["implementer_session"])
        self.assertEqual(record["session"], record["implementer_session"])
        self.assertNotIn("planner_pane", record)
        self.init("10", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1")
        herdr_env = self.env.copy(); herdr_env["HERDR_ENV"] = "1"
        for role in ("planner", "implementer"):
            self.assertEqual(self.script("start-worker.sh", "10", role, "pi", env=herdr_env).returncode, 0)
        record = self.record("10")
        for role in ("planner", "implementer"):
            self.assertEqual((record[f"{role}_worker"], record[f"{role}_pane"], record[f"{role}_backend"], record[f"{role}_session"]),
                             (f"{role}-10", "w1:p1", "pi", ""))

    def stub_agents(self):
        # Several named agents at once: <name>.gone marks an exited agent,
        # <name>.state holds a live agent's status (idle by default), and
        # pane-<id>.gone marks a pane closed by hand.
        agents = self.base / "agents"
        agents.mkdir(exist_ok=True)
        self.stub("herdr", '''echo "$*" >> "$CALL_LOG"
case "$1 $2" in
  "agent start") rm -f "$AGENTS/$3.gone"; echo started ;;
  "agent get")
    if [ -f "$AGENTS/$3.gone" ]; then echo \'{"error":{"code":"agent_not_found"}}\' >&2; exit 1; fi
    printf \'{"result":{"agent":{"agent_status":"%s"}}}\\n\' "$(cat "$AGENTS/$3.state" 2>/dev/null || echo idle)" ;;
  "agent prompt") touch "$AGENTS/$3.gone"; echo \'{"result":{}}\' ;;
  "pane split") echo \'{"result":{"pane":{"pane_id":"w1:p2"}}}\' ;;
  "pane close")
    if [ -f "$AGENTS/pane-$3.gone" ]; then echo \'{"error":{"code":"pane_not_found"}}\'; exit 1; fi
    echo \'{"result":{"type":"ok"}}\' ;;
  "pane process-info")
    if [ -f "$AGENTS/pane-$4.gone" ]; then echo \'{"error":{"code":"pane_not_found"}}\'; exit 1; fi
    echo \'{"result":{"process_info":{"shell_pid":1,"foreground_process_group_id":1}}}\' ;;
  "pane send-keys") echo \'{"result":{}}\' ;;
  *) exit 23 ;;
esac''')
        (self.skill / "routing.md").write_text("| Provider | On Herdr | End |\n|---|---|---|\n| claude | agent | `/exit` |\n| codex | agent | `/quit` |\n| opencode | turns | |\n")
        env = self.env.copy()
        env.update(HERDR_ENV="1", AGENTS=str(agents))
        return env, agents

    def test_resume_opens_a_phase_on_the_recorded_session(self):
        env, agents = self.stub_agents()
        self.init("10", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1")
        self.assertEqual(self.script("start-worker.sh", "10", "implementer", "codex", env=env).returncode, 0)
        self.assertEqual(self.script("start-worker.sh", "10", "reviewer", "claude", env=env).returncode, 0)
        self.log.write_text("")
        resumed = self.script("start-worker.sh", "10", "implementer", "codex", "--resume", env=env)
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(resumed.stdout.splitlines(), [f"path={self.repo}", "pane=w1:p1", "name=implementer-10"])
        self.assertNotIn("agent start", self.log.read_text())
        record = self.record("10")
        self.assertEqual((record["role"], record["backend"], record["worker"]), ("implementer", "codex", "implementer-10"))
        self.assertEqual([p["role"] for p in record["phases"]], ["implementer", "reviewer", "implementer"])

        before = self.record("10")
        mismatch = self.script("start-worker.sh", "10", "implementer", "claude", "--resume", env=env)
        self.assertEqual(mismatch.returncode, 4)
        self.assertEqual(len(mismatch.stderr.strip().splitlines()), 1)
        self.assertIn("fresh", mismatch.stderr)
        (agents / "implementer-10.state").write_text("working")
        busy = self.script("start-worker.sh", "10", "implementer", "codex", "--resume", env=env)
        self.assertEqual(busy.returncode, 1)
        self.assertIn("working", busy.stderr)
        (agents / "implementer-10.gone").touch()
        gone = self.script("start-worker.sh", "10", "implementer", "codex", "--resume", env=env)
        self.assertEqual(gone.returncode, 4)
        self.assertIn("fresh", gone.stderr)
        self.assertEqual(self.record("10"), before)

        self.init(branch="b", path=str(self.repo), runner="headless")
        self.assertEqual(self.script("start-worker.sh", "8", "implementer", "claude").returncode, 0)
        session = self.get("8", "implementer_session")
        self.assertEqual(self.script("start-worker.sh", "8", "reviewer", "codex").returncode, 0)
        resumed = self.script("start-worker.sh", "8", "implementer", "claude", "--resume")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(resumed.stdout.splitlines(), [f"path={self.repo}", f"session={session}"])
        self.assertEqual(self.get("8", "session"), session)
        self.state("set", "8", "implementer_session=")
        before = self.record()
        missing = self.script("start-worker.sh", "8", "implementer", "claude", "--resume")
        self.assertEqual(missing.returncode, 4)
        self.assertIn("fresh", missing.stderr)
        never = self.script("start-worker.sh", "8", "planner", "claude", "--resume")
        self.assertEqual(never.returncode, 4)
        self.assertEqual(self.record(), before)

    def test_end_worker_by_role_and_every_live_agent(self):
        env, agents = self.stub_agents()
        self.init("10", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1")
        self.assertEqual(self.script("start-worker.sh", "10", "implementer", "codex", env=env).returncode, 0)
        self.assertEqual(self.script("start-worker.sh", "10", "reviewer", "claude", env=env).returncode, 0)
        self.log.write_text("")
        ended = self.script("end-worker.sh", "10", "reviewer", env=env)
        self.assertEqual(ended.returncode, 0, ended.stderr)
        self.assertEqual(ended.stdout.splitlines(), ["ended=reviewer-10", "closed=w1:p2"])
        calls = self.log.read_text()
        self.assertIn("agent prompt reviewer-10 /exit", calls)
        self.assertIn("pane close w1:p2", calls)
        self.assertNotIn("implementer-10", calls)
        record = self.record("10")
        self.assertEqual((record["reviewer_worker"], record["reviewer_pane"]), ("", ""))
        self.assertEqual(record["implementer_worker"], "implementer-10")
        self.assertIn("ended", record["phases"][-1])

        self.assertEqual(self.script("start-worker.sh", "10", "reviewer", "claude", env=env).returncode, 0)
        self.log.write_text("")
        both = self.script("end-worker.sh", "10", env=env)
        self.assertEqual(both.returncode, 0, both.stderr)
        self.assertEqual(both.stdout.splitlines(), ["ended=reviewer-10", "closed=w1:p2", "ended=implementer-10"])
        calls = self.log.read_text()
        self.assertIn("agent prompt implementer-10 /quit", calls)
        self.assertIn("pane send-keys w1:p1 ctrl+u", calls)
        self.assertEqual(self.record("10")["reviewer_pane"], "")

        self.assertEqual(self.script("start-worker.sh", "10", "reviewer", "opencode", "--turns", env=env).returncode, 0)
        self.log.write_text("")
        turns = self.script("end-worker.sh", "10", "reviewer", env=env)
        self.assertEqual(turns.returncode, 0, turns.stderr)
        self.assertEqual(turns.stdout.splitlines(), ["closed=w1:p2"])
        self.assertNotIn("agent", self.log.read_text())

        (agents / "implementer-10.gone").unlink()
        (agents / "implementer-10.state").write_text("working")
        busy = self.script("end-worker.sh", "10", env=env)
        self.assertEqual(busy.returncode, 1)
        self.assertIn("working", busy.stderr)
        self.assertNotEqual(self.script("end-worker.sh", "10", "nobody", env=env).returncode, 0)

    def test_end_reviewer_whose_pane_was_closed_by_hand(self):
        env, agents = self.stub_agents()
        self.init("10", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1")
        self.assertEqual(self.script("start-worker.sh", "10", "implementer", "codex", env=env).returncode, 0)
        self.assertEqual(self.script("start-worker.sh", "10", "reviewer", "claude", env=env).returncode, 0)
        (agents / "reviewer-10.gone").touch()
        (agents / "pane-w1:p2.gone").touch()
        ended = self.script("end-worker.sh", "10", "reviewer", env=env)
        self.assertEqual(ended.returncode, 0, ended.stderr)
        self.assertEqual(ended.stdout.splitlines(), ["ended=reviewer-10", "closed=w1:p2"])
        record = self.record("10")
        self.assertEqual((record["reviewer_worker"], record["reviewer_pane"], record["worker"]), ("", "", ""))
        self.assertIn("ended", record["phases"][-1])
        resumed = self.script("start-worker.sh", "10", "implementer", "codex", "--resume", env=env)
        self.assertEqual(resumed.returncode, 0, resumed.stderr)

    def test_ending_legacy_reviewer_keeps_root_pane(self):
        env, agents = self.stub_agents()
        self.init("10", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1", role="reviewer",
                  backend="claude", implementer_backend="codex", worker="reviewer-10", session="")
        ended = self.script("end-worker.sh", "10", "reviewer", env=env)
        self.assertEqual(ended.returncode, 0, ended.stderr)
        self.assertEqual(ended.stdout.splitlines(), ["ended=reviewer-10"])
        self.assertNotIn("pane close", self.log.read_text())
        record = self.record("10")
        self.assertEqual((record["pane"], record["reviewer_worker"], record["worker"]), ("w1:p1", "", ""))

    def test_record_from_before_role_fields_keeps_both_agents(self):
        env, agents = self.stub_agents()
        self.init("10", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1", role="implementer",
                  backend="codex", implementer_backend="codex", worker="implementer-10", session="")
        started = self.script("start-worker.sh", "10", "reviewer", "claude", env=env)
        self.assertEqual(started.returncode, 0, started.stderr)
        record = self.record("10")
        self.assertEqual((record["implementer_worker"], record["implementer_pane"]), ("implementer-10", "w1:p1"))
        self.log.write_text("")
        ended = self.script("end-worker.sh", "10", "reviewer", env=env)
        self.assertEqual(ended.returncode, 0, ended.stderr)
        self.assertEqual(ended.stdout.splitlines(), ["ended=reviewer-10", "closed=w1:p2"])
        calls = self.log.read_text()
        self.assertIn("pane close w1:p2", calls)
        self.assertNotIn("w1:p1", calls)
        record = self.record("10")
        self.assertEqual((record["reviewer_worker"], record["reviewer_pane"], record["worker"]), ("", "", ""))
        resumed = self.script("start-worker.sh", "10", "implementer", "codex", "--resume", env=env)
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertIn("name=implementer-10", resumed.stdout)
        both = self.script("end-worker.sh", "10", env=env)
        self.assertEqual(both.returncode, 0, both.stderr)
        self.assertEqual(both.stdout.splitlines(), ["ended=implementer-10"])

    def test_phases_stay_sequential_across_a_resumed_fix_round(self):
        env, agents = self.stub_agents()
        self.init("10", branch="b", path=str(self.repo), runner="herdr", pane="w1:p1")
        steps = [("start-worker.sh", "10", "planner", "claude"), ("end-worker.sh", "10"),
                 ("start-worker.sh", "10", "implementer", "codex"), ("start-worker.sh", "10", "reviewer", "claude"),
                 ("end-worker.sh", "10", "reviewer"), ("start-worker.sh", "10", "implementer", "codex", "--resume")]
        for step in steps:
            result = self.script(*step, env=env)
            self.assertEqual(result.returncode, 0, f"{step}: {result.stderr}")
            phases = self.record("10")["phases"]
            self.assertLessEqual(sum("ended" not in p for p in phases), 1)
        phases = self.record("10")["phases"]
        self.assertEqual([p["role"] for p in phases], ["planner", "implementer", "reviewer", "implementer"])
        self.assertTrue(all("ended" in p for p in phases[:3]))
        self.assertNotIn("ended", phases[3])
        for earlier, later in zip(phases, phases[1:]):
            self.assertLessEqual(earlier["ended"], later["started"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
