# Requirements

## Introduction

The `twingate-schema-import` feature obtains the Twingate GraphQL schema via standard
GraphQL introspection (since Twingate does not publish an OpenAPI document) and
converts it into typed Python query/mutation builders and DTOs under
`source/packages/ccai/restclient/twingate/`.

The introspection is run against a real Twingate network by the maintainer; the
checked-in introspection result is the source of truth for what the client can call.

This feature does not author the client class — that is the `twingate-restclient`
feature's responsibility. This feature only produces the typed inputs/outputs.

---

## Requirements

### Requirement 1: Run GraphQL Introspection

**User Story:** As a maintainer, I want a single command that introspects a live
Twingate network and dumps the schema, so that re-syncing is mechanical.

#### Acceptance Criteria

1. WHEN the maintainer invokes the import script with a network slug + API token
   THE SYSTEM SHALL POST a GraphQL introspection query to
   `https://<slug>.twingate.com/api/graphql/v1` and save the response under
   `source/packages/ccai/restclient/twingate/_spec/schema.json`.
2. WHEN the upstream response is non-200 or contains GraphQL `errors` THE SYSTEM
   SHALL raise `ConfigurationError` with the network slug, status, and error payload
   and SHALL NOT overwrite the checked-in schema.
3. THE SYSTEM SHALL compute SHA-256 of the introspection JSON and save it to
   `_spec/schema.sha256` so manual edits can be detected.

### Requirement 2: Generate Typed DTOs

**User Story:** As a client author, I want every Twingate GraphQL `OBJECT` type to be
a Python `SchemaObject` class, so that responses parse into typed instances.

#### Acceptance Criteria

1. WHEN a type in the introspection result has `kind=OBJECT` and is not an internal
   `__*` type THE SYSTEM SHALL emit one Python `SchemaObject` subclass under `model/`.
2. THE SYSTEM SHALL map GraphQL scalar types: `String` → `str`, `Int` → `int`,
   `Boolean` → `bool`, `ID` → `str`, `Float` → `float`, plus typed wrappers for known
   Twingate scalars (`DateTime` → `datetime.datetime`, `JSON` → `Dict[str, Any]`).
3. WHEN a field type is `NON_NULL(<inner>)` THE SYSTEM SHALL emit the field without
   `Optional[...]`. WHEN a field type is `LIST(<inner>)` THE SYSTEM SHALL emit
   `List[<inner>]`.
4. WHERE a type is an `ENUM` THE SYSTEM SHALL emit a Python `enum.Enum` subclass with
   members matching the GraphQL enum values verbatim.

### Requirement 3: Generate Typed Query/Mutation Builders

**User Story:** As a client author, I want each top-level query and mutation in the
schema to be callable as a typed Python function that constructs the GraphQL body,
so that I don't write GraphQL strings by hand.

#### Acceptance Criteria

1. WHEN a top-level field exists on `Query` or `Mutation` THE SYSTEM SHALL emit a
   builder function `build_<field_name>(**typed_kwargs) -> GraphQLRequestBody` under
   `queries/` or `mutations/` respectively.
2. THE SYSTEM SHALL type-hint every argument using the rules from Requirement 2.
3. THE SYSTEM SHALL select every scalar field of the return type by default, plus
   any sub-objects requested via an optional `fields=` parameter.
4. THE SYSTEM SHALL emit a deterministic GraphQL body — sorted argument keys, stable
   whitespace — so identical inputs produce byte-identical bodies.

### Requirement 4: Round-Trip Property

**User Story:** As a maintainer, I want a runnable proof that the generator does not
lose information.

#### Acceptance Criteria

1. THE SYSTEM SHALL include a hypothesis property test asserting
   `from_dict(to_dict(x)) == x` for any populated instance of any generated `SchemaObject`.
2. THE SYSTEM SHALL include a property test asserting `build_<field_name>` is
   deterministic — identical kwargs produce byte-identical GraphQL bodies.
