from pathlib import Path

import pytest

from tcps.canonical import write_json
from tcps.model import TCPSRefused
from tcps.packs import builtin_pack, install_pack, installed_packs, pack_work_order, validate_pack
from tcps.replay import replay


def authority(root: Path) -> Path:
    path = root / ".tcps" / "authority.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(
        path,
        {
            "schema": "tcps.authority.v1",
            "authority_id": "pack-test",
            "allowed_roots": [str(root.resolve())],
            "allowed_operations": ["mkdir", "write_text"],
            "max_actions": 64,
            "allow_irreversible": False,
        },
    )
    (root / ".tcps" / "receipts.ndjson").touch()
    return path


def test_core_pack_contains_stratified_language_prompts():
    pack = builtin_pack("core-1979")
    assert "prompts/eve.en.md" in pack["files"]
    assert "prompts/wizard.zh.md" in pack["files"]
    assert "prompts/telco.ja.md" in pack["files"]
    assert "prompts/robot.ko.md" in pack["files"]
    assert "制造" in pack["files"]["prompts/wizard.zh.md"]
    assert "経路" in pack["files"]["prompts/telco.ja.md"]
    assert "실행" in pack["files"]["prompts/robot.ko.md"]


def test_pack_work_order_is_only_bounded_filesystem_operations():
    work = pack_work_order(builtin_pack("core-1979"))
    assert work["schema"] == "tcps.work.v1"
    assert all(action["op"] in {"mkdir", "write_text"} for action in work["actions"])
    assert all(action["path"].startswith(".tcps/packs/core-1979") or action["path"] == ".tcps/packs" for action in work["actions"])


def test_core_pack_install_is_receipted_and_replayable(tmp_path: Path):
    authority_path = authority(tmp_path)
    log = tmp_path / ".tcps" / "receipts.ndjson"
    result = install_pack(
        "builtin:core-1979",
        root=tmp_path,
        authority_path=authority_path,
        receipt_path=log,
    )
    assert result["state"] == "ALIVE"
    assert result["receipt_count"] > 0
    assert (tmp_path / ".tcps/packs/core-1979/prompts/eve.en.md").is_file()
    assert replay(log, tmp_path)["state"] == "ALIVE"
    listed = installed_packs(tmp_path)
    assert listed["state"] == "ALIVE"
    assert listed["packs"][0]["pack_id"] == "core-1979"


def test_pack_path_traversal_is_refused():
    pack = {
        "schema": "tcps.pack.v1",
        "pack_id": "bad",
        "version": "1",
        "kind": "workflow",
        "requires": [],
        "files": {"../escape.md": "no"},
    }
    with pytest.raises(TCPSRefused) as exc:
        validate_pack(pack)
    assert exc.value.refusal.code == "PACK_PATH_INVALID"


def test_pack_digest_tamper_is_refused():
    pack = dict(builtin_pack("core-1979"))
    pack["pack_digest"] = "blake3:" + "0" * 64
    with pytest.raises(TCPSRefused) as exc:
        validate_pack(pack)
    assert exc.value.refusal.code == "PACK_DIGEST_MISMATCH"
