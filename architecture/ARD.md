# Architecture Requirements Document — TCPS v1979.1.1

## 1. Architecture style

TCPS is a projectional production calculus with a small execution broker.

```text
parse → route → observe → admit/refuse → model
→ construct candidates → select → authorize
→ actuate → verify → receipt → replay → standing
```

Construction is reversible. Actuation is consequential. Standing is evidence-derived.

## 2. Logical planes

### Observation plane

Consumes `tcps.work.v1` and emits normalized observation with source digest. Observation alone has no authority.

### Modeling plane

Converts requested actions into a candidate graph. Unsupported operations are topology failures with typed refusal; they are not silently rewritten.

### Selection plane

Applies WIP and operation policy while preserving candidate identity.

### Authority plane

Binds the plan to exact policy content and execution root. Authority drift invalidates execution.

### Actuation plane

Executes only built-in operations. It cannot run arbitrary commands or make network calls. Path normalization occurs before mutation.

### Verification plane

Checks exact postconditions immediately after each mutation. A failed postcondition prevents receipt promotion.

### Evidence plane

Canonical JSON and BLAKE3 bind plan identity, intent identity, consequence, verification, sequence, and prior receipt.

### Replay plane

Validates the receipt chain and re-observes receipted world state. Replay does not rerun the original mutation.

### Projection plane

`ontology/tcps.ttl` plus `ggen.toml` manufactures generated contract projections. The ontology remains source authority.

## 3. Core objects

- WorkOrder
- Observation
- CandidateGraph
- Candidate
- AuthorityPolicy
- Plan
- Intent
- Consequence
- Verification
- Receipt
- Replay
- Refusal
- Standing

## 4. Core morphisms

```text
observe: WorkOrder → Observation | Refusal
construct: Observation → CandidateGraph | Refusal
select_authorize: CandidateGraph × Policy × Root → Plan | Refusal
actuate_verify_receipt: Plan × Policy × Root → Receipt* | Refusal
replay: Receipt* × Root → Replay
```

No morphism may inherit authority from an earlier object unless the exact authority digest is part of its input contract.

## 5. Trust boundaries

1. untrusted work order;
2. normalized observation;
3. admitted operation vocabulary;
4. policy authority;
5. authorized root;
6. actuation broker;
7. verified consequence;
8. receipt chain;
9. replay observation;
10. external production boundary.

## 6. Data architecture

Canonical runtime JSON is sorted, UTF-8, and separator-normalized before hashing. Receipts use BLAKE3-256. The bundled scalar BLAKE3 implementation exists to keep runtime execution dependency-free and auditable; optimized external implementations may be admitted later only behind equivalence tests.

RDF source uses PROV-O for entities/agents, DCTERMS for metadata, SKOS for controlled stage vocabulary, and ODRL for policy alignment.

## 7. Role projection architecture

The four interfaces are not four workflow engines. They are projections of one calculus:

```text
EVE    : human purpose → normalized O
WIZARD : O → reversible candidate graph
TELCO  : graph × policy → selected authorized plan
ROBOT  : plan × exact root → consequence × receipt
```

Language labels are presentation metadata; machine authority remains canonical JSON.

## 8. Security architecture

Least privilege is structural: observation and construction have no DO path; plan execution is restricted to built-in operations; policy digest and root identity are checked again at execution; traversal and irreversible mutation fail closed.

## 9. Resilience architecture

Each action is an independent stop-the-line boundary. Partial success is represented by the receipts already emitted; later actions do not retroactively certify earlier failures. Re-observation starts from durable artifacts and receipt history.

## 10. Enterprise deployment model

A large-enterprise deployment may wrap the local broker in customer-controlled identity, isolated workers, private networking, customer-managed keys, approved artifact stores, durable evidence stores, SIEM export, and external policy engines. Those deployment capabilities are not implied by the local CLI.

## 11. Verification architecture

Repository verification proceeds from cheapest high-information gates to execution:

```text
identity-zero scan
→ authority/schema/static consistency
→ byte compilation
→ unit/refusal tests
→ real CLI cycle
→ receipt verification
→ replay
→ deterministic offline bundle
→ ggen projection replay when toolchain available
```
