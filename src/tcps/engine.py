from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .authority import authority_digest, root_is_allowed
from .canonical import digest_object
from .model import Refusal, TCPSRefused
from .receipt import make_receipt

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
        op = action.get("op")
        if op not in ALLOWED_OPERATION_FIELDS:
            raise TCPSRefused(
                Refusal(
                    "OPERATION_UNSUPPORTED",
                    f"candidate-{index}",
                    "only bounded built-in operations may be constructed",
                    op,
                    sorted(ALLOWED_OPERATION_FIELDS),
                    "replace the operation with an admitted built-in or extend authority and verifier first",
                )
            )
        unknown = sorted(set(action) - ALLOWED_OPERATION_FIELDS[op])
        missing = sorted(ALLOWED_OPERATION_FIELDS[op] - set(action))
        if unknown or missing:
            raise TCPSRefused(
                Refusal(
                    "ACTION_SHAPE_INVALID",
                    f"candidate-{index}",
                    "operation fields match the bounded action schema exactly",
                    {"unknown": unknown, "missing": missing},
                    sorted(ALLOWED_OPERATION_FIELDS[op]),
                    "correct the action shape before selection",
                )
            )
        candidate = {
            "candidate_id": f"C{index:04d}",
            "operation": action,
            "reversible": op != "remove",
            "intent_digest": digest_object(action),
        }
        candidates.append(candidate)
    return {
        "schema": "tcps.candidate-graph.v1",
        "subject": observation["subject"],
        "observation_digest": digest_object(observation),
        "candidates": candidates,
        "stage": "WIZARD",
        "language": "zh-CN",
    }


def select_and_authorize(graph: dict[str, Any], policy: dict[str, Any], root: Path) -> dict[str, Any]:
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
    allowed_ops = set(policy["allowed_operations"])
    for candidate in candidates:
        op = candidate["operation"]["op"]
        if op not in allowed_ops:
            raise TCPSRefused(
                Refusal(
                    "OPERATION_NOT_AUTHORIZED",
                    candidate["candidate_id"],
                    "selected operation is admitted by policy",
                    op,
                    sorted(allowed_ops),
                    "change the work order or policy; do not bypass authorization",
                )
            )
        if not candidate["reversible"] and not policy["allow_irreversible"]:
            raise TCPSRefused(
                Refusal(
                    "IRREVERSIBLE_OPERATION_NOT_AUTHORIZED",
                    candidate["candidate_id"],
                    "irreversible selection requires explicit policy authority",
                    op,
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


def actuate(plan: dict[str, Any], policy: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    _verify_plan(plan, policy, root)
    receipts: list[dict[str, Any]] = []
    previous: str | None = None
    for sequence, candidate in enumerate(plan["selected"], start=1):
        action = candidate["operation"]
        target = _safe_target(root, action["path"])
        op = action["op"]
        before = None
        if target.exists() and target.is_file():
            before = target.read_bytes().hex()
        if op == "mkdir":
            target.mkdir(parents=True, exist_ok=True)
            consequence = {"op": op, "path": action["path"], "exists": target.is_dir()}
            verification = {"ok": target.is_dir(), "kind": "directory-exists"}
        elif op == "write_text":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(action["content"], encoding="utf-8")
            after = target.read_text(encoding="utf-8")
            consequence = {
                "op": op,
                "path": action["path"],
                "before_hex": before,
                "after_digest": digest_object({"text": after}),
            }
            verification = {"ok": after == action["content"], "kind": "exact-text-match"}
        elif op == "remove":
            if target.is_dir():
                if any(target.iterdir()):
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
                target.rmdir()
            elif target.exists():
                target.unlink()
            consequence = {"op": op, "path": action["path"], "exists": target.exists()}
            verification = {"ok": not target.exists(), "kind": "target-absent"}
        else:
            raise AssertionError("operation admitted earlier")
        if not verification["ok"]:
            raise TCPSRefused(
                Refusal(
                    "POSTCONDITION_FAILED",
                    candidate["candidate_id"],
                    "every actuation satisfies an exact postcondition before receipt",
                    consequence,
                    verification,
                    "stop the line and diagnose the earliest failed transition",
                )
            )
        receipt = make_receipt(
            sequence=sequence,
            previous=previous,
            subject=plan["subject"],
            authority=plan["authority_digest"],
            intent=candidate["intent_digest"],
            consequence=consequence,
            verification=verification,
        )
        item = receipt.as_dict()
        receipts.append(item)
        previous = receipt.receipt_id
    return receipts


def append_receipts(path: Path, receipts: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for receipt in receipts:
            handle.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
