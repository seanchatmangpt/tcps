# Toyota Code Production System 1979 — generated contract

Version: `1979.1.1`

Production cycle:

`OBSERVE → ADMIT → MODEL → SELECT → AUTHORIZE → PREPARE → ACTUATE → VERIFY → RECEIPT → REOBSERVE`

Role projections:

- `EVE` — `en`
- `WIZARD` — `zh-CN`
- `TELCO` — `ja-JP`
- `ROBOT` — `ko-KR`

DfCM production law:

- maximize: `value,urgency,evidence`
- minimize: `risk,cost,cycle_time`
- bounded frontier: `64`
- selection: `deterministic-reversible`
- irreversible selections: `0`
- planner authority: `SELECT`
- planner actuation: `NONE`
- class order: `expedite,fixed_date,standard,debt`
- max expedite in row: `1`
- one-piece pull: `true`

This file is a projection. `ontology/tcps.ttl` remains the semantic source.
