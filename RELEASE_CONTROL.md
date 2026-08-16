# Release Control — TCPS v1979.1.1

## Purpose

This document governs release claims, evidence ceilings, candidate promotion, replay, and retirement decisions.

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

A v1979.1.1 candidate may be admitted only when all mandatory repository controls are present, identity-zero verification succeeds, source compiles, the unit/integration suite passes, a real CLI cycle emits receipts, replay returns `ALIVE`, and deterministic transport produces byte-identical bundles.

Generation may be marked `GENERATED` only after the exact ggen projection command executes. If that toolchain is unavailable, the generation rail is `BLOCKED:GGEN_UNAVAILABLE`; source equivalence does not upgrade it.

## Production admission

Repository release admission is not external production proof. Production standing requires deployment-specific authority, identity, workload, tenancy, security boundary, operational telemetry, incident/recovery evidence, support ownership, and longitudinal receipts.

## Certification claims

The repository may define security, privacy, resilience, and control mappings. It must not claim SOC 2, ISO certification, regulatory compliance, zero risk, or Fortune 5 deployment without independent evidence.

## Retirement

Retiring or deleting any predecessor, adapter, data store, workflow, integration, or production path is a separate irreversible actuation. Release admission does not imply retirement admission.
