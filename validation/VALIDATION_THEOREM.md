# TCPS v1979.1.1 Validation Theorem

The release crown is conjunctive. No weighted score, partial success, model judgment, or documentation claim may substitute for a failed term.

## Production equation

Let `O` be observed input, `O*` admitted bounded input, `C(O*)` the reversible candidate set, `I*` selected and authorized intent, `P` durable prepared intent, `A` observed consequence, `R` durable final receipt, and `S` replayed standing.

```text
O -> O* -> C(O*) -> I* -> P -> A -> R -> S
```

```text
DO(I*) is admissible
iff authority(I*)
and durable(P)
and exact_root(I*)
and bounded_target(I*)
and pending_recovery = 0
```

```text
ALIVE(subject)
iff identity_zero
and authority_exact
and semantic_projection_exact
and poststate_exact
and durable(R)
and chain_contiguous
and replay_exact
and pending_recovery = 0
```

## Semantic-source theorem

`ontology/tcps.ttl` is the authority for the generated production contract. The exact admitted ggen projector must reproduce, with zero diff, the ten-stage cycle:

```text
OBSERVE -> ADMIT -> MODEL -> SELECT -> AUTHORIZE
-> PREPARE -> ACTUATE -> VERIFY -> RECEIPT -> REOBSERVE
```

Generated files do not become a second authority.

## Non-substitution laws

- observed is not admitted;
- generated is not inspected;
- selected is not authorized;
- authorized is not prepared;
- prepared is not executed;
- executed is not durably receipted;
- a hash is not a receipt;
- a historical receipt is not current standing;
- a green unit test is not repository release admission;
- repository release admission is not external production proof.

## Crash theorem

For one prepared actuation exactly four recovery classes are admitted:

1. `world == before` and no final receipt: abort prepared work; no actuation receives standing.
2. `world == expected` and no final receipt: reconstruct the final receipt from durable prepared intent plus re-observation.
3. final receipt durable and pending cleanup remains: prove the exact closing edge and clear the pending marker.
4. any other world state: `BLOCKED:RECOVERY_AMBIGUOUS`.

Recovery is forbidden to guess which consequence occurred.

## Ledger theorem

For final receipts `R_1 ... R_n` in one ledger:

```text
sequence(R_i) = i
previous(R_1) = null
previous(R_i) = id(R_(i-1)) for i > 1
id(R_i) = BLAKE3(canonical_body(R_i))
```

A later lawful receipt may supersede an earlier post-state on the same target. Replay verifies historical transition continuity and compares the world with the latest lawful post-state.

## Plant theorem

Plant observability is evidence-derived:

- Kanban constructs downstream demand but does not execute it.
- WIP exposes unresolved prepared actuation.
- Andon projects replay/recovery state.
- Metrics report only supported measures; unobserved wall-clock lead time remains `UNOBSERVED`.
- Kaizen creates a candidate with no authority and no actuation.
- Standing is derived from replay rather than asserted by a producer.

## Pack theorem

`workflow | integration | preset | extension | bundle | standard-work` are one typed Pack calculus. Pack installation has no privileged actuator: it compiles to bounded `tcps.work.v1` operations and crosses EVE -> WIZARD -> TELCO -> PREPARE -> ROBOT -> VERIFY -> RECEIPT.

The built-in `core-1979` pack carries the stratified interfaces EVE/English, WIZARD/中文, TELCO/日本語, and ROBOT/한국어. Language changes semantic presentation, never authority.

## Side-effect theorem

One work action may mutate only its declared target. Parent-directory creation is separate work. Absolute paths, dot traversal, symlink aliases, root escape, recursive deletion, undeclared operations, policy drift, plan drift, and concurrent ledger writers fail closed.

Durability order is:

```text
fsync(pre-receipt)
< durable declared mutation
< exact post-state observation
< fsync(final receipt)
< clear pending recovery
```

## Release falsifiers

The release is not `ALIVE` if any of these witnesses succeeds:

- predecessor product identity remains in tracked paths or text;
- malformed work or authority reaches DO;
- SELECT or CONSTRUCT can actuate;
- policy, plan, or root drift reaches DO;
- a target escapes the admitted root or is reached through a symlink alias;
- missing parent directories are created implicitly;
- two writers own one receipt ledger;
- final sequence restarts between plans;
- a crash leaves mutation without durable recoverable intent;
- replay rejects lawful supersession or accepts unreceipted drift;
- Pack installation bypasses the ordinary receipt boundary;
- Pack traversal or digest tampering is admitted;
- plant state is invented rather than derived from evidence;
- generated projections differ from the admitted ontology projection;
- exact-head CI did not execute the exact SHA admitted for merge.

## Claim ceiling

This theorem can establish repository-scoped `ALIVE` for v1979.1.1. It does not establish a named external deployment, regulatory certification, universal correctness, or absence of all implementation defects. Those claims require independent evidence.
