# Support model

A support case should include:

- TCPS version;
- exact repository or workspace identity;
- work-order digest;
- authority digest;
- plan digest when one exists;
- typed state/refusal code;
- receipt-chain head;
- replay result;
- exact command and exit code;
- environment/toolchain identity;
- sanitized logs that do not expose secrets.

Severity is consequence-based. A blocked production actuation, receipt corruption, or replay divergence in an admitted production path requires immediate stop-the-line handling. Documentation questions and unsupported capability requests do not inherit production severity automatically.
