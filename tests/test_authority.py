import json
from pathlib import Path

import pytest

from tcps.authority import load_authority, validate_authority
from tcps.model import TCPSRefused


def base(root: Path):
    return {
        "schema": "tcps.authority.v1",
        "authority_id": "test",
        "allowed_roots": [str(root)],
        "allowed_operations": ["write_text"],
        "max_actions": 1,
        "allow_irreversible": False,
    }


def test_unknown_authority_operation_is_refused(tmp_path: Path):
    policy = base(tmp_path)
    policy["allowed_operations"] = ["shell"]
    with pytest.raises(TCPSRefused) as exc:
        validate_authority(policy)
    assert exc.value.refusal.code == "AUTHORITY_OPERATION_UNSUPPORTED"


def test_boolean_is_not_valid_wip_limit(tmp_path: Path):
    policy = base(tmp_path)
    policy["max_actions"] = True
    with pytest.raises(TCPSRefused) as exc:
        validate_authority(policy)
    assert exc.value.refusal.code == "AUTHORITY_WIP_INVALID"


def test_undeclared_authority_field_is_refused(tmp_path: Path):
    policy = base(tmp_path)
    policy["ambient"] = True
    with pytest.raises(TCPSRefused) as exc:
        validate_authority(policy)
    assert exc.value.refusal.code == "AUTHORITY_SHAPE_INVALID"


def test_invalid_json_is_typed_refusal(tmp_path: Path):
    path = tmp_path / "authority.json"
    path.write_text("{")
    with pytest.raises(TCPSRefused) as exc:
        load_authority(path)
    assert exc.value.refusal.code == "INPUT_INVALID_JSON"
