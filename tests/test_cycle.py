from pathlib import Path

from tcps.engine import actuate, construct, observe, select_and_authorize
from tcps.receipt import verify_chain
from tcps.replay import replay


def policy(root: Path):
    return {
        "schema": "tcps.authority.v1",
        "authority_id": "test",
        "allowed_roots": [str(root.resolve())],
        "allowed_operations": ["mkdir", "write_text"],
        "max_actions": 8,
        "allow_irreversible": False,
    }


def work():
    return {
        "schema": "tcps.work.v1",
        "subject": "fixture",
        "purpose": "prove a receipted write",
        "observations": [{"kind": "request", "value": "create artifact"}],
        "actions": [
            {"op": "mkdir", "path": "out"},
            {"op": "write_text", "path": "out/result.txt", "content": "jidoka\n"},
        ],
    }


def test_full_cycle_and_replay(tmp_path: Path):
    observation = observe(work())
    assert observation["stage"] == "EVE"
    graph = construct(observation)
    assert graph["stage"] == "WIZARD"
    plan = select_and_authorize(graph, policy(tmp_path), tmp_path)
    assert plan["stage"] == "TELCO"
    receipts = actuate(plan, policy(tmp_path), tmp_path)
    assert (tmp_path / "out/result.txt").read_text() == "jidoka\n"
    assert verify_chain(receipts) == receipts[-1]["receipt_id"]

    receipt_log = tmp_path / "receipts.ndjson"
    receipt_log.write_text("\n".join(__import__("json").dumps(x, sort_keys=True) for x in receipts) + "\n")
    result = replay(receipt_log, tmp_path)
    assert result["state"] == "ALIVE"
    assert result["receipt_count"] == 2


def test_replay_detects_drift(tmp_path: Path):
    graph = construct(observe(work()))
    plan = select_and_authorize(graph, policy(tmp_path), tmp_path)
    receipts = actuate(plan, policy(tmp_path), tmp_path)
    receipt_log = tmp_path / "receipts.ndjson"
    receipt_log.write_text("\n".join(__import__("json").dumps(x, sort_keys=True) for x in receipts) + "\n")
    (tmp_path / "out/result.txt").write_text("drift\n")
    result = replay(receipt_log, tmp_path)
    assert result["state"] == "BUILD_BROKEN"
    assert result["drift"][0]["reason"] == "content-drift"
