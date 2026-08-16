# Release Control — TCPS v1979.1.1

## Purpose

This document governs release claims, evidence ceilings, candidate promotion, replay, crash recovery, and retirement decisions.

## Claim ceilings

| Ceiling | Meaning |
|---|---|
| `DOCUMENTED` | Requirement or design is stated. |
| `SCHEMA_VALIDATED` | Machine-readable authority conforms structurally. |
| `GENERATED` | The declared projector executed and emitted the artifact. |
| `COMPILED` | Exact source compiled or byte-compiled. |
| `TESTED` | Declared executable witnesses ran successfully. |
| `REFERENCE_CONFORMANT` | Independent verification established the bounded contract. |
| `PRODUCTION_PROVEN` | Longitudinal external evidence established production standing. |

A lower ceiling must never be phrased as a higher ceiling.

## Release admission

A v1979.1.1 candidate may be admitted only when all mandatory repository controls are present and the complete release conjunction is true:

```text
legacy_identity_residue = 0
required_surface_missing = 0
source_compile_failures = 0
unit_integration_failures = 0
fault_injection_failures = 0
real_cli_cycle_failures = 0
receipt_chain_failures = 0
pending_recovery = 0
replay_differences = 0
offline_bundle_differences = 0
ggen_projection_differences = 0
exact_head_ci_failures = 0
```

Fault injection must cover the pre-receipt/DO/final-receipt crash windows, ledger writer exclusion, cross-plan sequence continuity, lawful same-target supersession, path alias refusal, implicit-parent refusal, incomplete final-line recovery, and post-state drift.

Generation may be marked `GENERATED` only after the exact admitted ggen projector executes with its exact pinned toolchain and the generated projections are zero-diff. Source equivalence does not upgrade a blocked generation rail.

## Merge admission

The SHA merged to `main` must equal the exact PR head whose checks established the release conjunction. A synthetic merge coordinate, stale head, or unobserved successor is not admissible evidence.

## Production admission

Repository release admission is not external production proof. Production standing requires deployment-specific authority, identity, workload, tenancy, security boundary, operational telemetry, incident/recovery evidence, support ownership, and longitudinal receipts.

## Certification claims

The repository may define security, privacy, resilience, and control mappings. It must not claim SOC 2, ISO certification, regulatory compliance, zero risk, or Fortune 5 deployment without independent evidence.

## Retirement

Retiring or deleting any predecessor, adapter, data store, workflow, integration, or production path is a separate irreversible actuation. Release admission does not imply retirement admission.
