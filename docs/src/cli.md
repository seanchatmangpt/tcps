# CLI

## Initialize

```bash
tcps init .
```

This creates `.tcps/authority.json` and `.tcps/receipts.ndjson`. The default local authority admits `mkdir` and `write_text` under the initialized root and refuses irreversible actions.

## Full cycle

```bash
tcps run work.json --root .
```

`run` executes the same bounded stages exposed separately below. It does not bypass stage laws.

## EVE

```bash
tcps eve work.json --out .tcps/observation.json
```

Normalizes human-purpose input into an exact admitted observation with source digest. Malformed shapes and undeclared fields fail closed.

## WIZARD

```bash
tcps wizard .tcps/observation.json --out .tcps/graph.json
```

Constructs reversible candidates. Unsupported operation types are refused here.

## TELCO

```bash
tcps telco .tcps/graph.json --authority .tcps/authority.json --root . --out .tcps/plan.json
```

Applies WIP, operation, irreversibility, and root policy; then binds the plan to exact policy, graph, and root identities.

## ROBOT

```bash
tcps robot .tcps/plan.json --authority .tcps/authority.json --root .
```

Revalidates plan and authority, writes a durable pre-receipt, performs exactly one declared target mutation, makes that mutation durable, verifies the exact post-state, fsyncs the final receipt, then clears pending recovery state. Missing parent directories and symlink targets are refused rather than mutated implicitly.

## Replay

```bash
tcps replay --root .
```

Validates receipt identity, global sequence, predecessor edges, historical state transitions, current latest receipted consequences, and pending recovery state.

## Recover

```bash
tcps recover --receipts .tcps/receipts.ndjson --root .
```

Use after interrupted actuation. New DO work is refused while a durable pre-receipt is unresolved. Recovery closes only states that can be proven from the pre-receipt, final ledger, and current world; ambiguous state is `BLOCKED`.
