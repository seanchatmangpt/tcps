from pathlib import Path

import pytest

from tcps.engine import construct, observe, select_and_authorize
from tcps.model import TCPSRefused


def test_unknown_operation_is_refused():
    work = {
        "schema": "tcps.work.v1",
        "subject": "x",
        "purpose": "test",
        "observations": [],
        "actions": [{"op": "shell", "path": "x", "command": "rm -rf /"}],
    }
    with pytest.raises(TCPSRefused) as exc:
        construct(observe(work))
    assert exc.value.refusal.state == "REFUSED:OPERATION_UNSUPPORTED"


def test_irreversible_action_defaults_to_refused(tmp_path: Path):
    work = {
        "schema": "tcps.work.v1",
        "subject": "x",
        "purpose": "test",
        "observations": [],
        "actions": [{"op": "remove", "path": "old.txt"}],
    }
    graph = construct(observe(work))
    policy = {
        "schema": "tcps.authority.v1",
        "authority_id": "test",
        "allowed_roots": [str(tmp_path)],
        "allowed_operations": ["remove"],
        "max_actions": 1,
        "allow_irreversible": False,
    }
    with pytest.raises(TCPSRefused) as exc:
        select_and_authorize(graph, policy, tmp_path)
    assert exc.value.refusal.state == "REFUSED:IRREVERSIBLE_OPERATION_NOT_AUTHORIZED"


def test_dot_traversal_is_refused_before_mutation(tmp_path: Path):
    work = {
        "schema": "tcps.work.v1",
        "subject": "x",
        "purpose": "test",
        "observations": [],
        "actions": [{"op": "write_text", "path": "../escape.txt", "content": "no"}],
    }
    graph = construct(observe(work))
    policy = {
        "schema": "tcps.authority.v1",
        "authority_id": "test",
        "allowed_roots": [str(tmp_path)],
        "allowed_operations": ["write_text"],
        "max_actions": 1,
        "allow_irreversible": False,
    }
    plan = select_and_authorize(graph, policy, tmp_path)
    from tcps.engine import actuate
    with pytest.raises(TCPSRefused) as exc:
        actuate(plan, policy, tmp_path)
    assert exc.value.refusal.state == "REFUSED:TARGET_PATH_INVALID"
    assert not (tmp_path.parent / "escape.txt").exists()
