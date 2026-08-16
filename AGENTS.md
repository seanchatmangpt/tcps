# AGENTS.md — TCPS v1979.1.1

## Exact subject

This file governs `seanchatmangpt/tcps`.

- admitted reconstruction base commit: `bf88c9f9a82fa370c7a7257aa2b3cf10b457b65c`
- admitted predecessor tree: `76f0ac8eb6a67e8c684f0615cd9791319c422d5b`
- target release: `1979.1.1`
- reconstruction foundry: `seanchatmangpt/ggen-legacy@49c3a1eddf3d90560b9471573b6455dc240fe752`
- projection kernel: `seanchatmangpt/ggen@59c95cac18d49c62533918c906524be0fc4063ec`
- semantic source: `ontology/tcps.ttl`
- publication boundary: draft pull request unless merge is explicitly authorized

The admitted replacement is a new product tree. Predecessor source, documentation, package identity, command identity, generated assets, community catalogs, and integration-specific lifecycle machinery have no standing in the target tree unless independently re-admitted under TCPS authority.

## Mission

Manufacture code through the Toyota Code Production System 1979 calculus:

```text
observe → admit/refuse → model → preserve candidates
→ select → authorize → prepare → actuate → verify → receipt → reobserve
```

A plan is not execution. A selection is not authorization. Execution without durable prepared intent and a recoverable final receipt path is not production.

## Foundational order

1. Preserve purpose and recovery.
2. Fence unadmitted transitions.
3. Define objects, morphisms, authority, actuation, receipt, replay, and standing.
4. State exclusions.
5. Name falsifiers against the exact subject.
6. Preserve maximal reversible lawful possibilities before irreversible selection.
7. Bind every production claim to executable evidence.

## Absolute invariants

### Zero unreceipted actuation

Before DO, the exact plan, authority, root, operation, observed before-state, and expected post-state are bound into a BLAKE3-addressed pre-receipt and made durable. After DO, the exact consequence is re-observed, the final receipt is made durable, and only then may pending recovery state be cleared.

An unresolved pre-receipt blocks all new DO. Recovery may close only an exact expected post-state, abort an exact unchanged before-state, or clear cleanup after proving an already-durable final receipt. Ambiguous recovery is `BLOCKED`.

### One ledger, one writer, one history

A receipt ledger has one writer at a time. Final receipt sequence is monotonically contiguous across plans and every receipt binds its predecessor. Sequence never restarts because a new work order begins.

### SELECT, CONSTRUCT, and DO are distinct

Observation, model output, generated text, planner output, hooks, and candidate graphs have no ambient DO authority.

### O is not O*

```text
O  = partial or stale observation
O* = admitted, aligned, grounded, bounded observation
A  = μ(O*)
R  = receipt(A)
```

Track observed, admitted, executed, changed, verified, inferred, refused, blocked, unsupported, prepared, recovered, and replayed separately.

### Deterministic projection

`ontology/tcps.ttl` owns the generated runtime contract. `src/tcps/generated_contract.py` and `generated_contract.md` are projections. Change ontology or templates, execute the admitted ggen projector with its exact pinned toolchain, and require zero diff. Generated files never become an independent semantic authority.

### No arbitrary command authority

The v1979.1.1 runtime has no generic shell actuator. Built-in operations are closed and policy-filtered. Capability expansion requires a new schema, authority decision, verifier, tests, recovery semantics, and receipt semantics before DO access.

### One action, one declared target

A work action may mutate only its declared target. Parent creation is separate work. Recursive deletion is unsupported. Symlink targets and symlink path components are refused rather than followed through the actuation boundary.

### Path confinement

Targets are repository-relative and remain under the exact authorized root. Absolute paths, dot traversal, root escape, and aliases fail closed before mutation.

### Irreversible operations default deny

Destructive selection may exist in the candidate graph, but DO is refused unless policy explicitly admits irreversible authority.

### Claim ceilings

Documentation is not execution; CI metadata is not test evidence; a generated artifact is not admission; a receipt-shaped JSON object is not a verified receipt; a workflow definition is not a successful run; repository release admission is not external production proof.

## Typed states

Use exactly:

`UNKNOWN | PARTIAL_ALIVE | ALIVE | BLOCKED | BUILD_BROKEN | UNSUPPORTED | REFUSED:<CODE>`

`UNKNOWN` is not admitted. `UNSUPPORTED` is not refused. Missing required capability is `BLOCKED`; execution of an admitted boundary that fails is `BUILD_BROKEN`.

## Authority precedence

1. `AGENTS.md`
2. `RELEASE_CONTROL.md`
3. `authority/*.json`
4. `ontology/tcps.ttl`
5. `product/PRD.md`
6. `architecture/ARD.md`
7. `validation/VALIDATION_THEOREM.md`
8. schemas and verifier contracts
9. source and tests
10. operational documentation
11. generated reports

Contradiction returns `BLOCKED:AUTHORITY_CONTRADICTION`.

## Verification ladder

```text
python3 scripts/verify_reconstitution.py
→ python3 scripts/verify_repository.py
→ python3 -m compileall -q src
→ PYTHONPATH=src pytest -q
→ tcps init <temp-root>
→ exact tcps run work.json --root <temp-root>
→ exact tcps replay --root <temp-root>
→ crash-window and recovery falsifiers
→ deterministic offline bundle comparison
→ exact ggen sync run + zero-diff projection
→ exact-head hosted CI
```

The merge SHA must be the exact validated PR head. A synthetic merge coordinate or stale check cannot substitute for exact-head evidence.

## Repair law

Preserve the failing witness, classify the earliest failed transition, repair the narrowest cause, encode a permanent guard, rerun that boundary, and expand verification only after success. Never rerun an unchanged failure without a new hypothesis.

## Publication safety

Resolve exact base and head before writing. Preserve unrelated work. Never force-update shared refs. Default to a draft pull request. Do not merge without explicit authorization. When merge is authorized, merge only the exact validated head.

## Required receipt

Final reports state repository, base, branch, exact validated head, reconstruction foundry identity, projection kernel identity, transport failures, files manufactured, exact commands and exits, observed execution, fault-injection results, generated status, receipt/replay/recovery status, publication identity, scoped standing, exclusions, and falsifiers.
