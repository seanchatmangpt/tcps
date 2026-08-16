from __future__ import annotations

import os
from pathlib import Path, PurePath
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


def _refuse(code: str, object_id: str, law: str, observed: Any, expected: Any, repair: str) -> None:
    raise TCPSRefused(Refusal(code, object_id, law, observed, expected, repair))


def _safe_target(root: Path, relative: str) -> Path:
    pure = PurePath(relative)
    if not isinstance(relative, str) or not relative or pure.is_absolute() or any(part in {"..", "."} for part in pure.parts):
        _refuse(
            "TARGET_PATH_INVALID",
            str(relative),
            "targets are non-empty paths relative to the admitted root",
            relative,
            "relative path without dot traversal",
            "use a repository-relative target",
        )
    root = Path(root).resolve()
    lexical = root / pure
    cursor = root
    for part in pure.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink():
            _refuse(
                "SYMLINK_PATH_REFUSED",
                relative,
                "actuation paths do not traverse symlink components",
                str(cursor),
                "non-symlink path",
                "address the real path explicitly",
            )
    if lexical.is_symlink():
        _refuse(
            "SYMLINK_TARGET_REFUSED",
            relative,
            "actuation targets are not aliases",
            str(lexical),
            "non-symlink target",
            "address the real target explicitly",
        )
    target = lexical.resolve(strict=False)
    if root != target and root not in target.parents:
        _refuse(
            "TARGET_ESCAPES_ROOT",
            relative,
            "actuation remains inside the admitted root",
            str(target),
            str(root),
            "choose a target inside the admitted root",
        )
    return target


def _snapshot(target: Path) -> dict[str, Any]:
    if not target.exists():
        return {"kind": "absent"}
    if target.is_file():
        return {"kind": "file", "digest": digest_object({"bytes_hex": target.read_bytes().hex()})}
    if target.is_dir():
        return {"kind": "directory", "entries": sorted(item.name for item in target.iterdir())}
    return {"kind": "other"}


def _expected_snapshot(action: dict[str, Any], before: dict[str, Any]) -> dict[str, Any]:
    operation = action["op"]
    if operation == "write_text":
        return {"kind": "file", "digest": digest_object({"bytes_hex": action["content"].encode("utf-8").hex()})}
    if operation == "mkdir":
        return before if before.get("kind") == "directory" else {"kind": "directory", "entries": []}
    if operation == "remove":
        return {"kind": "absent"}
    raise AssertionError("operation admitted earlier")


def observe(manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        _refuse("WORK_SHAPE_INVALID", "work", "work order is an object", type(manifest).__name__, "object", "supply a JSON object")
    allowed = {"schema", "subject", "purpose", "observations", "actions"}
    unknown = sorted(set(manifest) - allowed)
    if unknown:
        _refuse("WORK_SHAPE_INVALID", str(manifest.get("subject", "unknown")), "work order has no undeclared fields", unknown, sorted(allowed), "remove undeclared fields")
    if manifest.get("schema") != "tcps.work.v1":
        _refuse("WORK_SCHEMA_UNSUPPORTED", str(manifest.get("schema")), "work enters through an admitted schema", manifest.get("schema"), "tcps.work.v1", "migrate the work order")
    required = ["subject", "purpose", "observations", "actions"]
    missing = [key for key in required if key not in manifest]
    if missing:
        _refuse("OBSERVATION_INCOMPLETE", str(manifest.get("subject", "unknown")), "work includes all required observations", missing, required, "supply the missing fields")
    if not isinstance(manifest["subject"], str) or not manifest["subject"]:
        _refuse("SUBJECT_INVALID", "work", "subject is a non-empty string", manifest["subject"], "non-empty string", "supply an exact subject")
    if not isinstance(manifest["purpose"], str) or not manifest["purpose"]:
        _refuse("PURPOSE_INVALID", manifest["subject"], "purpose is a non-empty string", manifest["purpose"], "non-empty string", "state the production purpose")
    if not isinstance(manifest["observations"], list) or not all(isinstance(item, dict) for item in manifest["observations"]):
        _refuse("OBSERVATIONS_INVALID", manifest["subject"], "observations are object records", manifest["observations"], "array<object>", "normalize observations")
    if not isinstance(manifest["actions"], list):
        _refuse("ACTIONS_INVALID", manifest["subject"], "actions are an ordered array", type(manifest["actions"]).__name__, "array", "supply an action array")
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
    if not isinstance(observation, dict) or observation.get("schema") != "tcps.observation.v1":
        _refuse("OBSERVATION_SCHEMA_UNSUPPORTED", "observation", "WIZARD consumes an admitted observation", observation.get("schema") if isinstance(observation, dict) else type(observation).__name__, "tcps.observation.v1", "run EVE admission first")
    requested = observation.get("requested_actions")
    if not isinstance(requested, list):
        _refuse("ACTIONS_INVALID", str(observation.get("subject", "unknown")), "requested actions are an ordered array", requested, "array", "re-run observation admission")
    candidates: list[dict[str, Any]] = []
    for index, action in enumerate(requested, start=1):
        if not isinstance(action, dict):
            _refuse("ACTION_SHAPE_INVALID", f"candidate-{index}", "each action is an object", type(action).__name__, "object", "normalize the action")
        operation = action.get("op")
        if operation not in ALLOWED_OPERATION_FIELDS:
            _refuse("OPERATION_UNSUPPORTED", f"candidate-{index}", "only bounded built-in operations may be constructed", operation, sorted(ALLOWED_OPERATION_FIELDS), "extend schema, authority, verifier, and receipt semantics before adding an operation")
        unknown = sorted(set(action) - ALLOWED_OPERATION_FIELDS[operation])
        missing = sorted(ALLOWED_OPERATION_FIELDS[operation] - set(action))
        if unknown or missing:
            _refuse("ACTION_SHAPE_INVALID", f"candidate-{index}", "operation fields match the bounded action schema exactly", {"unknown": unknown, "missing": missing}, sorted(ALLOWED_OPERATION_FIELDS[operation]), "correct the action shape")
        if not isinstance(action["path"], str) or not action["path"]:
            _refuse("ACTION_SHAPE_INVALID", f"candidate-{index}", "action path is a non-empty string", action["path"], "non-empty string", "supply an exact relative path")
        if operation == "write_text" and not isinstance(action["content"], str):
            _refuse("ACTION_SHAPE_INVALID", f"candidate-{index}", "write_text content is text", type(action["content"]).__name__, "string", "supply UTF-8 text")
        candidates.append({
            "candidate_id": f"C{index:04d}",
            "operation": action,
            "reversible": operation != "remove",
            "intent_digest": digest_object(action),
        })
    return {
        "schema": "tcps.candidate-graph.v1",
        "subject": observation["subject"],
        "observation_digest": digest_object(observation),
        "candidates": candidates,
        "stage": "WIZARD",
        "language": "zh-CN",
    }


def select_and_authorize(graph: dict[str, Any], policy: dict[str, Any], root: Path) -> dict[str, Any]:
    if not isinstance(graph, dict) or graph.get("schema") != "tcps.candidate-graph.v1" or not isinstance(graph.get("candidates"), list):
        _refuse("GRAPH_SCHEMA_UNSUPPORTED", "graph", "TELCO consumes the admitted candidate graph", graph.get("schema") if isinstance(graph, dict) else type(graph).__name__, "tcps.candidate-graph.v1", "run WIZARD construction first")
    candidates = graph["candidates"]
    if len(candidates) > int(policy["max_actions"]):
        _refuse("WIP_LIMIT_EXCEEDED", graph["subject"], "selected consequential WIP remains within policy", len(candidates), policy["max_actions"], "split work or independently change policy")
    if not root_is_allowed(root, policy):
        _refuse("ROOT_NOT_AUTHORIZED", str(Path(root).resolve()), "actuation root is admitted by policy", str(Path(root).resolve()), policy["allowed_roots"], "use an admitted root")
    selected: list[dict[str, Any]] = []
    allowed_operations = set(policy["allowed_operations"])
    for candidate in candidates:
        if not isinstance(candidate, dict) or not isinstance(candidate.get("operation"), dict):
            _refuse("CANDIDATE_INVALID", graph["subject"], "candidate shape is admitted", candidate, "candidate object", "reconstruct the graph")
        operation = candidate["operation"].get("op")
        if operation not in allowed_operations:
            _refuse("OPERATION_NOT_AUTHORIZED", str(candidate.get("candidate_id")), "selected operation is admitted by policy", operation, sorted(allowed_operations), "change work or authority; do not bypass authorization")
        if not candidate.get("reversible") and not policy["allow_irreversible"]:
            _refuse("IRREVERSIBLE_OPERATION_NOT_AUTHORIZED", str(candidate.get("candidate_id")), "irreversible selection requires explicit authority", operation, "allow_irreversible=true", "retain without DO or independently admit irreversible authority")
        selected.append(candidate)
    body = {
        "schema": "tcps.plan.v1",
        "subject": graph["subject"],
        "graph_digest": digest_object(graph),
        "authority_digest": authority_digest(policy),
        "root": str(Path(root).resolve()),
        "selected": selected,
        "stage": "TELCO",
        "language": "ja-JP",
    }
    return {**body, "plan_digest": digest_object(body)}


def _verify_plan(plan: dict[str, Any], policy: dict[str, Any], root: Path) -> None:
    if not isinstance(plan, dict) or plan.get("schema") != "tcps.plan.v1" or not isinstance(plan.get("selected"), list):
        _refuse("PLAN_SCHEMA_UNSUPPORTED", "plan", "ROBOT consumes an admitted plan", plan.get("schema") if isinstance(plan, dict) else type(plan).__name__, "tcps.plan.v1", "run TELCO selection and authorization")
    body = {key: value for key, value in plan.items() if key != "plan_digest"}
    expected = digest_object(body)
    if plan.get("plan_digest") != expected:
        _refuse("PLAN_DIGEST_MISMATCH", str(plan.get("subject", "unknown")), "execution consumes exactly the authorized plan", plan.get("plan_digest"), expected, "restore the authorized plan or re-run TELCO")
    current_authority = authority_digest(policy)
    if plan.get("authority_digest") != current_authority:
        _refuse("AUTHORITY_DIGEST_MISMATCH", str(plan.get("subject", "unknown")), "DO uses the exact authority admitted during selection", plan.get("authority_digest"), current_authority, "re-run TELCO under current authority")
    if plan.get("root") != str(Path(root).resolve()):
        _refuse("ROOT_IDENTITY_MISMATCH", str(plan.get("subject", "unknown")), "DO root equals the authorized root", str(Path(root).resolve()), plan.get("root"), "execute at the authorized root or re-plan")


def _validate_preconditions(target: Path, action: dict[str, Any]) -> None:
    if not target.parent.is_dir():
        _refuse("PARENT_NOT_ADMITTED", action["path"], "one action mutates only its declared target", str(target.parent), "existing directory", "add explicit mkdir work for each missing parent")
    if action["op"] == "write_text" and target.exists() and not target.is_file():
        _refuse("TARGET_TYPE_MISMATCH", action["path"], "write_text targets a file or absent path", _snapshot(target), "file|absent", "choose a file target")
    if action["op"] == "mkdir" and target.exists() and not target.is_dir():
        _refuse("TARGET_TYPE_MISMATCH", action["path"], "mkdir targets a directory or absent path", _snapshot(target), "directory|absent", "choose a directory target")
    if action["op"] == "remove" and target.is_dir() and any(target.iterdir()):
        _refuse("NONEMPTY_DIRECTORY_REMOVE_REFUSED", action["path"], "bounded remove never recursively erases unknown state", "non-empty directory", "empty directory or file", "remove children through separately admitted intents")


def _fsync_directory(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _apply(action: dict[str, Any], target: Path) -> None:
    operation = action["op"]
    if operation == "mkdir":
        if not target.exists():
            target.mkdir()
            _fsync_directory(target.parent)
        return
    if operation == "write_text":
        existed = target.exists()
        payload = action["content"].encode("utf-8")
        fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        try:
            offset = 0
            while offset < len(payload):
                written = os.write(fd, payload[offset:])
                if written <= 0:
                    raise OSError("short write")
                offset += written
            os.fsync(fd)
        finally:
            os.close(fd)
        if not existed:
            _fsync_directory(target.parent)
        return
    if operation == "remove":
        if target.is_dir():
            target.rmdir()
            _fsync_directory(target.parent)
        elif target.exists():
            target.unlink()
            _fsync_directory(target.parent)
        return
    raise AssertionError("operation admitted earlier")


def _consequence(action: dict[str, Any], before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {"op": action["op"], "path": action["path"], "before": before, "after": after, "changed": before != after}


def actuate(plan: dict[str, Any], policy: dict[str, Any], root: Path, receipt_path: Path | None = None) -> list[dict[str, Any]]:
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
            pre = make_pre_receipt(
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
            ledger.prepare(pre)
            _apply(action, target)
            after = _snapshot(target)
            verification = {"ok": after == expected, "kind": "exact-poststate"}
            if not verification["ok"]:
                _refuse("POSTCONDITION_FAILED", candidate["candidate_id"], "every DO satisfies its exact postcondition before final receipt", after, expected, "stop the line and recover before further DO")
            receipt = make_receipt(
                sequence=sequence,
                previous=previous,
                subject=plan["subject"],
                authority=plan["authority_digest"],
                intent=candidate["intent_digest"],
                pre_receipt=pre["pre_receipt_id"],
                consequence=_consequence(action, before, after),
                verification=verification,
            ).as_dict()
            ledger.finalize(receipt)
            emitted.append(receipt)
            previous = receipt["receipt_id"]
            sequence += 1
    return emitted


def recover(receipt_path: Path, root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    receipt_path = Path(receipt_path)
    with Ledger(receipt_path) as ledger:
        pending = ledger.pending()
        if pending is None:
            head, count = ledger.head_and_count()
            return {"schema": "tcps.recovery.v1", "state": "ALIVE", "recovered": False, "receipt_count": count, "chain_head": head}
        ledger.repair_incomplete_tail()
        existing = ledger.receipts()
        head = verify_chain(existing)
        expected_sequence = len(existing) + 1
        if pending["sequence"] <= len(existing):
            closed = existing[pending["sequence"] - 1]
            if closed.get("pre_receipt") == pending["pre_receipt_id"] and closed.get("previous") == pending["previous"]:
                ledger.abort_pending()
                return {"schema": "tcps.recovery.v1", "state": "ALIVE", "recovered": True, "resolution": "FINAL_RECEIPT_ALREADY_DURABLE", "receipt": closed}
            return {"schema": "tcps.recovery.v1", "state": "BLOCKED", "code": "RECOVERY_CHAIN_MISMATCH", "pre_receipt": pending["pre_receipt_id"]}
        if pending["sequence"] != expected_sequence or pending["previous"] != head:
            return {"schema": "tcps.recovery.v1", "state": "BLOCKED", "code": "RECOVERY_CHAIN_MISMATCH", "pre_receipt": pending["pre_receipt_id"], "observed": {"sequence": pending["sequence"], "previous": pending["previous"]}, "expected": {"sequence": expected_sequence, "previous": head}}
        if pending["root"] != str(root):
            return {"schema": "tcps.recovery.v1", "state": "BLOCKED", "code": "RECOVERY_ROOT_MISMATCH", "pre_receipt": pending["pre_receipt_id"]}
        target = _safe_target(root, pending["operation"]["path"])
        current = _snapshot(target)
        if current == pending["expected"]:
            verification = {"ok": True, "kind": "recovered-exact-poststate", "recovered": True}
            receipt = make_receipt(
                sequence=pending["sequence"],
                previous=pending["previous"],
                subject=pending["subject"],
                authority=pending["authority"],
                intent=pending["intent"],
                pre_receipt=pending["pre_receipt_id"],
                consequence=_consequence(pending["operation"], pending["before"], current),
                verification=verification,
            ).as_dict()
            ledger.finalize(receipt)
            return {"schema": "tcps.recovery.v1", "state": "ALIVE", "recovered": True, "receipt": receipt}
        if current == pending["before"]:
            pre_id = pending["pre_receipt_id"]
            ledger.abort_pending()
            return {"schema": "tcps.recovery.v1", "state": "PARTIAL_ALIVE", "recovered": False, "resolution": "ABORTED_PREPARED_NOT_ACTUATED", "pre_receipt": pre_id}
        return {"schema": "tcps.recovery.v1", "state": "BLOCKED", "code": "RECOVERY_AMBIGUOUS", "pre_receipt": pending["pre_receipt_id"], "observed": current, "before": pending["before"], "expected": pending["expected"]}
