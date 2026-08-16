# TCPS v1979.1.1 Validation Theorem

The release crown is conjunctive. No weighted score, partial success, model judgment, or documentation claim may substitute for a failed term.

## State equation

Let `O` be observed input, `O*` admitted input, `C(O*)` the reversible candidate set, `I*` the selected and authorized intent, `P` its durable pre-receipt, `A` the observed consequence, `R` the durable final receipt, and `S` replayed standing.

```text
O -> O* -> C(O*) -> I* -> P -> A -> R -> S
```

The actuation theorem is:

```text
DO(I*) is admissible
iff
authority(I*)
and durable(P)
and exact_root(I*)
and bounded_target(I*)
and no_pending_recovery
```

The completion theorem is:

```text
ALIVE(subject)
iff
identity_zero
and authority_exact
and candidate_lawful
and poststate_exact
and durable(R)
and chain_contiguous
and replay_exact
and pending_recovery = 0
```

## Non-substitution laws

- observed is not admitted;
- generated is not inspected;
- selected is not authorized;
- authorized is not executed;
- executed is not durably receipted;
- a hash is not a receipt;
- a historical receipt is not current standing;
- a green unit test is not repository release admission;
- repository release admission is not external production proof.

## Crash theorem

For one prepared actuation there are four admissible recovery observations:

1. `world == before` and no final receipt: abort prepared work; no actuation receives standing.
2. `world == expected` and no final receipt: reconstruct the final receipt from the durable pre-receipt and re-observation.
3. final receipt durable and pending cleanup remains: verify the exact closing edge and clear the pending marker.
4. any other world state: `BLOCKED:RECOVERY_AMBIGUOUS`.

The recovery engine is forbidden to guess which consequence occurred.

## Ledger theorem

For final receipts `R_1 ... R_n` in one ledger:

```text
sequence(R_i) = i
previous(R_1) = null
previous(R_i) = id(R_(i-1)) for i > 1
id(R_i) = BLAKE3(canonical_body(R_i))
```

A later lawful receipt may supersede an earlier post-state on the same target. Replay therefore verifies historical transition continuity and compares the world with the latest lawful post-state per target.

## Side-effect theorem

One action may mutate only its declared target. Parent-directory creation is separate work. Symlink aliases, root escape, recursive deletion, undeclared operations, policy drift, plan drift, and concurrent ledger writers fail closed.

Durability ordering is:

```text
fsync(pre-receipt)
< durable target mutation
< exact post-state observation
< fsync(final receipt)
< delete pending recovery marker
```

## Release falsifiers

The release is not ALIVE if any of these witnesses succeeds:

- predecessor identity remains in tracked paths or text;
- malformed or unsupported work reaches DO;
- SELECT can actuate;
- policy or plan drift reaches DO;
- target escapes the admitted root;
- missing parents are created implicitly;
- a symlink target is actuated through its alias;
- two writers own one receipt ledger;
- sequence restarts between plans;
- a crash leaves mutation with no recoverable durable intent;
- replay rejects a lawful later receipt merely because it superseded an earlier state;
- replay accepts unreceipted drift;
- generated projections differ from the admitted ontology projection;
- exact-head CI did not execute the subject being merged.

## Claim ceiling

This theorem can establish repository-scoped `ALIVE` for v1979.1.1. It does not establish a named external deployment, regulatory certification, universal correctness, or absence of all implementation defects. Those require independent evidence and retain their own standing.
