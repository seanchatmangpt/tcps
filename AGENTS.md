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
→ select → authorize → actuate → verify → receipt → reobserve
```

A plan is not execution. A selection is not authorization. An actuation without a valid receipt is not production.

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

No consequential operation has standing unless an admitted plan crosses the bounded actuation surface, an exact postcondition succeeds, and a BLAKE3 receipt is appended to the chain.

### SELECT, CONSTRUCT, and DO are distinct

Observation, model output, generated text, planner output, hooks, and candidate graphs have no ambient DO authority.

### O is not O*

```text
O  = partial or stale observation
O* = admitted, aligned, grounded, bounded observation
A  = μ(O*)
R  = receipt(A)
```

Track observed, admitted, executed, changed, verified, inferred, refused, blocked, and unsupported separately.

### Deterministic projection

`ontology/tcps.ttl` owns the generated runtime contract. `src/tcps/generated_contract.py` and `generated_contract.md` are projections. Change the ontology or templates, run ggen, and verify the resulting diff; do not create a second semantic authority in generated files.

### No arbitrary command authority

The v1979.1.1 runtime has no generic shell actuator. Built-in operations are closed and policy-filtered. Capability expansion requires a new schema, authority decision, verifier, tests, and receipt semantics before DO access.

### Path confinement

Targets are repository-relative and must remain under the exact authorized root after path resolution. Traversal outside the root is `REFUSED:TARGET_ESCAPES_ROOT`.

### Irreversible operations default deny

Destructive selection may exist in the candidate graph, but DO is refused unless the policy explicitly admits irreversible authority. Recursive deletion is not supported.

### Claim ceilings

Documentation is not execution; CI metadata is not test evidence; a generated artifact is not admission; a receipt-shaped JSON object is not a verified receipt; a workflow is not a successful run.

## Typed states

Use exactly:

`UNKNOWN | PARTIAL_ALIVE | ALIVE | BLOCKED | BUILD_BROKEN | UNSUPPORTED | REFUSED:<CODE>`

`UNKNOWN` is not admitted. `UNSUPPORTED` is not refused. Missing toolchains are `BLOCKED`, not `BUILD_BROKEN`.

## Authority precedence

1. `AGENTS.md`
2. `RELEASE_CONTROL.md`
3. `authority/*.json`
4. `ontology/tcps.ttl`
5. `product/PRD.md`
6. `architecture/ARD.md`
7. schemas and verifier contracts
8. source and tests
9. operational documentation
10. generated reports

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
→ deterministic offline bundle comparison
→ ggen sync + zero-diff projection check when ggen is available
```

Hosted CI supplements this ladder. It does not replace observed execution of the exact subject.

## Repair law

Preserve the failing witness, classify the earliest failed transition, repair the narrowest cause, encode a permanent guard, rerun that boundary, and expand verification only after success. Never rerun an unchanged failure without a new hypothesis.

## Publication safety

Resolve exact base and head before writing. Preserve unrelated work. Never force-update shared refs. Default to a draft pull request. Do not merge without explicit authorization.

## Required receipt

Final reports state repository, base, branch, head, reconstruction foundry identity, projection kernel identity, transport failures, files manufactured, exact commands and exits, observed execution, generated status, receipt/replay status, publication identity, scoped standing, exclusions, and falsifiers.
