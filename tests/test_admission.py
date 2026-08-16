from pathlib import Path

import pytest

from tcps.engine import construct, observe, select_and_authorize
from tcps.model import TCPSRefused


def test_work_order_rejects_undeclared_fields():
    work = {
        "schema": "tcps.work.v1",
        "subject": "x",
        "purpose": "p",
        "observations": [],
        "actions": [],
        "ambient_authority": True,
    }
    with pytest.raises(TCPSRefused) as exc:
        observe(work)
    assert exc.value.refusal.code == "WORK_SHAPE_INVALID"


def test_action_must_be_object():
    observation = observe(
        {
            "schema": "tcps.work.v1",
            "subject": "x",
            "purpose": "p",
            "observations": [],
            "actions": ["write something"],
        }
    )
    with pytest.raises(TCPSRefused) as exc:
        construct(observation)
    assert exc.value.refusal.code == "ACTION_SHAPE_INVALID"


def test_write_content_must_be_text():
    observation = observe(
        {
            "schema": "tcps.work.v1",
            "subject": "x",
            "purpose": "p",
            "observations": [],
            "actions": [{"op": "write_text", "path": "x", "content": 1}],
        }
    )
    with pytest.raises(TCPSRefused) as exc:
        construct(observation)
    assert exc.value.refusal.code == "ACTION_SHAPE_INVALID"


def test_telco_rejects_non_graph(tmp_path: Path):
    policy = {
        "schema": "tcps.authority.v1",
        "authority_id": "test",
        "allowed_roots": [str(tmp_path)],
        "allowed_operations": ["write_text"],
        "max_actions": 1,
        "allow_irreversible": False,
    }
    with pytest.raises(TCPSRefused) as exc:
        select_and_authorize({"schema": "wrong"}, policy, tmp_path)
    assert exc.value.refusal.code == "GRAPH_SCHEMA_UNSUPPORTED"
