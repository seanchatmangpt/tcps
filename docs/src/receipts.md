# Receipts and Replay

Each receipt binds:

- schema and sequence;
- previous receipt identity;
- subject;
- authority digest;
- intent digest;
- observed consequence;
- verification result;
- BLAKE3 receipt identity.

Receipt identity is BLAKE3 over canonical JSON excluding the `receipt_id` field itself.

The chain is append-oriented: each receipt names the previous receipt. Replay rejects digest mismatch, sequence gaps, and predecessor mismatch before checking current world state.

Replay does not blindly re-execute past mutation. It re-observes the receipted consequence. A changed file, missing directory, or resurrected removed target produces drift and lowers replay standing.
