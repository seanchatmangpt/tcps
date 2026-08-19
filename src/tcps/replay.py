from __future__ import annotations

from pathlib import Path, PurePath
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


def _apply_parent_membership(
    logical: dict[str, dict[str, Any]],
    latest: dict[str, tuple[dict[str, Any], dict[str, Any]]],
    receipt: dict[str, Any],
) -> None:
    consequence = receipt["consequence"]
    relative = PurePath(consequence["path"])
    parent = str(relative.parent)
    if parent == "." or parent not in logical:
        return
    state = logical[parent]
    if state.get("kind") != "directory" or not isinstance(state.get("entries"), list):
        return
    entries = set(state["entries"])
    before_absent = consequence["before"].get("kind") == "absent"
    after_absent = consequence["after"].get("kind") == "absent"
    if before_absent and not after_absent:
        entries.add(relative.name)
    elif not before_absent and after_absent:
        entries.discard(relative.name)
    updated = {"kind": "directory", "entries": sorted(entries)}
    logical[parent] = updated
    latest[parent] = (receipt, updated)


def replay(path: Path, root: Path) -> dict[str, Any]:
    path = Path(path)
    root = Path(root).resolve()
    receipts = load_receipts(path)
    head = verify_chain(receipts)
    drift: list[dict[str, Any]] = []

    # Historical post-states may be lawfully superseded. Build the final
    # receipted world, including directory membership caused by child acts,
    # while checking direct transition continuity along the way.
    logical: dict[str, dict[str, Any]] = {}
    latest: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for receipt in receipts:
        consequence = receipt["consequence"]
        relative = consequence["path"]
        if relative in logical and consequence["before"] != logical[relative]:
            drift.append(
                {
                    "receipt": receipt["receipt_id"],
                    "reason": "receipt-transition-mismatch",
                    "observed": consequence["before"],
                    "expected": logical[relative],
                }
            )
        logical[relative] = consequence["after"]
        latest[relative] = (receipt, consequence["after"])
        _apply_parent_membership(logical, latest, receipt)

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
