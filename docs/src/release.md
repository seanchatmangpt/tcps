# Release and Standing

TCPS uses bounded standing rather than a single green badge.

- `UNKNOWN`: not enough exact evidence.
- `PARTIAL_ALIVE`: some required boundaries executed, crown not proven.
- `ALIVE`: exact admitted subject executed and verified at the declared boundary.
- `BLOCKED`: required capability or toolchain was unavailable.
- `BUILD_BROKEN`: admitted boundary executed and failed.
- `UNSUPPORTED`: capability is outside the implementation topology.
- `REFUSED:<CODE>`: authority or law explicitly denied the transition.

Repository release admission and external production standing are different. A release candidate can satisfy every repository verifier and still have `UNKNOWN` external production standing until a real deployment produces its own evidence.

Likewise, control mappings do not establish certification. Independent assessment remains a separate evidence source.
