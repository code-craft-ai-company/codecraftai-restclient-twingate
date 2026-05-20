"""
    .. module:: devicesgroup
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains the :class:`DevicesGroup` api group
                   wrapping the Twingate ``devices`` GraphQL surface.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os

from typing import Any, Dict, Iterator, List, Optional

from automojo.restclient.base.restapigroup import RestApiGroup

from automojo.restclient.twingate.aspectstwingate import (
    AspectsTwingate, DEFAULT_TWINGATE_ASPECTS
)
from automojo.restclient.twingate.apigroups.graphqlsupport import (
    require_query_data, require_mutation_result, errors_indicate_not_found,
    is_not_found_text
)
from automojo.restclient.twingate.exceptions import VPNControlPlaneMutationError
from automojo.restclient.twingate.model.twingatedevice import TwingateDevice
from automojo.restclient.twingate.queries.build_devices import build_devices
from automojo.restclient.twingate.queries.build_node import build_device
from automojo.restclient.twingate.mutations.build_device_mutations import (
    build_devicedelete
)


def _device_from_node(*, node: Dict[str, Any]) -> TwingateDevice:
    """
        Project a GraphQL ``Device`` node dictionary into a
        :class:`TwingateDevice`.

        :param node: The GraphQL ``Device`` node dictionary.

        :returns: A :class:`TwingateDevice` instance.
    """
    rtnval = TwingateDevice(
        device_id=node.get("id", ""),
        name=node.get("name", "") or "",
        os_name=node.get("osName", "") or "",
        last_connected_at=node.get("lastConnectedAt", "") or "",
        is_trusted=node.get("isTrusted", False),
    )
    return rtnval


class DevicesGroup(RestApiGroup):
    """
        Api group wrapping the Twingate ``devices`` GraphQL surface —
        ``list``, ``iter``, ``get`` and ``delete``.

        Twingate ``Device`` nodes are the trusted-client registrations on a
        network. They are read-only apart from delete; there is no device
        create or update mutation.
    """

    def list(self, *, after: Optional[str] = None,
             aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> List[TwingateDevice]:
        """
            List the first page of devices.

            :param after: Optional cursor token for the next page.
            :param aspects: Behaviour control for the call.

            :returns: A list of :class:`TwingateDevice` records.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        request_body = build_devices(after=after)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        data = require_query_data(payload=payload, operation="devices")

        results = _extract_device_page(data=data)[0]
        rtnval = results
        return rtnval

    def iter(self, *,
             aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> Iterator[TwingateDevice]:
        """
            Iterate every device across all pages using cursor-based
            paging.

            :param aspects: Behaviour control for the call.

            :returns: An iterator over :class:`TwingateDevice` records.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        cursor: Optional[str] = None
        while True:
            request_body = build_devices(after=cursor)
            payload = self.client.graphql_call(
                body=request_body, aspects=aspects)
            data = require_query_data(payload=payload, operation="devices")

            page_items, next_cursor = _extract_device_page(data=data)
            for item in page_items:
                yield item

            if next_cursor is None:
                break
            cursor = next_cursor
        return

    def get(self, *, device_id: str,
            aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> Optional[TwingateDevice]:
        """
            Fetch a single device by identifier.

            :param device_id: Provider-assigned device identifier.
            :param aspects: Behaviour control for the call.

            :returns: The :class:`TwingateDevice`, or ``None`` when no
                device with the supplied identifier exists.

            :raises: :class:`VPNControlPlaneQueryError`.
        """
        request_body = build_device(device_id=device_id)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)
        data = require_query_data(payload=payload, operation="device")

        node = data.get("device")
        if node is None:
            rtnval: Optional[TwingateDevice] = None
            return rtnval

        rtnval = _device_from_node(node=node)
        return rtnval

    def delete(self, *, device_id: str,
               aspects: AspectsTwingate = DEFAULT_TWINGATE_ASPECTS) -> None:
        """
            Delete a device by identifier. Treats a not-found result as
            success so the call is idempotent.

            :param device_id: Provider-assigned device identifier.
            :param aspects: Behaviour control for the call.

            :returns: ``None``.

            :raises: :class:`VPNControlPlaneMutationError`.
        """
        if device_id is None or len(device_id) == 0:
            err_msg_lines = [
                "DevicesGroup.delete requires a non-empty 'device_id'.",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneMutationError(err_msg)

        request_body = build_devicedelete(device_id=device_id)
        payload = self.client.graphql_call(body=request_body, aspects=aspects)

        errors = payload.get("errors")
        if errors is not None and len(errors) > 0:
            if errors_indicate_not_found(errors=errors):
                return None
            err_msg_lines = [
                "Twingate deviceDelete returned top-level GraphQL errors.",
                f"DEVICE_ID: {device_id}",
                f"ERRORS: {errors}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneMutationError(
                err_msg, response_body=str(payload))

        data = payload.get("data")
        if data is None:
            err_msg_lines = [
                "Twingate deviceDelete returned no 'data' payload.",
                f"PAYLOAD: {payload}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneMutationError(
                err_msg, response_body=str(payload))

        result = data.get("deviceDelete")
        if result is None:
            err_msg_lines = [
                "Twingate deviceDelete returned no result object.",
                f"PAYLOAD: {payload}",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise VPNControlPlaneMutationError(
                err_msg, response_body=str(payload))

        if result.get("ok") is True:
            return None

        error_text = result.get("error")
        if error_text is not None and is_not_found_text(text=error_text):
            return None

        err_msg_lines = [
            "Twingate deviceDelete reported ok=False.",
            f"DEVICE_ID: {device_id}",
            f"ERROR: {error_text}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise VPNControlPlaneMutationError(err_msg, response_body=str(payload))


def _extract_device_page(*, data: Dict[str, Any]) -> tuple:
    """
        Extract one page of devices and the next cursor from a ``devices``
        query ``data`` block.

        :param data: The ``data`` block from a ``devices`` query.

        :returns: A two-tuple ``(items, next_cursor)``.
    """
    block = data.get("devices")
    if block is None:
        rtnval = ([], None)
        return rtnval

    edges = block.get("edges")
    if edges is None:
        edges = []

    results: List[TwingateDevice] = []
    for edge in edges:
        node = edge.get("node")
        if node is None:
            continue
        results.append(_device_from_node(node=node))

    next_cursor: Optional[str] = None
    page_info = block.get("pageInfo")
    if page_info is not None:
        has_next = page_info.get("hasNextPage", False)
        if has_next is True:
            next_cursor = page_info.get("endCursor")

    rtnval = (results, next_cursor)
    return rtnval


__all__ = ["DevicesGroup"]
