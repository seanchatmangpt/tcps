# TCPS v1979.1.1

**Toyota Code Production System 1979** is a deterministic production CLI for manufacturing code changes under explicit authority.

TCPS does not treat a plan, model output, prompt, or selected candidate as execution authority. Production standing exists only after an admitted action crosses a bounded actuation boundary, its exact consequence is independently checked, and durable evidence can be replayed.

```text
Observe → Admit → Model → Select → Authorize → Prepare → Actuate → Verify → Receipt → Reobserve
```

```text
A = μ(O*)
R = receipt(A)
```

`O*` is admitted and bounded observation. `μ` is lawful manufacture. `A` is the observed consequence. `R` binds consequence to authority, intent, prior evidence, verification, and replay.

## Production boundary

TCPS separates three planes:

- **SELECT** preserves and chooses lawful reversible candidates.
- **CONSTRUCT** manufactures graphs, plans, projections, packs, and intents without ambient execution authority.
- **DO** crosses the consequential boundary only through an admitted plan and durable pre-receipt.

The v1979.1.1 built-in actuation surface is deliberately closed: `mkdir`, `write_text`, and explicitly authorized `remove`. Arbitrary shell execution, network calls, package installation, deployment, secrets access, recursive deletion, implicit parent creation, and symlink alias actuation are not ambient capabilities.

## Role projections

| Role | Language | Responsibility |
|---|---|---|
| `EVE` | English | Purpose intake and observation admission |
| `WIZARD` | 中文 | Reversible manufacturing and candidate construction |
| `TELCO` | 日本語 | Selection, routing, and exact authority binding |
| `ROBOT` | 한국어 | Exact DO, post-state verification, receipt, and recovery handoff |

The language projection is a presentation boundary, not authority. Each downstream role receives less semantic freedom and more exact machine state.

## Quick start

```bash
python -m pip install -e '.[test]'
tcps init .
tcps pack install builtin:core-1979 --root .
```

The core pack installs the four language-stratified production prompts through the same receipted DO boundary used for code manufacture.

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

Pull it through the line:

```bash
tcps make work.json --root .
tcps replay --root .
```

Stage-by-stage:

```bash
tcps eve work.json --out .tcps/observation.json
tcps wizard .tcps/observation.json --out .tcps/graph.json
tcps telco .tcps/graph.json --root . --out .tcps/plan.json
tcps robot .tcps/plan.json --root .
tcps replay --root .
```

## Plant control

The plant can be observed without inventing state:

```bash
tcps standard
tcps kanban artifact "downstream needs artifact" --quantity 1
tcps wip
tcps andon
tcps metrics
tcps standing
tcps kaizen "stop reason" "proposed standard-work change"
```

- **Kanban** is a deterministic downstream demand packet; creating one does not execute work.
- **WIP** exposes unresolved actuation inventory rather than hiding it inside an agent session.
- **Andon** projects replay/recovery state into a line signal.
- **Metrics** derive only what receipts support; unobserved wall-clock lead time stays `UNOBSERVED` rather than being estimated.
- **Kaizen** creates a candidate with no authority and no actuation.

## Production packs

TCPS uses one Pack calculus for workflow, integration, preset, extension, bundle, and standard-work packaging. Pack kind changes meaning, not execution law.

```bash
tcps pack builtins
tcps pack validate ./my-pack.json
tcps pack install ./my-pack.json --root .
tcps pack list --root .
```

A pack install compiles into ordinary bounded `mkdir`/`write_text` work, then passes through EVE → WIZARD → TELCO → PREPARE → ROBOT → VERIFY → RECEIPT. Dependencies are explicit. Network acquisition is not ambient in v1979.1.1.

## Crash-safe receipt law

Before every consequential mutation, `ROBOT` writes and fsyncs a BLAKE3-addressed pre-receipt containing the exact plan, authority, root, operation, before-state, and expected post-state. The target mutation is then made durable, re-observed, and closed by a fsynced final receipt. Only after that final receipt is durable is pending recovery state removed.

One ledger has one writer and one monotonically increasing sequence across all plans.

If execution is interrupted:

```bash
tcps recover --receipts .tcps/receipts.ndjson --root .
```

Recovery never guesses. It can prove and close an already-actuated expected state, abort a prepared-but-unactuated state, clear cleanup left after an already-durable final receipt, or return `BLOCKED:RECOVERY_AMBIGUOUS`.

## Enterprise shape

The repository carries product, architecture, governance, security, privacy, resilience, operations, support, procurement, supply-chain, evidence, release, offline transport, retirement, formal validation, fault injection, exact-head CI, plant control, and receipted pack controls. These controls define an enterprise decision surface; they do not claim external certification or a named production deployment.

Canonical authority order:

1. `AGENTS.md`
2. `RELEASE_CONTROL.md`
3. `authority/*.json`
4. `ontology/tcps.ttl`
5. `product/PRD.md`
6. `architecture/ARD.md`
7. `validation/VALIDATION_THEOREM.md`
8. schemas and executable verifier contracts
9. implementation and fault-injection tests
10. explanatory documentation
11. generated projections

## Manufacture and validate

`ontology/tcps.ttl` is the semantic source for the generated contract. The admitted ggen projector must execute with its exact pinned toolchain and reproduce generated artifacts with zero diff.

```bash
ggen sync run
python3 scripts/verify_reconstitution.py
python3 scripts/verify_repository.py
PYTHONPATH=src pytest -q
python3 scripts/release_verifier.py
python3 scripts/build_offline_bundle.py --check-determinism
```

The full release theorem and falsifiers are in `validation/VALIDATION_THEOREM.md` and `RELEASE_CONTROL.md`.

## Standing

`ALIVE` is scoped to the exact subject actually executed and verified. Repository release admission, external production proof, regulatory certification, and universal correctness are distinct claims. TCPS does not promote one into another.
