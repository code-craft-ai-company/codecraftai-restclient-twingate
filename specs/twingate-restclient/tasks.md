# Implementation Plan — Twingate REST Client

## Aspects + Construction

- [ ] 1. Create `aspectstwingate.py` — `AspectsTwingate(AspectsRest)` + `DEFAULT_TWINGATE_ASPECTS` (includes `mutation_dependency_pause_seconds`)
- [ ] 2. Create `twingateclient.py` — `TwingateClient(RestClientBase)`
- [ ] 3. Constructor accepts `TwingateServiceAccountCredential`; derives endpoint URL from credential's network slug
- [ ] 4. Constructor rejects any other `BaseCredential` with `ConfigurationError`
- [ ] 5. Set Bearer header from credential's API token

## API Groups

- [ ] 6. `apigroups/resourcesgroup.py` — `list`, `iter`, `get`, `create`, `update`, `delete`
- [ ] 7. `apigroups/groupsgroup.py` — `list`, `iter`, `get`, `create`, `update`, `delete`
- [ ] 8. `apigroups/connectorsgroup.py` — `list`, `iter`, `get`, `create`, `generate_tokens`, `delete`
- [ ] 9. `apigroups/remotenetworksgroup.py` — `list`, `iter`, `get`, `create`, `update`, `delete`
- [ ] 10. `apigroups/devicesgroup.py` — `list`, `iter`, `get`, `delete`
- [ ] 11. Every method calls a generated builder from `queries/` or `mutations/`, POSTs through the base, parses into a generated `SchemaObject` DTO

## ACL Translator (Three-Phase Idempotent Apply)

- [ ] 12. `acltranslator/parser.py` — Tailscale-shaped flat-ACL JSON → intermediate Resources / Groups / Edges
- [ ] 13. `acltranslator/differ.py` — intermediate vs current → three-phase plan with set-diff
- [ ] 14. `acltranslator/executor.py` — plan → mutations with `mutation_dependency_pause_seconds` pauses
- [ ] 15. Malformed input raises `SemanticError` before any mutation runs
- [ ] 16. Second-apply idempotence: zero mutations on the second call

## IVPNControlPlane Conformance

- [ ] 17. `mint_authkey(*, reusable, ephemeral, tags, ttl_seconds, aspects)` — tag→connector name resolution, then `connectors.generate_tokens`
- [ ] 18. Single-tag enforcement (multi-tag → `SemanticError`)
- [ ] 19. `list_devices(*, aspects)` — `devices.list` adapter to `VPNDeviceRecord`
- [ ] 20. `delete_device(*, device_id, aspects)` — `devices.delete`
- [ ] 21. `apply_acl(*, acl_doc, aspects)` — invokes translator
- [ ] 22. `isinstance(client, IVPNControlPlane)` verified at runtime

## Tests

- [ ] 23. Example tests per api-group method (URL, GraphQL body, headers)
- [ ] 24. `IVPNControlPlane` isinstance test
- [ ] 25. `mint_authkey` tests: success, unresolved name, multi-tag rejection
- [ ] 26. `apply_acl` happy path test (small acl_doc → three phases)
- [ ] 27. `apply_acl` malformed-input test → `SemanticError`
- [ ] 28. Adapter tests: `VPNDeviceRecord` ↔ `TwingateDevice` round-trip
- [ ] 29. Property test: `apply_acl` is idempotent (hypothesis)
- [ ] 30. Property test: `apply_acl` is order-insensitive in input (hypothesis)
- [ ] 31. Property test: builder determinism end-to-end (hypothesis)

## M3 Shim

- [ ] 32. After this package is publishable, edit `automojo-interop/vpn/twingate/twingatecontrolplane.py` to re-export `TwingateClient as TwingateControlPlane` with a `DeprecationWarning` once per import path per process
