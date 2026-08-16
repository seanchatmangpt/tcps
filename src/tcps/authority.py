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
ADMITTED_OPERATIONS = {"mkdir", "write_text", "remove"}


def _refuse(code: str, path: str | Path, observed: Any, expected: Any, repair: str) -> None:
    raise TCPSRefused(
        Refusal(
            code,
            str(path),
            "authority is structurally admitted before it can authorize selection or DO",
            observed,
            expected,
            repair,
        )
    )


def validate_authority(policy: Any, object_id: str | Path = "authority") -> dict[str, Any]:
    if not isinstance(policy, dict):
        _refuse("AUTHORITY_SHAPE_INVALID", object_id, type(policy).__name__, "object", "supply an authority object")
    missing = sorted(REQUIRED_POLICY_FIELDS - set(policy))
    unknown = sorted(set(policy) - REQUIRED_POLICY_FIELDS)
    if missing:
        _refuse("AUTHORITY_INCOMPLETE", object_id, missing, sorted(REQUIRED_POLICY_FIELDS), "add the missing fields and re-admit the policy")
    if unknown:
        _refuse("AUTHORITY_SHAPE_INVALID", object_id, unknown, sorted(REQUIRED_POLICY_FIELDS), "remove undeclared authority fields")
    if policy["schema"] != "tcps.authority.v1":
        _refuse("AUTHORITY_SCHEMA_UNSUPPORTED", object_id, policy["schema"], "tcps.authority.v1", "migrate the policy to the admitted schema")
    if not isinstance(policy["authority_id"], str) or not policy["authority_id"]:
        _refuse("AUTHORITY_ID_INVALID", object_id, policy["authority_id"], "non-empty string", "supply an exact authority identity")
    roots = policy["allowed_roots"]
    if not isinstance(roots, list) or not roots or not all(isinstance(item, str) and item for item in roots):
        _refuse("AUTHORITY_ROOTS_INVALID", object_id, roots, "non-empty array of paths", "admit one or more exact roots")
    operations = policy["allowed_operations"]
    if not isinstance(operations, list) or not all(isinstance(item, str) for item in operations):
        _refuse("AUTHORITY_OPERATIONS_INVALID", object_id, operations, "array of operation names", "admit only named operations")
    unsupported = sorted(set(operations) - ADMITTED_OPERATIONS)
    if unsupported:
        _refuse("AUTHORITY_OPERATION_UNSUPPORTED", object_id, unsupported, sorted(ADMITTED_OPERATIONS), "extend schema, verifier, and receipt semantics before granting the operation")
    if len(operations) != len(set(operations)):
        _refuse("AUTHORITY_OPERATIONS_INVALID", object_id, operations, "unique operation names", "remove duplicate authority entries")
    max_actions = policy["max_actions"]
    if isinstance(max_actions, bool) or not isinstance(max_actions, int) or not 0 <= max_actions <= 10000:
        _refuse("AUTHORITY_WIP_INVALID", object_id, max_actions, "integer 0..10000", "set an explicit bounded WIP limit")
    if not isinstance(policy["allow_irreversible"], bool):
        _refuse("AUTHORITY_IRREVERSIBILITY_INVALID", object_id, policy["allow_irreversible"], "boolean", "state irreversible authority explicitly")
    return policy


def load_authority(path: str | Path) -> dict[str, Any]:
    return validate_authority(load_json(path), path)


def authority_digest(policy: dict[str, Any]) -> str:
    return digest_object(validate_authority(policy))


def root_is_allowed(root: Path, policy: dict[str, Any]) -> bool:
    policy = validate_authority(policy)
    root = Path(root).resolve()
    for configured in policy["allowed_roots"]:
        candidate = Path(configured).expanduser()
        candidate = ((Path.cwd() / candidate).resolve() if not candidate.is_absolute() else candidate.resolve())
        if root == candidate or candidate in root.parents:
            return True
    return False
