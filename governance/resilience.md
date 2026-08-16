# Resilience model

## Failure semantics

TCPS treats failures as typed transition failures rather than generic exceptions where a governing invariant exists.

## Recovery model

- immutable work and authority inputs are preferred;
- plans bind to policy and root identity;
- each successful action has its own receipt;
- replay reconstructs standing from durable evidence;
- no later stage silently overwrites a failed earlier stage;
- retries require a new hypothesis or changed input.

## Enterprise RTO/RPO

The local CLI does not assert an RTO or RPO. Production deployments shall publish measured recovery objectives for the worker, authority store, evidence store, and customer integration boundary separately.
