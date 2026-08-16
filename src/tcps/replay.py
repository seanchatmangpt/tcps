from __future__ import annotations

from pathlib import Path
from typing import Any

from .engine import _safe_target, _snapshot
from .ledger import load_pending, load_receipts
from .receipt import verify_chain


def _drift_reason(operation: str, observed: dict[str, Any]) -> str:
    if operation == "write_text":
        return "target-missing" if observed.get("kind") == "absent" else "content-drift"
    if operation == "mkdir":
        return "directory-missing" if observed.get("kind") == "absent" else "directory-drift"
    if operation == "remove":
        return "removed-target-present"
    return "poststate-drift"


def replay(path: Path, root: Path) -> dict[str, Any]:
    path = Path(path)
    root = Path(root).resolve()
    receipts = load_receipts(path)
    head = verify_chain(receipts)
    drift: list[dict[str, Any]] = []

    # Earlier post-states may be lawfully superseded by later receipts on the
    # same target. Prove ledger transition continuity, then compare the world
    # against only the latest receipted state for each target.
    logical_state: dict[str, dict[str, Any]] = {}
    latest: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for receipt in receipts:
        consequence = receipt["consequence"]
        relative = consequence["path"]
        if relative in logical_state and consequence["before"] != logical_state[relative]:
            drift.append(
                {
                    "receipt": receipt["receipt_id"],
                    "reason": "receipt-transition-mismatch",
                    "observed": consequence["before"],
                    "expected": logical_state[relative],
                }
            )
        logical_state[relative] = consequence["after"]
        latest[relative] = (receipt, consequence["after"])

    for relative, (receipt, expected) in latest.items():
        target = _safe_target(root, relative)
        observed = _snapshot(target)
        if observed != expected:
            drift.append(
                {
                    "receipt": receipt["receipt_id"],
                    "reason": _drift_reason(receipt["consequence"]["op"], observed),
                    "observed": observed,
                    "expected": expected,
                }
            )

    pending = load_pending(path)
    state = "BUILD_BROKEN" if drift else ("PARTIAL_ALIVE" if pending else "ALIVE")
    return {
        "schema": "tcps.replay.v1",
        "receipt_count": len(receipts),
        "chain_head": head,
        "drift": drift,
        "pending_pre_receipt": pending["pre_receipt_id"] if pending else None,
        "recovery_required": bool(pending),
        "state": state,
    }
