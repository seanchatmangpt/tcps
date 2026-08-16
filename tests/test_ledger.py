import json
import os
from pathlib import Path

import pytest

from tcps.canonical import digest_object
from tcps.engine import actuate, construct, observe, recover, select_and_authorize
from tcps.ledger import Ledger, load_receipts, pending_path
from tcps.model import TCPSRefused
from tcps.receipt import make_pre_receipt, verify_chain
from tcps.replay import replay


def policy(root: Path) -> dict[str, object]:
    return {
        "schema": "tcps.authority.v1",
        "authority_id": "test",
        "allowed_roots": [str(root.resolve())],
        "allowed_operations": ["mkdir", "write_text"],
        "max_actions": 8,
        "allow_irreversible": False,
    }


def plan(root: Path, subject: str = "x", content: str = "a") -> dict[str, object]:
    work = {
        "schema": "tcps.work.v1",
        "subject": subject,
        "purpose": "exercise durable ledger semantics",
        "observations": [],
        "actions": [{"op": "write_text", "path": f"{subject}.txt", "content": content}],
    }
    return select_and_authorize(construct(observe(work)), policy(root), root)


def pending_for(root: Path, subject: str = "a") -> tuple[Path, dict[str, object]]:
    log = root / ".tcps/receipts.ndjson"
    selected_plan = plan(root, subject)
    action = selected_plan["selected"][0]["operation"]
    pre = make_pre_receipt(
        sequence=1,
        previous=None,
        subject=subject,
        authority=selected_plan["authority_digest"],
        intent=selected_plan["selected"][0]["intent_digest"],
        plan_digest=selected_plan["plan_digest"],
        root=str(root.resolve()),
        operation=action,
        before={"kind": "absent"},
        expected={"kind": "file", "digest": digest_object({"bytes_hex": b"a".hex()})},
    )
    return log, pre


def test_second_plan_continues_global_chain(tmp_path: Path):
    log = tmp_path / ".tcps/receipts.ndjson"
    actuate(plan(tmp_path, "a"), policy(tmp_path), tmp_path, log)
    actuate(plan(tmp_path, "b"), policy(tmp_path), tmp_path, log)
    receipts = load_receipts(log)
    assert [item["sequence"] for item in receipts] == [1, 2]
    assert receipts[1]["previous"] == receipts[0]["receipt_id"]
    assert verify_chain(receipts) == receipts[-1]["receipt_id"]


def test_concurrent_writer_is_refused_before_mutation(tmp_path: Path):
    log = tmp_path / "receipts.ndjson"
    with Ledger(log):
        with pytest.raises(TCPSRefused) as exc:
            with Ledger(log):
                pass
    assert exc.value.refusal.code == "LEDGER_LOCKED"


def test_crash_after_actuation_requires_recovery(tmp_path: Path, monkeypatch):
    log = tmp_path / ".tcps/receipts.ndjson"
    original_finalize = Ledger.finalize

    def crash_before_final_receipt(self, receipt):
        raise RuntimeError("simulated crash window")

    monkeypatch.setattr(Ledger, "finalize", crash_before_final_receipt)
    with pytest.raises(RuntimeError):
        actuate(plan(tmp_path, "a"), policy(tmp_path), tmp_path, log)
    assert (tmp_path / "a.txt").read_text() == "a"
    assert replay(log, tmp_path)["state"] == "PARTIAL_ALIVE"
    with pytest.raises(TCPSRefused) as exc:
        actuate(plan(tmp_path, "b"), policy(tmp_path), tmp_path, log)
    assert exc.value.refusal.code == "RECOVERY_REQUIRED"
    monkeypatch.setattr(Ledger, "finalize", original_finalize)
    result = recover(log, tmp_path)
    assert result["state"] == "ALIVE"
    assert result["recovered"] is True
    assert replay(log, tmp_path)["state"] == "ALIVE"


def test_prepared_but_not_actuated_is_aborted(tmp_path: Path):
    log, pre = pending_for(tmp_path)
    with Ledger(log) as ledger:
        ledger.prepare(pre)
    assert replay(log, tmp_path)["state"] == "PARTIAL_ALIVE"
    result = recover(log, tmp_path)
    assert result["state"] == "PARTIAL_ALIVE"
    assert result["resolution"] == "ABORTED_PREPARED_NOT_ACTUATED"
    assert replay(log, tmp_path)["state"] == "ALIVE"


def test_ambiguous_recovery_blocks_without_guessing(tmp_path: Path):
    log, pre = pending_for(tmp_path)
    with Ledger(log) as ledger:
        ledger.prepare(pre)
    (tmp_path / "a.txt").write_text("other")
    result = recover(log, tmp_path)
    assert result["state"] == "BLOCKED"
    assert result["code"] == "RECOVERY_AMBIGUOUS"


def test_replay_detects_poststate_drift(tmp_path: Path):
    log = tmp_path / ".tcps/receipts.ndjson"
    actuate(plan(tmp_path, "a"), policy(tmp_path), tmp_path, log)
    (tmp_path / "a.txt").write_text("drift")
    result = replay(log, tmp_path)
    assert result["state"] == "BUILD_BROKEN"
    assert result["drift"][0]["reason"] == "content-drift"


def test_final_receipt_durable_pending_cleanup(tmp_path: Path, monkeypatch):
    log = tmp_path / ".tcps/receipts.ndjson"
    original_finalize = Ledger.finalize

    def final_without_pending_cleanup(self, receipt):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    monkeypatch.setattr(Ledger, "finalize", final_without_pending_cleanup)
    actuate(plan(tmp_path, "a"), policy(tmp_path), tmp_path, log)
    assert pending_path(log).exists()
    monkeypatch.setattr(Ledger, "finalize", original_finalize)
    result = recover(log, tmp_path)
    assert result["state"] == "ALIVE"
    assert result["resolution"] == "FINAL_RECEIPT_ALREADY_DURABLE"
    assert not pending_path(log).exists()
    assert replay(log, tmp_path)["state"] == "ALIVE"


def test_later_receipt_supersedes_prior_poststate_on_same_path(tmp_path: Path):
    log = tmp_path / ".tcps/receipts.ndjson"
    for subject, content in (("first", "one"), ("second", "two")):
        work = {
            "schema": "tcps.work.v1",
            "subject": subject,
            "purpose": "write shared target",
            "observations": [],
            "actions": [{"op": "write_text", "path": "shared.txt", "content": content}],
        }
        chosen = select_and_authorize(construct(observe(work)), policy(tmp_path), tmp_path)
        actuate(chosen, policy(tmp_path), tmp_path, log)
    result = replay(log, tmp_path)
    assert result["state"] == "ALIVE"
    assert result["receipt_count"] == 2


def test_write_does_not_create_unreceipted_parent_directories(tmp_path: Path):
    work = {
        "schema": "tcps.work.v1",
        "subject": "nested",
        "purpose": "refuse implicit side effects",
        "observations": [],
        "actions": [{"op": "write_text", "path": "missing/child.txt", "content": "x"}],
    }
    chosen = select_and_authorize(construct(observe(work)), policy(tmp_path), tmp_path)
    with pytest.raises(TCPSRefused) as exc:
        actuate(chosen, policy(tmp_path), tmp_path, tmp_path / ".tcps/receipts.ndjson")
    assert exc.value.refusal.code == "PARENT_NOT_ADMITTED"
    assert not (tmp_path / "missing").exists()


def test_symlink_target_is_refused(tmp_path: Path):
    real = tmp_path / "real.txt"
    real.write_text("before")
    link = tmp_path / "link.txt"
    link.symlink_to(real)
    work = {
        "schema": "tcps.work.v1",
        "subject": "symlink",
        "purpose": "refuse alias actuation",
        "observations": [],
        "actions": [{"op": "write_text", "path": "link.txt", "content": "after"}],
    }
    chosen = select_and_authorize(construct(observe(work)), policy(tmp_path), tmp_path)
    with pytest.raises(TCPSRefused) as exc:
        actuate(chosen, policy(tmp_path), tmp_path, tmp_path / ".tcps/receipts.ndjson")
    assert exc.value.refusal.code == "SYMLINK_TARGET_REFUSED"
    assert real.read_text() == "before"


def test_recovery_truncates_only_incomplete_final_receipt_tail(tmp_path: Path):
    log, pre = pending_for(tmp_path)
    with Ledger(log) as ledger:
        ledger.prepare(pre)
    (tmp_path / "a.txt").write_text("a")
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_bytes(b'{"schema":"tcps.receipt.v1"')
    result = recover(log, tmp_path)
    assert result["state"] == "ALIVE"
    assert result["recovered"] is True
    receipts = load_receipts(log)
    assert len(receipts) == 1
    assert verify_chain(receipts) == receipts[0]["receipt_id"]
