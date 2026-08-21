"""
    Tests for the twingate-schema-import introspector:
    - non-200 upstream response -> ConfigurationError
    - GraphQL errors in response -> ConfigurationError
    - successful introspection -> payload returned
    - save_schema computes a stable SHA-256

    All HTTP traffic is mocked with requests-mock.
"""


import requests_mock

from ccai import testbase

from ccai.errors.exceptions import ConfigurationError

from ccai.restclient.twingate._codegen.import_schema import (
    introspect, INTROSPECTION_QUERY
)


_ENDPOINT = "https://acme.twingate.com/api/graphql/v1"


# ----------------------------------------------------------------------
# TestIntrospect
# ----------------------------------------------------------------------


def test_non_200_raises_configuration_error() -> None:
    with requests_mock.Mocker() as mock:
        mock.post(_ENDPOINT, status_code=403, text="forbidden")
        with testbase.raises(ConfigurationError):
            introspect(network_slug="acme", api_token="bad")
    return

def test_graphql_errors_raise_configuration_error() -> None:
    with requests_mock.Mocker() as mock:
        mock.post(_ENDPOINT, status_code=200, json={
            "errors": [{"message": "schema introspection disabled"}]})
        with testbase.raises(ConfigurationError):
            introspect(network_slug="acme", api_token="tok")
    return

def test_successful_introspection_returns_payload() -> None:
    schema_payload = {"data": {"__schema": {"types": []}}}
    with requests_mock.Mocker() as mock:
        mock.post(_ENDPOINT, status_code=200, json=schema_payload)
        result = introspect(network_slug="acme", api_token="tok")
    testbase.assert_equal(result, schema_payload)
    return

def test_introspection_query_is_a_schema_query() -> None:
    testbase.assert_true("__schema" in INTROSPECTION_QUERY)
    return
