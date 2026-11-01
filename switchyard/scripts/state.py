#!/usr/bin/env python3
"""Read and update issue records in the main checkout's ignored state folder."""

from datetime import datetime, timezone
import shlex
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def fail(issue, message, status=1):
    print(f"Issue {issue}: {message}", file=sys.stderr)
    raise SystemExit(status)


def repo_root():
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    )
    first = next(line[9:] for line in result.stdout.splitlines() if line.startswith("worktree "))
    return Path(first)


def valid_key(issue):
    # The b suffix marks a best-of-N issue's second candidate.
    return re.fullmatch(r"[0-9]+b?", issue) is not None


def key_order(issue):
    return int(issue.rstrip("b")), issue


def issue_path(issue):
    if not valid_key(issue):
        fail(issue, "issue key must be digits, optionally followed by b")
    return repo_root() / ".switchyard" / "state" / f"{issue}.json"


def read_record(issue):
    path = issue_path(issue)
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        fail(issue, "no record. Run setup-worktree.sh, or state.py init", 3)
    except (OSError, json.JSONDecodeError) as exc:
        fail(issue, f"cannot read record: {exc}")


def write_record(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def fields(args, issue):
    result = {}
    for item in args:
        if "=" not in item:
            fail(issue, f"expected key=value, got {item}")
        key, value = item.split("=", 1)
        if not key:
            fail(issue, "field name cannot be empty")
        if key in {"issue", "phases", "archived"}:
            fail(issue, f"{key} is a reserved field")
        result[key] = value
    return result


def command(args):
    if not args:
        fail("?", "usage: state.py init|set|get|rm|status|phase-start|phase-end|turn-start|turn-end|archive|timings ...")
    action = args.pop(0)
    if action == "timings":
        timings(args)
        return
    if action == "status":
        status()
        return
    if not args:
        fail("?", f"{action} requires an issue number")
    issue = args.pop(0)
    path = issue_path(issue)
    if action == "init":
        record = {"issue": issue, **fields(args, issue)}
        write_record(path, record)
    elif action == "set":
        record = read_record(issue)
        record.update(fields(args, issue))
        write_record(path, record)
    elif action == "get":
        if len(args) != 1:
            fail(issue, "get requires one field name")
        value = read_record(issue).get(args[0])
        if value is None or value == "":
            fail(issue, f"field {args[0]} is missing or empty")
        print(value)
    elif action in {"phase-start", "phase-end", "turn-start", "turn-end", "archive"}:
        if args and (action != "archive" or args != ["--abandon"]):
            fail(issue, f"unexpected arguments for {action}")
        record = read_record(issue)
        if action == "archive" and record.get("archived"):
            return
        if action == "phase-start" and (not record.get("role") or not record.get("backend")):
            fail(issue, "phase-start requires role and backend")
        now = timestamp()
        if action == "turn-end":
            phase = open_phase(record)
            turns = phase.get("turns") if phase else None
            if turns and "ended" not in turns[-1]:
                turns[-1]["ended"] = now
                write_record(path, record)
            return
        if action == "turn-start":
            phase = open_phase(record)
            if phase is None:
                fail(issue, "no open phase. Start the worker with start-worker.sh")
            turns = phase.setdefault("turns", [])
            if not turns or "ended" in turns[-1]:
                turns.append({"started": now})
                write_record(path, record)
            return
        changed = close_phases(record, now)
        if action == "phase-start":
            role = record["role"]
            record.setdefault("phases", []).append({
                "role": role, "provider": record["backend"],
                "row": record.get(f"{role}_row", ""), "started": now,
                "turns": [{"started": now}],
            })
            changed = True
        elif action == "archive":
            rounds, verdict = review_result(record)
            summary = {key: record.get(key, "") for key in ("issue", "branch", "plan_size", "size")}
            summary.update(phases=record.get("phases", []), rounds=rounds, verdict=verdict,
                           abandoned=bool(args), archived=now)
            history = repo_root() / ".switchyard/history.jsonl"
            history.parent.mkdir(parents=True, exist_ok=True)
            with history.open("a") as handle:
                handle.write(json.dumps(summary) + "\n")
            record["archived"] = now
            changed = True
        if changed:
            write_record(path, record)
    elif action == "rm":
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    else:
        fail(issue, f"unknown command {action}")


def timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def close_phases(record, now):
    changed = False
    for phase in record.get("phases", []):
        if "ended" not in phase:
            phase["ended"] = now
            changed = True
            # Close the turn with the phase so a forgotten turn-end cannot
            # push busy time past the session's real length.
            for turn in phase.get("turns", []):
                if "ended" not in turn:
                    turn["ended"] = now
    return changed


def open_phase(record):
    phases = record.get("phases", [])
    if phases and "ended" not in phases[-1]:
        return phases[-1]
    return None


def review_result(record):
    if "rounds" in record:
        return record["rounds"], record["verdict"]
    if not record.get("path"):
        return "-", "-"
    folder = Path(record["path"]) / ".switchyard/reviews"
    files = [p for p in folder.glob("*.md") if p.stem.isascii() and p.stem.isdigit()]
    if not files:
        return "-", "-"
    lines = max(files, key=lambda p: int(p.stem)).read_text().splitlines()
    return len(files), lines[0].removeprefix("Verdict: ") if lines else "-"


def model(row):
    if not row:
        return "-"
    words = shlex.split(row)
    for index, word in enumerate(words):
        if word.startswith("--model="):
            return word.split("=", 1)[1]
        if word in {"--model", "-m"} and index + 1 < len(words):
            return words[index + 1]
    return "default"


def seconds(start, end):
    return int((datetime.fromisoformat(end.replace("Z", "+00:00")) -
                datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds())


def duration(value):
    if value < 60:
        return f"{value}s"
    if value < 3600:
        return f"{value // 60}m"
    return f"{value // 3600}h{value % 3600 // 60:02d}m"


def total_time(record, now):
    phases = record.get("phases", [])
    if not phases:
        return "0s"
    return duration(seconds(min(p["started"] for p in phases),
                            max(p.get("ended", now) for p in phases)))


def phase_busy(phase, now):
    """Seconds the phase was busy, or None when the phase has no turns."""
    turns = phase.get("turns")
    if turns is None:
        return None
    return sum(seconds(turn["started"], turn.get("ended", now)) for turn in turns)


def print_table(headers, rows):
    widths = [max(len(header), *(len(str(row[i])) for row in rows))
              for i, header in enumerate(headers)] if rows else [len(h) for h in headers]
    for row in [headers, *rows]:
        print("  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)).rstrip())


def timings(args):
    if len(args) > 1:
        fail("?", "usage: state.py timings [issue]")
    root = repo_root() / ".switchyard"
    history = []
    if (root / "history.jsonl").exists():
        for number, line in enumerate((root / "history.jsonl").read_text().splitlines(), 1):
            try:
                history.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"Cannot read history line {number}: {exc}", file=sys.stderr)
    now = timestamp()
    if args:
        issue = args[0]
        path = issue_path(issue)
        if path.exists():
            record = read_record(issue)
        else:
            record = next((r for r in reversed(history) if r["issue"] == issue), None)
        if record is None:
            print("No timings recorded.")
            return
        rows = []
        for phase in record.get("phases", []):
            phase_end = phase.get("ended", now)
            elapsed = duration(seconds(phase["started"], phase_end))
            if "ended" not in phase:
                elapsed = "running " + elapsed
            busy = phase_busy(phase, now)
            busy_text, wait_text = "-", "-"
            if busy is not None:
                phase_time = seconds(phase["started"], phase_end)
                shown = min(busy, phase_time)
                busy_text = duration(shown)
                wait_text = duration(phase_time - shown)
            rows.append([phase["role"], phase["provider"], model(phase["row"]), phase["started"],
                         elapsed, busy_text, wait_text])
        print_table(["ROLE", "PROVIDER", "MODEL", "STARTED", "TIME", "BUSY", "WAIT"], rows)
        rounds, verdict = review_result(record)
        if record.get("abandoned"):
            verdict = "abandoned"
        busy_values = [value for value in (phase_busy(phase, now) for phase in record.get("phases", []))
                       if value is not None]
        busy = duration(sum(busy_values)) if busy_values else "-"
        print(f"Rounds: {rounds}  Verdict: {verdict}  Busy: {busy}  Total: {total_time(record, now)}")
        return
    records = history[:]
    for path in sorted((root / "state").glob("*.json")):
        try:
            record = json.loads(path.read_text())
            if not record.get("archived"):
                records.append(record)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Cannot read {path}: {exc}", file=sys.stderr)
    if not records:
        print("No timings recorded.")
        return
    rows, totals = [], {}
    for record in records:
        rounds, verdict = review_result(record)
        busy_values = [value for value in (phase_busy(phase, now) for phase in record.get("phases", []))
                       if value is not None]
        busy = duration(sum(busy_values)) if busy_values else "-"
        rows.append([record["issue"], record.get("size") or "-", rounds,
                     "abandoned" if record.get("abandoned") else verdict, total_time(record, now), busy])
        for phase in record.get("phases", []):
            if "ended" not in phase:
                continue
            key = (phase["provider"], model(phase["row"]), phase["role"])
            count, elapsed, seen, busy_total = totals.get(key, (0, 0, False, 0))
            busy = phase_busy(phase, now)
            totals[key] = (count + 1, elapsed + seconds(phase["started"], phase["ended"]),
                           seen or busy is not None, busy_total + (busy or 0))
    print_table(["ISSUE", "SIZE", "ROUNDS", "VERDICT", "TOTAL", "BUSY"], rows)
    print()
    print_table(["PROVIDER", "MODEL", "ROLE", "PHASES", "TIME", "BUSY"],
                [[*key, count, duration(elapsed), duration(busy_total) if seen else "-"]
                 for key, (count, elapsed, seen, busy_total) in sorted(totals.items())])


def status():
    folder = repo_root() / ".switchyard" / "state"
    records = []
    if folder.exists():
        for path in folder.glob("*.json"):
            try:
                records.append(json.loads(path.read_text()))
            except (OSError, json.JSONDecodeError) as exc:
                print(f"Cannot read {path}: {exc}", file=sys.stderr)
    records.sort(key=lambda row: key_order(row["issue"]))
    if not records:
        print("No issues in flight.")
        return

    herdr_records = [r for r in records if r.get("runner") == "herdr" and r.get("worker")]
    agents = {}
    herdr_error = False
    if herdr_records:
        try:
            result = subprocess.run(["herdr", "agent", "list"], check=True, capture_output=True, text=True)
            payload = json.loads(result.stdout)
            rows = payload.get("result", {}).get("agents", payload.get("agents", []))
            agents = {row.get("name"): row for row in rows}
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            print(f"Could not read Herdr agents: {exc}", file=sys.stderr)
            herdr_error = True

    headers = ["ISSUE", "BRANCH", "PHASE", "BACKEND", "WORKER", "PANE", "STATE", "PR"]
    table = []
    for record in records:
        issue, branch = record.get("issue", "?"), record.get("branch", "-")
        worker = record.get("worker") or record.get("session") or "-"
        phase = record.get("role") or "setup"
        if record.get("waiting"):
            phase += ", waiting"
        live_state = "-"
        if not record.get("path") or not Path(record["path"]).is_dir():
            live_state = "no worktree"
        elif record.get("worker"):
            if herdr_error:
                live_state = "?"
            else:
                live_state = agents.get(record["worker"], {}).get("agent_status", "ended")
        pr = "-"
        try:
            result = subprocess.run(
                ["gh", "pr", "list", "--head", branch, "--state", "all", "--json", "number,state", "--limit", "1"],
                check=True, capture_output=True, text=True,
            )
            prs = json.loads(result.stdout)
            if prs:
                pr = f"#{prs[0]['number']} {prs[0]['state'].lower()}"
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as exc:
            print(f"Could not read PR for issue {issue}: {exc}", file=sys.stderr)
            pr = "?"
        table.append([issue, branch, phase, record.get("backend") or "-", worker,
                      record.get("pane") or "-", live_state, pr])
    widths = [max(len(headers[i]), *(len(row[i]) for row in table)) for i in range(len(headers))]
    print("  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    for row in table:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))


if __name__ == "__main__":
    try:
        command(sys.argv[1:])
    except subprocess.CalledProcessError as exc:
        fail("?", f"command failed: {exc}")
    except OSError as exc:
        fail("?", f"operating system error: {exc}")
