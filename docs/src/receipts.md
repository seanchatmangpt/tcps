# Receipts and Replay

TCPS uses a two-phase evidence boundary around every consequential actuation.

## Pre-receipt

Before `ROBOT` changes the world, it durably writes and fsyncs a `tcps.pre-receipt.v1` binding:

- global ledger sequence and previous final receipt;
- subject;
- authority digest;
- intent digest;
- plan digest;
- exact execution root;
- exact operation;
- observed before-state;
- expected post-state;
- BLAKE3 pre-receipt identity.

No new actuation may begin while a pre-receipt remains unresolved.

## Final receipt

After the mutation itself is made durable and the exact post-state is re-observed, the final receipt binds:

- schema and global sequence;
- previous final receipt identity;
- subject;
- authority digest;
- intent digest;
- the exact pre-receipt identity it closes;
- observed consequence, including before and after state;
- verification result;
- BLAKE3 receipt identity.

The final receipt is fsynced before the pending pre-receipt is removed. Receipt identity is BLAKE3 over canonical JSON excluding the `receipt_id` field itself.

## Global ledger

Sequence never restarts between plans in the same ledger:

```text
sequence(R_i) = i
previous(R_1) = null
previous(R_i) = id(R_(i-1))
```

Two writers cannot own one ledger concurrently.

## Replay

Replay validates digest identity, contiguous sequence, and predecessor edges before comparing the world with evidence. A later lawful receipt may supersede an earlier state on the same target, so replay verifies historical transition continuity and compares current state with the latest receipted state per target.

Changed content, missing directories, resurrected removed targets, or inconsistent historical transitions produce `BUILD_BROKEN`. An unresolved pre-receipt produces `PARTIAL_ALIVE` and `recovery_required=true`.

## Recovery

```bash
tcps recover --receipts .tcps/receipts.ndjson --root .
```

Recovery is evidence-driven:

1. **prepared but not actuated:** world equals `before`; abort the prepared record and return `PARTIAL_ALIVE` for that recovery operation;
2. **actuated but final receipt missing:** world equals `expected`; reconstruct and fsync the final receipt from the pre-receipt plus re-observation;
3. **final receipt durable but cleanup interrupted:** prove the final receipt closes the exact pending pre-receipt, then remove the stale pending marker;
4. **anything else:** return `BLOCKED:RECOVERY_AMBIGUOUS` and do not guess.

If a crash leaves only a non-newline-terminated partial final ledger line, recovery may truncate that incomplete tail only while the corresponding pre-receipt is still durable and the complete ledger prefix verifies.
