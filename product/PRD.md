# Product Requirements Document — TCPS v1979.1.1

## 1. Product thesis

Code production becomes governable when reversible construction is separated from irreversible execution and every consequential transition is bound to exact authority, observed consequence, independent verification, and replayable evidence.

TCPS turns that rule into an executable CLI and repository operating system.

## 2. Primary customers

The product is designed for large software estates where engineering leadership, platform teams, architecture, security, risk, operations, procurement, and audit all need the same work transition to mean the same thing.

Economic buyers may include CIO, CTO, VP Engineering, platform leadership, modernization leadership, security/risk leadership, and business owners accountable for continuity. Operational users include principal engineers, solution architects, platform teams, assurance engineers, technical program managers, and autonomous manufacturing systems.

## 3. Required outcomes

A bounded production cycle shall deliver:

1. admitted observation `O*`;
2. reversible candidate graph;
3. explicit selection;
4. exact authority binding;
5. bounded actuation plan;
6. observed consequence;
7. independent postcondition result;
8. BLAKE3 receipt chain;
9. replay result;
10. typed standing.

The generated source tree alone is not the product.

## 4. Functional requirements

### PRD-FR-001 — Observation admission

Every work order identifies an exact subject, purpose, observations, and requested actions. Missing or unsupported input fails closed with a typed refusal.

### PRD-FR-002 — Reversible candidate preservation

Construction must preserve lawful candidates before selection. Candidate creation does not grant execution authority.

### PRD-FR-003 — Bounded WIP

Policy defines the maximum number of selected consequential actions. Excess WIP is refused rather than silently truncated.

### PRD-FR-004 — Explicit authority

Every executable plan binds to an exact policy digest and root identity. Policy drift invalidates the plan.

### PRD-FR-005 — Root confinement

Every filesystem target resolves under the admitted root. Absolute paths and traversal outside the root are refused.

### PRD-FR-006 — Closed actuator set

v1979.1.1 admits only built-in operations with explicit schemas and postconditions. Arbitrary shell execution is excluded.

### PRD-FR-007 — Irreversibility gate

Destructive candidates may be modeled, but actuation requires explicit `allow_irreversible` policy. Recursive deletion is unsupported.

### PRD-FR-008 — Exact verification

Every actuation checks an exact postcondition before receipt creation. Verification failure stops the line.

### PRD-FR-009 — Receipts

Each material actuation emits a canonical BLAKE3 receipt binding subject, authority, intent, consequence, verification, sequence, and previous receipt.

### PRD-FR-010 — Replay

Replay validates chain identity and verifies the current world against receipted consequences. Drift is `BUILD_BROKEN` for the replayed subject.

### PRD-FR-011 — Deterministic projection

A canonical RDF graph drives generated runtime contract projections through ggen. Generated projections do not become a second authority.

### PRD-FR-012 — Identity reconstitution

The target source tree must contain no predecessor product identity, command namespace, package namespace, documentation navigation, or generated-brand residue.

### PRD-FR-013 — Enterprise evidence surface

The repository shall define product, architecture, governance, security, privacy, resilience, operations, support, procurement, supply-chain, release, transport, and retirement decisions.

### PRD-FR-014 — Offline transport

The repository can manufacture deterministic source bundles with content identity and no runtime network requirement.

## 5. Nonfunctional requirements

### Determinism

Identical admitted inputs, policy, root state, and toolchain must produce identical plans and receipt identities for identical consequences after declared normalization.

### Security

Default deny, least privilege, no ambient shell/network authority, path confinement, irreversible-action gating, immutable evidence semantics, and explicit supply-chain policy.

### Resilience

Every action is independently receipted. Replay begins from durable evidence, not volatile agent memory. Failure stops at the first violated invariant.

### Performance

Core planning and receipt operations must be linear in bounded work-order size. Enterprise deployments shall publish workload, environment, throughput, queue time, WIP, and replay latency rather than unqualified speed claims.

### Auditability

Every plan and receipt has content identity. Refusal objects identify the object, law, observed value, expected value, and repair path.

### Portability

The runtime uses the Python standard library only. Public RDF vocabularies carry provenance, terminology, metadata, and policy alignment.

## 6. Exclusions

v1979.1.1 does not provide arbitrary command execution, network automation, deployment connectors, recursive deletion, secret retrieval, package installation, production certification, regulatory certification, universal program equivalence, or automatic retirement authority.

These are extension surfaces, not hidden capabilities.

## 7. Release theorem

```text
legacy_identity_residue=0
required_authority_missing=0
required_enterprise_surface_missing=0
source_compile_failures=0
unit_integration_failures=0
real_cli_cycle_failures=0
receipt_chain_failures=0
replay_differences=0
offline_bundle_differences=0
release_admitted=true
```

External production standing remains a separate theorem.
