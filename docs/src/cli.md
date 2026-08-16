# CLI

## Initialize the control boundary

```bash
tcps init .
```

Initialization provisions `.tcps/authority.json` and the receipt ledger and returns `PARTIAL_ALIVE`. It is bootstrap/control-plane provisioning, not a claim that production work has been receipted.

## Install standard work

```bash
tcps pack install builtin:core-1979 --root .
```

The built-in pack carries the EVE/English, WIZARD/中文, TELCO/日本語, and ROBOT/한국어 prompt projections. Installation compiles to bounded work and crosses the normal receipt boundary.

## Pull a demand through the full line

```bash
tcps make work.json --root .
```

`make` performs the bounded cycle without bypassing its stages. `run` remains an equivalent full-cycle operator surface.

## Stage surfaces

```bash
tcps eve work.json --out .tcps/observation.json
tcps wizard .tcps/observation.json --out .tcps/graph.json
tcps telco .tcps/graph.json --authority .tcps/authority.json --root . --out .tcps/plan.json
tcps robot .tcps/plan.json --authority .tcps/authority.json --root .
```

EVE admits observation, WIZARD constructs reversible candidates, TELCO selects/binds authority, and ROBOT performs exact PREPARE/DO/VERIFY/final-receipt work. A downstream role does not inherit the upstream role's semantic freedom.

## Plant control

```bash
tcps standard
tcps kanban artifact "downstream needs artifact" --quantity 1
tcps wip
tcps andon
tcps metrics
tcps standing
tcps kaizen "stop reason" "proposed standard-work change"
```

These commands do not invent production state. WIP, Andon, metrics, and standing are evidence-derived. Kanban and Kaizen construct non-actuating control objects.

## Packs

```bash
tcps pack builtins
tcps pack validate ./my-pack.json
tcps pack install ./my-pack.json --root .
tcps pack list --root .
```

Pack kinds unify workflow, integration, preset, extension, bundle, and standard-work packaging. Missing dependency closure, unsafe paths, unknown kinds, and digest drift fail closed. Remote acquisition is not ambient in v1979.1.1.

## Replay and recovery

```bash
tcps replay --receipts .tcps/receipts.ndjson --root .
tcps recover --receipts .tcps/receipts.ndjson --root .
```

Replay proves the current world against the receipt chain. Recovery resolves an interrupted PREPARE/DO/final-receipt interval only from durable evidence; ambiguous state is `BLOCKED`.
