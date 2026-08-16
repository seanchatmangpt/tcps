# Product Requirements Document — TCPS v1979.1.1

## 1. Product thesis

Code production becomes governable when reversible construction is separated from consequential execution and every material transition is bound to exact authority, durable prepared intent, observed consequence, independent verification, replayable evidence, and explicit standing.

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
5. durable pre-receipt before DO;
6. bounded actuation;
7. observed consequence;
8. independent exact postcondition result;
9. BLAKE3 final receipt chain;
10. replay result;
11. typed standing.

The generated source tree alone is not the product.

## 4. Functional requirements

### PRD-FR-001 — Observation admission

Every work order identifies an exact subject, purpose, observations, and requested actions. Missing, malformed, undeclared, or unsupported input fails closed with a typed refusal.

### PRD-FR-002 — Reversible candidate preservation

Construction preserves lawful candidates before selection. Candidate creation does not grant execution authority.

### PRD-FR-003 — Bounded WIP

Policy defines the maximum number of selected consequential actions. Excess WIP is refused rather than silently truncated. Unresolved prepared actuation is explicit WIP and blocks new DO.

### PRD-FR-004 — Explicit authority

Every executable plan binds to an exact policy digest and root identity. Policy drift or root drift invalidates DO.

### PRD-FR-005 — Root confinement

Every filesystem target stays inside the admitted root. Absolute paths, dot traversal, symlink aliases, and implicit parent creation are refused before mutation.

### PRD-FR-006 — Closed actuator set

v1979.1.1 admits only built-in operations with explicit schemas and exact postconditions. Arbitrary shell and ambient network execution are excluded.

### PRD-FR-007 — Irreversibility gate

Destructive candidates may be modeled, but actuation requires explicit `allow_irreversible` policy. Recursive deletion is unsupported.

### PRD-FR-008 — Durable PREPARE boundary

Before every material DO, TCPS shall persist and fsync a pre-receipt binding global sequence, predecessor, subject, authority, intent, plan, root, exact operation, before-state, and expected post-state.

### PRD-FR-009 — Exact verification

Every actuation makes its declared mutation durable and then checks an exact post-state before final receipt creation. Verification failure stops the line and leaves recoverable evidence.

### PRD-FR-010 — Final receipts

Each material actuation emits a canonical BLAKE3 final receipt binding subject, authority, intent, pre-receipt, consequence, verification, global sequence, and previous final receipt. Final evidence is fsynced before pending recovery state is removed.

### PRD-FR-011 — Recovery

Interrupted execution must resolve from durable evidence and current world state. Exact before-state may abort, exact expected post-state may be finalized, an already-durable final receipt may complete cleanup, and ambiguous state must block without guessing.

### PRD-FR-012 — Replay

Replay validates chain identity, sequence, predecessor edges, historical transition continuity, pending recovery state, and current latest lawful post-state. Drift is `BUILD_BROKEN`.

### PRD-FR-013 — Deterministic projection

A canonical RDF graph drives generated runtime contract projections through the exact admitted ggen projector. Generated projections do not become a second authority. The projected cycle includes `PREPARE` as an explicit semantic stage.

### PRD-FR-014 — Identity reconstitution

The target source tree must contain no predecessor product identity, command namespace, package namespace, documentation navigation, or generated-brand residue.

### PRD-FR-015 — Plant control surface

The CLI shall expose deterministic standard work, Kanban demand packets, WIP, Andon, metrics, standing, Kaizen candidates, full-line `make`, recovery, and stage-specific EVE/WIZARD/TELCO/ROBOT commands. Observability commands shall derive state from evidence rather than inventing it.

### PRD-FR-016 — Stratified production prompts

The canonical standard-work pack shall project human-purpose admission through EVE/English, reversible manufacturing through WIZARD/中文, routing and authority through TELCO/日本語, and exact execution discipline through ROBOT/한국어. Language changes presentation and semantic scope, never authority.

### PRD-FR-017 — Production packs

Workflow, integration, preset, extension, bundle, and standard-work packaging collapse into one typed `tcps.pack.v1` calculus. Pack installation compiles into ordinary bounded TCPS work and receives no privileged filesystem path. Dependencies are explicit and missing dependency closure fails closed.

### PRD-FR-018 — Enterprise evidence surface

The repository shall define product, architecture, governance, security, privacy, resilience, operations, support, procurement, supply-chain, release, transport, recovery, validation, and retirement decisions.

### PRD-FR-019 — Offline transport

The repository can manufacture deterministic source bundles with content identity and no runtime network requirement.

## 5. Nonfunctional requirements

### Determinism

Identical admitted inputs, policy, root state, and toolchain produce identical plans and receipt identities for identical consequences after declared normalization.

### Security

Default deny, least privilege, no ambient shell/network authority, path confinement, symlink refusal, irreversible-action gating, one-writer evidence semantics, explicit supply-chain policy, and typed malformed-input refusal.

### Resilience

Every material action has durable intent before DO and durable final evidence after exact verification. Replay and recovery begin from durable evidence, not volatile agent memory. Failure stops at the first violated invariant.

### Performance

Core planning and receipt operations must be linear in bounded work-order size. Enterprise deployments publish workload, environment, throughput, queue time, WIP, and replay latency rather than unqualified speed claims.

### Auditability

Every plan, pre-receipt, final receipt, pack, Kanban packet, and generated standard has content identity where applicable. Refusal objects identify object, law, observed value, expected value, and repair path.

### Portability

The runtime uses the Python standard library only. Public RDF vocabularies carry provenance, terminology, metadata, and policy alignment.

## 6. Exclusions

v1979.1.1 does not provide arbitrary command execution, ambient network automation, deployment connectors, recursive deletion, secret retrieval, implicit package installation, production certification, regulatory certification, universal program equivalence, or automatic retirement authority.

Remote pack acquisition is not ambient; a future network transport must become an admitted TELCO capability with its own provenance, authority, verifier, and receipt semantics.

These are explicit extension surfaces, not hidden capabilities.

## 7. Release theorem

```text
legacy_identity_residue=0
required_authority_missing=0
required_enterprise_surface_missing=0
source_compile_failures=0
unit_integration_failures=0
fault_injection_failures=0
plant_surface_failures=0
pack_install_replay_failures=0
real_cli_cycle_failures=0
receipt_chain_failures=0
pending_recovery=0
replay_differences=0
offline_bundle_differences=0
ggen_projection_differences=0
exact_head_ci_failures=0
release_admitted=true
```

External production standing remains a separate theorem.
