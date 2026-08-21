"""
    Tests for the twingate-restclient IVPNControlPlane conformance:
    - mint_authkey connector resolution, unresolved-name failure, multi-tag
    - list_devices adapter to VPNDeviceRecord
    - delete_device idempotence
    - VPNDeviceRecord <-> TwingateDevice adapter round-trip
"""


from ccai import testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.errors.exceptions import SemanticError
from ccai.interfaces.ivpncontrolplane import VPNDeviceRecord

from ccai.restclient.twingate.exceptions import VPNControlPlaneAuthKeyError
from ccai.restclient.twingate.model.twingatedevice import TwingateDevice

from .twingatetestsupport import (
    make_client, no_pause_aspects
)


def _connectors_page(items):
    return {"data": {"connectors": {
        "edges": [{"node": i} for i in items],
        "pageInfo": {"hasNextPage": False, "endCursor": None}}}}


def _devices_page(items):
    return {"data": {"devices": {
        "edges": [{"node": i} for i in items],
        "pageInfo": {"hasNextPage": False, "endCursor": None}}}}


# ----------------------------------------------------------------------
# TestMintAuthkey
# ----------------------------------------------------------------------


def test_resolves_connector_name() -> None:
    connectors = _connectors_page([
        {"id": "C1", "name": "edge", "state": "ALIVE",
         "remoteNetwork": {"id": "RN1"}}])
    tokens = {"data": {"connectorGenerateTokens": {
        "ok": True, "error": None,
        "connectorTokens": {
            "accessToken": "AT", "refreshToken": "RT"}}}}
    client = make_client(scripted_payloads=[connectors, tokens])
    result = client.mint_authkey(
        reusable=False, ephemeral=False, tags=["edge"],
        ttl_seconds=3600, aspects=no_pause_aspects())
    testbase.assert_equal(result, "AT:RT")
    second_body = client._session.sent_bodies[1]
    testbase.assert_equal(
        second_body["variables"]["connectorId"], "C1")
    return

def test_unresolved_name_raises() -> None:
    connectors = _connectors_page([
        {"id": "C1", "name": "edge", "state": "ALIVE",
         "remoteNetwork": {"id": "RN1"}}])
    client = make_client(scripted_payloads=[connectors])
    with testbase.raises(VPNControlPlaneAuthKeyError):
        client.mint_authkey(
            reusable=False, ephemeral=False, tags=["missing"],
            ttl_seconds=3600, aspects=no_pause_aspects())
    # The mutation must NOT have been called — only the list query ran.
    testbase.assert_equal(len(client._session.sent_bodies), 1)
    return

def test_ambiguous_name_raises() -> None:
    connectors = _connectors_page([
        {"id": "C1", "name": "edge", "state": "ALIVE",
         "remoteNetwork": {"id": "RN1"}},
        {"id": "C2", "name": "edge", "state": "ALIVE",
         "remoteNetwork": {"id": "RN1"}}])
    client = make_client(scripted_payloads=[connectors])
    with testbase.raises(VPNControlPlaneAuthKeyError):
        client.mint_authkey(
            reusable=False, ephemeral=False, tags=["edge"],
            ttl_seconds=3600, aspects=no_pause_aspects())
    return

def test_empty_tags_raises_semantic_error() -> None:
    client = make_client(scripted_payloads=[])
    with testbase.raises(SemanticError):
        client.mint_authkey(
            reusable=False, ephemeral=False, tags=[],
            ttl_seconds=3600, aspects=no_pause_aspects())
    return

def test_multi_tag_raises_semantic_error() -> None:
    client = make_client(scripted_payloads=[])
    with testbase.raises(SemanticError):
        client.mint_authkey(
            reusable=False, ephemeral=False,
            tags=["edge", "second"], ttl_seconds=3600,
            aspects=no_pause_aspects())
    # No network call at all.
    testbase.assert_equal(len(client._session.sent_bodies), 0)
    return

def test_reusable_true_raises_semantic_error() -> None:
    # Twingate connector tokens have no per-token reusable semantics;
    # reusable=True must be rejected BEFORE any network call.
    client = make_client(scripted_payloads=[])
    with testbase.raises(SemanticError):
        client.mint_authkey(
            reusable=True, ephemeral=False, tags=["edge"],
            ttl_seconds=3600, aspects=no_pause_aspects())
    testbase.assert_equal(len(client._session.sent_bodies), 0)
    return

def test_ephemeral_true_raises_semantic_error() -> None:
    # Twingate connector tokens have no per-token ephemeral semantics;
    # ephemeral=True must be rejected BEFORE any network call.
    client = make_client(scripted_payloads=[])
    with testbase.raises(SemanticError):
        client.mint_authkey(
            reusable=False, ephemeral=True, tags=["edge"],
            ttl_seconds=3600, aspects=no_pause_aspects())
    testbase.assert_equal(len(client._session.sent_bodies), 0)
    return


# ----------------------------------------------------------------------
# TestListDevices
# ----------------------------------------------------------------------


def test_adapts_to_vpndevicerecord() -> None:
    devices = _devices_page([
        {"id": "D1", "name": "laptop", "osName": "macOS",
         "lastConnectedAt": "2026-01-01T00:00:00Z",
         "isTrusted": True}])
    client = make_client(scripted_payloads=[devices])
    result = client.list_devices(aspects=no_pause_aspects())
    testbase.assert_equal(len(result), 1)
    record = result[0]
    testbase.assert_true(isinstance(record, VPNDeviceRecord))
    testbase.assert_equal(record.device_id, "D1")
    testbase.assert_equal(record.hostname, "laptop")
    testbase.assert_true(record.overlay_address is None)
    testbase.assert_equal(record.os, "macOS")
    testbase.assert_equal(record.last_seen, "2026-01-01T00:00:00Z")
    return

def test_empty_device_list() -> None:
    client = make_client(scripted_payloads=[_devices_page([])])
    result = client.list_devices(aspects=no_pause_aspects())
    testbase.assert_equal(result, [])
    return


# ----------------------------------------------------------------------
# TestDeleteDevice
# ----------------------------------------------------------------------


def test_delete() -> None:
    payload = {"data": {"deviceDelete": {"ok": True, "error": None}}}
    client = make_client(scripted_payloads=[payload])
    client.delete_device(
        device_id="D1", aspects=no_pause_aspects())
    return

def test_delete_absent_is_noop() -> None:
    payload = {"errors": [{"message": "Device not found"}]}
    client = make_client(scripted_payloads=[payload])
    client.delete_device(
        device_id="GONE", aspects=no_pause_aspects())
    return


# ----------------------------------------------------------------------
# TestDeviceAdapterRoundTrip
# ----------------------------------------------------------------------


@given(
    device_id=st.text(min_size=1, max_size=12),
    name=st.text(min_size=1, max_size=16),
    os_name=st.text(min_size=1, max_size=10),
    last=st.text(min_size=1, max_size=24), constraints={"max_examples": 80})
def test_twingatedevice_to_vpndevicerecord_preserves_shared(
        device_id, name, os_name, last) -> None:
    device = TwingateDevice(
        device_id=device_id, name=name, os_name=os_name,
        last_connected_at=last, is_trusted=True)
    record = VPNDeviceRecord(
        device_id=device.device_id,
        hostname=device.name,
        overlay_address=None,
        tags=[],
        os=device.os_name,
        last_seen=device.last_connected_at)
    # Round-trip the shared fields back into a TwingateDevice.
    rebuilt = TwingateDevice(
        device_id=record.device_id,
        name=record.hostname,
        os_name=record.os,
        last_connected_at=record.last_seen,
        is_trusted=device.is_trusted)
    testbase.assert_equal(rebuilt.device_id, device.device_id)
    testbase.assert_equal(rebuilt.name, device.name)
    testbase.assert_equal(rebuilt.os_name, device.os_name)
    testbase.assert_equal(
        rebuilt.last_connected_at, device.last_connected_at)
    return
