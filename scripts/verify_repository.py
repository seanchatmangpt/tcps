#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "AGENTS.md",
    "RELEASE_CONTROL.md",
    "README.md",
    "SECURITY.md",
    "LEGAL.md",
    "pyproject.toml",
    "ggen.toml",
    "ontology/tcps.ttl",
    "authority/reconstitution.json",
    "authority/release.json",
    "authority/default-policy.json",
    "product/PRD.md",
    "architecture/ARD.md",
    "governance/claims-register.md",
    "governance/security.md",
    "governance/privacy.md",
    "governance/resilience.md",
    "governance/change-management.md",
    "operations/RUNBOOK.md",
    "operations/SUPPORT.md",
    "procurement/SUPPLY_CHAIN.md",
    "schemas/work.schema.json",
    "schemas/authority.schema.json",
    "schemas/plan.schema.json",
    "schemas/receipt.schema.json",
    "src/tcps/cli.py",
    "src/tcps/engine.py",
    "src/tcps/receipt.py",
    "src/tcps/replay.py",
    "src/tcps/generated_contract.py",
    ".github/workflows/ci.yml",
]


def check(condition: bool, code: str, detail: object, failures: list[dict[str, object]]) -> None:
    if not condition:
        failures.append({"code": code, "detail": detail})


def main() -> int:
    failures: list[dict[str, object]] = []
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    check(not missing, "REQUIRED_SURFACE_MISSING", missing, failures)

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    check(project["name"] == "tcps", "PACKAGE_IDENTITY_MISMATCH", project["name"], failures)
    check(project["version"] == "1979.1.1", "VERSION_MISMATCH", project["version"], failures)
    check(project.get("dependencies") == [], "RUNTIME_DEPENDENCIES_NOT_EMPTY", project.get("dependencies"), failures)

    generated = (ROOT / "src/tcps/generated_contract.py").read_text(encoding="utf-8")
    check('VERSION = "1979.1.1"' in generated, "GENERATED_VERSION_MISMATCH", None, failures)
    for stage in ("OBSERVE", "ADMIT", "MODEL", "SELECT", "AUTHORIZE", "ACTUATE", "VERIFY", "RECEIPT", "REOBSERVE"):
        check(f'"{stage}"' in generated, "GENERATED_STAGE_MISSING", stage, failures)

    reconstitution = json.loads((ROOT / "authority/reconstitution.json").read_text(encoding="utf-8"))
    check(reconstitution["strategy"] == "fresh-tree-reconstitution", "RECONSTITUTION_STRATEGY_MISMATCH", reconstitution.get("strategy"), failures)
    check(reconstitution["target_version"] == "1979.1.1", "AUTHORITY_VERSION_MISMATCH", reconstitution.get("target_version"), failures)

    workflow_files = list((ROOT / ".github/workflows").glob("*.yml")) + list((ROOT / ".github/workflows").glob("*.yaml"))
    check(len(workflow_files) == 1, "WORKFLOW_COUNT_MISMATCH", [str(p.relative_to(ROOT)) for p in workflow_files], failures)

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_reconstitution.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    check(proc.returncode == 0, "IDENTITY_ZERO_FAILED", proc.stdout + proc.stderr, failures)

    report = {
        "schema": "tcps.repository-verifier.v1",
        "version": "1979.1.1",
        "required_surface_missing": len(missing),
        "failures": failures,
        "state": "ALIVE" if not failures else "BUILD_BROKEN",
    }
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
