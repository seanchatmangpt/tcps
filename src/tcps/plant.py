from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import digest_object
from .generated_contract import CYCLE, ROLES, SYSTEM_NAME, VERSION
from .ledger import load_pending, load_receipts
from .receipt import verify_chain
from .replay import replay


def standard_work() -> dict[str, Any]:
    """Return the immutable machine-readable production standard."""
    body = {
        "schema": "tcps.standard-work.v1",
        "system": SYSTEM_NAME,
        "version": VERSION,
        "cycle": list(CYCLE),
        "roles": ROLES,
        "laws": [
            "downstream-is-customer",
            "selection-is-not-execution",
            "no-unreceipted-actuation",
            "unknown-is-not-admitted",
            "generated-is-not-verified",
            "replay-determines-standing",
        ],
        "authority_planes": ["SELECT", "CONSTRUCT", "DO"],
    }
    return {**body, "standard_digest": digest_object(body), "state": "ALIVE"}


def kanban(subject: str, purpose: str, *, quantity: int = 1, due_tick: int | None = None) -> dict[str, Any]:
    if not isinstance(subject, str) or not subject:
        raise ValueError("subject must be a non-empty string")
    if not isinstance(purpose, str) or not purpose:
        raise ValueError("purpose must be a non-empty string")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
        raise ValueError("quantity must be a positive integer")
    if due_tick is not None and (isinstance(due_tick, bool) or not isinstance(due_tick, int) or due_tick < 0):
        raise ValueError("due_tick must be a non-negative integer or null")
    body = {
        "schema": "tcps.kanban.v1",
        "customer_station": "STANDING",
        "subject": subject,
        "purpose": purpose,
        "quantity": quantity,
        "due_tick": due_tick,
    }
    return {**body, "kanban_digest": digest_object(body), "state": "PARTIAL_ALIVE"}


def wip(receipt_path: Path) -> dict[str, Any]:
    receipts = load_receipts(Path(receipt_path))
    verify_chain(receipts)
    pending = load_pending(Path(receipt_path))
    return {
        "schema": "tcps.wip.v1",
        "completed": len(receipts),
        "actuation_wip": 1 if pending else 0,
        "pending_pre_receipt": pending["pre_receipt_id"] if pending else None,
        "state": "PARTIAL_ALIVE" if pending else "ALIVE",
    }


def andon(receipt_path: Path, root: Path) -> dict[str, Any]:
    observed = replay(Path(receipt_path), Path(root))
    state = observed["state"]
    if state == "ALIVE":
        signal = "ALIVE"
    elif state == "PARTIAL_ALIVE":
        signal = "PARTIAL_ALIVE"
    else:
        signal = "BUILD_BROKEN"
    return {
        "schema": "tcps.andon.v1",
        "signal": signal,
        "recovery_required": observed["recovery_required"],
        "drift_count": len(observed["drift"]),
        "receipt_count": observed["receipt_count"],
        "state": signal,
    }


def metrics(receipt_path: Path, root: Path) -> dict[str, Any]:
    receipts = load_receipts(Path(receipt_path))
    head = verify_chain(receipts)
    observed = replay(Path(receipt_path), Path(root))
    verified = sum(1 for item in receipts if item.get("verification", {}).get("ok") is True)
    subjects = sorted({str(item.get("subject")) for item in receipts})
    count = len(receipts)
    return {
        "schema": "tcps.metrics.v1",
        "receipt_count": count,
        "subject_count": len(subjects),
        "subjects": subjects,
        "first_pass": (verified / count) if count else 1.0,
        "replay_ok": observed["state"] == "ALIVE",
        "actuation_wip": 1 if observed["recovery_required"] else 0,
        "escalation": len(observed["drift"]) + (1 if observed["recovery_required"] else 0),
        "sequence_ticks": count,
        "lead_ticks": None,
        "lead_ticks_status": "UNOBSERVED",
        "chain_head": head,
        "state": observed["state"],
    }


def kaizen(reason: str, proposal: str) -> dict[str, Any]:
    if not reason.strip() or not proposal.strip():
        raise ValueError("reason and proposal must be non-empty")
    body = {
        "schema": "tcps.kaizen-proposal.v1",
        "reason": reason.strip(),
        "proposal": proposal.strip(),
        "authority": "NONE",
        "actuation": "NONE",
    }
    return {**body, "proposal_digest": digest_object(body), "state": "PARTIAL_ALIVE"}


def standing(receipt_path: Path, root: Path) -> dict[str, Any]:
    observed = replay(Path(receipt_path), Path(root))
    return {
        "schema": "tcps.standing.v1",
        "standing": observed["state"],
        "chain_head": observed["chain_head"],
        "receipt_count": observed["receipt_count"],
        "recovery_required": observed["recovery_required"],
        "drift": observed["drift"],
        "state": observed["state"],
    }
