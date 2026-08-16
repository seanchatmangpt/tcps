#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYENV = {"PYTHONPATH": str(ROOT / "src")}


def run(command: list[str], *, env: dict[str, str] | None = None) -> dict[str, object]:
    merged = os.environ.copy()
    merged.update(env or {})
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, env=merged, check=False)
    return {"command": command, "exit": proc.returncode, "stdout": proc.stdout[-6000:], "stderr": proc.stderr[-6000:]}


def tcps(*args: str) -> list[str]:
    return [sys.executable, "-m", "tcps", *args]


def main() -> int:
    checks: list[dict[str, object]] = [
        run([sys.executable, "scripts/verify_reconstitution.py"]),
        run([sys.executable, "scripts/verify_repository.py"]),
        run([sys.executable, "-m", "compileall", "-q", "src"]),
        run([sys.executable, "-m", "pytest", "-q"], env=PYENV),
    ]

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        authority = root / ".tcps/authority.json"
        receipts = root / ".tcps/receipts.ndjson"
        plan = root / ".tcps/last-plan.json"

        checks.append(run(tcps("init", str(root)), env=PYENV))
        checks.append(run(tcps("standard"), env=PYENV))
        checks.append(run(tcps("kanban", "release-witness", "downstream release admission", "--quantity", "1", "--due-tick", "1"), env=PYENV))
        checks.append(run(tcps("pack", "validate", "builtin:core-1979"), env=PYENV))
        checks.append(run(tcps("pack", "install", "builtin:core-1979", "--root", str(root), "--authority", str(authority), "--receipts", str(receipts)), env=PYENV))
        checks.append(run(tcps("pack", "list", "--root", str(root)), env=PYENV))

        work = root / "work.json"
        work.write_text(json.dumps({
            "schema": "tcps.work.v1",
            "subject": "release-witness",
            "purpose": "prove exact receipted production",
            "observations": [{"kind": "release", "value": "witness"}],
            "actions": [{"op": "write_text", "path": "witness.txt", "content": "heijunka\n"}],
        }), encoding="utf-8")
        checks.append(run(tcps("make", str(work), "--authority", str(authority), "--root", str(root), "--receipts", str(receipts), "--plan-out", str(plan)), env=PYENV))
        checks.append(run(tcps("wip", "--receipts", str(receipts)), env=PYENV))
        checks.append(run(tcps("andon", "--receipts", str(receipts), "--root", str(root)), env=PYENV))
        checks.append(run(tcps("metrics", "--receipts", str(receipts), "--root", str(root)), env=PYENV))
        checks.append(run(tcps("standing", "--receipts", str(receipts), "--root", str(root)), env=PYENV))
        checks.append(run(tcps("kaizen", "release validation", "retain the failing witness and repair the earliest boundary"), env=PYENV))
        checks.append(run(tcps("replay", "--receipts", str(receipts), "--root", str(root)), env=PYENV))

    checks.append(run([sys.executable, "scripts/build_offline_bundle.py", "--check-determinism"]))
    failures = [item for item in checks if item["exit"] != 0]
    report = {
        "schema": "tcps.verifier.report.v1",
        "subject": "tcps@1979.1.1",
        "checks": checks,
        "failure_count": len(failures),
        "generation": "DELEGATED:EXACT_HEAD_GGEN_PROJECTION_JOB",
        "external_production": "UNKNOWN",
        "certification": "REFUSED:UNSUPPORTED_CLAIM",
        "state": "ALIVE" if not failures else "BUILD_BROKEN",
    }
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
