# Production Packs

TCPS collapses workflow, integration, preset, extension, bundle, and standard-work packaging into one typed **Pack** graph.

A pack is data:

```text
Pack = identity + version + kind + dependencies + bounded files + digest
```

Pack kinds are controlled vocabulary:

- `workflow`
- `integration`
- `preset`
- `extension`
- `bundle`
- `standard-work`

Different kinds may express different downstream intent, but they do not get different execution laws.

## Built-in CJK standard work

```bash
tcps pack builtins
```

The built-in `core-1979` pack contains four stratified prompt projections:

- EVE — English human-purpose admission
- WIZARD — 中文 reversible manufacture
- TELCO — 日本語 route, selection, and authority boundary
- ROBOT — 한국어 exact execution discipline

Language is a semantic interface boundary. Pack files do not grant DO authority.

## Install

```bash
tcps init .
tcps pack install builtin:core-1979 --root .
```

Installation is not a privileged copy operation. The pack compiler creates a `tcps.work.v1` work order containing only bounded `mkdir` and `write_text` intents. That work order passes through EVE, WIZARD, TELCO, PREPARE, ROBOT, verification, final receipt, and replay exactly like any other production work.

## Local manifests

```bash
tcps pack validate ./my-pack.json
tcps pack install ./my-pack.json --root .
```

A manifest has schema `tcps.pack.v1` and safe relative file paths. Absolute paths, traversal, unknown kinds, malformed dependencies, or digest drift are refused before DO.

Remote network acquisition is deliberately not ambient in v1979.1.1. A future remote transport must first become an admitted TELCO capability with its own authority, provenance, verifier, receipt, and supply-chain policy.

## Dependency closure

Pack dependencies name exact pack identities. Installation fails closed when a required pack is absent; dependencies are never downloaded implicitly.

## List

```bash
tcps pack list --root .
```

Installed manifests are revalidated from disk. A damaged manifest lowers pack-list standing to `BUILD_BROKEN` rather than being silently ignored.
