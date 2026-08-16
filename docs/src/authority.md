# Authority

Authority is explicit data, not ambient process privilege.

`tcps.authority.v1` contains:

- authority identity;
- allowed roots;
- allowed operations;
- WIP limit;
- irreversible-operation policy.

The entire authority document is canonicalized and hashed. TELCO binds that digest into the plan. ROBOT recomputes the digest before actuation. Editing authority after planning therefore invalidates the plan rather than silently broadening it.

Authority is also root-specific. A plan manufactured for one filesystem root cannot be replayed as an execution permit for another root.

Large-enterprise deployments can replace the local authority-file provisioning mechanism with approved identity and policy infrastructure without changing the core law: the exact authority consumed by SELECT must equal the exact authority consumed by DO.
