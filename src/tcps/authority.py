from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import digest_object, load_json
from .model import Refusal, TCPSRefused

REQUIRED_POLICY_FIELDS = {
    "schema",
    "authority_id",
    "allowed_roots",
    "allowed_operations",
    "max_actions",
    "allow_irreversible",
}


def load_authority(path: str | Path) -> dict[str, Any]:
    policy = load_json(path)
    missing = sorted(REQUIRED_POLICY_FIELDS - set(policy))
    if missing:
        raise TCPSRefused(
            Refusal(
                "AUTHORITY_INCOMPLETE",
                str(path),
                "authority documents contain all mandatory policy fields",
                missing,
                sorted(REQUIRED_POLICY_FIELDS),
                "add the missing fields and re-admit the policy",
            )
        )
    if policy["schema"] != "tcps.authority.v1":
        raise TCPSRefused(
            Refusal(
                "AUTHORITY_SCHEMA_UNSUPPORTED",
                str(path),
                "authority schema is explicitly supported",
                policy["schema"],
                "tcps.authority.v1",
                "migrate the policy to the admitted schema",
            )
        )
    return policy


def authority_digest(policy: dict[str, Any]) -> str:
    return digest_object(policy)


def root_is_allowed(root: Path, policy: dict[str, Any]) -> bool:
    root = root.resolve()
    for configured in policy["allowed_roots"]:
        candidate = Path(configured).expanduser()
        if not candidate.is_absolute():
            candidate = (Path.cwd() / candidate).resolve()
        else:
            candidate = candidate.resolve()
        if root == candidate or candidate in root.parents:
            return True
    return False
