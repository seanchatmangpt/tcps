#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, env: dict[str, str] | None = None) -> dict[str, object]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, env=merged, check=False)
    return {"command": command, "exit": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}


def main() -> int:
    checks: list[dict[str, object]] = []
    checks.append(run([sys.executable, "scripts/verify_reconstitution.py"]))
    checks.append(run([sys.executable, "scripts/verify_repository.py"]))
    checks.append(run([sys.executable, "-m", "compileall", "-q", "src"]))
    checks.append(run([sys.executable, "-m", "pytest", "-q"], env={"PYTHONPATH": str(ROOT / "src")}))

    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        init = run([sys.executable, "-m", "tcps", "init", str(temp_root)], env={"PYTHONPATH": str(ROOT / "src")})
        checks.append(init)
        work = temp_root / "work.json"
        work.write_text(
            json.dumps(
                {
                    "schema": "tcps.work.v1",
                    "subject": "release-witness",
                    "purpose": "prove exact receipted production",
                    "observations": [{"kind": "release", "value": "witness"}],
                    "actions": [{"op": "write_text", "path": "witness.txt", "content": "heijunka\n"}],
                }
            ),
            encoding="utf-8",
        )
        checks.append(
            run(
                [
                    sys.executable,
                    "-m",
                    "tcps",
                    "run",
                    str(work),
                    "--authority",
                    str(temp_root / ".tcps/authority.json"),
                    "--root",
                    str(temp_root),
                    "--receipts",
                    str(temp_root / ".tcps/receipts.ndjson"),
                    "--plan-out",
                    str(temp_root / ".tcps/last-plan.json"),
                ],
                env={"PYTHONPATH": str(ROOT / "src")},
            )
        )
        checks.append(
            run(
                [
                    sys.executable,
                    "-m",
                    "tcps",
                    "replay",
                    "--receipts",
                    str(temp_root / ".tcps/receipts.ndjson"),
                    "--root",
                    str(temp_root),
                ],
                env={"PYTHONPATH": str(ROOT / "src")},
            )
        )

    checks.append(run([sys.executable, "scripts/build_offline_bundle.py", "--check-determinism"]))
    failures = [item for item in checks if item["exit"] != 0]
    report = {
        "schema": "tcps.verifier.report.v1",
        "subject": "tcps@1979.1.1",
        "checks": checks,
        "failure_count": len(failures),
        "generation": "BLOCKED:GGEN_EXECUTION_NOT_OBSERVED",
        "external_production": "UNKNOWN",
        "certification": "REFUSED:UNSUPPORTED_CLAIM",
        "state": "ALIVE" if not failures else "BUILD_BROKEN",
    }
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
