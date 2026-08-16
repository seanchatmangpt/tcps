# Architecture Requirements Document — TCPS v1979.1.1

## 1. Architecture style

TCPS is a projectional production calculus with a small, closed execution broker.

```text
parse → observe → admit/refuse → model → construct candidates
→ select → authorize → PREPARE → actuate → verify
→ final receipt → reobserve/recover → standing
```

Construction is reversible. Actuation is consequential. Standing is evidence-derived.

## 2. Logical planes

### Observation plane

Consumes `tcps.work.v1` and emits normalized observation with source digest. Observation alone has no authority.

### Modeling plane

Converts requested actions into a candidate graph. Unsupported operations are typed topology failures; they are never silently rewritten.

### Selection plane

Applies WIP and operation policy while preserving candidate identity. Selection is not DO.

### Authority plane

Binds the plan to exact policy content and execution root. Authority drift or root drift invalidates DO.

### PREPARE plane

Before mutation, the exact global sequence, predecessor receipt, subject, authority, intent, plan, root, operation, before-state, and expected post-state are canonicalized into a BLAKE3 pre-receipt and made durable.

### Actuation plane

Executes only built-in operations. It cannot run arbitrary commands or make ambient network calls. Each action mutates only its declared target; missing parents and symlink aliases fail closed.

### Verification plane

Makes declared mutation state durable, re-observes it, and checks an exact post-state. A failed postcondition prevents final receipt promotion and leaves recovery evidence.

### Evidence plane

Canonical JSON and BLAKE3 bind prepared intent, consequence, verification, global sequence, and predecessor edges. One ledger has one writer.

### Replay and recovery plane

Replay validates historical chain/transition continuity and compares the world against the latest lawful post-state per target. Recovery resolves an interrupted PREPARE/DO/final-receipt interval only when durable evidence and current state prove one resolution.

### Plant-control plane

Standard work, Kanban, WIP, Andon, metrics, standing, and Kaizen are derived or constructed control objects. They do not receive ambient DO authority.

### Pack plane

`tcps.pack.v1` unifies workflow, integration, preset, extension, bundle, and standard-work packaging. A pack compiles into an ordinary `tcps.work.v1` graph and therefore crosses exactly the same authority and receipt boundaries as code work.

### Projection plane

`ontology/tcps.ttl` plus `ggen.toml` manufactures generated contract projections. The ontology is semantic authority and explicitly includes PREPARE in the ten-stage cycle.

## 3. Core objects

- WorkOrder
- Observation
- CandidateGraph
- Candidate
- AuthorityPolicy
- Plan
- PreReceipt
- Consequence
- Verification
- FinalReceipt
- Recovery
- Replay
- Kanban
- Andon
- Metrics
- KaizenProposal
- Pack
- Refusal
- Standing

## 4. Core morphisms

```text
observe: WorkOrder → Observation | Refusal
construct: Observation → CandidateGraph | Refusal
select_authorize: CandidateGraph × Policy × Root → Plan | Refusal
prepare: Plan × World → PreReceipt | Refusal
actuate_verify_receipt: PreReceipt × Plan × Policy × Root → FinalReceipt* | Refusal
recover: PreReceipt × FinalReceipt* × World → Recovery
replay: FinalReceipt* × World → Standing
pack_compile: Pack → WorkOrder | Refusal
```

No morphism inherits authority from an earlier object unless the exact authority digest is part of its input contract.

## 5. Trust boundaries

1. untrusted work/pack/control input;
2. normalized observation;
3. admitted operation vocabulary;
4. policy authority;
5. authorized root;
6. durable pre-receipt;
7. closed actuation broker;
8. verified consequence;
9. durable final receipt chain;
10. replay/recovery observation;
11. external production boundary.

## 6. Data architecture

Canonical runtime JSON is sorted, UTF-8, and separator-normalized before hashing. Receipts use BLAKE3-256. The bundled scalar implementation keeps runtime execution dependency-free and is validated against official block/chunk/tree boundary vectors.

RDF source uses PROV-O for entities/agents, DCTERMS for metadata, SKOS for controlled stage vocabulary, and ODRL for policy alignment.

## 7. Role projection architecture

The four language interfaces are projections of one calculus:

```text
EVE    / English : human purpose → admitted observation
WIZARD / 中文    : admitted observation → reversible candidate graph
TELCO  / 日本語  : graph × policy → selected authorized plan
ROBOT  / 한국어  : plan × durable PREPARE → exact consequence × final receipt
```

Machine authority remains canonical typed data. Semantic freedom decreases downstream.

## 8. Security architecture

Least privilege is structural: observation and construction have no DO path; execution is restricted to built-in operations; policy digest and root identity are checked at the execution boundary; absolute/dot traversal, symlink aliases, implicit parent mutation, recursive deletion, malformed authority, malformed work, and concurrent ledger writers fail closed.

The local runtime assumes the authorized workspace is operated inside an appropriate OS/process isolation boundary. Hostile concurrent mutation by processes outside that boundary is an external deployment threat and must be controlled by the enterprise worker sandbox.

## 9. Resilience architecture

Durability order is:

```text
fsync(pre-receipt)
< durable declared mutation
< exact re-observation
< fsync(final receipt)
< clear pending recovery
```

An interruption can therefore be classified as before-state, expected post-state, already-finalized, or ambiguous. Ambiguity blocks. Sequence continues across plans.

## 10. Plant and Pack architecture

The plant is pull-oriented: Kanban expresses downstream demand; WIP exposes unresolved production inventory; Andon exposes abnormal state; Kaizen constructs improvement candidates without applying them. Packs are portable production parts rather than privileged plugins. Their file effects are compiled into ordinary work orders, preserving one execution law across the system.

## 11. Enterprise deployment model

A large-enterprise deployment may wrap the local broker in customer-controlled identity, isolated workers, private networking, customer-managed keys, approved artifact stores, durable evidence stores, SIEM export, external policy engines, and controlled network transports. Those deployment capabilities are not implied by the local CLI.

## 12. Verification architecture

Repository verification proceeds from cheap high-information gates to exact execution:

```text
identity-zero scan
→ semantic-source/generated-contract consistency
→ authority/schema/static consistency
→ byte compilation
→ unit/refusal/cryptographic boundary tests
→ plant and pack tests
→ crash-window fault injection
→ real CLI make cycle
→ receipt verification
→ replay/recovery
→ deterministic offline bundle
→ exact ggen projection replay + zero diff
→ exact-head hosted CI
```
