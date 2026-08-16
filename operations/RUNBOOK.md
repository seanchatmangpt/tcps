# Operations runbook

## Start

```bash
tcps --version
tcps init <root>
```

Inspect `.tcps/authority.json` before executing a work order. Production deployments should provision this file from an external authority process rather than interactive editing on the worker.

## Execute

```bash
tcps run work.json --authority .tcps/authority.json --root .
```

A success response contains `state=ALIVE` only for the exact executed work subject and its bounded cycle.

## Replay

```bash
tcps replay --receipts .tcps/receipts.ndjson --root .
```

`BUILD_BROKEN` means receipted consequence and current world state diverge. Preserve evidence before repair.

## Stop the line

On refusal or failed replay:

1. preserve work order, policy, plan, receipt log, and observed state;
2. identify the earliest failed transition;
3. correct that transition without weakening its law;
4. add a permanent witness for the failure mode;
5. rerun the narrow boundary;
6. expand only after success.

## Backup

Receipt logs and authority documents are durability-critical. Enterprise deployments should store immutable copies outside the mutable work root.
