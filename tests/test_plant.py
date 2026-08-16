from pathlib import Path

from tcps.plant import andon, kanban, kaizen, metrics, standard_work, standing, wip


def test_standard_work_is_deterministic_and_complete():
    first = standard_work()
    second = standard_work()
    assert first == second
    assert first["state"] == "ALIVE"
    assert first["cycle"] == [
        "OBSERVE",
        "ADMIT",
        "MODEL",
        "SELECT",
        "AUTHORIZE",
        "PREPARE",
        "ACTUATE",
        "VERIFY",
        "RECEIPT",
        "REOBSERVE",
    ]
    assert first["roles"] == {"EVE": "en", "WIZARD": "zh-CN", "TELCO": "ja-JP", "ROBOT": "ko-KR"}


def test_kanban_is_deterministic_pull_signal():
    first = kanban("artifact", "downstream needs artifact", quantity=2, due_tick=7)
    second = kanban("artifact", "downstream needs artifact", quantity=2, due_tick=7)
    assert first == second
    assert first["quantity"] == 2
    assert first["state"] == "PARTIAL_ALIVE"


def test_kaizen_has_no_authority_or_actuation():
    proposal = kaizen("stop reason", "change standard work")
    assert proposal["authority"] == "NONE"
    assert proposal["actuation"] == "NONE"
    assert proposal["state"] == "PARTIAL_ALIVE"


def test_empty_ledger_plant_observations_are_alive(tmp_path: Path):
    log = tmp_path / ".tcps" / "receipts.ndjson"
    log.parent.mkdir()
    log.touch()
    assert wip(log)["actuation_wip"] == 0
    assert andon(log, tmp_path)["state"] == "ALIVE"
    assert metrics(log, tmp_path)["first_pass"] == 1.0
    assert metrics(log, tmp_path)["lead_ticks_status"] == "UNOBSERVED"
    assert standing(log, tmp_path)["standing"] == "ALIVE"
