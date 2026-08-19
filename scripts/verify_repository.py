#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "AGENTS.md", "RELEASE_CONTROL.md", "README.md", "SECURITY.md", "LEGAL.md",
    "pyproject.toml", "ggen.toml", "ontology/tcps.ttl",
    "authority/reconstitution.json", "authority/release.json", "authority/default-policy.json",
    "product/PRD.md", "architecture/ARD.md", "validation/VALIDATION_THEOREM.md",
    "governance/claims-register.md", "governance/security.md", "governance/privacy.md",
    "governance/resilience.md", "governance/change-management.md",
    "operations/RUNBOOK.md", "operations/SUPPORT.md", "procurement/SUPPLY_CHAIN.md",
    "schemas/work.schema.json", "schemas/authority.schema.json", "schemas/plan.schema.json",
    "schemas/pre-receipt.schema.json", "schemas/receipt.schema.json", "schemas/pack.schema.json",
    "schemas/kanban.schema.json",
    "src/tcps/cli.py", "src/tcps/engine.py", "src/tcps/ledger.py", "src/tcps/receipt.py",
    "src/tcps/replay.py", "src/tcps/plant.py", "src/tcps/packs.py", "src/tcps/dfcm.py",
    "src/tcps/generated_contract.py",
    "tests/test_ledger.py", "tests/test_plant.py", "tests/test_packs.py", "tests/test_dfcm.py",
    ".github/workflows/ci.yml",
]


def check(condition: bool, code: str, detail: object, failures: list[dict[str, object]]) -> None:
    if not condition:
        failures.append({"code": code, "detail": detail})


def main() -> int:
    failures: list[dict[str, object]] = []
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    check(not missing, "REQUIRED_SURFACE_MISSING", missing, failures)

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    check(project["name"] == "tcps", "PACKAGE_IDENTITY_MISMATCH", project["name"], failures)
    check(project["version"] == "1979.1.1", "VERSION_MISMATCH", project["version"], failures)
    check(project.get("dependencies") == [], "RUNTIME_DEPENDENCIES_NOT_EMPTY", project.get("dependencies"), failures)

    generated = (ROOT / "src/tcps/generated_contract.py").read_text(encoding="utf-8")
    check('VERSION = "1979.1.1"' in generated, "GENERATED_VERSION_MISMATCH", None, failures)
    for stage in ("OBSERVE", "ADMIT", "MODEL", "SELECT", "AUTHORIZE", "PREPARE", "ACTUATE", "VERIFY", "RECEIPT", "REOBSERVE"):
        check(f'"{stage}"' in generated, "GENERATED_STAGE_MISSING", stage, failures)
    for token in ("DFCM = {", '"planner_authority": "SELECT"', '"actuation": "NONE"', '"irreversible_selections": int("0")'):
        check(token in generated, "GENERATED_DFCM_LAW_MISSING", token, failures)

    ontology = (ROOT / "ontology/tcps.ttl").read_text(encoding="utf-8")
    for stage in ("OBSERVE", "ADMIT", "MODEL", "SELECT", "AUTHORIZE", "PREPARE", "ACTUATE", "VERIFY", "RECEIPT", "REOBSERVE"):
        check(f'"{stage}"' in ontology, "ONTOLOGY_STAGE_MISSING", stage, failures)
    for token in ("<urn:tcps:dfcm>", "Combinatorial maximalism before irreversible selection", "Pareto frontier", "Heijunka schedule", "Little's Law cycle time"):
        check(token in ontology, "ONTOLOGY_DFCM_LAW_MISSING", token, failures)

    engine = (ROOT / "src/tcps/engine.py").read_text(encoding="utf-8")
    ledger = (ROOT / "src/tcps/ledger.py").read_text(encoding="utf-8")
    cli = (ROOT / "src/tcps/cli.py").read_text(encoding="utf-8")
    receipt = (ROOT / "src/tcps/receipt.py").read_text(encoding="utf-8")
    packs = (ROOT / "src/tcps/packs.py").read_text(encoding="utf-8")
    dfcm = (ROOT / "src/tcps/dfcm.py").read_text(encoding="utf-8")
    check("make_pre_receipt" in engine, "PRE_RECEIPT_BOUNDARY_MISSING", None, failures)
    check("ledger.prepare(pre)" in engine or "ledger.prepare(pre_receipt)" in engine, "PRE_RECEIPT_NOT_DURABLE_BEFORE_DO", None, failures)
    check("os.fsync" in ledger, "LEDGER_FSYNC_MISSING", None, failures)
    check("RECOVERY_REQUIRED" in ledger, "RECOVERY_GATE_MISSING", None, failures)
    check("pre_receipt" in receipt, "FINAL_RECEIPT_PRE_BINDING_MISSING", None, failures)
    for command in ("make", "standard", "kanban", "wip", "andon", "metrics", "standing", "kaizen", "dfcm", "pack", "recover"):
        check(f'"{command}"' in cli, "PLANT_COMMAND_MISSING", command, failures)
    for role in ("EVE", "WIZARD", "TELCO", "ROBOT"):
        check(role in packs, "STRATIFIED_PROMPT_MISSING", role, failures)
    check("install_pack" in packs and "actuate(" in packs, "PACK_DO_BOUNDARY_MISSING", None, failures)
    for token in ("pareto_frontier", "heijunka_schedule", "verify_plan", '"planner_authority"', '"actuation"'):
        check(token in dfcm, "DFCM_RUNTIME_MISSING", token, failures)

    release = json.loads((ROOT / "authority/release.json").read_text(encoding="utf-8"))
    for crown in ("fault_injection_failures", "plant_surface_failures", "pack_install_replay_failures", "pending_recovery", "ggen_projection_differences", "exact_head_ci_failures"):
        check(release.get("required", {}).get(crown) == 0, "RELEASE_CROWN_MISSING", crown, failures)

    reconstitution = json.loads((ROOT / "authority/reconstitution.json").read_text(encoding="utf-8"))
    check(reconstitution["strategy"] == "fresh-tree-reconstitution", "RECONSTITUTION_STRATEGY_MISMATCH", reconstitution.get("strategy"), failures)
    check(reconstitution["target_version"] == "1979.1.1", "AUTHORITY_VERSION_MISMATCH", reconstitution.get("target_version"), failures)

    workflow_files = list((ROOT / ".github/workflows").glob("*.yml")) + list((ROOT / ".github/workflows").glob("*.yaml"))
    check(len(workflow_files) == 1, "WORKFLOW_COUNT_MISMATCH", [str(p.relative_to(ROOT)) for p in workflow_files], failures)

    proc = subprocess.run([sys.executable, str(ROOT / "scripts/verify_reconstitution.py")], cwd=ROOT, text=True, capture_output=True, check=False)
    check(proc.returncode == 0, "IDENTITY_ZERO_FAILED", proc.stdout + proc.stderr, failures)

    report = {
        "schema": "tcps.repository-verifier.v1", "version": "1979.1.1",
        "required_surface_missing": len(missing), "failures": failures,
        "state": "ALIVE" if not failures else "BUILD_BROKEN",
    }
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
