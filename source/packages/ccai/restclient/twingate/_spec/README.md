# `_spec/` — Twingate GraphQL Schema Snapshot

This directory is the home of the checked-in Twingate GraphQL introspection
result (`schema.json`) and its integrity hash (`schema.sha256`).

## Codegen status

Per the §9.2a decision rule in `PLAN-VPN-AND-CLOUD-PROVISIONING.md` and the
"Codegen Decision" section of the repository `AGENTS.md`: at package-authoring
time no live Twingate network + API token was available, so GraphQL
introspection could **not** be run. The typed DTOs, inputs, query builders and
mutation builders under `model/`, `inputs/`, `queries/` and `mutations/` were
**hand-authored** from the documented Twingate GraphQL surface (and validated
against the working M3 `TwingateControlPlane`).

`schema.json` here is a **representative hand-authored snapshot** covering the
type surface the client consumes (`Resource`, `Group`, `Connector`,
`RemoteNetwork`, `Device`, `ConnectorState`, `ProtocolsInput`). It is *not* a
full live introspection dump.

## Regenerating from a live network

A maintainer with a live Twingate network can produce the authoritative dump:

```
python -m ccai.restclient.twingate._codegen.import_schema \
    --network <slug> --token <api-token>
```

That rewrites `schema.json` + `schema.sha256` and the emitter
(`_codegen/emitter.py`) can then be used to validate or extend the hand-authored
modules.
