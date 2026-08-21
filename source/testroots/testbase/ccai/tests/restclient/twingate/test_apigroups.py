"""
    Tests for the twingate-restclient api-group surface:
    - each api-group method: GraphQL body, operationName, variables
    - cursor-based iter walks all pages
    - construction + endpoint URL derivation
    - IVPNControlPlane isinstance conformance
"""

import json

from ccai import testbase

from ccai.errors.exceptions import ConfigurationError
from ccai.credentials.basiccredential import BasicCredential
from ccai.interfaces.ivpncontrolplane import IVPNControlPlane

from ccai.restclient.twingate.twingateclient import (
    TwingateClient, GRAPHQL_LEAF
)
from ccai.restclient.twingate.exceptions import (
    TwingateApiError, TwingateAuthError, TwingateNotFoundError,
    TwingateRateLimitError, TwingateServerError
)
from ccai.restclient.twingate.model import (
    TwingateResource, TwingateGroup, TwingateConnector,
    TwingateRemoteNetwork, TwingateDevice
)

from .twingatetestsupport import (
    make_client, make_credential, no_pause_aspects
)


def _edge(node: dict) -> dict:
    return {"node": node}


def _page(items, *, has_next=False, end_cursor=None):
    return {
        "edges": [_edge(i) for i in items],
        "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor},
    }


# ----------------------------------------------------------------------
# TestConstruction
# ----------------------------------------------------------------------


def test_endpoint_host_from_slug() -> None:
    client = TwingateClient(credential=make_credential())
    testbase.assert_equal(client.host, "acme.twingate.com")
    return

def test_host_override() -> None:
    client = TwingateClient(
        credential=make_credential(), host="localhost")
    testbase.assert_equal(client.host, "localhost")
    return

def test_rejects_none_credential() -> None:
    with testbase.raises(ConfigurationError):
        TwingateClient(credential=None)
    return

def test_rejects_wrong_credential() -> None:
    wrong = BasicCredential(
        identifier="b", categories=["basic"],
        username="u", password="p")
    with testbase.raises(ConfigurationError):
        TwingateClient(credential=wrong)
    return

def test_authenticate_sets_bearer_header() -> None:
    client = TwingateClient(credential=make_credential())
    client.authenticate()
    auth = client._session.headers["Authorization"]
    testbase.assert_equal(auth, "Bearer tg-svc-test-token")
    testbase.assert_equal(
        client._session.headers["X-Network-Slug"], "acme")
    return

def test_isinstance_ivpncontrolplane() -> None:
    client = TwingateClient(credential=make_credential())
    testbase.assert_true(isinstance(client, IVPNControlPlane))
    return

def test_graphql_leaf_versioned() -> None:
    testbase.assert_equal(GRAPHQL_LEAF, "/api/graphql/v1")
    return


# ----------------------------------------------------------------------
# TestResourcesGroup
# ----------------------------------------------------------------------


def test_resources_list() -> None:
    payload = {"data": {"resources": _page([
        {"id": "R1", "name": "db", "address": {"value": "db.local"},
         "remoteNetwork": {"id": "RN1"}},
    ])}}
    client = make_client(scripted_payloads=[payload])
    result = client.resources.list(aspects=no_pause_aspects())
    testbase.assert_equal(len(result), 1)
    testbase.assert_equal(result[0].resource_id, "R1")
    testbase.assert_equal(result[0].address, "db.local")
    body = client._session.sent_bodies[0]
    testbase.assert_equal(body["operationName"], "ListResources")
    return

def test_resources_iter_walks_all_pages() -> None:
    page_one = {"data": {"resources": _page(
        [{"id": "R1", "name": "a", "address": {"value": "a"},
          "remoteNetwork": {"id": "RN1"}}],
        has_next=True, end_cursor="CUR")}}
    page_two = {"data": {"resources": _page(
        [{"id": "R2", "name": "b", "address": {"value": "b"},
          "remoteNetwork": {"id": "RN1"}}])}}
    client = make_client(scripted_payloads=[page_one, page_two])
    result = list(client.resources.iter(aspects=no_pause_aspects()))
    testbase.assert_equal([r.resource_id for r in result], ["R1", "R2"])
    second_body = client._session.sent_bodies[1]
    testbase.assert_equal(second_body["variables"], {"after": "CUR"})
    return

def test_resources_get() -> None:
    payload = {"data": {"resource": {
        "id": "R1", "name": "db", "address": {"value": "db.local"},
        "remoteNetwork": {"id": "RN1"}}}}
    client = make_client(scripted_payloads=[payload])
    result = client.resources.get(
        resource_id="R1", aspects=no_pause_aspects())
    testbase.assert_equal(result.resource_id, "R1")
    return

def test_resources_get_missing_returns_none() -> None:
    client = make_client(scripted_payloads=[{"data": {"resource": None}}])
    result = client.resources.get(
        resource_id="MISSING", aspects=no_pause_aspects())
    testbase.assert_true(result is None)
    return

def test_resources_create() -> None:
    payload = {"data": {"resourceCreate": {
        "ok": True, "error": None,
        "entity": {"id": "R9", "name": "web",
                   "address": {"value": "web.local"},
                   "remoteNetwork": {"id": "RN1"}}}}}
    client = make_client(scripted_payloads=[payload])
    result = client.resources.create(
        name="web", address="web.local", remote_network_id="RN1",
        aspects=no_pause_aspects())
    testbase.assert_equal(result.resource_id, "R9")
    body = client._session.sent_bodies[0]
    testbase.assert_equal(body["operationName"], "ResourceCreate")
    testbase.assert_equal(body["variables"]["remoteNetworkId"], "RN1")
    return

def test_resources_update() -> None:
    payload = {"data": {"resourceUpdate": {
        "ok": True, "error": None,
        "entity": {"id": "R1", "name": "db",
                   "address": {"value": "new.local"},
                   "remoteNetwork": {"id": "RN1"}}}}}
    client = make_client(scripted_payloads=[payload])
    result = client.resources.update(
        resource_id="R1", address="new.local",
        aspects=no_pause_aspects())
    testbase.assert_equal(result.address, "new.local")
    return

def test_resources_delete() -> None:
    payload = {"data": {"resourceDelete": {"ok": True, "error": None}}}
    client = make_client(scripted_payloads=[payload])
    client.resources.delete(
        resource_id="R1", aspects=no_pause_aspects())
    body = client._session.sent_bodies[0]
    testbase.assert_equal(body["operationName"], "ResourceDelete")
    return


# ----------------------------------------------------------------------
# TestGroupsGroup
# ----------------------------------------------------------------------


def test_groups_list() -> None:
    payload = {"data": {"groups": _page([
        {"id": "G1", "name": "admins"}])}}
    client = make_client(scripted_payloads=[payload])
    result = client.groups.list(aspects=no_pause_aspects())
    testbase.assert_equal(result[0].group_id, "G1")
    return

def test_groups_iter_all_pages() -> None:
    page_one = {"data": {"groups": _page(
        [{"id": "G1", "name": "a"}], has_next=True, end_cursor="C")}}
    page_two = {"data": {"groups": _page([{"id": "G2", "name": "b"}])}}
    client = make_client(scripted_payloads=[page_one, page_two])
    result = list(client.groups.iter(aspects=no_pause_aspects()))
    testbase.assert_equal([g.group_id for g in result], ["G1", "G2"])
    return

def test_groups_create() -> None:
    payload = {"data": {"groupCreate": {
        "ok": True, "error": None,
        "entity": {"id": "G9", "name": "ops"}}}}
    client = make_client(scripted_payloads=[payload])
    result = client.groups.create(
        name="ops", aspects=no_pause_aspects())
    testbase.assert_equal(result.group_id, "G9")
    return

def test_groups_update() -> None:
    payload = {"data": {"groupUpdate": {
        "ok": True, "error": None,
        "entity": {"id": "G1", "name": "renamed"}}}}
    client = make_client(scripted_payloads=[payload])
    result = client.groups.update(
        group_id="G1", name="renamed", aspects=no_pause_aspects())
    testbase.assert_equal(result.name, "renamed")
    return

def test_groups_get() -> None:
    payload = {"data": {"group": {"id": "G1", "name": "admins"}}}
    client = make_client(scripted_payloads=[payload])
    result = client.groups.get(
        group_id="G1", aspects=no_pause_aspects())
    testbase.assert_equal(result.name, "admins")
    return

def test_groups_delete() -> None:
    payload = {"data": {"groupDelete": {"ok": True, "error": None}}}
    client = make_client(scripted_payloads=[payload])
    client.groups.delete(group_id="G1", aspects=no_pause_aspects())
    body = client._session.sent_bodies[0]
    testbase.assert_equal(body["operationName"], "GroupDelete")
    return


# ----------------------------------------------------------------------
# TestConnectorsGroup
# ----------------------------------------------------------------------


def test_connectors_list() -> None:
    payload = {"data": {"connectors": _page([
        {"id": "C1", "name": "edge", "state": "ALIVE",
         "remoteNetwork": {"id": "RN1", "name": "aws"}}])}}
    client = make_client(scripted_payloads=[payload])
    result = client.connectors.list(aspects=no_pause_aspects())
    testbase.assert_equal(result[0].connector_id, "C1")
    testbase.assert_equal(result[0].state, "ALIVE")
    return

def test_connectors_iter() -> None:
    page = {"data": {"connectors": _page([
        {"id": "C1", "name": "edge", "state": "ALIVE",
         "remoteNetwork": {"id": "RN1"}}])}}
    client = make_client(scripted_payloads=[page])
    result = list(client.connectors.iter(aspects=no_pause_aspects()))
    testbase.assert_equal(len(result), 1)
    return

def test_connectors_get() -> None:
    payload = {"data": {"connector": {
        "id": "C1", "name": "edge", "state": "ALIVE",
        "remoteNetwork": {"id": "RN1"}}}}
    client = make_client(scripted_payloads=[payload])
    result = client.connectors.get(
        connector_id="C1", aspects=no_pause_aspects())
    testbase.assert_equal(result.connector_id, "C1")
    return

def test_connectors_create() -> None:
    payload = {"data": {"connectorCreate": {
        "ok": True, "error": None,
        "entity": {"id": "C9", "name": "edge2", "state": "ALIVE",
                   "remoteNetwork": {"id": "RN1"}}}}}
    client = make_client(scripted_payloads=[payload])
    result = client.connectors.create(
        remote_network_id="RN1", name="edge2",
        aspects=no_pause_aspects())
    testbase.assert_equal(result.connector_id, "C9")
    return

def test_connectors_generate_tokens() -> None:
    payload = {"data": {"connectorGenerateTokens": {
        "ok": True, "error": None,
        "connectorTokens": {
            "accessToken": "AT", "refreshToken": "RT"}}}}
    client = make_client(scripted_payloads=[payload])
    tokens = client.connectors.generate_tokens(
        connector_id="C1", aspects=no_pause_aspects())
    testbase.assert_equal(tokens["access_token"], "AT")
    testbase.assert_equal(tokens["refresh_token"], "RT")
    return

def test_connectors_delete() -> None:
    payload = {"data": {"connectorDelete": {"ok": True, "error": None}}}
    client = make_client(scripted_payloads=[payload])
    client.connectors.delete(
        connector_id="C1", aspects=no_pause_aspects())
    return

def test_connectors_delete_not_found_is_idempotent() -> None:
    payload = {"data": {"connectorDelete": {
        "ok": False, "error": "Connector not found"}}}
    client = make_client(scripted_payloads=[payload])
    client.connectors.delete(
        connector_id="GONE", aspects=no_pause_aspects())
    return


# ----------------------------------------------------------------------
# TestRemoteNetworksGroup
# ----------------------------------------------------------------------


def test_remote_networks_list() -> None:
    payload = {"data": {"remoteNetworks": _page([
        {"id": "RN1", "name": "aws", "location": "AWS"}])}}
    client = make_client(scripted_payloads=[payload])
    result = client.remote_networks.list(aspects=no_pause_aspects())
    testbase.assert_equal(result[0].remote_network_id, "RN1")
    return

def test_remote_networks_iter() -> None:
    page = {"data": {"remoteNetworks": _page([
        {"id": "RN1", "name": "aws", "location": "AWS"}])}}
    client = make_client(scripted_payloads=[page])
    result = list(
        client.remote_networks.iter(aspects=no_pause_aspects()))
    testbase.assert_equal(len(result), 1)
    return

def test_remote_networks_get() -> None:
    payload = {"data": {"remoteNetwork": {
        "id": "RN1", "name": "aws", "location": "AWS"}}}
    client = make_client(scripted_payloads=[payload])
    result = client.remote_networks.get(
        remote_network_id="RN1", aspects=no_pause_aspects())
    testbase.assert_equal(result.name, "aws")
    return

def test_remote_networks_create() -> None:
    payload = {"data": {"remoteNetworkCreate": {
        "ok": True, "error": None,
        "entity": {"id": "RN9", "name": "gcp", "location": "GOOGLE"}}}}
    client = make_client(scripted_payloads=[payload])
    result = client.remote_networks.create(
        name="gcp", location="GOOGLE", aspects=no_pause_aspects())
    testbase.assert_equal(result.remote_network_id, "RN9")
    return

def test_remote_networks_update() -> None:
    payload = {"data": {"remoteNetworkUpdate": {
        "ok": True, "error": None,
        "entity": {"id": "RN1", "name": "renamed",
                   "location": "AWS"}}}}
    client = make_client(scripted_payloads=[payload])
    result = client.remote_networks.update(
        remote_network_id="RN1", name="renamed",
        aspects=no_pause_aspects())
    testbase.assert_equal(result.name, "renamed")
    return

def test_remote_networks_delete() -> None:
    payload = {"data": {"remoteNetworkDelete": {
        "ok": True, "error": None}}}
    client = make_client(scripted_payloads=[payload])
    client.remote_networks.delete(
        remote_network_id="RN1", aspects=no_pause_aspects())
    return


# ----------------------------------------------------------------------
# TestDevicesGroup
# ----------------------------------------------------------------------


def test_devices_list() -> None:
    payload = {"data": {"devices": _page([
        {"id": "D1", "name": "laptop", "osName": "macOS",
         "lastConnectedAt": "2026-01-01T00:00:00Z",
         "isTrusted": True}])}}
    client = make_client(scripted_payloads=[payload])
    result = client.devices.list(aspects=no_pause_aspects())
    testbase.assert_equal(result[0].device_id, "D1")
    testbase.assert_equal(result[0].os_name, "macOS")
    return

def test_devices_iter() -> None:
    page = {"data": {"devices": _page([
        {"id": "D1", "name": "laptop", "osName": "Linux",
         "lastConnectedAt": "", "isTrusted": False}])}}
    client = make_client(scripted_payloads=[page])
    result = list(client.devices.iter(aspects=no_pause_aspects()))
    testbase.assert_equal(len(result), 1)
    return

def test_devices_get() -> None:
    payload = {"data": {"device": {
        "id": "D1", "name": "laptop", "osName": "Linux",
        "lastConnectedAt": "", "isTrusted": True}}}
    client = make_client(scripted_payloads=[payload])
    result = client.devices.get(
        device_id="D1", aspects=no_pause_aspects())
    testbase.assert_equal(result.device_id, "D1")
    return

def test_devices_delete() -> None:
    payload = {"data": {"deviceDelete": {"ok": True, "error": None}}}
    client = make_client(scripted_payloads=[payload])
    client.devices.delete(
        device_id="D1", aspects=no_pause_aspects())
    body = client._session.sent_bodies[0]
    testbase.assert_equal(body["operationName"], "DeviceDelete")
    return

def test_devices_delete_not_found_idempotent() -> None:
    payload = {"errors": [{"message": "device does not exist"}]}
    client = make_client(scripted_payloads=[payload])
    client.devices.delete(
        device_id="GONE", aspects=no_pause_aspects())
    return


# ----------------------------------------------------------------------
# TestHttpStatusReclassification
# ----------------------------------------------------------------------

"""
    Verifies that ``graphql_call`` reclassifies a non-2xx HTTP response
    into the typed :class:`TwingateApiError` hierarchy, preserving the
    status code and response body.
"""

def test_403_raises_auth_error() -> None:
    client = make_client(
        scripted_payloads=[{"errors": [{"message": "forbidden"}]}],
        status_code=403)
    with testbase.raises(TwingateAuthError) as ctx:
        client.connectors.list(aspects=no_pause_aspects())
    testbase.assert_equal(ctx.exception.status_code, 403)
    testbase.assert_true("forbidden" in ctx.exception.response_body)
    testbase.assert_true(isinstance(ctx.exception, TwingateApiError))
    return

def test_401_raises_auth_error() -> None:
    client = make_client(
        scripted_payloads=[{"errors": [{"message": "unauthorized"}]}],
        status_code=401)
    with testbase.raises(TwingateAuthError) as ctx:
        client.connectors.list(aspects=no_pause_aspects())
    testbase.assert_equal(ctx.exception.status_code, 401)
    return

def test_404_raises_not_found_error() -> None:
    client = make_client(
        scripted_payloads=[{"errors": [{"message": "missing"}]}],
        status_code=404)
    with testbase.raises(TwingateNotFoundError) as ctx:
        client.connectors.list(aspects=no_pause_aspects())
    testbase.assert_equal(ctx.exception.status_code, 404)
    return

def test_429_raises_rate_limit_error() -> None:
    client = make_client(
        scripted_payloads=[{"errors": [{"message": "slow down"}]}],
        status_code=429)
    with testbase.raises(TwingateRateLimitError) as ctx:
        client.connectors.list(aspects=no_pause_aspects())
    testbase.assert_equal(ctx.exception.status_code, 429)
    return

def test_500_raises_server_error() -> None:
    client = make_client(
        scripted_payloads=[{"errors": [{"message": "boom"}]}],
        status_code=500)
    with testbase.raises(TwingateServerError) as ctx:
        client.connectors.list(aspects=no_pause_aspects())
    testbase.assert_equal(ctx.exception.status_code, 500)
    testbase.assert_true("boom" in ctx.exception.response_body)
    return
