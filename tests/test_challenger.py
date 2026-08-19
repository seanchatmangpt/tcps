import json

import pytest

from specify_cli.challenger import Refusal, compile_brief


def case():
    return {
        "audience": "ciso",
        "claims": [
            {
                "id": "teach-1",
                "phase": "TEACH",
                "kind": "OBSERVED",
                "text": "The production agent can modify implementation files.",
                "source": "repo-tree",
                "tags": ["authority", "security"],
                "materiality": 2,
            },
            {
                "id": "teach-2",
                "phase": "TEACH",
                "kind": "VERIFIED",
                "text": "An acceptance court is stored separately from generated implementation.",
                "source": "exact-head-ci",
                "exact_subject": "b" * 40,
                "tags": ["authority", "compliance"],
                "materiality": 4,
            },
            {
                "id": "reframe",
                "phase": "REFRAME",
                "kind": "INFERRED",
                "text": "If one actor can rewrite both implementation and acceptance, green may cease to be independent evidence.",
                "tags": ["authority", "risk"],
                "materiality": 4,
            },
            {
                "id": "impact",
                "phase": "RATIONAL_IMPACT",
                "kind": "HYPOTHESIS",
                "text": "Verification may become the bottleneck as construction gets cheaper.",
                "tags": ["risk"],
                "materiality": 3,
            },
            {
                "id": "new-way",
                "phase": "NEW_WAY",
                "kind": "OBSERVED",
                "text": "Separate construction, acceptance, and consequential actuation.",
                "source": "constitution",
                "tags": ["authority", "security"],
                "materiality": 5,
            },
            {
                "id": "proof",
                "phase": "PROOF",
                "kind": "VERIFIED",
                "text": "The exact-subject court refused an out-of-policy change.",
                "source": "workflow-run",
                "exact_subject": "a" * 40,
                "standing": "PARTIAL_ALIVE",
                "tags": ["authority", "compliance"],
                "materiality": 5,
            },
        ],
    }


def refusal_code(payload):
    with pytest.raises(Refusal) as exc:
        compile_brief(payload)
    return exc.value.code


def test_compile_is_deterministic_and_non_actuating():
    first = compile_brief(case())
    second = compile_brief(case())
    assert first == second
    assert first["actuation"] is False
    assert first["irreversible_selections"] == 0
    assert len(first["receipt_sha256"]) == 64
    assert first["candidate_count"] == 2
    assert first["frontier_count"] >= 1


def test_inference_and_hypothesis_remain_labeled():
    result = compile_brief(case())
    assert result["brief"]["reframe"].startswith("[INFERRED]")
    assert result["brief"]["rational_impact"].startswith("[HYPOTHESIS]")
    assert result["brief"]["proof"].startswith("[VERIFIED]")


def test_pareto_prefers_stronger_teach_without_deleting_alternative_space():
    result = compile_brief(case())
    assert result["candidate_count"] == 2
    assert any("teach-2" in candidate["claim_ids"] for candidate in result["frontier"])


@pytest.mark.parametrize(
    ("mutator", "code"),
    [
        (lambda p: p["claims"][-1].pop("exact_subject"), "PROOF_WITHOUT_EXACT_SUBJECT"),
        (lambda p: p["claims"][-1].update(kind="INFERRED"), "UNSUPPORTED_CLAIM"),
        (lambda p: p["claims"][0].update(metric=True, source=None), "METRIC_WITHOUT_SOURCE"),
        (lambda p: p.update(audience="everyone"), "UNSUPPORTED_AUDIENCE"),
        (lambda p: p["claims"][-1].update(standing="ALIVE"), "ALIVE_WITHOUT_STANDING"),
        (lambda p: p["claims"][3].update(customer_outcome=True), "OUTCOME_AS_FACT"),
        (lambda p: p["claims"].append(dict(p["claims"][0])), "DUPLICATE_CLAIM_ID"),
        (lambda p: p["claims"][0].update(materiality=9), "INVALID_MATERIALITY"),
    ],
)
def test_refusals(mutator, code):
    payload = json.loads(json.dumps(case()))
    mutator(payload)
    assert refusal_code(payload) == code


def test_candidate_bound_is_fail_closed():
    payload = case()
    for phase in ("REFRAME", "RATIONAL_IMPACT", "NEW_WAY"):
        original = next(c for c in payload["claims"] if c["phase"] == phase)
        for i in range(1, 9):
            clone = dict(original)
            clone["id"] = f"{original['id']}-{i}"
            payload["claims"].append(clone)
    for i in range(3, 10):
        clone = dict(payload["claims"][0])
        clone["id"] = f"teach-{i}"
        payload["claims"].append(clone)
    assert refusal_code(payload) == "CANDIDATE_BOUND_EXCEEDED"
