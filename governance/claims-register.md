# Claims register

| Claim | Maximum current ceiling | Required evidence to raise ceiling |
|---|---|---|
| TCPS product and architecture are documented | `DOCUMENTED` | repository verification |
| Runtime source is syntactically valid | `COMPILED` after byte compilation | exact command receipt |
| BLAKE3 implementation matches declared vectors | `TESTED` after test execution | exact test receipt |
| Bounded CLI production cycle works | `TESTED` after real CLI execution | exact subject + receipts |
| Receipt replay detects drift | `TESTED` after mutation/replay witness | exact replay result |
| ggen projections are current | `GENERATED` only after exact ggen sync | projection receipt + zero diff |
| Release candidate is admitted | `REFERENCE_CONFORMANT` after full release theorem | verifier report |
| Fortune 5 deployment exists | `UNKNOWN` | named external deployment evidence |
| Regulatory or audit certification exists | `REFUSED:UNSUPPORTED_CLAIM` | independent certification evidence |

No document may promote a claim above this table without updating the authority and verifier that justifies the change.
