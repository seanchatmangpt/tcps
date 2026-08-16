# Security policy

TCPS treats arbitrary execution authority as a security boundary, not a convenience feature.

## Supported line

Security fixes target the active `1979.1.x` line unless a release notice states otherwise.

## Report privately

Do not publish exploit details in an issue before coordinated disclosure. Use GitHub private vulnerability reporting for this repository when available.

## Security invariants

- default-deny actuation policy;
- no ambient shell or network actuator;
- repository-root confinement after canonical path resolution;
- irreversible operations disabled by default;
- BLAKE3 receipt identity and predecessor chaining;
- exact postcondition verification before standing;
- read-only CI permissions by default;
- pinned build/test dependencies where external packages are required;
- generated projections are never authority;
- credentials and secrets are outside the work-order schema.

A security control described here is a design/control claim, not a certification claim.
