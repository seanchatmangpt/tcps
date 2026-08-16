from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .canonical import digest_object
from .model import Refusal, TCPSRefused
from .receipt import verify_chain


def load_receipts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    result: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise TCPSRefused(
                Refusal(
                    "RECEIPT_LOG_INVALID_JSON",
                    f"{path}:{line_number}",
                    "receipt log is canonical JSON Lines",
                    str(exc),
                    "valid JSON object",
                    "restore the original line from immutable evidence",
                )
            ) from exc
    return result


def replay(path: Path, root: Path) -> dict[str, Any]:
    receipts = load_receipts(path)
    head = verify_chain(receipts)
    drift: list[dict[str, Any]] = []
    for receipt in receipts:
        consequence = receipt["consequence"]
        target = (root / consequence["path"]).resolve()
        if consequence["op"] == "write_text":
            if not target.exists():
                drift.append({"receipt": receipt["receipt_id"], "reason": "target-missing"})
                continue
            current = target.read_text(encoding="utf-8")
            current_digest = digest_object({"text": current})
            if current_digest != consequence["after_digest"]:
                drift.append(
                    {
                        "receipt": receipt["receipt_id"],
                        "reason": "content-drift",
                        "observed": current_digest,
                        "expected": consequence["after_digest"],
                    }
                )
        elif consequence["op"] == "mkdir" and not target.is_dir():
            drift.append({"receipt": receipt["receipt_id"], "reason": "directory-missing"})
        elif consequence["op"] == "remove" and target.exists():
            drift.append({"receipt": receipt["receipt_id"], "reason": "removed-target-present"})
    return {
        "schema": "tcps.replay.v1",
        "receipt_count": len(receipts),
        "chain_head": head,
        "drift": drift,
        "state": "ALIVE" if not drift else "BUILD_BROKEN",
    }
