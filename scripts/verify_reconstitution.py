#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Encoded so the forbidden predecessor identity is not itself reintroduced into the tree.
FORBIDDEN = [
    bytes.fromhex(value).decode("ascii")
    for value in (
        "737065632d6b6974",
        "737065636b6974",
        "737065636966792d636c69",
        "6769746875622f737065632d6b6974",
        "2e73706563696679",
    )
]
TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".toml",
    ".json",
    ".yml",
    ".yaml",
    ".ttl",
    ".tera",
    ".txt",
    ".sh",
}


def main() -> int:
    violations: list[dict[str, str]] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        lowered_path = str(relative).lower()
        for token in FORBIDDEN:
            if token in lowered_path:
                violations.append({"path": str(relative), "kind": "path", "token_hex": token.encode().hex()})
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", "AGENTS.md", "SECURITY.md"}:
            continue
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        for token in FORBIDDEN:
            if token in text:
                violations.append({"path": str(relative), "kind": "content", "token_hex": token.encode().hex()})
    report = {
        "schema": "tcps.reconstitution-verifier.v1",
        "root": str(ROOT),
        "legacy_identity_residue": len(violations),
        "violations": violations,
        "state": "ALIVE" if not violations else "BUILD_BROKEN",
    }
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
