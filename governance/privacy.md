# Privacy model

TCPS work orders are engineering-control inputs, not a data lake.

The default schemas do not require personal data, secrets, credentials, customer content, telemetry payloads, or production datasets. Deployments should minimize work-order content to the facts needed for the production decision.

Enterprise operators shall define data classification, purpose, residency, retention, deletion, legal hold, evidence access, and subject-right handling for any environment that introduces regulated or personal information.

Receipt evidence should prefer content digests and bounded metadata over copying sensitive payloads.
