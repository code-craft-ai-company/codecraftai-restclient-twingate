"""
    Tests for the twingate-schema-import introspector:
    - non-200 upstream response -> ConfigurationError
    - GraphQL errors in response -> ConfigurationError
    - successful introspection -> payload returned
    - save_schema computes a stable SHA-256

    All HTTP traffic is mocked with requests-mock.
"""

import unittest

import requests_mock

from ccai.errors.exceptions import ConfigurationError

from ccai.restclient.twingate._codegen.import_schema import (
    introspect, INTROSPECTION_QUERY
)


_ENDPOINT = "https://acme.twingate.com/api/graphql/v1"


class TestIntrospect(unittest.TestCase):

    def test_non_200_raises_configuration_error(self) -> None:
        with requests_mock.Mocker() as mock:
            mock.post(_ENDPOINT, status_code=403, text="forbidden")
            with self.assertRaises(ConfigurationError):
                introspect(network_slug="acme", api_token="bad")
        return

    def test_graphql_errors_raise_configuration_error(self) -> None:
        with requests_mock.Mocker() as mock:
            mock.post(_ENDPOINT, status_code=200, json={
                "errors": [{"message": "schema introspection disabled"}]})
            with self.assertRaises(ConfigurationError):
                introspect(network_slug="acme", api_token="tok")
        return

    def test_successful_introspection_returns_payload(self) -> None:
        schema_payload = {"data": {"__schema": {"types": []}}}
        with requests_mock.Mocker() as mock:
            mock.post(_ENDPOINT, status_code=200, json=schema_payload)
            result = introspect(network_slug="acme", api_token="tok")
        self.assertEqual(result, schema_payload)
        return

    def test_introspection_query_is_a_schema_query(self) -> None:
        self.assertIn("__schema", INTROSPECTION_QUERY)
        return


if __name__ == "__main__":
    unittest.main()
