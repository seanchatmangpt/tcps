from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .blake3_ref import hexdigest
from .model import Refusal, TCPSRefused


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_object(value: Any) -> str:
    return f"blake3:{hexdigest(canonical_json(value))}"


def load_json(path: str | Path) -> Any:
    source = Path(path)
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TCPSRefused(
            Refusal(
                "INPUT_INVALID_JSON",
                str(source),
                "production inputs are valid JSON before admission",
                {"line": exc.lineno, "column": exc.colno, "message": exc.msg},
                "valid JSON",
                "repair the input without changing its authority",
            )
        ) from exc


def write_json(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
