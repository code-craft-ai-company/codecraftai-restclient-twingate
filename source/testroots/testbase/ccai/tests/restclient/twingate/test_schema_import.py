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
import unittest

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


class TestGraphQLRequestBody(unittest.TestCase):

    def test_as_payload_includes_operation_name(self) -> None:
        body = GraphQLRequestBody(
            query="query Q { x }", variables={"a": 1},
            operation_name="Q")
        payload = body.as_payload()
        self.assertEqual(payload["query"], "query Q { x }")
        self.assertEqual(payload["variables"], {"a": 1})
        self.assertEqual(payload["operationName"], "Q")
        return

    def test_as_payload_omits_none_operation_name(self) -> None:
        body = GraphQLRequestBody(query="query { x }")
        payload = body.as_payload()
        self.assertNotIn("operationName", payload)
        return

    def test_frozen(self) -> None:
        body = GraphQLRequestBody(query="q")
        with self.assertRaises(Exception):
            body.query = "other"
        return


class TestTypemap(unittest.TestCase):

    def test_scalar_type_objects(self) -> None:
        import datetime
        self.assertIs(python_type_for_scalar(scalar_name="String"), str)
        self.assertIs(python_type_for_scalar(scalar_name="Int"), int)
        self.assertIs(python_type_for_scalar(scalar_name="Boolean"), bool)
        self.assertIs(python_type_for_scalar(scalar_name="ID"), str)
        self.assertIs(python_type_for_scalar(scalar_name="Float"), float)
        self.assertIs(
            python_type_for_scalar(scalar_name="DateTime"),
            datetime.datetime)
        return

    def test_scalar_typenames(self) -> None:
        self.assertEqual(
            python_typename_for_scalar(scalar_name="JSON"), "Dict[str, Any]")
        self.assertEqual(
            python_typename_for_scalar(scalar_name="DateTime"),
            "datetime.datetime")
        return

    def test_unknown_scalar_defaults_to_str(self) -> None:
        self.assertIs(python_type_for_scalar(scalar_name="Mystery"), str)
        return


class TestEmitter(unittest.TestCase):

    def _fixture_schema(self) -> dict:
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

    def test_emit_skips_internal_types(self) -> None:
        emitted = emit_schema_modules(schema=self._fixture_schema())
        self.assertIn("connectorstate.py", emitted)
        self.assertIn("resource.py", emitted)
        self.assertNotIn("__internaltype.py", emitted)
        return

    def test_emit_enum_golden(self) -> None:
        emitted = emit_schema_modules(schema=self._fixture_schema())
        enum_source = emitted["connectorstate.py"]
        self.assertIn("class ConnectorState(enum.Enum):", enum_source)
        self.assertIn('ALIVE = "ALIVE"', enum_source)
        self.assertIn('DEAD = "DEAD"', enum_source)
        self.assertIn("DO NOT EDIT", enum_source)
        return

    def test_emit_object_golden(self) -> None:
        emitted = emit_schema_modules(schema=self._fixture_schema())
        obj_source = emitted["resource.py"]
        self.assertIn("class Resource(SchemaObject):", obj_source)
        self.assertIn("id: str = Field('str', required=True)", obj_source)
        self.assertIn("name: str = Field('str', required=False)", obj_source)
        return

    def test_non_null_drops_optional(self) -> None:
        expr = resolve_type_expression(type_ref={
            "kind": "NON_NULL",
            "ofType": {"kind": "SCALAR", "name": "String"}})
        self.assertEqual(expr, "str")
        return

    def test_list_wraps(self) -> None:
        expr = resolve_type_expression(type_ref={
            "kind": "LIST",
            "ofType": {"kind": "SCALAR", "name": "ID"}})
        self.assertEqual(expr, "List[str]")
        return


class TestGeneratedDtoSmoke(unittest.TestCase):

    def test_dto_imports(self) -> None:
        for cls in (TwingateResource, TwingateGroup, TwingateConnector,
                    TwingateRemoteNetwork, TwingateDevice):
            self.assertTrue(hasattr(cls, "from_dict"))
            self.assertTrue(hasattr(cls, "to_dict"))
        return

    def test_enum_members_verbatim(self) -> None:
        self.assertEqual(ConnectorState.ALIVE.value, "ALIVE")
        self.assertEqual(
            ConnectorState.DEAD_NO_HEARTBEAT.value, "DEAD_NO_HEARTBEAT")
        return

    def test_input_object_smoke(self) -> None:
        proto = ResourceProtocolsInput(allow_icmp=False)
        self.assertEqual(proto.allow_icmp, False)
        return


class TestBuilderFixtures(unittest.TestCase):

    def test_build_resources_no_cursor(self) -> None:
        body = queries.build_resources(after=None)
        self.assertEqual(body.operation_name, "ListResources")
        self.assertEqual(body.variables, {})
        self.assertIn("resources(after: $after)", body.query)
        return

    def test_build_resources_with_cursor(self) -> None:
        body = queries.build_resources(after="CUR1")
        self.assertEqual(body.variables, {"after": "CUR1"})
        return

    def test_build_resourcecreate_fixture(self) -> None:
        body = mutations.build_resourcecreate(
            name="db", address="db.acme.internal", remote_network_id="RN1")
        self.assertEqual(body.operation_name, "ResourceCreate")
        self.assertEqual(body.variables, {
            "name": "db",
            "address": "db.acme.internal",
            "remoteNetworkId": "RN1",
        })
        return


# ----------------------------------------------------------------------
# Property tests (hypothesis)
# ----------------------------------------------------------------------


class TestSchemaImportProperties(unittest.TestCase):

    @given(st.builds(
        TwingateResource,
        resource_id=st.text(min_size=1, max_size=12),
        name=st.text(min_size=1, max_size=12),
        address=st.text(min_size=1, max_size=20),
        remote_network_id=st.text(max_size=8)), constraints={"max_examples": 80})
    def test_resource_roundtrip(self, resource: TwingateResource) -> None:
        rebuilt = TwingateResource.from_dict(resource.to_dict())
        self.assertEqual(rebuilt, resource)
        return

    @given(st.builds(
        TwingateConnector,
        connector_id=st.text(min_size=1, max_size=12),
        name=st.text(min_size=1, max_size=12),
        remote_network_id=st.text(max_size=8),
        state=st.text(max_size=10)), constraints={"max_examples": 80})
    def test_connector_roundtrip(self, conn: TwingateConnector) -> None:
        rebuilt = TwingateConnector.from_dict(conn.to_dict())
        self.assertEqual(rebuilt, conn)
        return

    @given(st.one_of(st.none(), st.text(min_size=1, max_size=24)), constraints={"max_examples": 120})
    def test_builder_determinism(self, cursor) -> None:
        first = queries.build_resources(after=cursor)
        second = queries.build_resources(after=cursor)
        self.assertEqual(first, second)
        first_bytes = json.dumps(
            first.as_payload(), sort_keys=True).encode("utf-8")
        second_bytes = json.dumps(
            second.as_payload(), sort_keys=True).encode("utf-8")
        self.assertEqual(first_bytes, second_bytes)
        return

    @given(
        name=st.text(min_size=1, max_size=20),
        address=st.text(min_size=1, max_size=20),
        rnid=st.one_of(st.none(), st.text(min_size=1, max_size=10)), constraints={"max_examples": 120})
    def test_none_kwargs_omitted_from_variables(
            self, name, address, rnid) -> None:
        body = mutations.build_connectorcreate(
            remote_network_id=address, name=rnid)
        if rnid is None:
            self.assertNotIn("name", body.variables)
        else:
            self.assertIn("name", body.variables)
        return


if __name__ == "__main__":
    unittest.main()
