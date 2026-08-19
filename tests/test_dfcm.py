from __future__ import annotations

from copy import deepcopy
import json

import pytest

from tcps.dfcm import bottleneck, flow_metrics, kaizen_from_bottleneck, pareto_frontier, plan, verify_plan
from tcps.generated_contract import DFCM
from tcps.model import TCPSRefused


def work(subject: str, *, op: str = "write_text", path: str = "x.txt") -> dict:
    action = {"op": op, "path": path}
    if op == "write_text":
        action["content"] = subject + "\n"
    return {
        "schema": "tcps.work.v1",
        "subject": subject,
        "purpose": f"manufacture {subject}",
        "observations": [{"kind": "request", "value": subject}],
        "actions": [action],
    }


def candidate(
    work_id: str,
    *,
    subject: str | None = None,
    stream: str = "default",
    service: str = "standard",
    due: int | None = None,
    value: float = 0,
    urgency: float = 0,
    evidence: float = 0,
    risk: float = 0,
    cost: float = 0,
    cycle: float = 0,
    age: float = 0,
    op: str = "write_text",
) -> dict:
    return {
        "work_id": work_id,
        "work": work(subject or work_id, op=op, path=f"{work_id}.txt"),
        "acceptance": f"verify {work_id}",
        "value_stream": stream,
        "class_of_service": service,
        "due_tick": due,
        "value": value,
        "urgency": urgency,
        "evidence": evidence,
        "risk": risk,
        "cost": cost,
        "cycle_time": cycle,
        "age": age,
    }


def refusal_code(exc: TCPSRefused) -> str:
    return exc.refusal.code


def test_generated_dfcm_constitution_has_zero_actuation_authority():
    assert DFCM["selection"] == "deterministic-reversible"
    assert DFCM["irreversible_selections"] == 0
    assert DFCM["planner_authority"] == "SELECT"
    assert DFCM["actuation"] == "NONE"
    assert DFCM["one_piece_pull"] is True


def test_pareto_prunes_only_dominated_candidates():
    strong = candidate("strong", value=10, urgency=10, evidence=10, risk=1, cost=1, cycle=1)
    weak = candidate("weak", value=1, urgency=1, evidence=1, risk=9, cost=9, cycle=9)
    tradeoff = candidate("tradeoff", value=20, urgency=2, evidence=2, risk=5, cost=5, cycle=5)
    assert {x["work_id"] for x in pareto_frontier([weak, tradeoff, strong])} == {"strong", "tradeoff"}


def test_plan_is_order_invariant_and_self_replaying():
    rows = [
        candidate("runtime", stream="runtime", value=10, evidence=3, risk=1),
        candidate("evidence", stream="evidence", value=3, evidence=10, risk=1),
        candidate("weak", stream="runtime", value=1, evidence=1, risk=9, cost=9, cycle=9),
    ]
    forward = plan(rows, downstream_limit=4)
    backward = plan(list(reversed(rows)), downstream_limit=4)
    assert forward == backward
    assert verify_plan(forward)["state"] == "ALIVE"
    assert forward["planner_authority"] == "SELECT"
    assert forward["actuation"] == "NONE"
    assert forward["irreversible_selections"] == 0
    assert len(forward["inputs"]) == 3
    assert forward["input_digest"].startswith("blake3:")


def test_plan_survives_json_roundtrip_for_cli_replay():
    record = plan([candidate("a", value=5, evidence=1), candidate("b", value=1, evidence=5)])
    loaded = json.loads(json.dumps(record))
    assert verify_plan(loaded)["state"] == "ALIVE"


def test_plan_tampering_breaks_replay():
    record = plan([candidate("a", value=5, evidence=1), candidate("b", value=1, evidence=5)])
    forged = deepcopy(record)
    forged["selected"] = ["forged"]
    assert verify_plan(forged)["state"] == "BUILD_BROKEN"


def test_duplicate_work_id_refused():
    with pytest.raises(TCPSRefused) as ctx:
        plan([candidate("dup", subject="a"), candidate("dup", subject="b")])
    assert refusal_code(ctx.value) == "DFCM_DUPLICATE_WORK"


def test_duplicate_exact_work_refused_even_with_different_ids():
    first = candidate("one", subject="same")
    second = candidate("two", subject="same")
    second["work"] = deepcopy(first["work"])
    with pytest.raises(TCPSRefused) as ctx:
        plan([first, second])
    assert refusal_code(ctx.value) == "DFCM_DUPLICATE_WORK"


def test_non_object_candidate_is_typed_refusal():
    with pytest.raises(TCPSRefused) as ctx:
        plan(["not-an-object"])
    assert refusal_code(ctx.value) == "DFCM_CANDIDATE_INVALID"


def test_heijunka_alternates_value_streams_when_tradeoffs_survive():
    rows = [
        candidate("a1", stream="A", value=10, evidence=3, risk=2),
        candidate("a2", stream="A", value=8, evidence=8, risk=1),
        candidate("b1", stream="B", value=9, evidence=5, risk=2),
    ]
    record = plan(rows, downstream_limit=4)
    assert len(record["schedule"]) >= 2
    by_id = {c["work_id"]: c for c in record["inputs"]}
    assert by_id[record["schedule"][0]]["value_stream"] != by_id[record["schedule"][1]]["value_stream"]


def test_expedite_does_not_starve_lawful_non_expedite():
    rows = [
        candidate("e1", stream="A", service="expedite", value=10, evidence=1, risk=1),
        candidate("e2", stream="B", service="expedite", value=9, evidence=2, risk=1),
        candidate("s1", stream="C", service="standard", value=8, evidence=3, risk=1),
    ]
    record = plan(rows, downstream_limit=4)
    by_id = {c["work_id"]: c for c in record["inputs"]}
    classes = [by_id[x]["class_of_service"] for x in record["schedule"]]
    if len(classes) >= 2 and classes[0] == "expedite":
        assert classes[1] != "expedite"


def test_andon_blocks_pull_without_erasing_frontier():
    rows = [candidate("a", value=5, evidence=1), candidate("b", value=1, evidence=5)]
    record = plan(rows, downstream_limit=4, andon_active=True)
    assert record["state"] == "BLOCKED"
    assert record["blocked_reason"] == "ANDON_ACTIVE"
    assert record["selected"] == []
    assert len(record["frontier"]) == 2
    assert verify_plan(record)["state"] == "ALIVE"


def test_capacity_block_preserves_frontier_and_distinguishes_wip_overrun():
    rows = [candidate("a", value=5, evidence=1), candidate("b", value=1, evidence=5)]
    full = plan(rows, downstream_wip=2, downstream_limit=2)
    over = plan(rows, downstream_wip=3, downstream_limit=2)
    assert full["blocked_reason"] == "NO_KANBAN_CAPACITY"
    assert over["blocked_reason"] == "WIP_LIMIT_EXCEEDED"
    assert full["frontier"] == over["frontier"]


def test_destructive_candidate_can_remain_selectable_but_not_actuated():
    destructive = candidate("remove", value=10, evidence=10, risk=1, cost=1, cycle=1, op="remove")
    record = plan([destructive])
    assert record["selected"] == ["remove"]
    assert record["planner_authority"] == "SELECT"
    assert record["actuation"] == "NONE"
    assert record["irreversible_selections"] == 0


def test_flow_metrics_exposes_takt_little_law_and_flow_efficiency():
    result = flow_metrics(480, 12, 0.05, 10, observed_cycle_ticks=200, touch_ticks=50, lead_ticks=200)
    assert result["takt_ticks_per_item"] == 40
    assert result["process_ticks_per_item"] == 20
    assert result["little_law_cycle_ticks"] == 200
    assert result["little_law_residual_ticks"] == 0
    assert result["flow_efficiency"] == 0.25
    assert result["meets_takt"] is True


def test_flow_efficiency_requires_touch_and_lead_as_pair():
    with pytest.raises(TCPSRefused) as ctx:
        flow_metrics(480, 12, 0.05, 10, touch_ticks=50)
    assert refusal_code(ctx.value) == "DFCM_METRIC_INVALID"


def test_bottleneck_and_kaizen_are_deterministic_non_actuating():
    observation = bottleneck([
        {"stage": "observe", "wip": 2, "wip_limit": 8, "throughput": 1.0, "defects": 0},
        {"stage": "construct", "wip": 4, "wip_limit": 4, "throughput": 0.2, "defects": 1},
        {"stage": "verify", "wip": 2, "wip_limit": 4, "throughput": 0.5, "defects": 0},
    ])
    assert observation["bottleneck"] == "construct"
    proposal = kaizen_from_bottleneck(observation)
    assert proposal["target_stage"] == "construct"
    assert proposal["authority"] == "NONE"
    assert proposal["actuation"] == "NONE"
    assert proposal["may_mutate_acceptance"] is False
    assert proposal["may_mutate_wip_law"] is False


def test_bottleneck_tie_break_prefers_lexicographically_lower_stage():
    observation = bottleneck([
        {"stage": "beta", "wip": 1, "wip_limit": 1, "throughput": 1.0, "defects": 0},
        {"stage": "alpha", "wip": 1, "wip_limit": 1, "throughput": 1.0, "defects": 0},
    ])
    assert observation["bottleneck"] == "alpha"


def test_unknown_class_is_refused_before_selection():
    row = candidate("x")
    row["class_of_service"] = "magic"
    with pytest.raises(TCPSRefused) as ctx:
        plan([row])
    assert refusal_code(ctx.value) == "DFCM_CLASS_UNSUPPORTED"
