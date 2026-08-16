# TCPS v1979.1.1

**Toyota Code Production System 1979** is a deterministic production CLI for manufacturing code changes under explicit authority.

TCPS does not treat a plan, model output, prompt, or selected candidate as execution authority. Production standing exists only after an admitted action crosses the actuation boundary, its exact consequence is independently checked, and a tamper-evident receipt is chained for replay.

```text
Observe → Admit → Model → Select → Authorize → Actuate → Verify → Receipt → Reobserve
```

The operating law is simple:

```text
A = μ(O*)
R = receipt(A)
```

`O*` is admitted and bounded observation. `μ` is lawful manufacture. `A` is the observed consequence. `R` binds the consequence to authority, intent, verification, prior receipt, and replay.

## Product boundary

TCPS separates three planes:

- **SELECT** preserves and chooses lawful reversible candidates.
- **CONSTRUCT** manufactures plans, projections, and intents without ambient execution authority.
- **DO** crosses the consequential boundary only through an admitted plan and emits a receipt for every action.

The current built-in actuation surface is deliberately small: `mkdir`, `write_text`, and explicitly authorized `remove`. Arbitrary shell execution, network calls, package installation, deployment, secrets access, and recursive deletion are not ambient capabilities.

## Role projections

The same production calculus is projected through four progressively narrower interfaces:

| Role | Language | Responsibility |
|---|---|---|
| `EVE` | English | Purpose intake and observation normalization |
| `WIZARD` | 中文 | Reversible manufacturing and candidate construction |
| `TELCO` | 日本語 | Capability routing, selection, and authority binding |
| `ROBOT` | 한국어 | Exact execution, verification, receipt, and replay handoff |

The language projection does not change authority. Each downstream role receives less freedom and more exact machine state.

## Quick start

```bash
python -m pip install -e '.[test]'
tcps init .
```

Create a work order:

```json
{
  "schema": "tcps.work.v1",
  "subject": "hello-production",
  "purpose": "manufacture one receipted artifact",
  "observations": [{"kind": "request", "value": "create hello.txt"}],
  "actions": [
    {"op": "write_text", "path": "hello.txt", "content": "jidoka\n"}
  ]
}
```

Then execute the full cycle:

```bash
tcps run work.json --root .
tcps replay --root .
```

Or inspect each production stage explicitly:

```bash
tcps eve work.json --out .tcps/observation.json
tcps wizard .tcps/observation.json --out .tcps/graph.json
tcps telco .tcps/graph.json --root . --out .tcps/plan.json
tcps robot .tcps/plan.json --root .
tcps replay --root .
```

## Enterprise shape

The repository carries product, architecture, governance, security, privacy, resilience, operations, support, procurement, supply-chain, evidence, release, offline transport, and retirement controls. These controls define the decision surface; they do not claim certification or external deployment.

Canonical authority order:

1. `AGENTS.md`
2. `RELEASE_CONTROL.md`
3. `authority/*.json`
4. `ontology/tcps.ttl`
5. `product/PRD.md`
6. `architecture/ARD.md`
7. schemas and executable verifier contracts
8. implementation and tests
9. explanatory documentation
10. generated projections

## Manufacture and verify

The semantic source is `ontology/tcps.ttl`. `ggen.toml` projects the runtime contract and generated contract documentation. Generated artifacts are not independent authority.

```bash
ggen sync --manifest ggen.toml --profile enterprise-strict --audit
python3 scripts/verify_reconstitution.py
python3 scripts/verify_repository.py
PYTHONPATH=src pytest -q
python3 scripts/build_offline_bundle.py --check-determinism
```

If the ggen runtime is unavailable, generation standing is `BLOCKED`, not silently promoted from source inspection.

## Standing

The repository can establish local `ALIVE` only for an exact subject actually executed through the full bounded cycle. Repository-wide production, compliance, certification, and external Fortune 5 deployment remain separate claims requiring their own evidence.
