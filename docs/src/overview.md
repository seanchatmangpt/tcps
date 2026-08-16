# Overview

TCPS v1979.1.1 treats code production as a controlled physical-style production system rather than an unconstrained conversation with a model.

The canonical cycle is:

```text
Observe → Admit → Model → Select → Authorize → Actuate → Verify → Receipt → Reobserve
```

The key distinction is authority. Observation can inform construction. Construction can enumerate possibilities. Selection can choose among them. None of those stages may mutate the world merely because a model or planner produced output.

Production begins only when an exact plan, exact policy digest, and exact root identity enter the bounded actuator. Production standing exists only after postcondition verification and receipt issuance.

This makes the process itself first-class data. The receipt chain is not reporting layered on top of production; it is part of the production contract.
