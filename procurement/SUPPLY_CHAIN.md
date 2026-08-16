# Supply-chain and procurement posture

## Runtime dependencies

The TCPS runtime has no third-party Python package dependencies. BLAKE3-256 is implemented in-tree and covered by declared reference vectors.

## Build and test dependencies

The packaging backend and test runner are exact-version pinned in `pyproject.toml`. External build environments should additionally lock artifact hashes in their approved package mirror.

## Projection dependency

Generated contract projections use an exact admitted ggen source coordinate recorded in `AGENTS.md` and `authority/reconstitution.json`. Projection execution must record the exact tool identity and receipt.

## CI actions

The CI workflow grants read-only repository permission and pins the checkout action by immutable commit identity. Any added action requires source review, immutable pinning, and authority update.

## Enterprise procurement packet

A production adoption packet should include license inventory, dependency inventory, vulnerability results, provenance, SBOM, build recipe, deterministic bundle identity, support ownership, data flow, deployment topology, business continuity, incident process, and exceptions.

Control documentation does not constitute vendor approval or certification.
