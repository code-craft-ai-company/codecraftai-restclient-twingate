"""
    Tests for the twingate-schema-import feature:
    - GraphQLRequestBody dataclass + None-omission
    - typemap scalar resolution
    - emitter fixture-based golden output
    - generated DTO smoke imports + round-trip
    - builder determinism

    All hypothesis property tests run inside this unittest harness.
"""

import json

from ccai import testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.restclient.twingate.graphqlrequestbody import GraphQLRequestBody
from ccai.restclient.twingate._codegen.typemap import (
    python_type_for_scalar, python_typename_for_scalar
)
from ccai.restclient.twingate._codegen.emitter import (
    emit_schema_modules, resolve_type_expression
)
from ccai.restclient.twingate import queries, mutations
from ccai.restclient.twingate.model import (
    TwingateResource, TwingateGroup, TwingateConnector,
    TwingateRemoteNetwork, TwingateDevice, ConnectorState
)
from ccai.restclient.twingate.inputs import ResourceProtocolsInput


# ----------------------------------------------------------------------
# TestGraphQLRequestBody
# ----------------------------------------------------------------------


def test_as_payload_includes_operation_name() -> None:
    body = GraphQLRequestBody(
        query="query Q { x }", variables={"a": 1},
        operation_name="Q")
    payload = body.as_payload()
    testbase.assert_equal(payload["query"], "query Q { x }")
    testbase.assert_equal(payload["variables"], {"a": 1})
    testbase.assert_equal(payload["operationName"], "Q")
    return

def test_as_payload_omits_none_operation_name() -> None:
    body = GraphQLRequestBody(query="query { x }")
    payload = body.as_payload()
    testbase.assert_true("operationName" not in payload)
    return

def test_frozen() -> None:
    body = GraphQLRequestBody(query="q")
    with testbase.raises(Exception):
        body.query = "other"
    return


# ----------------------------------------------------------------------
# TestTypemap
# ----------------------------------------------------------------------


def test_scalar_type_objects() -> None:
    import datetime
    testbase.assert_true(python_type_for_scalar(scalar_name="String") is str)
    testbase.assert_true(python_type_for_scalar(scalar_name="Int") is int)
    testbase.assert_true(python_type_for_scalar(scalar_name="Boolean") is bool)
    testbase.assert_true(python_type_for_scalar(scalar_name="ID") is str)
    testbase.assert_true(python_type_for_scalar(scalar_name="Float") is float)
    testbase.assert_true(python_type_for_scalar(scalar_name="DateTime") is datetime.datetime)
    return

def test_scalar_typenames() -> None:
    testbase.assert_equal(
        python_typename_for_scalar(scalar_name="JSON"), "Dict[str, Any]")
    testbase.assert_equal(
        python_typename_for_scalar(scalar_name="DateTime"),
        "datetime.datetime")
    return

def test_unknown_scalar_defaults_to_str() -> None:
    testbase.assert_true(python_type_for_scalar(scalar_name="Mystery") is str)
    return


# ----------------------------------------------------------------------
# TestEmitter
# ----------------------------------------------------------------------


def _fixture_schema() -> dict:
    rtnval = {
        "types": [
            {"kind": "ENUM", "name": "ConnectorState",
             "enumValues": [{"name": "ALIVE"}, {"name": "DEAD"}]},
            {"kind": "OBJECT", "name": "Resource", "fields": [
                {"name": "id", "type": {
                    "kind": "NON_NULL", "ofType": {
                        "kind": "SCALAR", "name": "ID"}}},
                {"name": "name", "type": {
                    "kind": "SCALAR", "name": "String"}},
            ]},
            {"kind": "OBJECT", "name": "__InternalType", "fields": []},
        ]
    }
    return rtnval

def test_emit_skips_internal_types() -> None:
    emitted = emit_schema_modules(schema=_fixture_schema())
    testbase.assert_true("connectorstate.py" in emitted)
    testbase.assert_true("resource.py" in emitted)
    testbase.assert_true("__internaltype.py" not in emitted)
    return

def test_emit_enum_golden() -> None:
    emitted = emit_schema_modules(schema=_fixture_schema())
    enum_source = emitted["connectorstate.py"]
    testbase.assert_true("class ConnectorState(enum.Enum):" in enum_source)
    testbase.assert_true('ALIVE = "ALIVE"' in enum_source)
    testbase.assert_true('DEAD = "DEAD"' in enum_source)
    testbase.assert_true("DO NOT EDIT" in enum_source)
    return

def test_emit_object_golden() -> None:
    emitted = emit_schema_modules(schema=_fixture_schema())
    obj_source = emitted["resource.py"]
    testbase.assert_true("class Resource(SchemaObject):" in obj_source)
    testbase.assert_true("id: str = Field('str', required=True)" in obj_source)
    testbase.assert_true("name: str = Field('str', required=False)" in obj_source)
    return

def test_non_null_drops_optional() -> None:
    expr = resolve_type_expression(type_ref={
        "kind": "NON_NULL",
        "ofType": {"kind": "SCALAR", "name": "String"}})
    testbase.assert_equal(expr, "str")
    return

def test_list_wraps() -> None:
    expr = resolve_type_expression(type_ref={
        "kind": "LIST",
        "ofType": {"kind": "SCALAR", "name": "ID"}})
    testbase.assert_equal(expr, "List[str]")
    return


# ----------------------------------------------------------------------
# TestGeneratedDtoSmoke
# ----------------------------------------------------------------------


def test_dto_imports() -> None:
    for cls in (TwingateResource, TwingateGroup, TwingateConnector,
                TwingateRemoteNetwork, TwingateDevice):
        testbase.assert_true(hasattr(cls, "from_dict"))
        testbase.assert_true(hasattr(cls, "to_dict"))
    return

def test_enum_members_verbatim() -> None:
    testbase.assert_equal(ConnectorState.ALIVE.value, "ALIVE")
    testbase.assert_equal(
        ConnectorState.DEAD_NO_HEARTBEAT.value, "DEAD_NO_HEARTBEAT")
    return

def test_input_object_smoke() -> None:
    proto = ResourceProtocolsInput(allow_icmp=False)
    testbase.assert_equal(proto.allow_icmp, False)
    return


# ----------------------------------------------------------------------
# TestBuilderFixtures
# ----------------------------------------------------------------------


def test_build_resources_no_cursor() -> None:
    body = queries.build_resources(after=None)
    testbase.assert_equal(body.operation_name, "ListResources")
    testbase.assert_equal(body.variables, {})
    testbase.assert_true("resources(after: $after)" in body.query)
    return

def test_build_resources_with_cursor() -> None:
    body = queries.build_resources(after="CUR1")
    testbase.assert_equal(body.variables, {"after": "CUR1"})
    return

def test_build_resourcecreate_fixture() -> None:
    body = mutations.build_resourcecreate(
        name="db", address="db.acme.internal", remote_network_id="RN1")
    testbase.assert_equal(body.operation_name, "ResourceCreate")
    testbase.assert_equal(body.variables, {
        "name": "db",
        "address": "db.acme.internal",
        "remoteNetworkId": "RN1",
    })
    return


# ----------------------------------------------------------------------
# Property tests (hypothesis)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# TestSchemaImportProperties
# ----------------------------------------------------------------------


@given(st.builds(
    TwingateResource,
    resource_id=st.text(min_size=1, max_size=12),
    name=st.text(min_size=1, max_size=12),
    address=st.text(min_size=1, max_size=20),
    remote_network_id=st.text(max_size=8)), constraints={"max_examples": 80})
def test_resource_roundtrip(resource: TwingateResource) -> None:
    rebuilt = TwingateResource.from_dict(resource.to_dict())
    testbase.assert_equal(rebuilt, resource)
    return

@given(st.builds(
    TwingateConnector,
    connector_id=st.text(min_size=1, max_size=12),
    name=st.text(min_size=1, max_size=12),
    remote_network_id=st.text(max_size=8),
    state=st.text(max_size=10)), constraints={"max_examples": 80})
def test_connector_roundtrip(conn: TwingateConnector) -> None:
    rebuilt = TwingateConnector.from_dict(conn.to_dict())
    testbase.assert_equal(rebuilt, conn)
    return

@given(st.one_of(st.none(), st.text(min_size=1, max_size=24)), constraints={"max_examples": 120})
def test_builder_determinism(cursor) -> None:
    first = queries.build_resources(after=cursor)
    second = queries.build_resources(after=cursor)
    testbase.assert_equal(first, second)
    first_bytes = json.dumps(
        first.as_payload(), sort_keys=True).encode("utf-8")
    second_bytes = json.dumps(
        second.as_payload(), sort_keys=True).encode("utf-8")
    testbase.assert_equal(first_bytes, second_bytes)
    return

@given(
    name=st.text(min_size=1, max_size=20),
    address=st.text(min_size=1, max_size=20),
    rnid=st.one_of(st.none(), st.text(min_size=1, max_size=10)), constraints={"max_examples": 120})
def test_none_kwargs_omitted_from_variables(
        name, address, rnid) -> None:
    body = mutations.build_connectorcreate(
        remote_network_id=address, name=rnid)
    if rnid is None:
        testbase.assert_true("name" not in body.variables)
    else:
        testbase.assert_true("name" in body.variables)
    return
