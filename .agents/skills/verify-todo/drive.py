#!/usr/bin/env python3
"""Run todo_cli in an isolated run directory and record evidence.

Records what happened; it asserts nothing. Expected values live in features/.

    drive.py launch                      create a run directory, print its path
    drive.py doctor <run>                read-only readiness checks -> <run>/doctor.json
    drive.py step <run> <name> -- ARGV   run ARGV, record -> <run>/steps/NN-<name>.json
    drive.py cleanup <run>               remove <run>/home and <run>/data; keep evidence
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RUNS = REPO / ".evidence" / "verify-todo"
COMMANDS = ("add", "list", "complete", "edit", "delete")


def fail(message: str) -> int:
    print(f"drive.py: {message}", file=sys.stderr)
    return 1


def run_dir(arg: str) -> Path:
    run = Path(arg).resolve()
    if run.parent != RUNS.resolve() or not run.is_dir():
        raise SystemExit(fail(f"not a run directory under {RUNS}: {arg}"))
    return run


def data_file(run: Path) -> Path:
    # Launch creates data/ but not data/store/, so the product's own directory creation is observable.
    return run / "data" / "store" / "todos.json"


def env_for(run: Path) -> dict:
    return {**os.environ, "HOME": str(run / "home"), "TODO_CLI_FILE": str(data_file(run))}


def data_state(run: Path) -> dict:
    path = data_file(run)
    if not path.is_file():
        return {"dir_exists": path.parent.is_dir(), "exists": False}
    raw = path.read_bytes()
    return {"dir_exists": True, "exists": True, "sha256": hashlib.sha256(raw).hexdigest(), "bytes_b64": base64.b64encode(raw).decode(), "text": raw.decode("utf-8", "replace")}


def git_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()


def launch() -> int:
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run = RUNS / f"{stamp}-{os.getpid()}"
    for sub in ("home", "data", "steps"):
        (run / sub).mkdir(parents=True)
    print(run)
    return 0


def doctor(run: Path) -> int:
    env = env_for(run)

    def cmd(*argv):
        proc = subprocess.run(argv, cwd=REPO, env=env, capture_output=True, text=True)
        return {"argv": list(argv), "exit": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}

    checks = {
        "python": cmd("python3", "--version"),
        "help": cmd("python3", "-m", "todo_cli", "--help"),
        "data_path": cmd("python3", "-c", "from todo_cli import store; print(store.data_path())"),
        "git_head": cmd("git", "rev-parse", "HEAD"),
        "git_status": cmd("git", "status", "--porcelain"),
    }
    listed = re.search(r"\{([a-z,]+)\}", checks["help"]["stdout"])
    resolved = checks["data_path"]["stdout"].strip()
    problems = []
    if checks["python"]["exit"] != 0 or not (checks["python"]["stdout"] + checks["python"]["stderr"]).startswith("Python 3."):
        problems.append("python3 is not Python 3")
    if checks["help"]["exit"] != 0 or not listed or set(listed.group(1).split(",")) != set(COMMANDS):
        problems.append(f"--help does not list exactly {COMMANDS}")
    if Path(resolved) != data_file(run):
        problems.append(f"data path {resolved!r} is not inside this run")
    if checks["git_head"]["exit"] != 0:
        problems.append("not a git checkout")
    report = {"run": str(run), "repo": str(REPO), "checks": checks, "problems": problems, "ok": not problems}
    (run / "doctor.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"doctor: {'ok' if not problems else 'FAILED'} head={checks['git_head']['stdout'].strip()} data={resolved}")
    for p in problems:
        print(f"  x {p}")
    return 0 if not problems else 1


def step(run: Path, name: str, argv: list[str]) -> int:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        return fail("step name must be lowercase letters, digits and hyphens")
    if not argv:
        return fail("missing command after --")
    doctor_report = run / "doctor.json"
    if not doctor_report.is_file() or not json.loads(doctor_report.read_text())["ok"]:
        return fail("run doctor first; it must pass")
    if json.loads(doctor_report.read_text())["checks"]["git_head"]["stdout"].strip() != git_head():
        return fail("HEAD has changed since Doctor ran; launch a new run")
    if not (run / "home").is_dir():
        return fail("this run has been cleaned up; launch a new run")
    steps = run / "steps"
    number = len(list(steps.glob("*.json"))) + 1
    before = data_state(run)
    proc = subprocess.run(argv, cwd=REPO, env=env_for(run), capture_output=True, text=True)
    after = data_state(run)
    record = {"step": number, "name": name, "argv": argv, "exit": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr,
              "data_before": before, "data_after": after, "data_changed": before != after}
    out = steps / f"{number:02d}-{name}.json"
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(f"{out.name}: exit={proc.returncode} data_changed={record['data_changed']}")
    print(f"  stdout: {proc.stdout!r}")
    print(f"  stderr: {proc.stderr!r}")
    return 0


def cleanup(run: Path) -> int:
    for sub in ("home", "data"):
        shutil.rmtree(run / sub, ignore_errors=True)
    left = [sub for sub in ("home", "data") if (run / sub).exists()]
    if left:
        return fail(f"cleanup could not remove {left} in {run}")
    kept = sorted(p.relative_to(run).as_posix() for p in run.rglob("*") if p.is_file())
    print(f"cleanup: removed home/ and data/; kept {len(kept)} evidence files in {run}")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        return fail(__doc__.strip())
    command, rest = argv[0], argv[1:]
    if command == "launch" and not rest:
        return launch()
    if command in ("doctor", "cleanup") and len(rest) == 1:
        return (doctor if command == "doctor" else cleanup)(run_dir(rest[0]))
    if command == "step" and len(rest) >= 3 and rest[2] == "--":
        return step(run_dir(rest[0]), rest[1], rest[3:])
    return fail(__doc__.strip())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
