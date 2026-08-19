# Security control model

## Threat model

Primary threats are authority confusion, path escape, arbitrary execution, policy drift, tampered plans, forged receipts, partial-state concealment, unbounded deletion, and supply-chain substitution.

## Preventive controls

- closed built-in actuator vocabulary;
- no ambient shell or network execution;
- canonical root resolution and traversal refusal;
- exact policy digest bound into plans;
- plan digest verified before DO;
- irreversible mutation disabled by default;
- non-empty directory deletion refused;
- standard-library runtime dependency surface;
- generated projections excluded from semantic authority.

## Detective controls

- BLAKE3 receipt identity;
- predecessor-linked receipt chain;
- replay against current world state;
- identity-zero repository scan;
- exact dependency pins for build/test tooling;
- read-only CI permissions;
- machine-readable release authority.

## Response controls

A failed invariant stops the line. Recovery preserves the failure object and repairs the earliest failed transition before expanding scope.
