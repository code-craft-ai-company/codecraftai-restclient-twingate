# Requirements

## Introduction

The `twingate-restclient` feature is the public face of the
`automojo-restclient-twingate` package: a `RestClientBase` subclass that POSTs
GraphQL queries and mutations to the Twingate Admin API. The package consumes the
generated builders + DTOs from `twingate-schema-import`. It implements the
`IVPNControlPlane` Protocol from `automojo-interfaces` so consumers can substitute
it transparently, with the asymmetry that Twingate's RBAC model is not flat-ACL —
`apply_acl(...)` performs an idempotent three-phase translation.

---

## Requirements

### Requirement 1: Construct from Credential

**User Story:** As a consumer, I want to construct the client with a typed
credential, so that auth is a closed problem inside the client.

#### Acceptance Criteria

1. WHEN the consumer constructs `TwingateClient(host=..., credential=<TwingateServiceAccountCredential>)` THE SYSTEM SHALL accept the credential and use the API token as a Bearer header.
2. IF the credential is any other `BaseCredential` subclass THEN THE SYSTEM SHALL raise `ConfigurationError` at construction time.
3. THE SYSTEM SHALL derive the GraphQL endpoint URL from the credential's network slug.

### Requirement 2: IVPNControlPlane Conformance

#### Acceptance Criteria

1. THE SYSTEM SHALL implement every method on `IVPNControlPlane`: `mint_authkey`, `list_devices`, `delete_device`, `apply_acl`.
2. THE SYSTEM SHALL pass `isinstance(client, IVPNControlPlane)` via the runtime-checkable Protocol.
3. THE SYSTEM SHALL document — in the class docstring and per-method docstring — every place where Twingate's surface diverges from the protocol's Tailscale-shaped intent.

### Requirement 3: API Group Surface

**User Story:** As a consumer, I want every Twingate domain exposed as a typed Python method on a logical group.

#### Acceptance Criteria

1. THE SYSTEM SHALL expose groups: `resources`, `groups`, `connectors`, `remote_networks`, `devices`.
2. THE SYSTEM SHALL implement each group as a `RestApiGroup` subclass whose methods consume the generated query/mutation builders from `twingate-schema-import`.
3. THE SYSTEM SHALL accept `aspects: AspectsRest = DEFAULT_TWINGATE_ASPECTS` on every behaviour-bearing call.
4. WHERE the upstream query is paginated THE SYSTEM SHALL expose both `list(...)` (first page) and `iter(...)` (walks all pages via cursor-based paging on the base).

### Requirement 4: Idempotent Three-Phase apply_acl

**User Story:** As a consumer used to Tailscale-shaped flat-ACL JSON, I want
`apply_acl(acl_doc)` to converge to the requested state on Twingate, so that I
don't write provider-specific logic at the call site.

#### Acceptance Criteria

1. WHEN `apply_acl` is invoked THE SYSTEM SHALL parse `acl_doc` as a Tailscale-shaped flat-ACL JSON document.
2. THE SYSTEM SHALL translate the parsed document into a three-phase plan: (a) resources to ensure/update/delete, (b) groups to ensure/update/delete, (c) resource-group assignments to ensure/delete.
3. THE SYSTEM SHALL execute the three phases in order, pausing `mutation_dependency_pause_seconds` between phases.
4. WHEN the same `acl_doc` is applied twice THE SYSTEM SHALL produce zero mutations on the second call (idempotence).
5. IF the parsed document is malformed THEN THE SYSTEM SHALL raise `SemanticError` with the malformation detail and SHALL NOT execute any mutation.
6. THE SYSTEM SHALL document in the docstring that Twingate has no flat-ACL primitive and that this method is a translation, not a faithful representation.

### Requirement 5: Connector-Name → Connector-ID Resolution for mint_authkey

**User Story:** As a consumer used to Tailscale's `mint_authkey(tags=[...])` call,
I want to pass a tag (name) and have it work on Twingate.

#### Acceptance Criteria

1. THE SYSTEM SHALL treat `tags[0]` as the connector name when minting a Twingate connector token.
2. WHEN the connector name resolves uniquely against `connectors.list()` THE SYSTEM SHALL call `connectorGenerateTokens(connectorId=<resolved-id>)`.
3. IF the connector name does not resolve THEN THE SYSTEM SHALL raise an error naming the missing connector and SHALL NOT call the mutation.
4. IF multiple `tags` are provided THEN THE SYSTEM SHALL raise `SemanticError` since Twingate connector tokens are scoped to a single connector.
