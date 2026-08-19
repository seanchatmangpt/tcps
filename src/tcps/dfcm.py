from __future__ import annotations

from typing import Any, Iterable

from .canonical import digest_object
from .engine import observe
from .generated_contract import DFCM
from .model import Refusal, TCPSRefused

_MAXIMIZE = tuple(DFCM["maximize"])
_MINIMIZE = tuple(DFCM["minimize"])
_CLASS_RANK = {name: index for index, name in enumerate(DFCM["class_order"])}
_ALLOWED_CANDIDATE_FIELDS = {
    "work_id",
    "work",
    "acceptance",
    "value_stream",
    "class_of_service",
    "due_tick",
    "value",
    "urgency",
    "evidence",
    "risk",
    "cost",
    "cycle_time",
    "age",
}


def _dfcm_payload() -> dict[str, Any]:
    return {key: list(value) if isinstance(value, tuple) else value for key, value in DFCM.items()}


def _refuse(code: str, object_id: str, law: str, observed: Any, expected: Any, repair: str) -> None:
    raise TCPSRefused(Refusal(code, object_id, law, observed, expected, repair))


def _nonnegative_number(value: Any, *, object_id: str, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        _refuse(
            "DFCM_METRIC_INVALID",
            object_id,
            "DfCM objective coordinates are finite non-negative numbers",
            {field: value},
            "number >= 0",
            "repair the observation without changing the objective law",
        )
    result = float(value)
    if result == float("inf") or result != result:
        _refuse(
            "DFCM_METRIC_INVALID",
            object_id,
            "DfCM objective coordinates are finite non-negative numbers",
            {field: value},
            "finite number >= 0",
            "repair the observation without changing the objective law",
        )
    return result


def normalize_candidate(raw: Any, index: int = 0) -> dict[str, Any]:
    object_id = f"candidate-{index}" if index else "candidate"
    if not isinstance(raw, dict):
        _refuse("DFCM_CANDIDATE_INVALID", object_id, "candidate is an object", type(raw).__name__, "object", "normalize the candidate")
    unknown = sorted(set(raw) - _ALLOWED_CANDIDATE_FIELDS)
    missing = sorted({"work_id", "work", "acceptance"} - set(raw))
    if unknown or missing:
        _refuse(
            "DFCM_CANDIDATE_INVALID",
            str(raw.get("work_id", object_id)),
            "candidate fields match the bounded scheduling schema",
            {"unknown": unknown, "missing": missing},
            sorted(_ALLOWED_CANDIDATE_FIELDS),
            "remove undeclared fields and supply required fields",
        )
    work_id = raw["work_id"]
    if not isinstance(work_id, str) or not work_id.strip():
        _refuse("DFCM_CANDIDATE_INVALID", object_id, "work_id is a non-empty string", work_id, "non-empty string", "supply a stable work identity")
    work_id = work_id.strip()
    acceptance = raw["acceptance"]
    if not isinstance(acceptance, str) or not acceptance.strip():
        _refuse("DFCM_ACCEPTANCE_MISSING", work_id, "candidate binds explicit acceptance before selection", acceptance, "non-empty acceptance", "state the acceptance court before planning")
    observation = observe(raw["work"])
    value_stream = raw.get("value_stream", "default")
    if not isinstance(value_stream, str) or not value_stream.strip():
        _refuse("DFCM_CANDIDATE_INVALID", work_id, "value_stream is a non-empty string", value_stream, "non-empty string", "name the value stream")
    class_of_service = raw.get("class_of_service", "standard")
    if class_of_service not in _CLASS_RANK:
        _refuse("DFCM_CLASS_UNSUPPORTED", work_id, "class of service is bounded by generated standard work", class_of_service, list(_CLASS_RANK), "use an admitted class or change the ontology")
    due_tick = raw.get("due_tick")
    if due_tick is not None and (isinstance(due_tick, bool) or not isinstance(due_tick, int) or due_tick < 0):
        _refuse("DFCM_CANDIDATE_INVALID", work_id, "due_tick is non-negative or null", due_tick, "integer >= 0 | null", "repair the fixed-date observation")
    normalized = {
        "schema": "tcps.dfcm-candidate.v1",
        "work_id": work_id,
        "subject": observation["subject"],
        "work": raw["work"],
        "work_digest": observation["source_digest"],
        "acceptance": acceptance.strip(),
        "acceptance_digest": digest_object({"acceptance": acceptance.strip()}),
        "value_stream": value_stream.strip(),
        "class_of_service": class_of_service,
        "due_tick": due_tick,
    }
    for field in (*_MAXIMIZE, *_MINIMIZE, "age"):
        normalized[field] = _nonnegative_number(raw.get(field, 0), object_id=work_id, field=field)
    return normalized


def _validate_normalized(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict) or candidate.get("schema") != "tcps.dfcm-candidate.v1":
        _refuse("DFCM_CANDIDATE_INVALID", str(candidate.get("work_id", "candidate")) if isinstance(candidate, dict) else "candidate", "replay consumes a normalized DfCM candidate", candidate.get("schema") if isinstance(candidate, dict) else type(candidate).__name__, "tcps.dfcm-candidate.v1", "re-plan from admitted input")
    raw = {key: candidate[key] for key in _ALLOWED_CANDIDATE_FIELDS if key in candidate}
    expected = normalize_candidate(raw)
    if expected != candidate:
        _refuse("DFCM_CANDIDATE_DRIFT", candidate.get("work_id", "candidate"), "normalized candidate replays exactly", candidate, expected, "restore the admitted candidate or re-plan")
    return expected


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    no_worse = True
    better = False
    for field in _MAXIMIZE:
        no_worse = no_worse and a[field] >= b[field]
        better = better or a[field] > b[field]
    for field in _MINIMIZE:
        no_worse = no_worse and a[field] <= b[field]
        better = better or a[field] < b[field]
    return bool(no_worse and better)


def pareto_frontier(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    items = list(candidates)
    if not items:
        _refuse("DFCM_FRONTIER_EMPTY", "queue", "at least one admitted candidate exists before selection", 0, ">= 1", "observe or admit work before planning")
    if len(items) > int(DFCM["max_frontier"]):
        _refuse("DFCM_FRONTIER_BOUND", "queue", "reversible exploration remains bounded", len(items), DFCM["max_frontier"], "partition the queue without changing acceptance")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict) and item.get("schema") == "tcps.dfcm-candidate.v1":
            normalized.append(_validate_normalized(item))
        else:
            normalized.append(normalize_candidate(item, index))
    ids = [item["work_id"] for item in normalized]
    if len(ids) != len(set(ids)):
        _refuse("DFCM_DUPLICATE_WORK", "queue", "one work identity appears once in the admitted queue", ids, "unique work_id", "deduplicate observations before planning")
    digests = [item["work_digest"] for item in normalized]
    if len(digests) != len(set(digests)):
        _refuse("DFCM_DUPLICATE_WORK", "queue", "one exact work order appears once in the admitted queue", digests, "unique work_digest", "deduplicate exact work before planning")
    frontier = [item for item in normalized if not any(other["work_id"] != item["work_id"] and dominates(other, item) for other in normalized)]
    return sorted(frontier, key=lambda item: (item["work_id"], item["work_digest"]))


def _selection_key(item: dict[str, Any]) -> tuple[Any, ...]:
    due = item["due_tick"] if item["class_of_service"] == "fixed_date" and item["due_tick"] is not None else 2**63 - 1
    return (
        _CLASS_RANK[item["class_of_service"]],
        due,
        -item["urgency"],
        -item["value"],
        -item["evidence"],
        item["risk"],
        item["cost"],
        item["cycle_time"],
        -item["age"],
        item["work_id"],
        item["work_digest"],
    )


def heijunka_schedule(frontier: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    remaining = sorted(list(frontier), key=_selection_key)
    scheduled: list[dict[str, Any]] = []
    last_stream: str | None = None
    expedite_run = 0
    max_expedite = int(DFCM["max_expedite_in_row"])
    while remaining:
        pool = remaining
        if expedite_run >= max_expedite:
            non_expedite = [item for item in pool if item["class_of_service"] != "expedite"]
            if non_expedite:
                pool = non_expedite
        different_stream = [item for item in pool if item["value_stream"] != last_stream]
        if different_stream:
            pool = different_stream
        chosen = min(pool, key=_selection_key)
        scheduled.append(chosen)
        remaining.remove(chosen)
        last_stream = chosen["value_stream"]
        expedite_run = expedite_run + 1 if chosen["class_of_service"] == "expedite" else 0
    return scheduled


def _plan_from_normalized(normalized: list[dict[str, Any]], *, downstream_wip: int, downstream_limit: int, andon_active: bool) -> dict[str, Any]:
    frontier = pareto_frontier(normalized)
    schedule = heijunka_schedule(frontier)
    capacity = max(0, downstream_limit - downstream_wip)
    if andon_active:
        selected: list[dict[str, Any]] = []
        state = "BLOCKED"
        blocked_reason = "ANDON_ACTIVE"
    elif downstream_wip > downstream_limit:
        selected = []
        state = "BLOCKED"
        blocked_reason = "WIP_LIMIT_EXCEEDED"
    elif capacity < 1:
        selected = []
        state = "BLOCKED"
        blocked_reason = "NO_KANBAN_CAPACITY"
    else:
        selected = schedule[:1] if DFCM["one_piece_pull"] else schedule[:capacity]
        state = "PARTIAL_ALIVE"
        blocked_reason = None
    inputs = sorted(normalized, key=lambda item: (item["work_id"], item["work_digest"]))
    body = {
        "schema": "tcps.dfcm-plan.v1",
        "dfcm": _dfcm_payload(),
        "inputs": inputs,
        "input_digest": digest_object(inputs),
        "subjects": sorted({item["subject"] for item in inputs}),
        "frontier": [item["work_id"] for item in frontier],
        "frontier_digest": digest_object(frontier),
        "schedule": [item["work_id"] for item in schedule],
        "schedule_digest": digest_object(schedule),
        "selected": [item["work_id"] for item in selected],
        "selected_digest": digest_object(selected),
        "downstream_wip": downstream_wip,
        "downstream_limit": downstream_limit,
        "available_capacity": capacity,
        "andon_active": andon_active,
        "blocked_reason": blocked_reason,
        "selection_reversible": True,
        "irreversible_selections": int(DFCM["irreversible_selections"]),
        "planner_authority": DFCM["planner_authority"],
        "actuation": DFCM["actuation"],
        "state": state,
    }
    return {**body, "plan_digest": digest_object(body)}


def plan(candidates: Iterable[dict[str, Any]], *, downstream_wip: int = 0, downstream_limit: int = 1, andon_active: bool = False) -> dict[str, Any]:
    if isinstance(downstream_wip, bool) or not isinstance(downstream_wip, int) or downstream_wip < 0:
        _refuse("DFCM_WIP_INVALID", "downstream", "WIP is a non-negative integer", downstream_wip, "integer >= 0", "reobserve the downstream queue")
    if isinstance(downstream_limit, bool) or not isinstance(downstream_limit, int) or downstream_limit < 1:
        _refuse("DFCM_WIP_INVALID", "downstream", "WIP limit is a positive integer", downstream_limit, "integer >= 1", "change WIP law only through independent authority")
    if not isinstance(andon_active, bool):
        _refuse("DFCM_ANDON_INVALID", "line", "Andon state is boolean", andon_active, "boolean", "reobserve the line signal")
    normalized = [normalize_candidate(item, index + 1) for index, item in enumerate(candidates)]
    return _plan_from_normalized(normalized, downstream_wip=downstream_wip, downstream_limit=downstream_limit, andon_active=andon_active)


def verify_plan(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict) or record.get("schema") != "tcps.dfcm-plan.v1":
        return {"schema": "tcps.dfcm-replay.v1", "state": "BUILD_BROKEN", "reason": "PLAN_SCHEMA_UNSUPPORTED"}
    body = {key: value for key, value in record.items() if key != "plan_digest"}
    if record.get("plan_digest") != digest_object(body):
        return {"schema": "tcps.dfcm-replay.v1", "state": "BUILD_BROKEN", "reason": "PLAN_DIGEST_MISMATCH"}
    try:
        inputs = [_validate_normalized(item) for item in record.get("inputs", [])]
        expected = _plan_from_normalized(inputs, downstream_wip=record["downstream_wip"], downstream_limit=record["downstream_limit"], andon_active=record["andon_active"])
    except (KeyError, TCPSRefused):
        return {"schema": "tcps.dfcm-replay.v1", "state": "BUILD_BROKEN", "reason": "PLAN_REPLAY_REFUSED"}
    return {
        "schema": "tcps.dfcm-replay.v1",
        "state": "ALIVE" if expected == record else "BUILD_BROKEN",
        "reason": None if expected == record else "PLAN_REPLAY_MISMATCH",
        "plan_digest": record.get("plan_digest"),
        "input_digest": record.get("input_digest"),
        "frontier_digest": record.get("frontier_digest"),
        "schedule_digest": record.get("schedule_digest"),
    }


def flow_metrics(available_ticks: float, demand_items: float, throughput_per_tick: float, wip_items: float, *, observed_cycle_ticks: float | None = None, touch_ticks: float | None = None, lead_ticks: float | None = None) -> dict[str, Any]:
    values = {"available_ticks": available_ticks, "demand_items": demand_items, "throughput_per_tick": throughput_per_tick, "wip_items": wip_items}
    for field, value in values.items():
        minimum_positive = field != "wip_items"
        number = _nonnegative_number(value, object_id="flow", field=field)
        if minimum_positive and number == 0:
            _refuse("DFCM_METRIC_INVALID", "flow", "flow denominators are positive", {field: value}, "> 0", "reobserve the production interval")
        values[field] = number
    for field, value in (("observed_cycle_ticks", observed_cycle_ticks), ("touch_ticks", touch_ticks), ("lead_ticks", lead_ticks)):
        if value is not None:
            values[field] = _nonnegative_number(value, object_id="flow", field=field)
    takt = values["available_ticks"] / values["demand_items"]
    process = 1.0 / values["throughput_per_tick"]
    little_cycle = values["wip_items"] / values["throughput_per_tick"]
    observed_cycle = values.get("observed_cycle_ticks")
    flow_efficiency = None
    if (touch_ticks is None) != (lead_ticks is None):
        _refuse("DFCM_METRIC_INVALID", "flow", "flow efficiency requires touch and lead observations together", {"touch": touch_ticks, "lead": lead_ticks}, "both touch_ticks and lead_ticks", "supply both observations or neither")
    if touch_ticks is not None and lead_ticks is not None:
        if values.get("lead_ticks", 0) == 0:
            _refuse("DFCM_METRIC_INVALID", "flow", "lead time is positive when flow efficiency is requested", lead_ticks, "> 0", "supply an observed lead interval")
        if values.get("touch_ticks", 0) > values["lead_ticks"]:
            _refuse("DFCM_METRIC_INVALID", "flow", "touch time does not exceed lead time", {"touch": touch_ticks, "lead": lead_ticks}, "touch <= lead", "repair the observation")
        flow_efficiency = values.get("touch_ticks", 0) / values["lead_ticks"]
    body = {
        "schema": "tcps.dfcm-flow.v1",
        **values,
        "takt_ticks_per_item": takt,
        "process_ticks_per_item": process,
        "little_law_cycle_ticks": little_cycle,
        "little_law_residual_ticks": None if observed_cycle is None else observed_cycle - little_cycle,
        "flow_efficiency": flow_efficiency,
        "meets_takt": process <= takt,
        "state": "PARTIAL_ALIVE",
    }
    return {**body, "metric_digest": digest_object(body)}


def bottleneck(stages: Iterable[dict[str, Any]]) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(stages, start=1):
        if not isinstance(raw, dict) or set(raw) != {"stage", "wip", "wip_limit", "throughput", "defects"}:
            _refuse("DFCM_BOTTLENECK_INPUT_INVALID", f"stage-{index}", "bottleneck observation has exact fields", raw, ["stage", "wip", "wip_limit", "throughput", "defects"], "normalize stage observations")
        stage = raw["stage"]
        if not isinstance(stage, str) or not stage.strip() or stage in seen:
            _refuse("DFCM_BOTTLENECK_INPUT_INVALID", str(stage), "stage identity is unique and non-empty", stage, "unique non-empty stage", "repair stage identity")
        seen.add(stage)
        wip = _nonnegative_number(raw["wip"], object_id=stage, field="wip")
        limit = _nonnegative_number(raw["wip_limit"], object_id=stage, field="wip_limit")
        throughput = _nonnegative_number(raw["throughput"], object_id=stage, field="throughput")
        defects = _nonnegative_number(raw["defects"], object_id=stage, field="defects")
        if limit == 0 or throughput == 0:
            _refuse("DFCM_BOTTLENECK_INPUT_INVALID", stage, "WIP limit and throughput are positive", {"wip_limit": limit, "throughput": throughput}, "> 0", "reobserve the stage")
        normalized.append({"stage": stage, "wip": wip, "wip_limit": limit, "throughput": throughput, "defects": defects, "pressure": wip / limit, "cycle_ticks": 1.0 / throughput})
    if not normalized:
        _refuse("DFCM_BOTTLENECK_INPUT_INVALID", "plant", "at least one stage is observed", 0, ">= 1", "observe the plant")
    winner = max(sorted(normalized, key=lambda item: item["stage"]), key=lambda item: (item["pressure"], item["cycle_ticks"], item["defects"]))
    body = {
        "schema": "tcps.dfcm-bottleneck.v1",
        "stages": sorted(normalized, key=lambda item: item["stage"]),
        "bottleneck": winner["stage"],
        "pressure": winner["pressure"],
        "cycle_ticks": winner["cycle_ticks"],
        "defects": winner["defects"],
        "authority": "NONE",
        "actuation": "NONE",
        "state": "PARTIAL_ALIVE",
    }
    return {**body, "observation_digest": digest_object(body)}


def kaizen_from_bottleneck(observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(observation, dict) or observation.get("schema") != "tcps.dfcm-bottleneck.v1":
        _refuse("DFCM_KAIZEN_INPUT_INVALID", "kaizen", "Kaizen consumes an admitted bottleneck observation", observation.get("schema") if isinstance(observation, dict) else type(observation).__name__, "tcps.dfcm-bottleneck.v1", "observe the bottleneck first")
    body = {
        "schema": "tcps.dfcm-kaizen.v1",
        "target_stage": observation["bottleneck"],
        "reason_digest": observation["observation_digest"],
        "proposal": "run a reversible capacity, queue, or input-quality experiment at the observed constraint",
        "authority": "NONE",
        "actuation": "NONE",
        "may_mutate_acceptance": False,
        "may_mutate_wip_law": False,
        "state": "PARTIAL_ALIVE",
    }
    return {**body, "proposal_digest": digest_object(body)}
