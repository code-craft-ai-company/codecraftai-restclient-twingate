# Implementation Plan — Twingate Schema Import

## Hand-Authored Foundation

- [ ] 1. Create `graphqlrequestbody.py` — `GraphQLRequestBody(query, variables, operation_name)` frozen dataclass
- [ ] 2. Create `_codegen/typemap.py` — GraphQL scalar → Python type with `DateTime` → `datetime`, `JSON` → `Dict[str, Any]`

## Introspector

- [ ] 3. Create `_codegen/import_schema.py` with `--network` + `--token` argparse surface
- [ ] 4. POST the canonical GraphQL introspection query; capture full `__schema` payload
- [ ] 5. On non-200 or `errors` present, raise `ConfigurationError` and do not overwrite `_spec/schema.json`
- [ ] 6. Compute SHA-256 of the response; save to `_spec/schema.sha256`

## Emitter

- [ ] 7. `_codegen/emitter.py` — walks `_schema.types`
- [ ] 8. Emit OBJECT types under `model/` as `SchemaObject` subclasses
- [ ] 9. Emit ENUM types under `model/` as `enum.Enum` subclasses with members verbatim
- [ ] 10. Emit INPUT_OBJECT types under `inputs/` as `SchemaObject` subclasses
- [ ] 11. Emit `Query` top-level fields under `queries/build_<f>.py`
- [ ] 12. Emit `Mutation` top-level fields under `mutations/build_<f>.py`
- [ ] 13. Field selection: by default select every scalar of the return type; accept optional `fields=` for sub-objects
- [ ] 14. Deterministic output — sorted args, stable whitespace, no timestamps
- [ ] 15. Emit `__init__.py` re-exports in every generated directory

## Generated Output Wiring

- [ ] 16. Run the importer against a real Twingate network; check in `_spec/schema.json` + `_spec/schema.sha256`
- [ ] 17. Verify every generated module imports cleanly

## Tests

- [ ] 18. Fixture-based emitter test (small introspection JSON → golden output diff)
- [ ] 19. Import smoke test for every generated class/function
- [ ] 20. Hand-authored builder fixture: `build_resources(after=None)` produces a specific GraphQL body string
- [ ] 21. Property test: `from_dict(to_dict(x)) == x` for any populated generated `SchemaObject` (hypothesis)
- [ ] 22. Property test: builder determinism — `build_<f>(**kw)` twice with equal kwargs produces byte-identical body (hypothesis)
- [ ] 23. Property test: `None` kwargs are omitted from `variables` (hypothesis)

## Documentation

- [ ] 24. Document regen flow in README
- [ ] 25. `DO NOT EDIT` header in every generated file with regen command
