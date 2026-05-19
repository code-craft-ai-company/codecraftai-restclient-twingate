# Design

## Overview

`twingate-schema-import` is a maintainer-facing import script plus generated output.
The script lives at `source/packages/automojo/restclient/twingate/_codegen/import_schema.py`
and is invoked by hand against a real Twingate network when the upstream schema
changes.

Generated output is **checked in**. CI does not regenerate.

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│ Maintainer                                                         │
│   $ python -m automojo.restclient.twingate._codegen.import_schema \│
│       --network <slug> --token <api-token>                         │
│                                                                    │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │ Introspector                                              │    │
│   │   POST https://<slug>.twingate.com/api/graphql/v1         │    │
│   │   body: { query: "{ __schema { types {...} ... } }" }     │    │
│   │   → schema.json under _spec/                              │    │
│   └──────────────────────────────────────────────────────────┘    │
│             │                                                      │
│   ┌─────────▼──────────────────────────────────────────────────┐  │
│   │ Emitter — walks _schema.types                               │  │
│   │   for OBJECT kinds   → model/<name>.py (SchemaObject)       │  │
│   │   for ENUM kinds     → model/<name>.py (enum.Enum)          │  │
│   │   for INPUT_OBJECT   → inputs/<name>.py (SchemaObject)      │  │
│   │   for top-level Query fields    → queries/build_<f>.py      │  │
│   │   for top-level Mutation fields → mutations/build_<f>.py    │  │
│   └─────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

## Data Model

A query builder returns a `GraphQLRequestBody` dataclass:

```python
@dataclass(frozen=True)
class GraphQLRequestBody:
    query: str
    variables: Dict[str, Any]
    operation_name: Optional[str]
```

The HTTP layer (in `tailscale-restclient`'s sibling repo design) POSTs this with
`{"query": ..., "variables": ..., "operationName": ...}` as the JSON body.

Builders use `variables` (not query-string interpolation) so values are properly
typed and safe.

## Module Layout

```
source/packages/automojo/restclient/twingate/
  _spec/
    schema.json
    schema.sha256
  _codegen/
    __init__.py
    import_schema.py
    emitter.py
    typemap.py
  model/                  # OBJECT and ENUM types (generated)
    __init__.py
    twingateresource.py
    twingategroup.py
    twingateconnector.py
    twingateremotenetwork.py
    twingatedevice.py
    ...
  inputs/                 # INPUT_OBJECT types (generated)
    __init__.py
    ...
  queries/                # builders for top-level Query fields (generated)
    __init__.py
    build_resources.py
    build_groups.py
    ...
  mutations/              # builders for top-level Mutation fields (generated)
    __init__.py
    build_resourcecreate.py
    build_connectorgeneratetokens.py
    ...
  graphqlrequestbody.py   # the dataclass (hand-authored)
```

## See Also

- [twingate-restclient](../twingate-restclient/design.md)
- `automojo-restclient-base` — `SchemaObject`, `SchemaField`

## Testing Strategy

**Example-based tests:**
- Fixture-based emitter test (small introspection JSON → golden generated files).
- Smoke-import every generated module.
- Build a representative query/mutation; assert the GraphQL body matches a hand-
  authored fixture.

**Property tests (hypothesis):**
- For any populated instance of any generated `SchemaObject`, `from_dict(to_dict(x)) == x`.
- For any builder function with valid typed kwargs, `build_<f>(**kw)` is deterministic
  — running it twice with `==`-equal kwargs produces byte-identical `GraphQLRequestBody`.
- Variable name escaping: any kwarg whose value is `None` does not appear in `variables`.
