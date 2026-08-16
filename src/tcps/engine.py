from __future__ import annotations

from pathlib import Path
from typing import Any

from .authority import authority_digest, root_is_allowed
from .canonical import digest_object
from .ledger import Ledger
from .model import Refusal, TCPSRefused
from .receipt import make_pre_receipt, make_receipt, verify_chain

ALLOWED_OPERATION_FIELDS = {
    "write_text": {"op", "path", "content"},
    "mkdir": {"op", "path"},
    "remove": {"op", "path"},
}


def _safe_target(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise TCPSRefused(
            Refusal(
                "TARGET_PATH_INVALID",
                relative,
                "targets are non-empty paths relative to the admitted root",
                relative,
                "relative path",
                "use a repository-relative target",
            )
        )
    root = root.resolve()
    target = (root / relative).resolve()
    if root != target and root not in target.parents:
        raise TCPSRefused(
            Refusal(
                "TARGET_ESCAPES_ROOT",
                relative,
                "actuation remains inside the admitted root",
                str(target),
                str(root),
                "choose a target inside the admitted root",
            )
        )
    return target


def _snapshot(target: Path) -> dict[str, Any]:
    if not target.exists():
        return {"kind": "absent"}
    if target.is_file():
        return {
            "kind": "file",
            "digest": digest_object({"bytes_hex": target.read_bytes().hex()}),
        }
    if target.is_dir():
        return {
            "kind": "directory",
            "entries": sorted(path.name for path in target.iterdir()),
        }
    return {"kind": "other"}


def _expected_snapshot(action: dict[str, Any], before: dict[str, Any]) -> dict[str, Any]:
    operation = action["op"]
    if operation == "write_text":
        return {
            "kind": "file",
            "digest": digest_object({"bytes_hex": action["content"].encode("utf-8").hex()}),
        }
    if operation == "mkdir":
        if before.get("kind") == "directory":
            return before
        return {"kind": "directory", "entries": []}
    if operation == "remove":
        return {"kind": "absent"}
    raise AssertionError(f"unsupported admitted operation: {operation}")


def observe(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema") != "tcps.work.v1":
        raise TCPSRefused(
            Refusal(
                "WORK_SCHEMA_UNSUPPORTED",
                str(manifest.get("schema")),
                "work enters through an admitted schema",
                manifest.get("schema"),
                "tcps.work.v1",
                "migrate the work order to tcps.work.v1",
            )
        )
    required = ["subject", "purpose", "observations", "actions"]
    missing = [key for key in required if key not in manifest]
    if missing:
        raise TCPSRefused(
            Refusal(
                "OBSERVATION_INCOMPLETE",
                str(manifest.get("subject", "unknown")),
                "observable work includes subject, purpose, observations, and actions",
                missing,
                required,
                "supply the missing observation fields",
            )
        )
    return {
        "schema": "tcps.observation.v1",
        "subject": manifest["subject"],
        "purpose": manifest["purpose"],
        "facts": manifest["observations"],
        "requested_actions": manifest["actions"],
        "source_digest": digest_object(manifest),
        "stage": "EVE",
        "language": "en",
    }


def construct(observation: dict[str, Any]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for index, action in enumerate(observation["requested_actions"], start=1):
        operation = action.get("op")
        if operation not in ALLOWED_OPERATION_FIELDS:
            raise TCPSRefused(
                Refusal(
                    "OPERATION_UNSUPPORTED",
                    f"candidate-{index}",
                    "only bounded built-in operations may be constructed",
                    operation,
                    sorted(ALLOWED_OPERATION_FIELDS),
                    "replace the operation with an admitted built-in or extend authority and verifier first",
                )
            )
        unknown = sorted(set(action) - ALLOWED_OPERATION_FIELDS[operation])
        missing = sorted(ALLOWED_OPERATION_FIELDS[operation] - set(action))
        if unknown or missing:
            raise TCPSRefused(
                Refusal(
                    "ACTION_SHAPE_INVALID",
                    f"candidate-{index}",
                    "operation fields match the bounded action schema exactly",
                    {"unknown": unknown, "missing": missing},
                    sorted(ALLOWED_OPERATION_FIELDS[operation]),
                    "correct the action shape before selection",
                )
            )
        candidates.append(
            {
                "candidate_id": f"C{index:04d}",
                "operation": action,
                "reversible": operation != "remove",
                "intent_digest": digest_object(action),
            }
        )
    return {
        "schema": "tcps.candidate-graph.v1",
        "subject": observation["subject"],
        "observation_digest": digest_object(observation),
        "candidates": candidates,
        "stage": "WIZARD",
        "language": "zh-CN",
    }


def select_and_authorize(
    graph: dict[str, Any], policy: dict[str, Any], root: Path
) -> dict[str, Any]:
    candidates = graph["candidates"]
    if len(candidates) > int(policy["max_actions"]):
        raise TCPSRefused(
            Refusal(
                "WIP_LIMIT_EXCEEDED",
                graph["subject"],
                "selected consequential WIP remains within policy",
                len(candidates),
                policy["max_actions"],
                "split the work order or increase the admitted limit through policy change",
            )
        )
    if not root_is_allowed(root, policy):
        raise TCPSRefused(
            Refusal(
                "ROOT_NOT_AUTHORIZED",
                str(root.resolve()),
                "actuation root is admitted by policy",
                str(root.resolve()),
                policy["allowed_roots"],
                "use an admitted root or change policy through its own authority process",
            )
        )

    selected: list[dict[str, Any]] = []
    allowed_operations = set(policy["allowed_operations"])
    for candidate in candidates:
        operation = candidate["operation"]["op"]
        if operation not in allowed_operations:
            raise TCPSRefused(
                Refusal(
                    "OPERATION_NOT_AUTHORIZED",
                    candidate["candidate_id"],
                    "selected operation is admitted by policy",
                    operation,
                    sorted(allowed_operations),
                    "change the work order or policy; do not bypass authorization",
                )
            )
        if not candidate["reversible"] and not policy["allow_irreversible"]:
            raise TCPSRefused(
                Refusal(
                    "IRREVERSIBLE_OPERATION_NOT_AUTHORIZED",
                    candidate["candidate_id"],
                    "irreversible selection requires explicit policy authority",
                    operation,
                    "allow_irreversible=true",
                    "retain the candidate without actuation or explicitly admit irreversible authority",
                )
            )
        selected.append(candidate)

    plan_body = {
        "schema": "tcps.plan.v1",
        "subject": graph["subject"],
        "graph_digest": digest_object(graph),
        "authority_digest": authority_digest(policy),
        "root": str(root.resolve()),
        "selected": selected,
        "stage": "TELCO",
        "language": "ja-JP",
    }
    return {**plan_body, "plan_digest": digest_object(plan_body)}


def _verify_plan(plan: dict[str, Any], policy: dict[str, Any], root: Path) -> None:
    body = {key: value for key, value in plan.items() if key != "plan_digest"}
    expected = digest_object(body)
    if plan.get("plan_digest") != expected:
        raise TCPSRefused(
            Refusal(
                "PLAN_DIGEST_MISMATCH",
                plan.get("subject", "unknown"),
                "execution consumes exactly the authorized plan",
                plan.get("plan_digest"),
                expected,
                "restore the authorized plan or re-run selection",
            )
        )
    if plan.get("authority_digest") != authority_digest(policy):
        raise TCPSRefused(
            Refusal(
                "AUTHORITY_DIGEST_MISMATCH",
                plan.get("subject", "unknown"),
                "execution uses the exact authority admitted during selection",
                plan.get("authority_digest"),
                authority_digest(policy),
                "re-run selection under the current policy",
            )
        )
    if plan.get("root") != str(root.resolve()):
        raise TCPSRefused(
            Refusal(
                "ROOT_IDENTITY_MISMATCH",
                plan.get("subject", "unknown"),
                "execution root equals the authorized root",
                str(root.resolve()),
                plan.get("root"),
                "execute at the authorized root or re-plan",
            )
        )


def _validate_preconditions(target: Path, action: dict[str, Any]) -> None:
    if action["op"] == "remove" and target.is_dir() and any(target.iterdir()):
        raise TCPSRefused(
            Refusal(
                "NONEMPTY_DIRECTORY_REMOVE_REFUSED",
                action["path"],
                "bounded remove does not recursively erase unknown state",
                "non-empty directory",
                "empty directory or file",
                "remove children through separately admitted intents",
            )
        )


def _apply(action: dict[str, Any], target: Path) -> None:
    operation = action["op"]
    if operation == "mkdir":
        target.mkdir(parents=True, exist_ok=True)
    elif operation == "write_text":
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(action["content"], encoding="utf-8")
    elif operation == "remove":
        if target.is_dir():
            target.rmdir()
        elif target.exists():
            target.unlink()
    else:
        raise AssertionError(f"unsupported admitted operation: {operation}")


def _consequence(
    action: dict[str, Any], before: dict[str, Any], after: dict[str, Any]
) -> dict[str, Any]:
    return {
        "op": action["op"],
        "path": action["path"],
        "before": before,
        "after": after,
        "changed": before != after,
    }


def actuate(
    plan: dict[str, Any],
    policy: dict[str, Any],
    root: Path,
    receipt_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Execute an admitted plan through a crash-recoverable two-phase receipt boundary."""
    root = Path(root).resolve()
    _verify_plan(plan, policy, root)
    receipt_path = Path(receipt_path) if receipt_path else root / ".tcps/receipts.ndjson"
    emitted: list[dict[str, Any]] = []

    with Ledger(receipt_path) as ledger:
        ledger.require_clean()
        existing = ledger.receipts()
        previous = verify_chain(existing)
        sequence = len(existing) + 1

        for candidate in plan["selected"]:
            action = candidate["operation"]
            target = _safe_target(root, action["path"])
            _validate_preconditions(target, action)
            before = _snapshot(target)
            expected = _expected_snapshot(action, before)

            pre_receipt = make_pre_receipt(
                sequence=sequence,
                previous=previous,
                subject=plan["subject"],
                authority=plan["authority_digest"],
                intent=candidate["intent_digest"],
                plan_digest=plan["plan_digest"],
                root=str(root),
                operation=action,
                before=before,
                expected=expected,
            )
            ledger.prepare(pre_receipt)

            _apply(action, target)
            after = _snapshot(target)
            verification = {"ok": after == expected, "kind": "exact-poststate"}
            if not verification["ok"]:
                raise TCPSRefused(
                    Refusal(
                        "POSTCONDITION_FAILED",
                        candidate["candidate_id"],
                        "every actuation satisfies an exact postcondition before final receipt",
                        after,
                        expected,
                        "stop the line and run recovery before further actuation",
                    )
                )

            receipt = make_receipt(
                sequence=sequence,
                previous=previous,
                subject=plan["subject"],
                authority=plan["authority_digest"],
                intent=candidate["intent_digest"],
                pre_receipt=pre_receipt["pre_receipt_id"],
                consequence=_consequence(action, before, after),
                verification=verification,
            ).as_dict()
            ledger.finalize(receipt)
            emitted.append(receipt)
            previous = receipt["receipt_id"]
            sequence += 1

    return emitted


def recover(receipt_path: Path, root: Path) -> dict[str, Any]:
    """Resolve an interrupted two-phase actuation from durable evidence and world state."""
    root = Path(root).resolve()
    receipt_path = Path(receipt_path)

    with Ledger(receipt_path) as ledger:
        pending = ledger.pending()
        if pending is None:
            head, count = ledger.head_and_count()
            return {
                "schema": "tcps.recovery.v1",
                "state": "ALIVE",
                "recovered": False,
                "receipt_count": count,
                "chain_head": head,
            }

        existing = ledger.receipts()
        head = verify_chain(existing)
        expected_sequence = len(existing) + 1

        if pending["sequence"] <= len(existing):
            closed = existing[pending["sequence"] - 1]
            if (
                closed.get("pre_receipt") == pending["pre_receipt_id"]
                and closed.get("previous") == pending["previous"]
            ):
                ledger.abort_pending()
                return {
                    "schema": "tcps.recovery.v1",
                    "state": "ALIVE",
                    "recovered": True,
                    "resolution": "FINAL_RECEIPT_ALREADY_DURABLE",
                    "receipt": closed,
                }
            return {
                "schema": "tcps.recovery.v1",
                "state": "BLOCKED",
                "code": "RECOVERY_CHAIN_MISMATCH",
                "pre_receipt": pending["pre_receipt_id"],
            }

        if pending["sequence"] != expected_sequence or pending["previous"] != head:
            return {
                "schema": "tcps.recovery.v1",
                "state": "BLOCKED",
                "code": "RECOVERY_CHAIN_MISMATCH",
                "pre_receipt": pending["pre_receipt_id"],
                "observed": {
                    "sequence": pending["sequence"],
                    "previous": pending["previous"],
                },
                "expected": {"sequence": expected_sequence, "previous": head},
            }

        if pending["root"] != str(root):
            return {
                "schema": "tcps.recovery.v1",
                "state": "BLOCKED",
                "code": "RECOVERY_ROOT_MISMATCH",
                "pre_receipt": pending["pre_receipt_id"],
            }

        target = _safe_target(root, pending["operation"]["path"])
        current = _snapshot(target)

        if current == pending["expected"]:
            consequence = _consequence(pending["operation"], pending["before"], current)
            verification = {
                "ok": True,
                "kind": "recovered-exact-poststate",
                "recovered": True,
            }
            receipt = make_receipt(
                sequence=pending["sequence"],
                previous=pending["previous"],
                subject=pending["subject"],
                authority=pending["authority"],
                intent=pending["intent"],
                pre_receipt=pending["pre_receipt_id"],
                consequence=consequence,
                verification=verification,
            ).as_dict()
            ledger.finalize(receipt)
            return {
                "schema": "tcps.recovery.v1",
                "state": "ALIVE",
                "recovered": True,
                "receipt": receipt,
            }

        if current == pending["before"]:
            pre_receipt_id = pending["pre_receipt_id"]
            ledger.abort_pending()
            return {
                "schema": "tcps.recovery.v1",
                "state": "PARTIAL_ALIVE",
                "recovered": False,
                "resolution": "ABORTED_PREPARED_NOT_ACTUATED",
                "pre_receipt": pre_receipt_id,
            }

        return {
            "schema": "tcps.recovery.v1",
            "state": "BLOCKED",
            "code": "RECOVERY_AMBIGUOUS",
            "pre_receipt": pending["pre_receipt_id"],
            "observed": current,
            "before": pending["before"],
            "expected": pending["expected"],
        }
