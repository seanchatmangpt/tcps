"""DfCM Challenger value compiler for Toyota Code Production System.

The compiler does not invent customer facts. It expands admitted claims into a
bounded narrative possibility space, Pareto-prunes dominated presentations, and
returns a deterministic reversible recommendation plus a replay digest.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

PROTOCOL = "challenger-value/1"
MAX_CANDIDATES = 4096
PHASES = ("TEACH", "REFRAME", "RATIONAL_IMPACT", "NEW_WAY", "PROOF")
PHASE_KIND = {
    "TEACH": {"OBSERVED", "VERIFIED"},
    "REFRAME": {"INFERRED", "HYPOTHESIS", "VERIFIED"},
    "RATIONAL_IMPACT": {"HYPOTHESIS", "VERIFIED"},
    "NEW_WAY": {"OBSERVED", "VERIFIED", "INFERRED"},
    "PROOF": {"VERIFIED"},
}
BUYERS = {
    "cio-cto": {
        "tags": {"governance", "integration", "throughput", "risk"},
        "diagnostic": "Can you trace one AI-generated production change from exact input through independent acceptance evidence and replay?",
    },
    "ciso": {
        "tags": {"security", "authority", "risk", "compliance"},
        "diagnostic": "Which controls are mechanically outside your agents' authority to change?",
    },
    "cfo": {
        "tags": {"cost", "roi", "verification", "coordination"},
        "diagnostic": "Can you separate AI construction savings from the human verification cost created downstream?",
    },
    "platform": {
        "tags": {"platform", "ontology", "integration", "verification"},
        "diagnostic": "Which platform invariants are generated from canonical semantics rather than synchronized by hand?",
    },
    "fortune5-buyer": {
        "tags": {"coordination", "governance", "scale", "risk"},
        "diagnostic": "Which coordination steps could disappear if constraints, evidence, and handoffs were executable?",
    },
    "hiring-manager": {
        "tags": {"throughput", "verification", "governance", "skills"},
        "diagnostic": "How do you evaluate engineers who operate software factories rather than manually author every artifact?",
    },
}


class Refusal(ValueError):
    """Typed admission refusal."""

    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(f"REFUSED:{code}: {detail}")


@dataclass(frozen=True)
class Claim:
    id: str
    phase: str
    kind: str
    text: str
    source: str | None
    exact_subject: str | None
    tags: tuple[str, ...]
    metric: bool
    customer_outcome: bool
    standing: str | None
    standing_evidence: bool
    materiality: int

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "Claim":
        try:
            cid = str(value["id"]).strip()
            phase = str(value["phase"]).upper()
            kind = str(value["kind"]).upper()
            text = str(value["text"]).strip()
        except KeyError as exc:
            raise Refusal("MALFORMED_CLAIM", f"missing {exc.args[0]}") from exc
        materiality = value.get("materiality", 0)
        if not isinstance(materiality, int) or not 0 <= materiality <= 5:
            raise Refusal("INVALID_MATERIALITY", cid)
        tags_raw = value.get("tags", [])
        if not isinstance(tags_raw, list) or not all(isinstance(tag, str) for tag in tags_raw):
            raise Refusal("INVALID_TAGS", cid)
        return cls(
            id=cid,
            phase=phase,
            kind=kind,
            text=text,
            source=str(value["source"]).strip() if value.get("source") else None,
            exact_subject=str(value["exact_subject"]).strip() if value.get("exact_subject") else None,
            tags=tuple(sorted(set(tags_raw))),
            metric=bool(value.get("metric", False)),
            customer_outcome=bool(value.get("customer_outcome", False)),
            standing=str(value["standing"]).strip() if value.get("standing") else None,
            standing_evidence=value.get("standing_evidence") is True,
            materiality=materiality,
        )


@dataclass(frozen=True)
class Candidate:
    id: str
    claim_ids: tuple[str, ...]
    evidence_density: int
    buyer_relevance: int
    falsifiability: int
    materiality: int
    claim_risk: int

    @property
    def vector(self) -> tuple[int, int, int, int, int]:
        return (
            self.evidence_density,
            self.buyer_relevance,
            self.falsifiability,
            self.materiality,
            -self.claim_risk,
        )


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _is_exact_subject(value: str | None) -> bool:
    if value is None or len(value) != 40:
        return False
    return all(ch in "0123456789abcdef" for ch in value.lower())


def _admit_claim(claim: Claim) -> None:
    if not claim.id:
        raise Refusal("EMPTY_CLAIM_ID", claim.phase)
    if claim.phase not in PHASE_KIND:
        raise Refusal("UNSUPPORTED_PHASE", claim.phase)
    if claim.kind not in PHASE_KIND[claim.phase]:
        raise Refusal("UNSUPPORTED_CLAIM", f"{claim.phase} cannot use {claim.kind}")
    if not claim.text:
        raise Refusal("EMPTY_CLAIM", claim.id)
    if claim.metric and not claim.source:
        raise Refusal("METRIC_WITHOUT_SOURCE", claim.id)
    if claim.customer_outcome and claim.kind != "VERIFIED":
        raise Refusal("OUTCOME_AS_FACT", claim.id)
    if claim.phase == "PROOF":
        if not claim.source:
            raise Refusal("PROOF_WITHOUT_SOURCE", claim.id)
        if not _is_exact_subject(claim.exact_subject):
            raise Refusal("PROOF_WITHOUT_EXACT_SUBJECT", claim.id)
        if claim.standing == "ALIVE" and not claim.standing_evidence:
            raise Refusal("ALIVE_WITHOUT_STANDING", claim.id)


def admit_case(payload: dict[str, Any]) -> tuple[str, tuple[Claim, ...]]:
    audience = str(payload.get("audience", "")).strip()
    if audience not in BUYERS:
        raise Refusal("UNSUPPORTED_AUDIENCE", audience)
    raw_claims = payload.get("claims")
    if not isinstance(raw_claims, list) or not raw_claims:
        raise Refusal("NO_CLAIMS", "claims must be a non-empty list")
    claims = tuple(Claim.from_mapping(item) for item in raw_claims)
    ids = [claim.id for claim in claims]
    if len(ids) != len(set(ids)):
        raise Refusal("DUPLICATE_CLAIM_ID", "claim ids must be unique")
    for claim in claims:
        _admit_claim(claim)
    present = {claim.phase for claim in claims}
    for phase in PHASES:
        if phase not in present:
            raise Refusal("MISSING_PHASE", phase)
    return audience, claims


def _score_combo(audience: str, combo: tuple[Claim, ...]) -> Candidate:
    buyer_tags = BUYERS[audience]["tags"]
    evidence_density = sum(1 for claim in combo if claim.source)
    buyer_relevance = len(set().union(*(set(c.tags) for c in combo)) & buyer_tags)
    falsifiability = sum(
        1 for claim in combo if claim.source and claim.kind in {"OBSERVED", "VERIFIED"}
    ) + sum(1 for claim in combo if _is_exact_subject(claim.exact_subject))
    materiality = sum(claim.materiality for claim in combo)
    claim_risk = sum(
        2 if claim.kind == "HYPOTHESIS" else 1 if claim.kind == "INFERRED" else 0
        for claim in combo
    )
    claim_ids = tuple(claim.id for claim in combo)
    cid = canonical_digest({"audience": audience, "claims": claim_ids})[:16]
    return Candidate(
        id=cid,
        claim_ids=claim_ids,
        evidence_density=evidence_density,
        buyer_relevance=buyer_relevance,
        falsifiability=falsifiability,
        materiality=materiality,
        claim_risk=claim_risk,
    )


def dominates(left: Candidate, right: Candidate) -> bool:
    lv, rv = left.vector, right.vector
    return all(a >= b for a, b in zip(lv, rv)) and any(a > b for a, b in zip(lv, rv))


def pareto_frontier(candidates: Iterable[Candidate]) -> tuple[Candidate, ...]:
    ordered = sorted(candidates, key=lambda c: c.id)
    frontier = [
        candidate
        for candidate in ordered
        if not any(dominates(other, candidate) for other in ordered if other.id != candidate.id)
    ]
    return tuple(sorted(frontier, key=lambda c: (tuple(-x for x in c.vector), c.id)))


def expand_frontier(audience: str, claims: tuple[Claim, ...]) -> tuple[int, tuple[Candidate, ...]]:
    buckets = {phase: [c for c in claims if c.phase == phase] for phase in PHASES}
    count = 1
    for phase in PHASES:
        count *= len(buckets[phase])
    if count > MAX_CANDIDATES:
        raise Refusal("CANDIDATE_BOUND_EXCEEDED", f"{count}>{MAX_CANDIDATES}")
    candidates = (
        _score_combo(audience, combo)
        for combo in itertools.product(*(buckets[phase] for phase in PHASES))
    )
    return count, pareto_frontier(candidates)


def _label(claim: Claim) -> str:
    return f"[{claim.kind}] {claim.text}"


def compile_brief(payload: dict[str, Any]) -> dict[str, Any]:
    audience, claims = admit_case(payload)
    candidate_count, frontier = expand_frontier(audience, claims)
    if not frontier:
        raise Refusal("EMPTY_FRONTIER", "no nondominated narrative candidate")
    by_id = {claim.id: claim for claim in claims}
    selected = frontier[0]
    chosen = [by_id[cid] for cid in selected.claim_ids]
    phase_claim = {claim.phase: claim for claim in chosen}
    result = {
        "protocol": PROTOCOL,
        "audience": audience,
        "candidate_count": candidate_count,
        "frontier_count": len(frontier),
        "frontier": [
            {
                "id": c.id,
                "claim_ids": list(c.claim_ids),
                "scores": {
                    "evidence_density": c.evidence_density,
                    "buyer_relevance": c.buyer_relevance,
                    "falsifiability": c.falsifiability,
                    "materiality": c.materiality,
                    "claim_risk": c.claim_risk,
                },
            }
            for c in frontier
        ],
        "recommended_candidate": selected.id,
        "brief": {
            "teach": _label(phase_claim["TEACH"]),
            "reframe": _label(phase_claim["REFRAME"]),
            "rational_impact": _label(phase_claim["RATIONAL_IMPACT"]),
            "new_way": _label(phase_claim["NEW_WAY"]),
            "proof": _label(phase_claim["PROOF"]),
            "take_control": BUYERS[audience]["diagnostic"],
        },
        "authority": {
            "select": "reversible-presentation",
            "construct": "brief-only",
            "do": "none",
        },
        "irreversible_selections": 0,
        "actuation": False,
    }
    result["receipt_sha256"] = canonical_digest(result)
    return result


def render_markdown(result: dict[str, Any]) -> str:
    brief = result["brief"]
    return "\n\n".join(
        (
            brief["teach"],
            brief["reframe"],
            brief["rational_impact"],
            brief["new_way"],
            brief["proof"],
            brief["take_control"],
            f"Receipt: {result['receipt_sha256']}",
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m specify_cli.challenger",
        description="Compile admitted evidence into a DfCM Challenger brief.",
    )
    parser.add_argument("case", type=Path, help="JSON Challenger case")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.case.read_text(encoding="utf-8"))
        result = compile_brief(payload)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"REFUSED:MALFORMED_INPUT: {exc}")
        return 2
    except Refusal as exc:
        print(str(exc))
        return 2
    if args.json_output:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
