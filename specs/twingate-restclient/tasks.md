# Implementation Plan — Twingate REST Client

## Aspects + Construction

- [x] 1. Create `aspectstwingate.py` — `AspectsTwingate(AspectsRest)` + `DEFAULT_TWINGATE_ASPECTS` (includes `mutation_dependency_pause_seconds`)
- [x] 2. Create `twingateclient.py` — `TwingateClient(RestClientBase)`
- [x] 3. Constructor accepts `TwingateServiceAccountCredential`; derives endpoint URL from credential's network slug
- [x] 4. Constructor rejects any other `BaseCredential` with `ConfigurationError`
- [x] 5. Set Bearer header from credential's API token

## API Groups

- [x] 6. `apigroups/resourcesgroup.py` — `list`, `iter`, `get`, `create`, `update`, `delete`
- [x] 7. `apigroups/groupsgroup.py` — `list`, `iter`, `get`, `create`, `update`, `delete`
- [x] 8. `apigroups/connectorsgroup.py` — `list`, `iter`, `get`, `create`, `generate_tokens`, `delete`
- [x] 9. `apigroups/remotenetworksgroup.py` — `list`, `iter`, `get`, `create`, `update`, `delete`
- [x] 10. `apigroups/devicesgroup.py` — `list`, `iter`, `get`, `delete`
- [x] 11. Every method calls a generated builder from `queries/` or `mutations/`, POSTs through the base, parses into a generated `SchemaObject` DTO

## ACL Translator (Three-Phase Idempotent Apply)

- [x] 12. `acltranslator/parser.py` — Tailscale-shaped flat-ACL JSON → intermediate Resources / Groups / Edges
- [x] 13. `acltranslator/differ.py` — intermediate vs current → three-phase plan with set-diff
- [x] 14. `acltranslator/executor.py` — plan → mutations with `mutation_dependency_pause_seconds` pauses
- [x] 15. Malformed input raises `SemanticError` before any mutation runs
- [x] 16. Second-apply idempotence: zero mutations on the second call

## IVPNControlPlane Conformance

- [x] 17. `mint_authkey(*, reusable, ephemeral, tags, ttl_seconds, aspects)` — tag→connector name resolution, then `connectors.generate_tokens`
- [x] 18. Single-tag enforcement (multi-tag → `SemanticError`)
- [x] 19. `list_devices(*, aspects)` — `devices.list` adapter to `VPNDeviceRecord`
- [x] 20. `delete_device(*, device_id, aspects)` — `devices.delete`
- [x] 21. `apply_acl(*, acl_doc, aspects)` — invokes translator
- [x] 22. `isinstance(client, IVPNControlPlane)` verified at runtime

## Tests

- [x] 23. Example tests per api-group method (URL, GraphQL body, headers)
- [x] 24. `IVPNControlPlane` isinstance test
- [x] 25. `mint_authkey` tests: success, unresolved name, multi-tag rejection
- [x] 26. `apply_acl` happy path test (small acl_doc → three phases)
- [x] 27. `apply_acl` malformed-input test → `SemanticError`
- [x] 28. Adapter tests: `VPNDeviceRecord` ↔ `TwingateDevice` round-trip
- [x] 29. Property test: `apply_acl` is idempotent (hypothesis)
- [x] 30. Property test: `apply_acl` is order-insensitive in input (hypothesis)
- [x] 31. Property test: builder determinism end-to-end (hypothesis)

## M3 Shim

- [~] 32. After this package is publishable, edit `codecraftai-interop/vpn/twingate/twingatecontrolplane.py` to re-export `TwingateClient as TwingateControlPlane` with a `DeprecationWarning` once per import path per process
  - DEFERRED — out of scope for the M3b `codecraftai-restclient-twingate`
    implementation task. The shim edit touches the separate `codecraftai-interop`
    repository; the M3b milestone calls for it as a distinct step performed
    against that repo (IMPLEMENTATION-PLAN §1.18b / M3b). This task left
    untouched here so it is not silently marked complete.
