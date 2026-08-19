# Enterprise Operating Model

Fortune-5-grade is an engineering decision surface, not a marketing adjective.

The repository therefore separates and documents:

- product intent;
- architecture;
- security;
- privacy;
- resilience;
- change management;
- operations;
- support;
- supply chain and procurement;
- evidence and replay;
- release admission;
- external production standing;
- retirement authority.

The local CLI intentionally does not contain every enterprise connector. Identity providers, deployment brokers, private networking, HSM/KMS, SIEM, artifact registries, CMDB, ticketing, legal hold, and external evidence stores belong behind explicit adapters and authority boundaries.

Adding an adapter is not a reason to grant observers or planners ambient execution rights. The adapter must still consume an admitted intent and return an observed, independently verifiable consequence suitable for a receipt.
